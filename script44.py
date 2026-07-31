import os
import time
import base64
import io
import fitz  # PyMuPDF
from PIL import Image
from flask import Flask, Blueprint, render_template_string, request, jsonify, send_file

# ==========================================
# INITIALIZE FLASK APP & BLUEPRINT
# ==========================================
app = Flask(__name__)
script44_bp = Blueprint('script44', __name__)
COMPANY_BRAND = os.environ.get('COMPANY_NAME', 'Data Mining Terminal')

# In-Memory Cache Store for PDF sessions
SESSION_CACHE = {}

class PurePythonPDFEngine:
    """
    Handles PDF rendering, page extractions, line-by-line text editable masking,
    and vector-level saving operations using PyMuPDF (fitz).
    """
    def __init__(self, pdf_bytes):
        self.doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    def get_page_count(self):
        return len(self.doc)

    def render_page_image(self, page_idx, zoom=1.25):
        if page_idx < 0 or page_idx >= len(self.doc):
            return None
        page = self.doc[page_idx]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to Base64 PNG
        img_bytes = pix.tobytes("png")
        encoded_img = base64.b64encode(img_bytes).decode('utf-8')
        
        return {
            "image": f"data:image/png;base64,{encoded_img}",
            "width": pix.width,
            "height": pix.height
        }

    def extract_editable_lines(self, page_idx):
        if page_idx < 0 or page_idx >= len(self.doc):
            return []
        
        page = self.doc[page_idx]
        text_page = page.get_text("dict")
        extracted_items = []

        for block in text_page.get("blocks", []):
            if "lines" not in block:
                continue

            for line in block["lines"]:
                line_text = ""
                min_x0, min_y0 = float("inf"), float("inf")
                max_x1, max_y1 = float("-inf"), float("-inf")
                font_sizes = []

                # Merge all spans inside a line into ONE single string & bounding box
                for span in line["spans"]:
                    txt = span["text"]
                    if not txt:
                        continue
                    line_text += txt
                    bbox = span["bbox"]
                    min_x0 = min(min_x0, bbox[0])
                    min_y0 = min(min_y0, bbox[1])
                    max_x1 = max(max_x1, bbox[2])
                    max_y1 = max(max_y1, bbox[3])
                    font_sizes.append(span["size"])

                line_text = line_text.strip()
                if line_text and min_x0 < float("inf"):
                    pdf_rect = [min_x0, min_y0, max_x1, max_y1]
                    avg_font_size = sum(font_sizes) / len(font_sizes)
                    
                    extracted_items.append({
                        "pdf_rect": pdf_rect,
                        "text": line_text,
                        "font_size": avg_font_size
                    })

        return extracted_items

    def apply_edits_and_save(self, page_idx, edits_data):
        page = self.doc[page_idx]

        for item in edits_data:
            orig_rect = item["pdf_rect"]
            new_text = item["text"]
            font_size = item["font_size"]

            # Erase original vector background line
            rect_obj = fitz.Rect(
                orig_rect[0] - 1,
                orig_rect[1] - 1,
                orig_rect[2] + 4,
                orig_rect[3] + 1
            )
            page.draw_rect(rect_obj, color=(1, 1, 1), fill=(1, 1, 1))

            # Insert updated text
            if new_text.strip():
                insert_point = fitz.Point(orig_rect[0], orig_rect[3] - 1)
                page.insert_text(
                    insert_point,
                    new_text,
                    fontsize=font_size,
                    color=(0, 0, 0)
                )

        output_buffer = io.BytesIO()
        self.doc.save(output_buffer)
        output_buffer.seek(0)
        return output_buffer


# ==========================================
# BLUEPRINT & FLASK ROUTES
# ==========================================
@script44_bp.route('/')
def index():
    return render_template_string(HTML_WORKSPACE, company=COMPANY_BRAND)


@script44_bp.route('/api/upload', methods=['POST'])
def upload_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No PDF file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "Empty filename"}), 400

        pdf_bytes = file.read()
        engine = PurePythonPDFEngine(pdf_bytes)
        
        session_id = f"PDF_{int(time.time() * 1000)}"
        SESSION_CACHE[session_id] = engine

        return jsonify({
            "success": True,
            "session_id": session_id,
            "filename": file.filename,
            "total_pages": engine.get_page_count()
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@script44_bp.route('/api/render', methods=['POST'])
def render_page():
    try:
        payload = request.get_json() or {}
        session_id = payload.get('session_id')
        page_idx = payload.get('page_idx', 0)
        zoom = payload.get('zoom', 1.25)

        if session_id not in SESSION_CACHE:
            return jsonify({"success": False, "error": "Session expired or invalid"}), 404

        engine = SESSION_CACHE[session_id]
        page_data = engine.render_page_image(page_idx, zoom)

        return jsonify({
            "success": True,
            "page_data": page_data
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@script44_bp.route('/api/extract_text', methods=['POST'])
def extract_text():
    try:
        payload = request.get_json() or {}
        session_id = payload.get('session_id')
        page_idx = payload.get('page_idx', 0)

        if session_id not in SESSION_CACHE:
            return jsonify({"success": False, "error": "Session expired or invalid"}), 404

        engine = SESSION_CACHE[session_id]
        editable_items = engine.extract_editable_lines(page_idx)

        return jsonify({
            "success": True,
            "items": editable_items,
            "count": len(editable_items)
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@script44_bp.route('/api/export', methods=['POST'])
def export_pdf():
    try:
        payload = request.get_json() or {}
        session_id = payload.get('session_id')
        page_idx = payload.get('page_idx', 0)
        edits_data = payload.get('edits', [])

        if session_id not in SESSION_CACHE:
            return jsonify({"success": False, "error": "Session expired or invalid"}), 404

        engine = SESSION_CACHE[session_id]
        pdf_stream = engine.apply_edits_and_save(page_idx, edits_data)

        return send_file(
            pdf_stream,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="edited_output.pdf"
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==========================================
# FRONTEND UI TEMPLATE (HTML5/TAILWIND/JS)
# ==========================================
HTML_WORKSPACE = """
<!DOCTYPE html>
<html lang="en" id="themeRoot" class="theme-dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company }} | Script 44 Pure Python PDF Desktop Editor</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-main: #0f172a;
            --bg-card: #1e293b;
            --bg-header: #020617;
            --border-color: #334155;
            --text-title: #f8fafc;
            --text-muted: #94a3b8;
        }
        body {
            background-color: var(--bg-main);
            color: var(--text-title);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            user-select: none;
        }
        .canvas-container {
            position: relative;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            background-color: #ffffff;
            display: inline-block;
        }
        .text-overlay-input {
            position: absolute;
            background: #ffffff;
            color: #000000;
            border: 1px dashed transparent;
            outline: none;
            padding: 0px 2px;
            box-sizing: border-box;
            z-index: 10;
        }
        .text-overlay-input:focus, .text-overlay-input.selected {
            border-color: #38bdf8;
            box-shadow: 0 0 0 1px #38bdf8;
        }
    </style>
</head>
<body class="antialiased min-h-screen flex flex-col">

    <!-- Top Header -->
    <header class="bg-[#020617] border-b border-[#1e293b] px-6 py-3 flex justify-between items-center z-50">
        <div class="flex items-center gap-3">
            <div class="p-2 bg-indigo-600 rounded-lg text-white shadow-md">
                <i class="fa-solid fa-file-pdf text-lg"></i>
            </div>
            <div>
                <h1 class="font-bold text-sm tracking-wide text-white">Pure Python Desktop PDF Editor</h1>
                <span class="text-[10px] block text-sky-400 font-mono">SCRIPT 44 RESPONSIVE ENGINE</span>
            </div>
        </div>
        <div class="text-xs text-slate-400 font-mono" id="statusLbl">
            Status: No PDF Loaded
        </div>
    </header>

    <!-- Responsive Toolbar -->
    <div class="bg-[#1e293b] border-b border-[#334155] px-4 py-2 flex flex-wrap items-center justify-between gap-3 z-40">
        <div class="flex items-center gap-2">
            <input type="file" id="fileInput" accept="application/pdf" class="hidden" onchange="uploadPDFFile(event)">
            <button onclick="document.getElementById('fileInput').click()" class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded text-xs transition flex items-center gap-1.5 cursor-pointer">
                <i class="fa-solid fa-folder-open"></i> Open PDF
            </button>

            <button id="btnExtract" onclick="makeTextEditable()" disabled class="px-3 py-1.5 bg-slate-700 opacity-50 text-white font-bold rounded text-xs transition flex items-center gap-1.5">
                <i class="fa-solid fa-pen-to-square"></i> Make Text Editable
            </button>

            <button id="btnAddText" onclick="addNewText()" disabled class="px-3 py-1.5 bg-slate-700 opacity-50 text-white font-bold rounded text-xs transition flex items-center gap-1.5">
                <i class="fa-solid fa-plus"></i> Click-to-Add Text
            </button>

            <button id="btnDelete" onclick="deleteSelected()" disabled class="px-3 py-1.5 bg-red-900/60 opacity-50 text-white font-bold rounded text-xs transition flex items-center gap-1.5">
                <i class="fa-solid fa-trash"></i> Delete Selected
            </button>
        </div>

        <!-- Page Controls -->
        <div class="flex items-center gap-2">
            <button id="btnPrev" onclick="prevPage()" disabled class="px-2.5 py-1 bg-slate-700 text-white rounded text-xs">◀ Prev</button>
            <span id="pageLbl" class="text-xs font-mono px-2 text-white">0/0</span>
            <button id="btnNext" onclick="nextPage()" disabled class="px-2.5 py-1 bg-slate-700 text-white rounded text-xs">Next ▶</button>
        </div>

        <!-- Zoom & Save Controls -->
        <div class="flex items-center gap-3">
            <div class="flex items-center bg-slate-800 rounded px-2 py-1 border border-slate-700">
                <button onclick="zoomOut()" class="text-xs text-white px-1.5 font-bold hover:text-sky-400">🔍 -</button>
                <span id="zoomLbl" class="text-xs font-mono font-bold text-sky-400 px-2">125%</span>
                <button onclick="zoomIn()" class="text-xs text-white px-1.5 font-bold hover:text-sky-400">🔍 +</button>
            </div>

            <button id="btnSave" onclick="saveExportPDF()" disabled class="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded text-xs transition flex items-center gap-1.5">
                <i class="fa-solid fa-floppy-disk"></i> Save & Export
            </button>
        </div>
    </div>

    <!-- Workspace Viewport -->
    <main class="flex-1 overflow-auto p-6 flex justify-center items-start bg-[#0f172a] relative" id="workspace" onwheel="handleWheelZoom(event)">
        <div id="canvasWrapper" class="canvas-container hidden">
            <img id="pdfImageBg" class="block pointer-events-none" alt="PDF Render">
            <div id="overlayLayer" class="absolute inset-0"></div>
        </div>
        <div id="placeholderText" class="text-slate-500 font-mono text-sm mt-20 flex flex-col items-center gap-2">
            <i class="fa-solid fa-file-arrow-up text-4xl"></i>
            <span>Upload a PDF file to begin line-by-line workspace editing</span>
        </div>
    </main>

    <script>
        let currentSessionId = null;
        let currentPageIdx = 0;
        let totalPages = 0;
        let zoomLevel = 1.25;
        const minZoom = 0.5;
        const maxZoom = 3.0;

        let editableItems = [];
        let selectedItemIndex = null;

        async function uploadPDFFile(event) {
            const file = event.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);

            document.getElementById('statusLbl').innerText = "Status: Uploading and rendering PDF...";

            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                const res = await response.json();

                if (res.success) {
                    currentSessionId = res.session_id;
                    currentPageIdx = 0;
                    totalPages = res.total_pages;

                    document.getElementById('statusLbl').innerText = `Loaded: ${res.filename}`;
                    document.getElementById('placeholderText').classList.add('hidden');
                    document.getElementById('canvasWrapper').classList.remove('hidden');

                    enableToolbarControls();
                    updatePageControls();
                    renderPage();
                } else {
                    alert('Upload Error: ' + res.error);
                }
            } catch (err) {
                console.error(err);
                alert('File Processing Failed.');
            }
        }

        function enableToolbarControls() {
            const extractBtn = document.getElementById('btnExtract');
            extractBtn.disabled = false;
            extractBtn.classList.remove('opacity-50', 'bg-slate-700');
            extractBtn.classList.add('bg-indigo-600', 'hover:bg-indigo-500');

            document.getElementById('btnAddText').disabled = false;
            document.getElementById('btnAddText').classList.remove('opacity-50');

            document.getElementById('btnDelete').disabled = false;
            document.getElementById('btnDelete').classList.remove('opacity-50');

            document.getElementById('btnSave').disabled = false;
            document.getElementById('btnSave').classList.remove('opacity-50');
        }

        function updatePageControls() {
            document.getElementById('pageLbl').innerText = `${currentPageIdx + 1}/${totalPages}`;
            document.getElementById('btnPrev').disabled = currentPageIdx <= 0;
            document.getElementById('btnNext').disabled = currentPageIdx >= totalPages - 1;
        }

        async function renderPage() {
            if (!currentSessionId) return;

            try {
                const response = await fetch('/api/render', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: currentSessionId,
                        page_idx: currentPageIdx,
                        zoom: zoomLevel
                    })
                });
                const res = await response.json();

                if (res.success) {
                    const img = document.getElementById('pdfImageBg');
                    img.src = res.page_data.image;
                    img.style.width = res.page_data.width + 'px';
                    img.style.height = res.page_data.height + 'px';

                    const wrapper = document.getElementById('canvasWrapper');
                    wrapper.style.width = res.page_data.width + 'px';
                    wrapper.style.height = res.page_data.height + 'px';

                    reRenderOverlays();
                }
            } catch (err) {
                console.error(err);
            }
        }

        async function makeTextEditable() {
            if (!currentSessionId) return;

            try {
                const response = await fetch('/api/extract_text', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: currentSessionId,
                        page_idx: currentPageIdx
                    })
                });
                const res = await response.json();

                if (res.success) {
                    editableItems = res.items;
                    reRenderOverlays();
                    document.getElementById('statusLbl').innerText = `Extracted ${res.count} lines cleanly on Page ${currentPageIdx + 1}`;
                }
            } catch (err) {
                console.error(err);
            }
        }

        function reRenderOverlays() {
            const overlayLayer = document.getElementById('overlayLayer');
            overlayLayer.innerHTML = '';

            editableItems.forEach((item, index) => {
                createOverlayInput(item, index);
            });
        }

        function createOverlayInput(item, index) {
            const overlayLayer = document.getElementById('overlayLayer');
            const input = document.createElement('input');

            const x0 = item.pdf_rect[0] * zoomLevel;
            const y0 = item.pdf_rect[1] * zoomLevel;
            const x1 = item.pdf_rect[2] * zoomLevel;
            const y1 = item.pdf_rect[3] * zoomLevel;

            const scaledFontSize = Math.max(7, Math.floor(item.font_size * zoomLevel * 0.8));
            const boxWidth = Math.max(Math.floor(x1 - x0) + 4, 20);

            input.type = 'text';
            input.value = item.text;
            input.className = 'text-overlay-input';
            input.style.left = `${x0}px`;
            input.style.top = `${y0}px`;
            input.style.width = `${boxWidth}px`;
            input.style.fontSize = `${scaledFontSize}px`;

            input.oninput = (e) => {
                item.text = e.target.value;
                autoResizeInput(input, scaledFontSize);
            };

            input.onclick = (e) => {
                e.stopPropagation();
                selectItem(index, input);
            };

            overlayLayer.appendChild(input);
            autoResizeInput(input, scaledFontSize);
        }

        function autoResizeInput(input, fontSize) {
            const textLen = input.value.length;
            const calcWidth = Math.max(20, Math.floor(textLen * fontSize * 0.6) + 8);
            input.style.width = `${calcWidth}px`;
        }

        function addNewText() {
            const newItem = {
                pdf_rect: [100, 100, 180, 115],
                text: "Type Text Here",
                font_size: 10
            };
            editableItems.push(newItem);
            reRenderOverlays();
        }

        function selectItem(index, inputElem) {
            selectedItemIndex = index;
            document.querySelectorAll('.text-overlay-input').forEach(el => el.classList.remove('selected'));
            inputElem.classList.add('selected');
        }

        function deleteSelected() {
            if (selectedItemIndex === null) {
                alert("Click on any text box to select it first.");
                return;
            }
            editableItems.splice(selectedItemIndex, 1);
            selectedItemIndex = null;
            reRenderOverlays();
        }

        function prevPage() {
            if (currentPageIdx > 0) {
                currentPageIdx--;
                editableItems = [];
                updatePageControls();
                renderPage();
            }
        }

        function nextPage() {
            if (currentPageIdx < totalPages - 1) {
                currentPageIdx++;
                editableItems = [];
                updatePageControls();
                renderPage();
            }
        }

        function zoomIn() {
            if (zoomLevel < maxZoom) {
                zoomLevel += 0.25;
                applyZoom();
            }
        }

        function zoomOut() {
            if (zoomLevel > minZoom) {
                zoomLevel -= 0.25;
                applyZoom();
            }
        }

        function handleWheelZoom(event) {
            if (event.ctrlKey) {
                event.preventDefault();
                if (event.deltaY < 0) zoomIn();
                else zoomOut();
            }
        }

        function applyZoom() {
            document.getElementById('zoomLbl').innerText = `${Math.floor(zoomLevel * 100)}%`;
            renderPage();
        }

        async function saveExportPDF() {
            if (!currentSessionId) return;

            try {
                const response = await fetch('/api/export', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: currentSessionId,
                        page_idx: currentPageIdx,
                        edits: editableItems
                    })
                });

                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = "Edited_PDF_Export.pdf";
                document.body.appendChild(a);
                a.click();
                a.remove();
            } catch (err) {
                console.error(err);
                alert("Save Failed.");
            }
        }

        document.getElementById('workspace').onclick = () => {
            selectedItemIndex = null;
            document.querySelectorAll('.text-overlay-input').forEach(el => el.classList.remove('selected'));
        };
    </script>
</body>
</html>
"""

# Register Blueprint & Start Application Direct
app.register_blueprint(script44_bp)

if __name__ == '__main__':
    print("PDF Editor Launching on http://127.0.0.1:5000/ ...")
    app.run(host='0.0.0.0', port=5000, debug=True)

