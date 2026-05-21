import requests
import re
from flask import Flask, request, jsonify
from flask_cors import CORS  # 解决前端跨域

app = Flask(__name__)
CORS(app)  # 允许所有域名访问，方便前端调试

def extract_video_id(url):
    """从 YouTube 链接提取 video ID"""
    patterns = [
        r'youtube\.com/watch\?v=([^&]+)',
        r'youtu\.be/([^?]+)',
        r'youtube\.com/embed/([^?]+)',
        r'youtube\.com/v/([^?]+)',
        r'youtube\.com/shorts/([^?]+)'
    ]
    for p in patterns:
        match = re.search(p, url)
        if match:
            return match.group(1)
    return None

def parse_with_gzmp3api(video_url):
    """核心逻辑：调用 gzmp3.com 获取下载链接"""
    video_id = extract_video_id(video_url)
    if not video_id:
        raise ValueError("无效的 YouTube 链接")
    
    headers = {
        "origin": "https://www.gzmp3.com",
        "referer": "https://www.gzmp3.com/",
        "content-type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # 第一步：prepare
    prepare_url = "https://www.gzmp3.com/prepare.php"
    data = {"url": f"https://www.youtube.com/watch?v={video_id}", "format": "mp3"}
    resp_pre = requests.post(prepare_url, headers=headers, data=data, timeout=30)
    resp_pre.raise_for_status()
    prepare_json = resp_pre.json()
    file_name = prepare_json.get('file')
    if not file_name:
        raise Exception("gzmp3.com 未返回 file 字段")
    
    # 第二步：获取下载地址（同时测试是否可访问）
    download_url = f"https://www.gzmp3.com/download.php?file={file_name}"
    resp_down = requests.get(download_url, headers=headers, timeout=30)
    resp_down.raise_for_status()
    
    # 提取文件信息
    content = resp_down.content
    file_size_bytes = len(content)
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
    # 尝试从 download_url 提取扩展名，默认 mp3
    ext = download_url.split('.')[-1].split('?')[0]
    if ext not in ['mp3', 'm4a', 'webm']:
        ext = 'mp3'
    
    # 获取视频标题（可选：从 gzmp3 页面或 YouTube 原始信息抓取，这里简单使用 video_id）
    title = f"YouTube Video {video_id}"
    thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    
    return {
        "success": True,
        "video_id": video_id,
        "title": title,
        "thumbnail": thumbnail,
        "download_url": download_url,
        "file_size_bytes": file_size_bytes,
        "file_size_mb": file_size_mb,
        "ext": ext,
        "filename": f"{video_id}.{ext}"
    }

@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"success": False, "error": "缺少 url 参数"}), 400
    
    video_url = data['url'].strip()
    try:
        result = parse_with_gzmp3api(video_url)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/')
def index():
    return jsonify({"message": "YouTube MP3 API is running", "endpoint": "/api/download"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)