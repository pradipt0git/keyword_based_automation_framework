import os
import json
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

CAPTURED_XPATHS_DIR = os.path.join(os.path.dirname(__file__), '../captured_xpaths')

TEMPLATE = r'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>XPath UI Tree View</title>
    <style>
        ul { list-style-type: none; }
        .element-details { margin-left: 20px; display: none; }
        .element.open > .element-details { display: block; }
        .element-name-input { width: 200px; }
        .tree-toggle { cursor: pointer; }
    </style>
</head>
<body>
    <h2>XPath UI Tree View</h2>
    <button id="capture-xpath-btn">Capture XPath</button>
    <button id="stop-capture-btn">Stop Capture</button>
    <button id="refresh-btn">Refresh</button>
    <div id="tree-root"></div>
    <script>
        let captureProcessRunning = false;
        document.getElementById('capture-xpath-btn').onclick = async function() {
            this.disabled = true;
            document.getElementById('stop-capture-btn').disabled = false;
            this.textContent = 'Capturing...';
            captureProcessRunning = true;
            const resp = await fetch('/api/capture_xpath', { method: 'POST' });
            const result = await resp.json();
            alert(result.success ? 'Capture complete!' : ('Error: ' + (result.error || 'Unknown error')));
            this.disabled = false;
            document.getElementById('stop-capture-btn').disabled = true;
            this.textContent = 'Capture XPath';
            captureProcessRunning = false;
            await renderTree();
        };
        document.getElementById('stop-capture-btn').onclick = async function() {
            this.disabled = true;
            await fetch('/api/stop_capture', { method: 'POST' });
            document.getElementById('capture-xpath-btn').disabled = false;
            document.getElementById('capture-xpath-btn').textContent = 'Capture XPath';
            captureProcessRunning = false;
        };
        document.getElementById('stop-capture-btn').disabled = true;
        document.getElementById('refresh-btn').onclick = async function() {
            await renderTree();
        };
        async function fetchData() {
            const resp = await fetch('/api/data');
            return await resp.json();
        }
        function createElementTree(page, elements, pageIdx) {
            const pageLi = document.createElement('li');
            pageLi.classList.add('collapsed');
            // File name input (without extension)
            const fileName = page.replace(/\.json$/, '');
            const fileNameInput = document.createElement('input');
            fileNameInput.type = 'text';
            fileNameInput.value = fileName;
            fileNameInput.className = 'element-name-input';
            fileNameInput.style.fontWeight = 'bold';
            fileNameInput.style.width = '250px';
            // Save icon
            const saveBtn = document.createElement('button');
            saveBtn.innerHTML = '💾';
            saveBtn.title = 'Save (rename file)';
            saveBtn.onclick = async () => {
                const newName = fileNameInput.value.trim();
                if (!newName || newName === fileName) return;
                const resp = await fetch('/api/rename_json', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ old: page, new: newName + '.json' })
                });
                const result = await resp.json();
                if (result.success) {
                    alert('File renamed!');
                    await renderTree();
                } else {
                    alert('Rename failed: ' + (result.error || 'Unknown error'));
                }
            };
            // Page collapse/expand button
            const pageCollapseBtn = document.createElement('button');
            pageCollapseBtn.textContent = '[+]';
            pageCollapseBtn.title = 'Collapse/Expand Page';
            pageCollapseBtn.onclick = () => {
                const isCollapsed = pageLi.classList.toggle('collapsed');
                pageCollapseBtn.textContent = isCollapsed ? '[+]' : '[–]';
                ul.style.display = isCollapsed ? 'none' : 'block';
            };
            // Move this after ul is defined
            // Tree toggle (for spacing only)
            const pageToggle = document.createElement('span');
            pageToggle.textContent = ' ';
            pageToggle.className = 'tree-toggle';
            pageLi.appendChild(fileNameInput);
            pageLi.appendChild(saveBtn);
            pageLi.appendChild(pageCollapseBtn);
            pageLi.appendChild(pageToggle);
            const ul = document.createElement('ul');
            ul.style.display = 'none'; // Default collapsed
            elements.forEach((el, elIdx) => {
                const elLi = document.createElement('li');
                elLi.className = 'element';
                // Name input and save button
                const nameInput = document.createElement('input');
                nameInput.type = 'text';
                nameInput.value = el.name || '';
                nameInput.className = 'element-name-input';
                nameInput.style.marginRight = '4px';
                const saveNameBtn = document.createElement('button');
                saveNameBtn.innerHTML = '💾';
                saveNameBtn.title = 'Save Name';
                saveNameBtn.onclick = async () => {
                    const newName = nameInput.value;
                    await fetch('/api/update_name', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ page, index: elIdx, name: newName })
                    });
                };
                elLi.appendChild(nameInput);
                elLi.appendChild(saveNameBtn);
                // Expand/collapse
                const expandBtn = document.createElement('button');
                expandBtn.textContent = '[+]';
                expandBtn.onclick = () => {
                    elLi.classList.toggle('open');
                    expandBtn.textContent = elLi.classList.contains('open') ? '[-]' : '[+]';
                };
                elLi.appendChild(expandBtn);
                // Details (collapsible JSON)
                const detailsDiv = document.createElement('div');
                detailsDiv.className = 'element-details';
                // Xpath textbox and save button (shown after expand/collapse)
                const xpathBox = document.createElement('input');
                xpathBox.type = 'text';
                xpathBox.value = (el.selectors && el.selectors.xpath) ? el.selectors.xpath : '';
                xpathBox.className = 'element-name-input';
                xpathBox.style.marginBottom = '4px';
                xpathBox.style.width = '70%';
                const saveXpathBtn = document.createElement('button');
                saveXpathBtn.innerHTML = '💾';
                saveXpathBtn.title = 'Save XPath';
                saveXpathBtn.onclick = async () => {
                    const newXpath = xpathBox.value;
                    await fetch('/api/update_xpath', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ page, index: elIdx, xpath: newXpath })
                    });
                };
                // Use <details> and <summary> for collapsible JSON
                const detailsTag = document.createElement('details');
                detailsTag.open = false;
                const summaryTag = document.createElement('summary');
                summaryTag.textContent = 'Show JSON';
                detailsTag.appendChild(summaryTag);
                // Pretty JSON with syntax highlighting
                const pre = document.createElement('pre');
                pre.style.margin = '0';
                pre.style.fontSize = '13px';
                pre.textContent = JSON.stringify(el, null, 2);
                detailsTag.appendChild(pre);
                detailsDiv.appendChild(xpathBox);
                detailsDiv.appendChild(saveXpathBtn);
                detailsDiv.appendChild(detailsTag);
                elLi.appendChild(detailsDiv);
                // Show/hide detailsDiv (xpath box + JSON) on expand/collapse
                elLi.classList.remove('open');
                detailsDiv.style.display = 'none';
                expandBtn.onclick = () => {
                    elLi.classList.toggle('open');
                    expandBtn.textContent = elLi.classList.contains('open') ? '[-]' : '[+]';
                    detailsDiv.style.display = elLi.classList.contains('open') ? 'block' : 'none';
                };
                ul.appendChild(elLi);
            });
            pageLi.appendChild(ul);
            return pageLi;
        }
        async function renderTree() {
            const data = await fetchData();
            const root = document.getElementById('tree-root');
            root.innerHTML = '';
            const ul = document.createElement('ul');
            Object.entries(data).forEach(([page, elements], pageIdx) => {
                ul.appendChild(createElementTree(page, elements, pageIdx));
            });
            root.appendChild(ul);
        }
        renderTree();
    </script>
</body>
</html>
'''

def get_all_json_data():
    data = {}
    for fname in os.listdir(CAPTURED_XPATHS_DIR):
        if fname.endswith('.json'):
            fpath = os.path.join(CAPTURED_XPATHS_DIR, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    arr = json.load(f)
                    data[fname] = arr
            except Exception:
                continue
    return data

@app.route('/')
def index():
    return render_template_string(TEMPLATE)

@app.route('/api/data')
def api_data():
    return jsonify(get_all_json_data())

@app.route('/api/update_name', methods=['POST'])
def api_update_name():
    req = request.json
    page = req['page']
    idx = req['index']
    new_name = req['name']
    fpath = os.path.join(CAPTURED_XPATHS_DIR, page)
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            arr = json.load(f)
        if 0 <= idx < len(arr):
            arr[idx]['name'] = new_name
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(arr, f, indent=2, ensure_ascii=False)
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': False, 'error': 'Invalid index'})

@app.route('/api/capture_xpath', methods=['POST'])
def api_capture_xpath():
    import subprocess
    try:
        # Use the venv Python executable
        venv_python = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.venv/Scripts/python.exe'))
        script_path = os.path.join(os.path.dirname(__file__), 'capture_xpath.py')
        # Store the process globally so it can be killed
        global capture_process
        capture_process = subprocess.Popen([venv_python, script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = capture_process.communicate()
        retcode = capture_process.returncode
        capture_process = None
        if retcode == 0:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': stderr})
    except Exception as e:
        capture_process = None
        return jsonify({'success': False, 'error': str(e)})

# Endpoint to stop the capture_xpath process
capture_process = None
@app.route('/api/stop_capture', methods=['POST'])
def api_stop_capture():
    global capture_process
    if capture_process and capture_process.poll() is None:
        try:
            capture_process.terminate()
            capture_process = None
            return jsonify({'success': True, 'message': 'Capture stopped.'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    else:
        return jsonify({'success': False, 'error': 'No capture process running.'})

@app.route('/api/rename_json', methods=['POST'])
def api_rename_json():
    req = request.json
    old = req.get('old')
    new = req.get('new')
    if not old or not new or old == new:
        return jsonify({'success': False, 'error': 'Invalid file names'})
    old_path = os.path.join(CAPTURED_XPATHS_DIR, old)
    new_path = os.path.join(CAPTURED_XPATHS_DIR, new)
    try:
        if not os.path.exists(old_path):
            return jsonify({'success': False, 'error': 'Old file does not exist'})
        if os.path.exists(new_path):
            return jsonify({'success': False, 'error': 'New file already exists'})
        os.rename(old_path, new_path)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
@app.route('/api/update_xpath', methods=['POST'])
def api_update_xpath():
    req = request.json
    page = req['page']
    idx = req['index']
    new_xpath = req['xpath']
    fpath = os.path.join(CAPTURED_XPATHS_DIR, page)
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            arr = json.load(f)
        if 0 <= idx < len(arr):
            arr[idx].setdefault('selectors', {})['xpath'] = new_xpath
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(arr, f, indent=2, ensure_ascii=False)
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': False, 'error': 'Invalid index'})
                
def open_browser(url):
    import time
    time.sleep(1.5)
    import webbrowser
    webbrowser.open(url)

if __name__ == '__main__':
    port = 5005
    url = f'http://127.0.0.1:{port}/'
    from multiprocessing import Process
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        Process(target=open_browser, args=(url,)).start()
    app.run(port=port, debug=True)
