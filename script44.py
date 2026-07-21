import os
from flask import Blueprint, render_template_string, Flask

script44_bp = Blueprint('script44', __name__)

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Script 44 | Professional PDF Editor</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- PDF Libraries -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <script src="https://unpkg.com/pdf-lib@1.17.1/dist/pdf-lib.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; background: #0f172a; color: #f1f5f9; }
        .canvas-wrapper {
            position: relative;
            max-width: 100%;
            overflow: auto;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
            border-radius: 0.75rem;
            background: #ffffff;
        }
    </style>
</head>
<body class="min-h-screen flex flex-col">

    <!-- HEADER -->
    <header class="border-b border-slate-800 bg-slate-950 px-4 py-3 sticky top-0 z-50 flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-3">
            <div class="p-2 bg-indigo-600 rounded-lg text-white shadow-md">
                <i class="fa-solid fa-file-pen text-lg"></i>
            </div>
            <div>
                <h1 class="text-sm font-bold text-white tracking-wide">Script 44 PDF Editor</h1>
                <p class="text-xs text-slate-400">Responsive & Interactive Text Overwrite</p>
            </div>
        </div>
        <div id="file-status" class="text-xs bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300 truncate max-w-[200px] sm:max-w-xs">
            No File Loaded
        </div>
    </header>

    <!-- RESPONSIVE TOOLBAR -->
    <nav class="border-b border-slate-800 bg-slate-900/95 backdrop-blur p-3 sticky top-14 z-40 flex flex-wrap gap-2 items-center justify-between">
        <div class="flex flex-wrap items-center gap-2">
            <label class="bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs px-3.5 py-2 rounded-lg cursor-pointer transition flex items-center gap-2 shadow">
                <i class="fa-solid fa-cloud-arrow-up"></i> Upload PDF
                <input type="file" id="pdfInput" accept="application/pdf" class="hidden">
            </label>

            <button onclick="extractAndMakeEditable()" id="btnExtract" class="bg-slate-700 hover:bg-slate-600 text-slate-100 font-medium text-xs px-3.5 py-2 rounded-lg transition flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                <i class="fa-solid fa-i-cursor text-indigo-400"></i> Make Text Editable
            </button>

            <button onclick="addNewText()" class="bg-slate-700 hover:bg-slate-600 text-slate-100 font-medium text-xs px-3.5 py-2 rounded-lg transition flex items-center gap-2">
                <i class="fa-solid fa-plus text-emerald-400"></i> Add Text
            </button>

            <button onclick="deleteSelected()" class="bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 font-medium text-xs px-3.5 py-2 rounded-lg transition flex items-center gap-2">
                <i class="fa-solid fa-trash"></i> Delete
            </button>
        </div>

        <div>
            <button id="exportBtn" onclick="exportPDF()" class="bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs px-4 py-2 rounded-lg transition flex items-center gap-2 shadow disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                <i class="fa-solid fa-download"></i> Save & Export
            </button>
        </div>
    </nav>

    <!-- MAIN CANVAS AREA -->
    <main class="flex-1 p-4 sm:p-6 flex justify-center items-center overflow-auto bg-slate-950/50">
        <div class="canvas-wrapper">
            <canvas id="pdfCanvas"></canvas>
        </div>
    </main>

    <!-- SCRIPT LOGIC -->
    <script>
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

        let fabricCanvas = null;
        let pdfDoc = null;
        let pdfBytesOriginal = null;
        let pageViewport = null;

        function initCanvas() {
            fabricCanvas = new fabric.Canvas('pdfCanvas', {
                preserveObjectStacking: true,
                selection: true
            });
        }

        document.getElementById('pdfInput').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            try {
                pdfBytesOriginal = await file.arrayBuffer();
                pdfDoc = await pdfjsLib.getDocument({ data: pdfBytesOriginal }).promise;
                
                document.getElementById('file-status').textContent = file.name;
                document.getElementById('btnExtract').disabled = false;
                document.getElementById('exportBtn').disabled = false;

                await renderPage(1);
            } catch (err) {
                alert('PDF Load Error: ' + err.message);
                console.error(err);
            }
        });

        async function renderPage(pageNum) {
            fabricCanvas.clear();
            const page = await pdfDoc.getPage(pageNum);
            
            // Responsive scale calculation based on screen width
            const screenWidth = window.innerWidth;
            let scale = 1.5;
            if (screenWidth < 640) scale = 1.0;

            pageViewport = page.getViewport({ scale: scale });

            const tempCanvas = document.createElement('canvas');
            const tempCtx = tempCanvas.getContext('2d');
            tempCanvas.width = pageViewport.width;
            tempCanvas.height = pageViewport.height;

            await page.render({ canvasContext: tempCtx, viewport: pageViewport }).promise;

            fabricCanvas.setWidth(pageViewport.width);
            fabricCanvas.setHeight(pageViewport.height);

            // Set PDF page as background image
            fabric.Image.fromURL(tempCanvas.toDataURL(), (img) => {
                fabricCanvas.setBackgroundImage(img, fabricCanvas.renderAll.bind(fabricCanvas));
            });
        }

        async function extractAndMakeEditable() {
            if (!pdfDoc) return;

            const page = await pdfDoc.getPage(1);
            const textContent = await page.getTextContent();

            textContent.items.forEach((item) => {
                if (!item.str || !item.str.trim()) return;

                const tx = pdfjsLib.Util.transformPath(pageViewport.transform, item.transform);
                const x = tx[4];
                const y = pageViewport.height - tx[5];
                const fontSize = Math.max(10, item.height * pageViewport.scale);

                // 1. Whiteout box to hide original text
                const whiteoutRect = new fabric.Rect({
                    left: x - 2,
                    top: y - fontSize,
                    width: (item.width * pageViewport.scale) + 4,
                    height: fontSize * 1.3,
                    fill: '#ffffff',
                    selectable: false,
                    evented: false,
                    excludeFromExport: false
                });

                // 2. Interactive Editable Text Layer over it
                const editableText = new fabric.IText(item.str, {
                    left: x,
                    top: y - fontSize,
                    fontSize: fontSize,
                    fill: '#000000',
                    fontFamily: 'Arial',
                    editable: true,
                    selectable: true,
                    hasControls: true,
                    lockScalingX: true,
                    lockScalingY: true
                });

                fabricCanvas.add(whiteoutRect);
                fabricCanvas.add(editableText);
                // Bring text to front so it's easily clickable
                editableText.bringToFront();
            });

            fabricCanvas.renderAll();
            alert('Text is now fully editable! Click on any text box to edit or double-click to type.');
        }

        function addNewText() {
            const text = new fabric.IText('New Text', {
                left: 50,
                top: 50,
                fontSize: 18,
                fill: '#000000',
                fontFamily: 'Arial',
                editable: true
            });
            fabricCanvas.add(text);
            fabricCanvas.setActiveObject(text);
            text.bringToFront();
            fabricCanvas.renderAll();
        }

        function deleteSelected() {
            const activeObj = fabricCanvas.getActiveObject();
            if (activeObj) {
                fabricCanvas.remove(activeObj);
                fabricCanvas.renderAll();
            } else {
                alert('Please select a text or object to delete first.');
            }
        }

        async function exportPDF() {
            if (!pdfBytesOriginal) return;

            try {
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
                link.download = 'edited-document.pdf';
                link.click();
            } catch (err) {
                alert('Export failed: ' + err.message);
                console.error(err);
            }
        }

        window.addEventListener('DOMContentLoaded', initCanvas);
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
