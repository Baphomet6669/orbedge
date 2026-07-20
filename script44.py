import os
from flask import Blueprint, render_template_string

script44_bp = Blueprint('script44', __name__)

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Script 44 | Professional PDF Editor</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- PDF Libraries -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <script src="https://unpkg.com/pdf-lib@1.17.1/dist/pdf-lib.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #f1f5f9;
            min-height: 100vh;
        }

        .btn-primary {
            @apply bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold px-4 py-2.5 rounded-lg transition-all duration-200 shadow-lg hover:shadow-indigo-500/50 flex items-center gap-2;
        }

        .btn-secondary {
            @apply bg-gray-700 hover:bg-gray-600 text-gray-100 font-semibold px-3 py-1.5 rounded-lg transition-all duration-200 flex items-center gap-1.5 text-sm;
        }

        .btn-danger {
            @apply bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 font-semibold px-3 py-1.5 rounded-lg transition-all duration-200 flex items-center gap-1.5 text-sm;
        }

        .input-field {
            @apply bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50;
        }

        .canvas-container {
            position: relative;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
            overflow: hidden;
        }

        .canvas-container canvas {
            display: block;
            max-width: 100%;
            height: auto;
        }

        .toolbar-group {
            @apply bg-gray-800/50 backdrop-blur border border-gray-700/50 rounded-lg p-3 flex flex-wrap gap-2 items-center;
        }

        .status-badge {
            @apply inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold;
        }

        .status-success {
            @apply bg-emerald-500/20 text-emerald-400 border border-emerald-500/30;
        }

        .status-info {
            @apply bg-blue-500/20 text-blue-400 border border-blue-500/30;
        }

        .status-loading {
            @apply bg-indigo-500/20 text-indigo-400 border border-indigo-500/30;
        }

        .divider {
            @apply h-6 w-px bg-gray-700;
        }

        .slider {
            @apply w-24 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer;
        }

        .slider::-webkit-slider-thumb {
            appearance: none;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            cursor: pointer;
            box-shadow: 0 0 8px rgba(99, 102, 241, 0.5);
        }

        .slider::-moz-range-thumb {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            cursor: pointer;
            border: none;
            box-shadow: 0 0 8px rgba(99, 102, 241, 0.5);
        }

        .modal {
            @apply fixed inset-0 bg-black/50 backdrop-blur flex items-center justify-center z-50 hidden;
        }

        .modal.active {
            @apply flex;
        }

        .modal-content {
            @apply bg-gray-900 border border-gray-800 rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl;
        }
    </style>
</head>
<body class="antialiased">

    <!-- HEADER -->
    <header class="border-b border-gray-800 bg-gray-950/80 backdrop-blur px-6 py-4 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="p-2.5 bg-gradient-to-tr from-indigo-600 to-purple-500 rounded-xl shadow-lg shadow-indigo-500/20">
                    <i class="fa-solid fa-file-signature text-lg text-white"></i>
                </div>
                <div>
                    <h1 class="text-lg font-bold tracking-tight text-white">Script 44</h1>
                    <p class="text-xs text-gray-400 mt-0.5">Professional Native Text Overwrite Engine</p>
                </div>
            </div>
            <div id="file-info" class="status-badge status-info hidden">
                <i class="fa-solid fa-circle text-current"></i>
                <span id="file-name">No file loaded</span>
            </div>
        </div>
    </header>

    <!-- TOOLBAR -->
    <div class="border-b border-gray-800 bg-gray-900/50 backdrop-blur px-6 py-4 sticky top-16 z-40">
        <div class="max-w-7xl mx-auto">
            <div class="toolbar-group mb-3">
                <label class="btn-primary cursor-pointer text-sm">
                    <i class="fa-solid fa-upload"></i> Load PDF
                    <input type="file" id="pdfInput" accept="application/pdf" class="hidden">
                </label>
                
                <div class="divider"></div>

                <button onclick="addNewText()" class="btn-secondary">
                    <i class="fa-solid fa-plus text-indigo-400"></i> Add Text
                </button>

                <label class="btn-secondary cursor-pointer">
                    <i class="fa-solid fa-image text-emerald-400"></i> Add Image
                    <input type="file" id="imageInput" accept="image/*" class="hidden">
                </label>

                <button onclick="deleteSelected()" class="btn-danger">
                    <i class="fa-solid fa-trash"></i> Delete
                </button>

                <div class="divider"></div>

                <button onclick="undoAction()" class="btn-secondary">
                    <i class="fa-solid fa-undo text-amber-400"></i> Undo
                </button>

                <button onclick="redoAction()" class="btn-secondary">
                    <i class="fa-solid fa-redo text-amber-400"></i> Redo
                </button>

                <div class="ml-auto">
                    <button id="exportBtn" onclick="exportPDF()" class="btn-primary text-sm" disabled>
                        <i class="fa-solid fa-download"></i> Export PDF
                    </button>
                </div>
            </div>

            <!-- Text Formatting -->
            <div id="textToolbar" class="toolbar-group hidden">
                <label class="flex items-center gap-2 text-sm">
                    <span class="text-gray-300 w-20">Font:</span>
                    <select id="fontSelect" onchange="updateTextFont()" class="input-field w-32">
                        <option>Arial</option>
                        <option>Times New Roman</option>
                        <option>Courier New</option>
                        <option>Georgia</option>
                        <option>Verdana</option>
                    </select>
                </label>

                <label class="flex items-center gap-2 text-sm">
                    <span class="text-gray-300 w-20">Size:</span>
                    <input type="number" id="fontSize" min="8" max="72" value="16" onchange="updateTextSize()" class="input-field w-16">
                </label>

                <label class="flex items-center gap-2 text-sm">
                    <span class="text-gray-300 w-20">Color:</span>
                    <input type="color" id="textColor" value="#000000" onchange="updateTextColor()" class="w-10 h-10 rounded cursor-pointer border border-gray-600">
                </label>

                <div class="divider"></div>

                <label class="flex items-center gap-2 text-sm cursor-pointer">
                    <input type="checkbox" id="boldCheck" onchange="updateTextStyle()">
                    <span>Bold</span>
                </label>

                <label class="flex items-center gap-2 text-sm cursor-pointer">
                    <input type="checkbox" id="italicCheck" onchange="updateTextStyle()">
                    <span>Italic</span>
                </label>

                <label class="flex items-center gap-2 text-sm">
                    <span class="text-gray-300 w-24">Opacity:</span>
                    <input type="range" id="opacitySlider" min="0" max="1" step="0.1" value="1" onchange="updateOpacity()" class="slider w-24">
                </label>
            </div>
        </div>
    </div>

    <!-- STATUS BAR -->
    <div class="border-b border-gray-800 bg-gray-900/30 px-6 py-2">
        <div class="max-w-7xl mx-auto flex items-center justify-between">
            <div id="status-message" class="text-xs text-gray-400 flex items-center gap-2">
                <i class="fa-solid fa-info-circle text-blue-400"></i>
                <span>PDF upload karo, aur kisi bhi puraane text par double-click karke use badal do!</span>
            </div>
            <div id="page-info" class="text-xs text-gray-500 hidden">
                <span id="current-page">1</span> / <span id="total-pages">0</span>
            </div>
        </div>
    </div>

    <!-- CANVAS AREA -->
    <main class="flex-1 p-6 overflow-auto bg-gray-950/30">
        <div class="max-w-6xl mx-auto">
            <div class="canvas-container">
                <canvas id="pdfCanvas"></canvas>
            </div>
        </div>
    </main>

    <!-- PAGE NAVIGATION -->
    <div id="pageNav" class="border-t border-gray-800 bg-gray-900/50 backdrop-blur px-6 py-3 sticky bottom-0 hidden">
        <div class="max-w-7xl mx-auto flex items-center justify-center gap-4">
            <button onclick="previousPage()" class="btn-secondary">
                <i class="fa-solid fa-chevron-left"></i> Previous
            </button>
            <div class="flex items-center gap-2">
                <span class="text-sm">Page</span>
                <input type="number" id="pageInput" min="1" value="1" onchange="gotoPage()" class="input-field w-12 text-center">
                <span class="text-sm">of <span id="pageCount">0</span></span>
            </div>
            <button onclick="nextPage()" class="btn-secondary">
                Next <i class="fa-solid fa-chevron-right"></i>
            </button>
        </div>
    </div>

    <script>
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

        let fabricCanvas = null;
        let pdfDocument = null;
        let pdfBytes = null;
        let currentPage = 1;
        let totalPages = 0;
        let history = [];
        let historyIndex = -1;
        let selectedObject = null;

        const statusEl = document.getElementById('status-message');
        const exportBtn = document.getElementById('exportBtn');
        const pageNav = document.getElementById('pageNav');
        const textToolbar = document.getElementById('textToolbar');

        function initFabric() {
            const canvas = document.getElementById('pdfCanvas');
            fabricCanvas = new fabric.Canvas('pdfCanvas', {
                preserveObjectStacking: true,
                enableRetinaScaling: true,
            });

            fabricCanvas.on('object:added', saveHistory);
            fabricCanvas.on('object:modified', saveHistory);
            fabricCanvas.on('object:removed', saveHistory);
            fabricCanvas.on('selection:created', showTextToolbar);
            fabricCanvas.on('selection:updated', showTextToolbar);
            fabricCanvas.on('selection:cleared', hideTextToolbar);
        }

        document.getElementById('pdfInput').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            updateStatus('loading', 'PDF parse ho raha hai...');
            try {
                pdfBytes = await file.arrayBuffer();
                pdfDocument = await pdfjsLib.getDocument({ data: pdfBytes }).promise;
                totalPages = pdfDocument.numPages;
                currentPage = 1;

                document.getElementById('file-name').textContent = file.name;
                document.getElementById('file-info').classList.remove('hidden');
                document.getElementById('total-pages').textContent = totalPages;
                document.getElementById('pageCount').textContent = totalPages;
                document.getElementById('pageInput').value = 1;
                document.getElementById('pageInput').max = totalPages;
                
                if (totalPages > 1) {
                    pageNav.classList.remove('hidden');
                }
                
                document.getElementById('page-info').classList.remove('hidden');
                exportBtn.disabled = false;

                history = [];
                historyIndex = -1;

                await renderPage(1);
                updateStatus('success', 'PDF ready! Text par click karke edit karo!');
            } catch (error) {
                updateStatus('error', 'PDF load error: ' + error.message);
                console.error(error);
            }
        });

        async function renderPage(pageNum) {
            if (!pdfDocument) return;

            try {
                fabricCanvas.clear();
                const page = await pdfDocument.getPage(pageNum);
                const viewport = page.getViewport({ scale: 2 });

                const tempCanvas = document.createElement('canvas');
                const tempCtx = tempCanvas.getContext('2d');
                tempCanvas.width = viewport.width;
                tempCanvas.height = viewport.height;

                await page.render({ canvasContext: tempCtx, viewport }).promise;

                fabricCanvas.setWidth(viewport.width);
                fabricCanvas.setHeight(viewport.height);

                fabric.Image.fromURL(tempCanvas.toDataURL(), (img) => {
                    fabricCanvas.setBackgroundImage(img, fabricCanvas.renderAll.bind(fabricCanvas));
                });

                const textContent = await page.getTextContent();
                textContent.items.forEach((item, index) => {
                    if (!item.str || !item.str.trim()) return;

                    const tx = pdfjsLib.Util.transformPath(viewport.transform, item.transform);
                    const x = tx[4];
                    const y = viewport.height - tx[5];
                    const fontSize = Math.max(12, (item.height || 12) * 1.5);

                    const textObject = new fabric.IText(item.str, {
                        left: x,
                        top: y - fontSize,
                        fontSize: fontSize,
                        fill: '#000000',
                        fontFamily: 'Arial',
                        editable: true,
                        hasControls: true,
                        hasBorders: true,
                        selectable: true,
                        originX: 'left',
                        originY: 'top',
                        metadata: { isOriginalText: true, pageNum: pageNum }
                    });

                    fabricCanvas.add(textObject);
                });

                currentPage = pageNum;
                document.getElementById('current-page').textContent = pageNum;
                document.getElementById('pageInput').value = pageNum;

                saveHistory();
            } catch (error) {
                updateStatus('error', 'Page render error: ' + error.message);
                console.error(error);
            }
        }

        function addNewText() {
            if (!fabricCanvas) return alert('Pehle PDF load karo!');

            const text = new fabric.IText('Edit this text', {
                left: 100,
                top: 100,
                fontSize: 16,
                fill: '#000000',
                fontFamily: 'Arial',
                editable: true,
                selectable: true,
                hasControls: true,
                hasBorders: true,
                metadata: { isNewText: true }
            });

            fabricCanvas.add(text);
            fabricCanvas.setActiveObject(text);
            fabricCanvas.renderAll();
        }

        function showTextToolbar() {
            const activeObj = fabricCanvas.getActiveObject();
            if (activeObj && activeObj.type === 'i-text') {
                selectedObject = activeObj;
                document.getElementById('fontSelect').value = activeObj.fontFamily || 'Arial';
                document.getElementById('fontSize').value = activeObj.fontSize || 16;
                document.getElementById('textColor').value = rgbToHex(activeObj.fill || '#000000');
                document.getElementById('boldCheck').checked = activeObj.fontWeight === 'bold';
                document.getElementById('italicCheck').checked = activeObj.fontStyle === 'italic';
                document.getElementById('opacitySlider').value = activeObj.opacity || 1;
                
                textToolbar.classList.remove('hidden');
            }
        }

        function hideTextToolbar() {
            textToolbar.classList.add('hidden');
            selectedObject = null;
        }

        function updateTextFont() {
            if (!selectedObject) return;
            selectedObject.set({ fontFamily: document.getElementById('fontSelect').value });
            fabricCanvas.renderAll();
        }

        function updateTextSize() {
            if (!selectedObject) return;
            selectedObject.set({ fontSize: parseInt(document.getElementById('fontSize').value) });
            fabricCanvas.renderAll();
        }

        function updateTextColor() {
            if (!selectedObject) return;
            selectedObject.set({ fill: document.getElementById('textColor').value });
            fabricCanvas.renderAll();
        }

        function updateTextStyle() {
            if (!selectedObject) return;
            selectedObject.set({
                fontWeight: document.getElementById('boldCheck').checked ? 'bold' : 'normal',
                fontStyle: document.getElementById('italicCheck').checked ? 'italic' : 'normal',
            });
            fabricCanvas.renderAll();
        }

        function updateOpacity() {
            if (!selectedObject) return;
            const opacity = parseFloat(document.getElementById('opacitySlider').value);
            selectedObject.set({ opacity: opacity });
            fabricCanvas.renderAll();
        }

        function deleteSelected() {
            const activeObj = fabricCanvas.getActiveObject();
            if (activeObj) {
                fabricCanvas.remove(activeObj);
                fabricCanvas.renderAll();
                hideTextToolbar();
            }
        }

        document.getElementById('imageInput').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (event) => {
                fabric.Image.fromURL(event.target.result, (img) => {
                    img.scaleToWidth(200);
                    img.set({ left: 100, top: 100 });
                    fabricCanvas.add(img);
                    fabricCanvas.setActiveObject(img);
                    fabricCanvas.renderAll();
                });
            };
            reader.readAsDataURL(file);
        });

        function saveHistory() {
            historyIndex++;
            history = history.slice(0, historyIndex);
            history.push(JSON.stringify(fabricCanvas.toJSON()));
        }

        function undoAction() {
            if (historyIndex > 0) {
                historyIndex--;
                loadHistoryState(history[historyIndex]);
            }
        }

        function redoAction() {
            if (historyIndex < history.length - 1) {
                historyIndex++;
                loadHistoryState(history[historyIndex]);
            }
        }

        function loadHistoryState(state) {
            fabricCanvas.loadFromJSON(state, () => {
                fabricCanvas.renderAll();
            });
        }

        function previousPage() {
            if (currentPage > 1) {
                renderPage(currentPage - 1);
            }
        }

        function nextPage() {
            if (currentPage < totalPages) {
                renderPage(currentPage + 1);
            }
        }

        function gotoPage() {
            const pageNum = parseInt(document.getElementById('pageInput').value);
            if (pageNum >= 1 && pageNum <= totalPages) {
                renderPage(pageNum);
            }
        }

        async function exportPDF() {
            if (!pdfBytes) return alert('Pehle PDF load karo!');

            updateStatus('loading', 'PDF export ho raha hai...');
            try {
                const pdfDoc = await PDFLib.PDFDocument.load(pdfBytes);
                const page = pdfDoc.getPages()[currentPage - 1];
                
                if (!page) throw new Error('Page not found');

                const canvasImage = fabricCanvas.toDataURL({ format: 'png', multiplier: 2 });
                const pngImage = await pdfDoc.embedPng(canvasImage);
                const { width, height } = page.getSize();

                page.drawImage(pngImage, {
                    x: 0,
                    y: 0,
                    width: width,
                    height: height,
                });

                const pdfBytes = await pdfDoc.save();
                downloadPDF(pdfBytes, 'edited-document.pdf');
                updateStatus('success', 'PDF export complete!');
            } catch (error) {
                updateStatus('error', 'Export failed: ' + error.message);
                console.error(error);
            }
        }

        function downloadPDF(bytes, filename) {
            const blob = new Blob([bytes], { type: 'application/pdf' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            link.click();
            URL.revokeObjectURL(url);
        }

        function updateStatus(type, message) {
            statusEl.innerHTML = `
                <i class="fa-solid ${
                    type === 'loading' ? 'fa-spinner animate-spin text-indigo-400' :
                    type === 'success' ? 'fa-circle-check text-emerald-400' :
                    type === 'error' ? 'fa-circle-exclamation text-red-400' :
                    'fa-info-circle text-blue-400'
                }"></i>
                <span>${message}</span>
            `;
        }

        function rgbToHex(color) {
            if (color.startsWith('#')) return color;
            const rgb = color.match(/\\d+/g);
            if (!rgb) return '#000000';
            return '#' + rgb.map(x => {
                const hex = parseInt(x).toString(16);
                return hex.length === 1 ? '0' + hex : hex;
            }).join('');
        }

        window.addEventListener('DOMContentLoaded', () => {
            initFabric();
        });
    </script>
</body>
</html>
"""

@script44_bp.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_LAYOUT)

if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(script44_bp)
    app.run(debug=True, port=5000)
