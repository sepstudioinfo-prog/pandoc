from flask import Flask, request, send_file, jsonify
import subprocess
import tempfile
import os
import uuid
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <h1>Markdown → DOCX Converter</h1>
    <p>Send POST request to /convert with markdown in body</p>
    <form method="POST" action="/convert" enctype="multipart/form-data">
        <textarea name="markdown" rows="10" cols="50" placeholder="Type markdown here..."></textarea><br>
        <input type="submit" value="Convert to DOCX">
    </form>
    '''

@app.route('/convert', methods=['POST'])
def convert():
    try:
        # Get markdown from form or raw body
        if request.form.get('markdown'):
            md_content = request.form['markdown']
        else:
            md_content = request.data.decode('utf-8')
        
        if not md_content.strip():
            return jsonify({'error': 'Empty markdown content'}), 400
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as md_file:
            md_file.write(md_content)
            md_path = md_file.name
        
        docx_path = f"/tmp/{uuid.uuid4()}.docx"
        
        # Run pandoc conversion
        result = subprocess.run(
            ['pandoc', md_path, '-o', docx_path],
            capture_output=True,
            text=True,
            timeout=60  # 60 seconds max
        )
        
        # Clean up markdown file
        os.unlink(md_path)
        
        if result.returncode != 0:
            return jsonify({'error': f'Pandoc error: {result.stderr}'}), 500
        
        # Send the DOCX file
        return send_file(
            docx_path,
            as_attachment=True,
            download_name=f'converted_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx',
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Conversion timed out (60s limit)'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'markdown-to-docx'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)