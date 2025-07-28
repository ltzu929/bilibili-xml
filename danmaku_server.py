from flask import Flask, request, jsonify, Response, send_from_directory
import requests
import re
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 静态文件托管，支持直接通过 http://127.0.0.1:5000/ 访问前端页面
@app.route('/')
def index():
    return send_from_directory('webpage', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('webpage', path)

def get_cid_from_url(bilibili_url):
    """
    从B站视频URL中提取BV号或av号，并通过B站API获取cid（弹幕文件ID）
    """
    match = re.search(r'/video/(BV[0-9A-Za-z]+|av\\d+)', bilibili_url)
    if not match:
        return None
    vid = match.group(1)
    if vid.startswith('BV'):
        api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={vid}"
    else:
        api_url = f"https://api.bilibili.com/x/web-interface/view?aid={vid[2:]}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.bilibili.com"
    }
    resp = requests.get(api_url, headers=headers)
    print("B站API返回：", resp.text)  # 调试用
    if resp.status_code != 200:
        return None
    data = resp.json()
    cid = data.get("data", {}).get("cid")
    return cid

@app.route('/danmaku', methods=['GET'])
def get_danmaku():
    """
    弹幕代理接口，前端传入B站视频URL，返回弹幕XML
    """
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "Missing url parameter"}), 400
    cid = get_cid_from_url(video_url)
    if not cid:
        return jsonify({"error": "Invalid Bilibili video URL or failed to get cid"}), 400
    danmaku_url = f"https://comment.bilibili.com/{cid}.xml"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.bilibili.com"
    }
    resp = requests.get(danmaku_url, headers=headers)
    if resp.status_code != 200:
        return jsonify({"error": "Failed to fetch danmaku XML"}), 500
    return Response(resp.content, mimetype='application/xml')

if __name__ == '__main__':

    import threading
    import time

    app.run(host='127.0.0.1', port=5000)