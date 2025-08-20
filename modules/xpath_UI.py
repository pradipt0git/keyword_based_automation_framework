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
        :root {
            --bg-main: #1e1e1e;
            --bg-secondary: #252526;
            --bg-hover: #2a2d2e;
            --text-primary: #cccccc;
            --text-secondary: #858585;
            --accent-blue: #0e639c;
            --accent-blue-hover: #1177bb;
            --border-color: #454545;
            --tree-line-color: #353535;
            --input-bg: #3c3c3c;
            --tree-indent: 20px;
        }
        body {
            background: var(--bg-main);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            margin: 0;
            padding: 20px;
            line-height: 1.4;
        }
        h2 {
            color: var(--text-primary);
            margin: 0 0 20px 0;
            font-weight: 400;
            font-size: 1.5em;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
        }
        #tree-root {
            margin: 20px 0;
            padding: 0;
            background: var(--bg-secondary);
            border-radius: 6px;
            border: 1px solid var(--border-color);
        }
        ul {
            list-style-type: none;
            padding-left: 20px;
            margin: 0;
            position: relative;
        }
        li {
            margin: 2px 0;
            position: relative;
            padding-left: 20px;
        }
        /* Tree node container */
        .tree-node {
            position: relative;
            display: flex;
            align-items: center;
            min-height: 28px;
        }
        /* Button container */
        .tree-controls {
            position: absolute;
            left: -20px;
            top: 0;
            bottom: 0;
            width: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .child-list {
            max-height: 0;
            overflow: hidden;
            opacity: 0;
            transition: all 0.3s ease-out;
            transform: translateY(-10px);
        }
        li.open > .child-list {
            max-height: 2000px;
            opacity: 1;
            overflow: visible;
            transform: translateY(0);
        }
        /* Tree structure */
        li:last-child > .tree-node > .tree-line-container > .tree-line-vertical {
            display: none;
        }
        .element-details {
            display: none;
            margin: 0;
            max-height: 0;
            overflow: hidden;
            background: var(--bg-main);
            border-radius: 4px;
            border: 1px solid var(--border-color);
            padding: 0;
            position: relative;
            transform: translateY(-10px);
            opacity: 0;
            transition: all 0.3s ease-out, opacity 0.3s ease-out;
            will-change: max-height, padding, margin, opacity, transform;
        }
        .element-details::before {
            content: "";
            position: absolute;
            left: -16px;
            top: -8px;
            bottom: 8px;
            width: 2px;
            background: var(--border-color);
            opacity: 0;
            transition: opacity 0.3s ease-out;
        }
        .element-details.expanded {
            display: block;
        }
        .element.open > .element-details {
            transform: translateY(0);
        }
        .element.open > .element-details::before {
            opacity: 1;
        }
        /* Ensure buttons are clickable */
        .tree-btn {
            z-index: 2;
            cursor: pointer;
            position: relative;
        }

        /* JSON Container Styles */
        .json-container {
            margin-top: 12px;
            border-top: 1px solid var(--border-color);
            padding-top: 12px;
        }

        .json-toggle {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            padding: 4px 8px;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 6px;
            margin: 0;
            transition: color 0.2s ease;
        }

        .json-toggle:hover {
            color: var(--text-primary);
        }

        .toggle-icon {
            font-family: monospace;
            font-size: 14px;
            display: inline-block;
            width: 12px;
            text-align: center;
            transition: transform 0.3s ease;
        }

        .json-container.expanded .toggle-icon {
            transform: rotate(180deg);
        }

        .json-content {
            max-height: 0;
            overflow: hidden;
            opacity: 0;
            transition: all 0.3s ease-out;
            margin-top: 8px;
            background: var(--bg-main);
            border-radius: 4px;
        }

        .json-container.expanded .json-content {
            opacity: 1;
            padding: 8px;
            border: 1px solid var(--border-color);
            margin-bottom: 8px;
        }
        .element-name-input {
            width: 220px;
            background: var(--input-bg);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 6px 8px;
            font-size: 13px;
            transition: all 0.2s;
        }
        .element-name-input:focus {
            outline: none;
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 1px var(--accent-blue);
        }
        .item-container {
            display: flex;
            align-items: center;
            min-height: 28px;
            position: relative;
            padding: 2px 0;
        }
        button {
            background: transparent;
            color: var(--text-secondary);
            border: none;
            padding: 4px;
            margin: 0 4px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 24px;
            height: 24px;
            transition: color 0.2s;
        }
        button:active {
            background: #1a1d22;
        }
        button:focus {
            outline: 2px solid #4e9cff;
        }
        button[disabled] {
            opacity: 0.5;
            cursor: not-allowed;
        }
        button.save-btn {
            background: linear-gradient(90deg, #2d7cff 60%, #4e9cff 100%);
            color: #fff;
            font-weight: bold;
            box-shadow: 0 2px 8px #4e9cff33;
        }
        button.save-btn:hover {
            background: linear-gradient(90deg, #4e9cff 60%, #2d7cff 100%);
            color: #fff;
        }
        button.tree-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-family: monospace;
            font-size: 14px;
            padding: 0;
            margin: 0;
            width: 20px;
            height: 20px;
            line-height: 20px;
            display: flex;
            align-items: center;
            transition: transform 0.3s ease;
            justify-content: center;
            z-index: 2;
            opacity: 0.7;
            border-radius: 3px;
            position: relative;
            width: 16px;
            height: 16px;
            font-size: 16px;
            line-height: 16px;
        }
        button.tree-btn::before {
            content: attr(data-icon);
            display: block;
            width: 16px;
            height: 16px;
            text-align: center;
            line-height: 16px;
            transition: transform 0.3s ease;
        }
        .open > div > .tree-controls > .tree-btn::before {
            transform: rotate(90deg);
        }
        button.tree-btn:hover {
            background: var(--bg-hover);
            opacity: 1;
        }
        .tree-toggle {
            cursor: pointer;
        }
        li.collapsed > ul {
            display: none;
        }
        li.collapsed > button.tree-btn {
            color: #4e9cff;
        }
        pre {
            background: #181c20;
            color: #b8e1ff;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            overflow-x: auto;
        }
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 10px;
            background: #23272e;
        }
        ::-webkit-scrollbar-thumb {
            background: #333a;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <h2>XPath UI Tree View</h2>
    <div class="action-buttons">
        <button id="capture-xpath-btn">Capture XPath</button>
        <button id="stop-capture-btn">Stop Capture</button>
        <button id="refresh-btn">↻ Refresh</button>
    </div>
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
            const treeNode = document.createElement('div');
            treeNode.className = 'tree-node';
            
            // Tree lines
            const lineContainer = document.createElement('div');
            lineContainer.className = 'tree-line-container';
            const verticalLine = document.createElement('div');
            verticalLine.className = 'tree-line-vertical';
            const horizontalLine = document.createElement('div');
            horizontalLine.className = 'tree-line-horizontal';
            lineContainer.appendChild(verticalLine);
            lineContainer.appendChild(horizontalLine);
            treeNode.appendChild(lineContainer);
            
            // Controls container (for button)
            const treeControls = document.createElement('div');
            treeControls.className = 'tree-controls';
            treeNode.appendChild(treeControls);
            
            const itemContainer = document.createElement('div');
            itemContainer.className = 'item-container';
            
            // Page collapse/expand button
            const pageCollapseBtn = document.createElement('button');
            pageCollapseBtn.setAttribute('data-icon', '+');
            pageCollapseBtn.title = 'Expand/Collapse';
            pageCollapseBtn.className = 'tree-btn';
            // Button positioning handled by CSS
            pageCollapseBtn.onclick = () => {
                pageLi.classList.toggle('open');
                pageCollapseBtn.setAttribute('data-icon', pageLi.classList.contains('open') ? '>' : '+');
            };
            
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
            saveBtn.innerHTML = '✓';
            saveBtn.title = 'Save (rename file)';
            saveBtn.className = 'save-btn';
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
            // Tree toggle (for spacing only)
            const pageToggle = document.createElement('span');
            pageToggle.textContent = ' ';
            pageToggle.className = 'tree-toggle';
            treeControls.appendChild(pageCollapseBtn);
            itemContainer.appendChild(fileNameInput);
            itemContainer.appendChild(saveBtn);
            treeNode.appendChild(itemContainer);
            pageLi.appendChild(treeNode);
            const ul = document.createElement('ul');
            ul.classList.add('child-list');
            elements.forEach((el, elIdx) => {
                const elLi = document.createElement('li');
                elLi.className = 'element';
                
                const treeNode = document.createElement('div');
                treeNode.className = 'tree-node';
                
                // Tree spacing for hierarchy
                
                // Controls container (for button)
                const treeControls = document.createElement('div');
                treeControls.className = 'tree-controls';
                treeNode.appendChild(treeControls);
                
                const itemContainer = document.createElement('div');
                itemContainer.className = 'item-container';
                
                // Expand/collapse button
                const expandBtn = document.createElement('button');
                expandBtn.setAttribute('data-icon', '+');
                expandBtn.className = 'tree-btn';
                expandBtn.title = 'Expand/Collapse';
                expandBtn.addEventListener('click', function(e) {
                    console.log('Click detected on element button');
                    e.stopPropagation(); // Prevent event bubbling
                    elLi.classList.toggle('open');
                    expandBtn.setAttribute('data-icon', elLi.classList.contains('open') ? '>' : '+');
                    
                    // Remove previous transition end listener if exists
                    detailsDiv.removeEventListener('transitionend', detailsDiv._transitionEndHandler);
                    
                    if (elLi.classList.contains('open')) {
                        console.log('Opening element details');
                        // Set initial height to trigger animation
                        detailsDiv.style.display = 'block';
                        setTimeout(() => {
                            detailsDiv.style.padding = '12px';
                            detailsDiv.style.margin = '8px 0 8px 12px';
                            const height = detailsDiv.scrollHeight;
                            console.log('Content height:', height);
                            detailsDiv.style.maxHeight = height + 'px';
                            detailsDiv.style.opacity = '1';
                        }, 10);
                    } else {
                        console.log('Closing element details');
                        detailsDiv.style.maxHeight = '0';
                        detailsDiv.style.padding = '0';
                        detailsDiv.style.margin = '0';
                        detailsDiv.style.opacity = '0';
                        
                        // Add transition end listener
                        detailsDiv._transitionEndHandler = function() {
                            if (!elLi.classList.contains('open')) {
                                detailsDiv.style.display = 'none';
                            }
                        };
                        detailsDiv.addEventListener('transitionend', detailsDiv._transitionEndHandler);
                    }
                });
                
                // Name input and save button
                const nameInput = document.createElement('input');
                nameInput.type = 'text';
                nameInput.value = el.name || '';
                nameInput.className = 'element-name-input';
                
                const saveNameBtn = document.createElement('button');
                saveNameBtn.innerHTML = '✓';
                saveNameBtn.title = 'Save Name';
                saveNameBtn.className = 'save-btn';
                saveNameBtn.onclick = async () => {
                    const newName = nameInput.value;
                    await fetch('/api/update_name', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ page, index: elIdx, name: newName })
                    });
                };
                treeControls.appendChild(expandBtn);
                itemContainer.appendChild(nameInput);
                itemContainer.appendChild(saveNameBtn);
                treeNode.appendChild(itemContainer);
                elLi.appendChild(treeNode);
                // Details (collapsible JSON)
                const detailsDiv = document.createElement('div');
                detailsDiv.className = 'element-details';

                const detailsContent = document.createElement('div');
                detailsContent.className = 'details-content';
                detailsDiv.appendChild(detailsContent);

                // Xpath textbox and save button (shown after expand/collapse)
                const xpathBox = document.createElement('input');
                xpathBox.type = 'text';
                xpathBox.value = (el.selectors && el.selectors.xpath) ? el.selectors.xpath : '';
                xpathBox.className = 'element-name-input';
                xpathBox.style.marginBottom = '4px';
                xpathBox.style.width = '70%';
                const saveXpathBtn = document.createElement('button');
                saveXpathBtn.innerHTML = '✓';
                saveXpathBtn.title = 'Save XPath';
                saveXpathBtn.className = 'save-btn';
                saveXpathBtn.onclick = async () => {
                    const newXpath = xpathBox.value;
                    await fetch('/api/update_xpath', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ page, index: elIdx, xpath: newXpath })
                    });
                };
                // Use custom collapsible for JSON display
                const jsonContainer = document.createElement('div');
                jsonContainer.className = 'json-container';
                
                const jsonToggle = document.createElement('button');
                jsonToggle.className = 'json-toggle';
                jsonToggle.innerHTML = '<span class="toggle-icon">+</span> Show JSON';
                
                const jsonContent = document.createElement('div');
                jsonContent.className = 'json-content';
                
                // Pretty JSON with syntax highlighting
                const pre = document.createElement('pre');
                pre.style.margin = '0';
                pre.style.fontSize = '13px';
                
                jsonToggle.addEventListener('click', function() {
                    const isExpanded = jsonContainer.classList.toggle('expanded');
                    this.querySelector('.toggle-icon').textContent = isExpanded ? '−' : '+';
                    
                    if (isExpanded) {
                        // First set a minimum height to make content visible for calculation
                        jsonContent.style.maxHeight = '1000px';
                        // Calculate the real heights
                        const jsonHeight = jsonContent.scrollHeight;
                        const preHeight = pre.offsetHeight;
                        // Set the actual heights
                        jsonContent.style.maxHeight = (preHeight + 16) + 'px'; // Adding padding
                        
                        // Update parent details div height
                        setTimeout(() => {
                            const totalHeight = detailsDiv.scrollHeight;
                            detailsDiv.style.maxHeight = totalHeight + 'px';
                        }, 0);
                    } else {
                        jsonContent.style.maxHeight = '0';
                        // Update parent details div height after json collapse
                        setTimeout(() => {
                            const totalHeight = detailsDiv.scrollHeight;
                            detailsDiv.style.maxHeight = totalHeight + 'px';
                        }, 300); // Wait for JSON collapse animation
                    }
                });
                pre.textContent = JSON.stringify(el, null, 2);
                jsonContent.appendChild(pre);
                jsonContainer.appendChild(jsonToggle);
                jsonContainer.appendChild(jsonContent);
                
                detailsContent.appendChild(xpathBox);
                detailsContent.appendChild(saveXpathBtn);
                detailsContent.appendChild(jsonContainer);
                elLi.appendChild(detailsDiv);
                // Initialize the element as collapsed
                elLi.classList.remove('open');
                detailsDiv.style.display = 'none';
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
