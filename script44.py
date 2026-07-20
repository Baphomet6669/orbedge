import os
from flask import Blueprint, render_template_string

# =========================================================================
# INITIALIZE BLUEPRINT FOR SCRIPT 44 (DIRECT PDF CANVAS STUDIO)
# =========================================================================
script44_bp = Blueprint('script44', __name__)

# Inline HTML Layout (Client-side Canvas Studio with PDF.js + Fabric.js + PDF-Lib)
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OrbitEdge Media | Direct PDF Studio</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- PDF Engine Libraries (Browser Native) -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
    <script src="https://unpkg.com/pdf-lib@1.17.1/dist/pdf-lib.min.js"></script>

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=300;400;500;600;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #090d16; color: #f1f5f9; }
        .canvas-container { margin: 0 auto !important; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5); border-radius: 8px; overflow: hidden; }
    </style>
</head>
<body class="antialiased selection:bg-indigo-600 selection:text-white min-h-screen flex flex-col">

    <!-- HEADER NAVIGATION -->
    <header class="border-b border-gray-800 bg-gray-950/70 backdrop-blur px-6 py-4 sticky top-0 z-50 flex items-center justify-between">
        <div class="flex items-center gap-3">
            <div class="p-2.5 bg-gradient-to-tr from-indigo-600 to-violet-500 rounded-xl shadow-lg shadow-indigo-500/20">
                <i class="fa-solid fa-file-pdf text-lg text-white"></i>
            </div>
            <div>
                <h1 class="text-base font-bold tracking-tight text-white leading-none">Shivam Singh Dashboard</h1>
                <span class="text-[10px] uppercase text-gray-400 tracking-widest mt-1 block">Script 44 // Direct PDF Studio</span>
            </div>
        </div>
        <div class="flex items-center gap-2 text-xs font-semibold bg-indigo-500/10 border border-indigo-500/20 px-3.5 py-1.5 rounded-xl text-indigo-400">
            <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span> Canvas Engine Ready
        </div>
    </header>

    <!-- TOOLBAR CONTROLS -->
    <div class="bg-gray-900 border-b border-gray-800 px-6 py-3 flex flex-wrap items-center gap-3 justify-between">
        <div class="flex flex-wrap items-center gap-3 text-xs">
            
            <!-- PDF LOAD -->
            <label class="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-4 py-2 rounded-xl transition cursor-pointer flex items-center gap-2 shadow-md">
                <i class="fa-solid fa-folder-open"></i> Load PDF
                <input type="file" id="pdfInput" accept="application/pdf" class="hidden">
            </label>

            <!-- EDIT TOOLS -->
            <div class="flex items-center gap-2 bg-gray-950 border border-gray-800 p-1.5 rounded-xl">
                <button onclick="addText()" class="bg-gray-800 hover:bg-gray-700 text-gray-200 px-3 py-1.5 rounded-lg font-semibold transition cursor-pointer flex items-center gap-1.5">
                    <i class="fa-solid fa-font text-indigo-400"></i> Add Text
                </button>
                
                <label class="bg-gray-800 hover:bg-gray-700 text-gray-200 px-3 py-1.5 rounded-lg font-semibold transition cursor-pointer flex items-center gap-1.5">
                    <i class="fa-solid fa-image text-emerald-400"></i> Add Image
                    <input type="file" id="imageInput" accept="image/*" class="hidden">
                </label>

                <button onclick="deleteSelected()" class="bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 px-3 py-1.5 rounded-lg font-semibold transition cursor-pointer flex items-center gap-1.5">
                    <i class="fa-solid fa-trash"></i> Delete
                </button>
            </div>
        </div>

        <!-- EXPORT ACTION -->
        <button onclick="exportEditedPDF()" class="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold px-5 py-2 rounded-xl transition cursor-pointer text-xs shadow-lg shadow-emerald-500/10 flex items-center gap-2">
            <i class="fa-solid fa-download"></i> Save & Export PDF
        </button>
    </div>

    <!-- MAIN WORKSPACE -->
    <main class="flex-1 bg-gray-950 p-6 overflow-auto flex flex-col items-center justify-center relative">
        <div id="status-bar" class="mb-4 text-xs font-semibold text-gray-400 flex items-center gap-2">
            <i class="fa-solid fa-circle-info text-indigo-400"></i> Select or upload a PDF file to render layout...
        </div>

        <div id="canvas-wrapper" class="border border-gray-800 rounded-xl overflow-hidden bg-white">
            <canvas id="pdfCanvas"></canvas>
        </div>
    </main>

    <!-- CLIENT JAVASCRIPT ENGINE -->
    <script>
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js';
        
        let fabricCanvas = new fabric.Canvas('pdfCanvas');
        let currentPdfDoc = null;
        let pdfBytes = null;
        const statusEl = document.getElementById('status-bar');

        document.getElementById('pdfInput').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            statusEl.innerHTML = `<span class="text-indigo-400"><i class="fa-solid fa-spinner animate-spin"></i> Parsing PDF stream...</span>`;
            pdfBytes = await file.arrayBuffer();
            currentPdfDoc = await pdfjsLib.getDocument({ data: pdfBytes }).promise;
            renderPage(1);
        });

        async function renderPage(pageNum) {
            fabricCanvas.clear();
            const page = await currentPdfDoc.getPage(pageNum);
            const viewport = page.getViewport({ scale: 1.5 });

            const tempCanvas = document.createElement('canvas');
            const tempCtx = tempCanvas.getContext('2d');
            tempCanvas.width = viewport.width;
            tempCanvas.height = viewport.height;

            await page.render({ canvasContext: tempCtx, viewport: viewport }).promise;

            fabricCanvas.setWidth(viewport.width);
            fabricCanvas.setHeight(viewport.height);

            // PDF Render as background
            fabric.Image.fromURL(tempCanvas.toDataURL(), (img) => {
                fabricCanvas.setBackgroundImage(img, fabricCanvas.renderAll.bind(fabricCanvas));
            });

            // Extract native text strings directly into editable Fabric Text blocks
            const textContent = await page.getTextContent();
            textContent.items.forEach(item => {
                const tx = pdfjsLib.Util.transformPath(viewport.transform, item.transform);
                const x = tx[4];
                const y = viewport.height - tx[5];

                if (item.str && item.str.trim().length > 0) {
                    const textObj = new fabric.IText(item.str, {
                        left: x,
                        top: y - (item.height || 12),
                        fontSize: Math.max(12, (item.height || 12) * 1.1),
                        fill: '#000000',
                        fontFamily: 'Arial',
                        editable: true
                    });
                    fabricCanvas.add(textObj);
                }
            });

            statusEl.innerHTML = `<span class="text-emerald-400"><i class="fa-solid fa-circle-check"></i> PDF Loaded successfully! Double click any text to edit or drag new elements.</span>`;
        }

        function addText() {
            const text = new fabric.IText('Double Click To Edit', {
                left: 100,
                top: 100,
                fontSize: 18,
                fill: '#000000',
                editable: true
            });
            fabricCanvas.add(text);
            fabricCanvas.setActiveObject(text);
        }

        document.getElementById('imageInput').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (event) => {
                fabric.Image.fromURL(event.target.result, (img) => {
                    img.scaleToWidth(180);
                    img.set({ left: 100, top: 100 });
                    fabricCanvas.add(img);
                    fabricCanvas.setActiveObject(img);
                });
            };
            reader.readAsDataURL(file);
        });

        function deleteSelected() {
            const activeObj = fabricCanvas.getActiveObject();
            if (activeObj) {
                fabricCanvas.remove(activeObj);
            }
        }

        async function exportEditedPDF() {
            if (!pdfBytes) {
                alert("Pehle Koi PDF File upload karo!");
                return;
            }

            statusEl.innerHTML = `<span class="text-indigo-400"><i class="fa-solid fa-spinner animate-spin"></i> Generating PDF document stream...</span>`;
            const dataUrl = fabricCanvas.toDataURL({ format: 'png', multiplier: 2 });
            
            const pdfDoc = await PDFLib.PDFDocument.create();
            const page = pdfDoc.addPage([fabricCanvas.width, fabricCanvas.height]);
            
            const pngImage = await pdfDoc.embedPng(dataUrl);
            page.drawImage(pngImage, {
                x: 0,
                y: 0,
                width: fabricCanvas.width,
                height: fabricCanvas.height
            });

            const savedBytes = await pdfDoc.save();
            const blob = new Blob([savedBytes], { type: "application/pdf" });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = "edited_output.pdf";
            link.click();
            
            statusEl.innerHTML = `<span class="text-emerald-400"><i class="fa-solid fa-circle-check"></i> Export Complete! Download initiated.</span>`;
        }
    </script>
</body>
</html>
"""

# =========================================================================
# FLASK ROUTING GATEWAYS
# =========================================================================
@script44_bp.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_LAYOUT)

