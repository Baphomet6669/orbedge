import os
from flask import Blueprint, render_template_string, Flask

script44_bp = Blueprint('script44', __name__)

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Script 44 | Smart PDF Text Replacement Engine</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- PDF Libraries -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <script src="https://unpkg.com/pdf-lib@1.17.1/dist/pdf-lib.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; background: #0f172a; color: #f1f5f9; }
        .canvas-container-custom { position: relative; background: #ffffff; box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin: 0 auto; }
        .btn-btn { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; font-size: 0.875rem; font-weight: 600; border-radius: 0.5rem; transition: all 0.2s; }
        .btn-primary { background: linear-gradient(135deg, #6366f1, #a855f7); color: white; }
        .btn-primary:hover { opacity: 0.9; }
        .btn-secondary { background: #334155; color: #f8fafc; }
        .btn-secondary:hover { background: #475569; }
    </style>
</head>
<body class="min-h-screen flex flex-col">

    <!-- HEADER -->
    <header class="border-b border-slate-800 bg-slate-950 p-4 sticky top-0 z-50 flex items-center justify-between">
        <div class="flex items-center gap-3">
            <div class="p-2 bg-indigo-600 rounded-lg text-white">
                <i class="fa-solid fa-file-pen text-xl"></i>
            </div>
            <div>
                <h1 class="text-base font-bold text-white">Script 44 Engine</h1>
                <p class="text-xs text-slate-400">PDF Text Whiteout & Replace System</p>
            </div>
        </div>
        <div id="file-status" class="text-xs bg-slate-800 px-3 py-1.5 rounded-full border border-slate-700 text-slate-300">
            No File Loaded
        </div>
    </header>

    <!-- TOOLBAR -->
    <div class="border-b border-slate-800 bg-slate-900/90 p-3 flex flex-wrap gap-3 items-center justify-between sticky top-16 z-40">
        <div class="flex items-center gap-2">
            <label class="btn-btn btn-primary cursor-pointer">
                <i class="fa-solid fa-file-upload"></i> Open PDF
                <input type="file" id="pdfInput" accept="application/pdf" class="hidden">
            </label>

            <button onclick="extractAndMakeEditable()" id="btnExtract" class="btn-btn btn-secondary" disabled>
                <i class="fa-solid fa-i-cursor text-indigo-400"></i> Make Existing Text Editable
            </button>

            <button onclick="addNewText()" class="btn-btn btn-secondary">
                <i class="fa-solid fa-plus text-emerald-400"></i> Add Text
            </button>

            <button onclick="deleteSelected()" class="btn-btn btn-secondary text-red-400">
                <i class="fa-solid fa-trash"></i> Delete
            </button>
        </div>

        <div>
            <button id="exportBtn" onclick="exportPDF()" class="btn-btn btn-primary" disabled>
                <i class="fa-solid fa-download"></i> Save PDF
            </button>
        </div>
    </div>

    <!-- MAIN CANVAS -->
    <main class="flex-1 p-6 overflow-auto flex justify-center items-start">
        <div class="canvas-container-custom">
            <canvas id="pdfCanvas"></canvas>
        </div>
    </main>

    <!-- JS LOGIC -->
    <script>
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

        let fabricCanvas = null;
        let pdfDoc = null;
        let pdfBytesOriginal = null;
        let pageViewport = null;

        function initCanvas() {
            fabricCanvas = new fabric.Canvas('pdfCanvas', {
                preserveObjectStacking: true
            });
        }

        document.getElementById('pdfInput').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            pdfBytesOriginal = await file.arrayBuffer();
            pdfDoc = await pdfjsLib.getDocument({ data: pdfBytesOriginal }).promise;
            
            document.getElementById('file-status').textContent = file.name;
            document.getElementById('btnExtract').disabled = false;
            document.getElementById('exportBtn').disabled = false;

            renderPage(1);
        });

        async function renderPage(pageNum) {
            fabricCanvas.clear();
            const page = await pdfDoc.getPage(pageNum);
            pageViewport = page.getViewport({ scale: 1.5 });

            const tempCanvas = document.createElement('canvas');
            const tempCtx = tempCanvas.getContext('2d');
            tempCanvas.width = pageViewport.width;
            tempCanvas.height = pageViewport.height;

            await page.render({ canvasContext: tempCtx, viewport: pageViewport }).promise;

            fabricCanvas.setWidth(pageViewport.width);
            fabricCanvas.setHeight(pageViewport.height);

            fabric.Image.fromURL(tempCanvas.toDataURL(), (img) => {
                fabricCanvas.setBackgroundImage(img, fabricCanvas.renderAll.bind(fabricCanvas));
            });
        }

        // टेक्स्ट एक्सट्रेक्ट करके एडिटेबल बनाना (Whiteout Mode)
        async function extractAndMakeEditable() {
            if (!pdfDoc) return;

            const page = await pdfDoc.getPage(1);
            const textContent = await page.getTextContent();

            textContent.items.forEach((item) => {
                if (!item.str.trim()) return;

                const tx = pdfjsLib.Util.transformPath(pageViewport.transform, item.transform);
                const x = tx[4];
                const y = pageViewport.height - tx[5];
                const fontSize = Math.max(10, item.height * pageViewport.scale);

                // 1. पुराने टेक्स्ट को छिपाने के लिए वाइट बॉक्स (Whiteout Box)
                const whiteoutRect = new fabric.Rect({
                    left: x - 2,
                    top: y - fontSize,
                    width: item.width * pageViewport.scale + 4,
                    height: fontSize * 1.2,
                    fill: 'white',
                    selectable: false,
                    evented: false
                });

                // 2. पुराने टेक्स्ट के ऊपर नया Editable Text Object
                const editableText = new fabric.IText(item.str, {
                    left: x,
                    top: y - fontSize,
                    fontSize: fontSize,
                    fill: '#000000',
                    fontFamily: 'sans-serif',
                    editable: true
                });

                fabricCanvas.add(whiteoutRect);
                fabricCanvas.add(editableText);
            });

            fabricCanvas.renderAll();
            alert('Existing text is now editable! Non-editable areas are covered with whiteout overlay.');
        }

        function addNewText() {
            const text = new fabric.IText('New Text', {
                left: 100,
                top: 100,
                fontSize: 20,
                fill: '#000000',
            });
            fabricCanvas.add(text);
            fabricCanvas.setActiveObject(text);
        }

        function deleteSelected() {
            const active = fabricCanvas.getActiveObject();
            if (active) fabricCanvas.remove(active);
        }

        async function exportPDF() {
            const pdfDocLib = await PDFLib.PDFDocument.load(pdfBytesOriginal);
            const page = pdfDocLib.getPages()[0];

            const canvasDataUrl = fabricCanvas.toDataURL({ format: 'png', multiplier: 2 });
            const pngImage = await pdfDocLib.embedPng(canvasDataUrl);

            const { width, height } = page.getSize();
            page.drawImage(pngImage, {
                x: 0,
                y: 0,
                width: width,
                height: height
            });

            const savedBytes = await pdfDocLib.save();
            const blob = new Blob([savedBytes], { type: 'application/pdf' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'edited.pdf';
            link.click();
        }

        window.onload = initCanvas;
    </script>
</body>
</html>
"""

@script44_bp.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_LAYOUT)

app = Flask(__name__)
app.register_blueprint(script44_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

