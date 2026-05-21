import requests, re, json, os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def extract_video_id(url):
    patterns = [r'youtube\.com/watch\?v=([^&]+)', r'youtu\.be/([^?]+)']
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None

@app.route('/api/prepare', methods=['POST'])
def prepare():
    data = request.get_json()
    video_url = data.get('url')
    video_id = extract_video_id(video_url)
    if not video_id:
        return jsonify({'error': '无效链接'}), 400

    headers = {
        'origin': 'https://www.gzmp3.com',
        'referer': 'https://www.gzmp3.com/',
        'content-type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    prepare_resp = requests.post(
        'https://www.gzmp3.com/prepare.php',
        headers=headers,
        data={'url': f'https://www.youtube.com/watch?v={video_id}', 'format': 'mp3'},
        timeout=30
    )
    prepare_resp.raise_for_status()
    prepare_json = prepare_resp.json()
    file_name = prepare_json.get('file')
    if not file_name:
        return jsonify({'error': '获取 file 失败'}), 500

    download_url = f'https://www.gzmp3.com/download.php?file={file_name}'
    return jsonify({'download_url': download_url, 'file_name': file_name, 'video_id': video_id})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)