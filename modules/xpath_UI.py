import os
import json
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

CAPTURED_XPATHS_DIR = os.path.join(os.path.dirname(__file__), '../captured_xpaths')
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '../config/xpath_ui_template.html')

def load_template():
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        return f.read()

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
    template = load_template()
    return render_template_string(template)

@app.route('/api/data')
def api_data():
    return jsonify(get_all_json_data())

@app.route('/api/update_name', methods=['POST'])
def api_update_name():
    try:
        req = request.json
        page = req['page']
        idx = req['index']
        new_name = req['name']
        fpath = os.path.join(CAPTURED_XPATHS_DIR, page)
        
        with open(fpath, 'r', encoding='utf-8') as f:
            arr = json.load(f)
        if 0 <= idx < len(arr):
            arr[idx]['name'] = new_name
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(arr, f, indent=2, ensure_ascii=False)
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Invalid index'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/reorder', methods=['POST'])
def api_reorder():
    try:
        req = request.json
        page = req['page']
        old_index = req['oldIndex']
        new_index = req['newIndex']
        fpath = os.path.join(CAPTURED_XPATHS_DIR, page)
        
        with open(fpath, 'r', encoding='utf-8') as f:
            arr = json.load(f)
        if 0 <= old_index < len(arr) and 0 <= new_index < len(arr):
            item = arr.pop(old_index)
            arr.insert(new_index, item)
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(arr, f, indent=2, ensure_ascii=False)
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Invalid indices'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/reorder_files', methods=['POST'])
def api_reorder_files():
    try:
        req = request.json
        old_index = req['oldIndex']
        new_index = req['newIndex']
        
        # Get list of JSON files
        files = [f for f in os.listdir(CAPTURED_XPATHS_DIR) if f.endswith('.json')]
        files.sort()
        
        if 0 <= old_index < len(files) and 0 <= new_index < len(files):
            file_to_move = files[old_index]
            files.remove(file_to_move)
            files.insert(new_index, file_to_move)
            
            # Update the order by renaming files with temporary names first
            temp_names = []
            for i, fname in enumerate(files):
                old_path = os.path.join(CAPTURED_XPATHS_DIR, fname)
                temp_name = f"temp_{i}_{fname}"
                temp_path = os.path.join(CAPTURED_XPATHS_DIR, temp_name)
                os.rename(old_path, temp_path)
                temp_names.append(temp_name)
            
            # Rename back to original names in the new order
            for temp_name, final_name in zip(temp_names, files):
                temp_path = os.path.join(CAPTURED_XPATHS_DIR, temp_name)
                final_path = os.path.join(CAPTURED_XPATHS_DIR, final_name)
                os.rename(temp_path, final_path)
                
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Invalid indices'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
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

@app.route('/api/delete_json', methods=['POST'])
def api_delete_json():
    req = request.json
    fname = req.get('file')
    if not fname or not fname.endswith('.json'):
        return jsonify({'success': False, 'error': 'Invalid file name'})
    fpath = os.path.join(CAPTURED_XPATHS_DIR, fname)
    try:
        if not os.path.exists(fpath):
            return jsonify({'success': False, 'error': 'File does not exist'})
        os.remove(fpath)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/delete_field', methods=['POST'])
def api_delete_field():
    req = request.json
    page = req.get('page')
    idx = req.get('index')
    if page is None or idx is None:
        return jsonify({'success': False, 'error': 'Missing page or index'})
    fpath = os.path.join(CAPTURED_XPATHS_DIR, page)
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            arr = json.load(f)
        idx = int(idx)
        if 0 <= idx < len(arr):
            arr.pop(idx)
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(arr, f, indent=2, ensure_ascii=False)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Invalid index'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = 5005
    url = f'http://127.0.0.1:{port}/'
    from multiprocessing import Process
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        Process(target=open_browser, args=(url,)).start()
    app.run(port=port, debug=True)
