import os
from flask import Blueprint, render_template_string, Flask

script44_bp = Blueprint('script44', __name__)

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sejda-Style Professional PDF Editor</title>
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
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
            border-radius: 0.5rem;
            background: #ffffff;
        }
        .editable-text {
            cursor: text;
        }
        .editable-text:hover {
            opacity: 0.8;
        }
        .text-input-popup {
            position: fixed;
            background: white;
            padding: 12px;
            border-radius: 8px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            z-index: 1000;
            border: 2px solid #6366f1;
            min-width: 200px;
        }
        .text-input-popup input {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
        }
        .text-input-popup button {
            margin-top: 8px;
            width: 100%;
            padding: 6px;
            background: #6366f1;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
        }
        .text-input-popup button:hover {
            background: #4f46e5;
        }
    </style>
</head>
<body class="min-h-screen flex flex-col">

    <!-- HEADER -->
    <header class="border-b border-slate-800 bg-slate-950 px-6 py-3 sticky top-0 z-50 flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-3">
            <div class="p-2 bg-indigo-600 rounded-lg text-white shadow-md">
                <i class="fa-solid fa-file-pen text-lg"></i>
            </div>
            <div>
                <h1 class="text-base font-bold text-white tracking-wide">Sejda-Style PDF Editor</h1>
                <p class="text-xs text-slate-400">Click on text to edit directly • Drag to move • Delete with ease</p>
            </div>
        </div>
        <div id="file-status" class="text-xs bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300 truncate max-w-[200px] sm:max-w-xs">
            No File Loaded
        </div>
    </header>

    <!-- TOOLBAR -->
    <nav class="border-b border-slate-800 bg-slate-900/95 backdrop-blur px-6 py-3 sticky top-14 z-40 flex flex-wrap gap-3 items-center justify-between">
        <div class="flex flex-wrap items-center gap-3">
            <label class="bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs px-4 py-2.5 rounded-lg cursor-pointer transition flex items-center gap-2 shadow">
                <i class="fa-solid fa-cloud-arrow-up"></i> Upload PDF
                <input type="file" id="pdfInput" accept="application/pdf" class="hidden">
            </label>

            <button onclick="addNewText()" id="btnAddText" class="bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs px-4 py-2.5 rounded-lg transition flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed" disabled>
                <i class="fa-solid fa-plus text-emerald-400"></i> Add New Text
            </button>

            <button onclick="deleteSelected()" id="btnDelete" class="bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 font-medium text-xs px-4 py-2.5 rounded-lg transition flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed" disabled>
                <i class="fa-solid fa-trash"></i> Delete Selected
            </button>
        </div>

        <div>
            <button id="exportBtn" onclick="exportPDF()" class="bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs px-5 py-2.5 rounded-lg transition flex items-center gap-2 shadow disabled:opacity-40 disabled:cursor-not-allowed" disabled>
                <i class="fa-solid fa-download"></i> Save & Export PDF
            </button>
        </div>
    </nav>

    <!-- MAIN CANVAS CONTAINER -->
    <main class="flex-1 p-6 flex justify-center items-center overflow-auto bg-slate-950/60">
        <div class="canvas-wrapper">
            <canvas id="pdfCanvas"></canvas>
        </div>
    </main>

    <!-- LOGIC -->
    <script>
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

        let fabricCanvas = null;
        let pdfDoc = null;
        let pdfBytesOriginal = null;
        let pageViewport = null;
        let textElementsMap = [];
        let editingText = null;

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
                pdfDoc = await pdfjsLib.getDocument({ data: pdfBytesOriginal.slice(0) }).promise;
                
                document.getElementById('file-status').textContent = file.name;
                document.getElementById('btnAddText').disabled = false;
                document.getElementById('btnDelete').disabled = false;
                document.getElementById('exportBtn').disabled = false;

                await renderPage(1);
                await extractAndMakeEditable();
            } catch (err) {
                alert('Failed to load PDF: ' + err.message);
                console.error(err);
            }
        });

        async function renderPage(pageNum) {
            fabricCanvas.clear();
            textElementsMap = [];
            const page = await pdfDoc.getPage(pageNum);
            
            const screenWidth = window.innerWidth - 80;
            const unscaledViewport = page.getViewport({ scale: 1.0 });
            const calculatedScale = Math.min(1.5, screenWidth / unscaledViewport.width);

            pageViewport = page.getViewport({ scale: calculatedScale });

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

        async function extractAndMakeEditable() {
            if (!pdfDoc) return;

            const page = await pdfDoc.getPage(1);
            const textContent = await page.getTextContent();

            textContent.items.forEach((item) => {
                if (!item.str || !item.str.trim()) return;

                const tx = pdfjsLib.Util.transformPath(pageViewport.transform, item.transform);
                const x = tx[4];
                const fontSize = Math.abs(tx[3]) || (item.height * pageViewport.scale);
                const y = pageViewport.height - tx[5] - (fontSize * 0.8);

                // White mask to cover original text
                const whiteoutRect = new fabric.Rect({
                    left: x - 1,
                    top: y,
                    width: (item.width * pageViewport.scale) + 4,
                    height: fontSize * 1.2,
                    fill: '#ffffff',
                    selectable: false,
                    evented: false,
                    isMask: true
                });

                // Editable text
                const editableText = new fabric.IText(item.str, {
                    left: x,
                    top: y,
                    fontSize: fontSize,
                    fill: '#000000',
                    fontFamily: 'Helvetica, Arial, sans-serif',
                    editable: false,
                    selectable: true,
                    hasControls: true,
                    transparentCorners: false,
                    cornerColor: '#6366f1',
                    cornerSize: 6,
                    pdfX: x / pageViewport.scale,
                    pdfY: (pageViewport.height - y - fontSize) / pageViewport.scale,
                    pdfFontSize: fontSize / pageViewport.scale,
                    originalMask: whiteoutRect,
                    isEditable: true
                });

                // Click handler for direct editing
                editableText.on('mousedown', (e) => {
                    if (e.e.detail === 2) { // Double click
                        editableText.enterEditing();
                        editableText.selectAll();
                    }
                });

                // Single click to show popup editor
                editableText.on('selected', () => {
                    showTextEditPopup(editableText);
                });

                fabricCanvas.add(whiteoutRect);
                fabricCanvas.add(editableText);
                editableText.bringToFront();
                
                textElementsMap.push(editableText);
            });

            fabricCanvas.renderAll();
        }

        function showTextEditPopup(textObj) {
            // Remove existing popup if any
            const existingPopup = document.querySelector('.text-input-popup');
            if (existingPopup) existingPopup.remove();

            const popup = document.createElement('div');
            popup.className = 'text-input-popup';
            
            const input = document.createElement('input');
            input.type = 'text';
            input.value = textObj.text;
            input.placeholder = 'Edit text here';
            
            const saveBtn = document.createElement('button');
            saveBtn.textContent = 'Save';
            
            popup.appendChild(input);
            popup.appendChild(saveBtn);
            document.body.appendChild(popup);

            // Position popup near text
            const rect = fabricCanvas.getElement().getBoundingClientRect();
            popup.style.left = (rect.left + textObj.left + 10) + 'px';
            popup.style.top = (rect.top + textObj.top - 50) + 'px';

            input.focus();
            input.select();

            const updateText = () => {
                textObj.text = input.value || 'Text';
                fabricCanvas.renderAll();
                popup.remove();
                fabricCanvas.discardActiveObject();
                fabricCanvas.renderAll();
            };

            saveBtn.onclick = updateText;
            input.onkeypress = (e) => {
                if (e.key === 'Enter') updateText();
            };
            input.onblur = updateText;
        }

        function addNewText() {
            const text = new fabric.IText('Click to edit text', {
                left: 100,
                top: 100,
                fontSize: 16,
                fill: '#000000',
                fontFamily: 'Helvetica, Arial, sans-serif',
                editable: false,
                selectable: true,
                transparentCorners: false,
                cornerColor: '#6366f1',
                cornerSize: 6,
                isEditable: true
            });

            text.on('selected', () => {
                showTextEditPopup(text);
            });

            text.on('mousedown', (e) => {
                if (e.e.detail === 2) {
                    text.enterEditing();
                    text.selectAll();
                }
            });
            
            fabricCanvas.add(text);
            fabricCanvas.setActiveObject(text);
            text.bringToFront();
            fabricCanvas.renderAll();
            showTextEditPopup(text);
        }

        function deleteSelected() {
            const activeObj = fabricCanvas.getActiveObject();
            if (activeObj) {
                if (activeObj.originalMask) {
                    fabricCanvas.remove(activeObj.originalMask);
                }
                fabricCanvas.remove(activeObj);
                fabricCanvas.renderAll();
                alert('Text deleted!');
            } else {
                alert('Please click on a text block first to select it for deletion.');
            }
        }

        async function exportPDF() {
            if (!pdfBytesOriginal) return;

            try {
                const pdfDocLib = await PDFLib.PDFDocument.load(pdfBytesOriginal);
                const page = pdfDocLib.getPages()[0];
                const font = await pdfDocLib.embedFont(PDFLib.StandardFonts.Helvetica);

                // Draw masks to erase old text positions
                const objects = fabricCanvas.getObjects();
                for (const obj of objects) {
                    if (obj.isMask) {
                        const pdfX = obj.left / pageViewport.scale;
                        const pdfY = (pageViewport.height - obj.top - obj.height) / pageViewport.scale;
                        page.drawRectangle({
                            x: pdfX,
                            y: pdfY,
                            width: obj.width / pageViewport.scale,
                            height: obj.height / pageViewport.scale,
                            color: PDFLib.rgb(1, 1, 1)
                        });
                    }
                }

                // Draw new or updated text
                for (const obj of objects) {
                    if (obj.type === 'i-text' && obj.text) {
                        const pdfX = obj.left / pageViewport.scale;
                        const pdfFontSize = (obj.fontSize * (obj.scaleY || 1)) / pageViewport.scale;
                        const pdfY = (pageViewport.height - obj.top - (obj.height * (obj.scaleY || 1))) / pageViewport.scale;

                        page.drawText(obj.text, {
                            x: pdfX,
                            y: pdfY,
                            size: Math.max(6, pdfFontSize),
                            font: font,
                            color: PDFLib.rgb(0, 0, 0)
                        });
                    }
                }

                const savedBytes = await pdfDocLib.save();
                const blob = new Blob([savedBytes], { type: 'application/pdf' });
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'edited-document.pdf';
                link.click();

            } catch (err) {
                console.error('Vector export warning, falling back to dynamic rendering:', err);
                
                // Fallback: Hybrid high-res canvas composite export
                const pdfDocLib = await PDFLib.PDFDocument.load(pdfBytesOriginal);
                const page = pdfDocLib.getPages()[0];
                
                const canvasDataUrl = fabricCanvas.toDataURL({ format: 'png', multiplier: 2 });
                const pngImage = await pdfDocLib.embedPng(canvasDataUrl);
                
                const { width, height } = page.getSize();
                page.drawImage(pngImage, { x: 0, y: 0, width, height });

                const savedBytes = await pdfDocLib.save();
                const blob = new Blob([savedBytes], { type: 'application/pdf' });
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'edited-document.pdf';
                link.click();
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
