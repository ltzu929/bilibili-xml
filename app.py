from flask import Flask, render_template, request, jsonify, url_for, send_file
import re
import requests
import json
import logging
import jieba
import jieba.analyse
import numpy as np
from scipy import signal
from collections import defaultdict
import os
import time
import sqlite3
import xml.etree.ElementTree as ET
from datetime import datetime
import matplotlib.pyplot as plt
import tempfile
import shutil
import zipfile
import io
import base64
import atexit
import signal as sys_signal

# 配置日志
logging.basicConfig(level=logging.INFO)

# 创建Flask应用
app = Flask(__name__)

# 确保数据目录存在
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    
# 确保缓存目录存在
CACHE_DIR = os.path.join(DATA_DIR, 'cache')
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# 加载自定义词典
dict_path = os.path.join(DATA_DIR, 'user_dict.txt')
if os.path.exists(dict_path):
    jieba.load_userdict(dict_path)

# 清理缓存的函数
def clean_cache():
    """清理缓存目录中的所有文件"""
    try:
        if os.path.exists(CACHE_DIR):
            for filename in os.listdir(CACHE_DIR):
                file_path = os.path.join(CACHE_DIR, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    logging.error(f"清理缓存文件失败: {str(e)}")
            logging.info("缓存已清理")
    except Exception as e:
        logging.error(f"清理缓存目录失败: {str(e)}")

# 注册程序退出时的回调函数，清理缓存
atexit.register(clean_cache)

# 注册信号处理，确保在不同情况下都能清理缓存
def signal_handler(sig, frame):
    """处理终止信号，清理缓存后退出"""
    clean_cache()
    exit(0)

# 注册常见的终止信号
sys_signal.signal(sys_signal.SIGINT, signal_handler)  # Ctrl+C
sys_signal.signal(sys_signal.SIGTERM, signal_handler) # 终止信号

# 路由：首页
@app.route('/')
def index():
    return render_template('index.html')

# API路由：分析弹幕
@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    video_url = data.get('video_url')
    
    if not video_url:
        return jsonify({"error": "未提供视频URL"}), 400
    
    try:
        # 从URL中提取视频ID
        video_id = extract_video_id(video_url)
        if not video_id:
            return jsonify({"error": "无法从URL中提取视频ID"}), 400
            
        # 获取视频分P信息
        video_info = get_video_info(video_id)
        if not video_info or not video_info.get('cids'):
            return jsonify({"error": "无法获取视频信息"}), 400
            
        # 分析弹幕
        result = process_danmaku(video_id, video_info)
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"分析失败: {str(e)}", exc_info=True)
        return jsonify({"error": f"分析失败: {str(e)}"}), 500

# API路由：导出分析结果
@app.route('/api/export', methods=['POST'])
def export_results():
    data = request.json
    export_type = data.get('type', 'csv')
    analysis_data = data.get('data')
    
    if not analysis_data:
        return jsonify({"error": "未提供分析数据"}), 400
        
    try:
        if export_type == 'csv':
            # 创建临时文件
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, 'danmaku_analysis.zip')
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                # 导出弹幕密度数据
                density_path = os.path.join(temp_dir, 'density.csv')
                with open(density_path, 'w', encoding='utf-8') as f:
                    f.write('时间(秒),弹幕数量\n')
                    for i, count in zip(analysis_data['density']['x'], analysis_data['density']['total']):
                        f.write(f'{i},{count}\n')
                zipf.write(density_path, 'density.csv')
                
                # 导出热词数据
                hotwords_path = os.path.join(temp_dir, 'hotwords.csv')
                with open(hotwords_path, 'w', encoding='utf-8') as f:
                    f.write('时间段,关键词,权重\n')
                    for period, words in analysis_data['hot_words']:
                        for word, weight in words:
                            f.write(f'{period},{word},{weight}\n')
                zipf.write(hotwords_path, 'hotwords.csv')
                
                # 导出弹幕内容
                comments_path = os.path.join(temp_dir, 'comments.csv')
                with open(comments_path, 'w', encoding='utf-8') as f:
                    f.write('时间(秒),弹幕内容\n')
                    for second, comments in analysis_data['comments'].items():
                        for comment in comments:
                            f.write(f'{second},"{comment}"\n')
                zipf.write(comments_path, 'comments.csv')
            
            # 返回ZIP文件
            return send_file(zip_path, mimetype='application/zip',
                             as_attachment=True, download_name='danmaku_analysis.zip')
        
        elif export_type == 'image':
            # 创建图表图像
            plt.figure(figsize=(10, 6))
            plt.plot(analysis_data['density']['x'], analysis_data['density']['total'])
            plt.title('弹幕密度分析')
            plt.xlabel('时间(秒)')
            plt.ylabel('弹幕数量')
            plt.grid(True)
            
            # 保存为内存中的图像
            img_io = io.BytesIO()
            plt.savefig(img_io, format='png')
            img_io.seek(0)
            plt.close()
            
            # 转为base64
            img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
            return jsonify({'image': f'data:image/png;base64,{img_base64}'})
        
        else:
            return jsonify({"error": "不支持的导出类型"}), 400
    
    except Exception as e:
        logging.error(f"导出失败: {str(e)}")
        return jsonify({"error": f"导出失败: {str(e)}"}), 500
    finally:
        # 清理临时文件
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir, ignore_errors=True)

def extract_video_id(url):
    """从URL中提取视频ID"""
    # 提取BV号
    bv_match = re.search(r'bilibili\.com/video/([^/?&#]+)', url)
    if bv_match:
        return bv_match.group(1)
    return None

def get_video_info(video_id):
    """获取视频信息，包括标题、分P信息等"""
    try:
        # 检查缓存
        cache_file = os.path.join(CACHE_DIR, f"{video_id}_info.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 获取视频分P列表
        api_url = f"https://api.bilibili.com/x/player/pagelist?bvid={video_id}&jsonp=jsonp"
        response = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        
        page_data = response.json()
        if page_data["code"] != 0:
            logging.error(f"获取视频信息失败: {page_data['message']}")
            return None
            
        pagelist = page_data["data"]
        if not pagelist:
            logging.error("未找到视频分P信息")
            return None
            
        # 获取视频基本信息
        api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={video_id}"
        response = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        
        video_data = response.json()
        if video_data["code"] != 0:
            logging.error(f"获取视频信息失败: {video_data['message']}")
            return None
        
        # 整合信息
        result = {
            "title": video_data["data"]["title"],
            "author": video_data["data"]["owner"]["name"],
            "cids": [page["cid"] for page in pagelist],
            "pages": [{
                "cid": page["cid"],
                "page": page["page"],
                "part": page["part"],
                "duration": page["duration"]
            } for page in pagelist]
        }
        
        # 保存到缓存
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f)
            
        return result
    except Exception as e:
        logging.error(f"获取视频信息失败: {str(e)}")
        return None

def get_danmaku(video_id, cid):
    """获取指定CID的弹幕数据"""
    try:
        # 检查缓存
        cache_file = os.path.join(CACHE_DIR, f"{video_id}_{cid}_danmaku.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 获取弹幕XML
        api_url = f"https://api.bilibili.com/x/v1/dm/list.so?oid={cid}"
        response = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        
        # 解析XML
        root = ET.fromstring(response.content)
        danmaku_list = []
        
        for d in root.findall('.//d'):
            p_attrs = d.get('p').split(',')
            danmaku_list.append({
                "time": float(p_attrs[0]),  # 出现时间（秒）
                "type": int(p_attrs[1]),    # 弹幕类型
                "size": int(p_attrs[2]),    # 字体大小
                "color": int(p_attrs[3]),   # 颜色
                "timestamp": int(p_attrs[4]), # 时间戳
                "pool": int(p_attrs[5]),    # 弹幕池
                "user_id": p_attrs[6],      # 用户ID（加密）
                "row_id": p_attrs[7],       # 弹幕ID
                "text": d.text              # 弹幕内容
            })
        
        # 保存到缓存
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(danmaku_list, f)
            
        return danmaku_list
    except Exception as e:
        logging.error(f"获取弹幕失败: {str(e)}")
        return []

def process_danmaku(video_id, video_info):
    """处理弹幕数据"""
    all_danmaku = []
    
    # 获取所有分P的弹幕
    for cid in video_info['cids']:
        danmaku = get_danmaku(video_id, cid)
        all_danmaku.extend(danmaku)
    
    # 弹幕按时间排序
    all_danmaku.sort(key=lambda x: x['time'])
    
    # 按秒统计弹幕数量（而非分钟）
    density = defaultdict(int)
    call_density = defaultdict(int)  # 打call密度统计
    ha_density = defaultdict(int)    # "哈"密度统计
    question_density = defaultdict(int)  # "？"密度统计
    comments_by_second = defaultdict(list)
    
    for dm in all_danmaku:
        # 使用秒作为索引，而不是分钟
        second = int(dm['time'])
        text = dm['text']
        density[second] += 1
        comments_by_second[second].append(text)
        
        # 识别打call弹幕
        if re.search(r'[oO]+[hH]*|[wW]+|666+|233+|前方高能|awsl|kksk|wsl|草|114514', text):
            call_density[second] += 1
            
        # 识别"哈"弹幕
        if re.search(r'[哈嗨]|h{2,}a{1,}', text, re.IGNORECASE):
            ha_density[second] += 1
            
        # 识别带问号的弹幕
        if '？' in text or '?' in text:
            question_density[second] += 1
    
    # 获取时间范围（秒）
    max_second = max(density.keys()) if density else 0
    
    # 填充缺失的秒数
    x_axis = []
    y_axis = []
    call_y_axis = []
    ha_y_axis = []
    question_y_axis = []
    
    # 为了减少数据量，可以考虑每5秒或10秒采样一次
    # 这里使用每秒都记录的方式
    for i in range(max_second + 1):
        x_axis.append(i)
        y_axis.append(density[i])
        call_y_axis.append(call_density[i])
        ha_y_axis.append(ha_density[i])
        question_y_axis.append(question_density[i])
    
    # 弹幕平滑处理
    if len(y_axis) > 2:
        # 确保窗口长度是奇数且小于数据长度
        window_length = min(21, len(y_axis) - 1)  # 使用更大的窗口，因为数据点更多了
        # 如果长度是偶数，减1使其变为奇数
        if window_length % 2 == 0:
            window_length -= 1
        # 确保窗口长度至少为3（savgol_filter的最小要求）
        window_length = max(3, window_length)
        
        # 只有当数据点足够多时才进行平滑
        if window_length < len(y_axis):
            smooth_y = signal.savgol_filter(y_axis, window_length, 2)
            smooth_y = [max(0, int(y)) for y in smooth_y]
        else:
            smooth_y = y_axis
    else:
        smooth_y = y_axis

    # 打call平滑处理
    if len(call_y_axis) > 2:
        window_length = min(21, len(call_y_axis) - 1)
        if window_length % 2 == 0:
            window_length -= 1
        window_length = max(3, window_length)
        
        if window_length < len(call_y_axis):
            smooth_call_y = signal.savgol_filter(call_y_axis, window_length, 2)
            smooth_call_y = [max(0, int(y)) for y in smooth_call_y]
        else:
            smooth_call_y = call_y_axis
    else:
        smooth_call_y = call_y_axis
    
    # "哈"密度平滑处理
    if len(ha_y_axis) > 2:
        window_length = min(21, len(ha_y_axis) - 1)
        if window_length % 2 == 0:
            window_length -= 1
        window_length = max(3, window_length)
        
        if window_length < len(ha_y_axis):
            smooth_ha_y = signal.savgol_filter(ha_y_axis, window_length, 2)
            smooth_ha_y = [max(0, int(y)) for y in smooth_ha_y]
        else:
            smooth_ha_y = ha_y_axis
    else:
        smooth_ha_y = ha_y_axis
    
    # "？"密度平滑处理
    if len(question_y_axis) > 2:
        window_length = min(21, len(question_y_axis) - 1)
        if window_length % 2 == 0:
            window_length -= 1
        window_length = max(3, window_length)
        
        if window_length < len(question_y_axis):
            smooth_question_y = signal.savgol_filter(question_y_axis, window_length, 2)
            smooth_question_y = [max(0, int(y)) for y in smooth_question_y]
        else:
            smooth_question_y = question_y_axis
    else:
        smooth_question_y = question_y_axis
    
    # 格式化时间函数 - 移到这里，在使用前定义
    def format_time(seconds):
        minutes, secs = divmod(seconds, 60)
        return f"{minutes:02d}:{secs:02d}"
    
    # 分析热词 - 现在使用更小的窗口，比如每30秒
    hot_words = []
    window_size = 30  # 30秒一个窗口
    
    for start in range(0, max_second + 1, window_size):
        end = min(start + window_size, max_second + 1)
        window_comments = []
        
        for i in range(start, end):
            window_comments.extend(comments_by_second[i])
        
        if window_comments:
            # 过滤特殊符号和短弹幕
            filtered_comments = []
            for comment in window_comments:
                # 过滤掉纯表情、特殊符号等
                if re.search(r'[\u4e00-\u9fa5a-zA-Z0-9]', comment):
                    filtered_comments.append(comment)
            
            if filtered_comments:
                # 提取关键词
                text = ' '.join(filtered_comments)
                keywords = jieba.analyse.extract_tags(text, topK=10, withWeight=True)
                hot_words.append([f"{format_time(start)}-{format_time(end-1)}", [(word, round(weight * 100, 2)) for word, weight in keywords]])
    
    # 提取时间戳信息并转换为MM:SS格式
    timestamp_format = {}
    start_timestamp = None
    
    for dm in all_danmaku:
        if start_timestamp is None:
            start_timestamp = dm['timestamp'] / 1000
        
        # 计算相对于开始的时间（秒）
        relative_second = int(dm['time'])
        actual_time = datetime.fromtimestamp(dm['timestamp'] / 1000)
        formatted_time = actual_time.strftime("%H:%M:%S")
        
        if relative_second not in timestamp_format:
            timestamp_format[relative_second] = formatted_time
    
    # 确保弹幕数据格式统一并且是按索引排序的
    comments_indexed = {}
    for i in range(max_second + 1):
        # 将每秒的弹幕数据转换为列表并保存
        comments_indexed[str(i)] = comments_by_second.get(i, [])[:50]  # 每秒最多50条弹幕
    
    # 准备格式化的时间轴标签
    time_labels = {}
    for second in x_axis:
        time_labels[str(second)] = format_time(second)
    
    # 返回结果
    return {
        "density": {
            "x": x_axis,
            "total": y_axis,
            "smooth": smooth_y,
            "time_labels": time_labels  # 添加格式化的时间标签
        },
        "call_density": smooth_call_y,
        "ha_density": smooth_ha_y,
        "question_density": smooth_question_y,
        "hot_words": hot_words,
        "comments": comments_indexed,  # 使用规范化的索引结构
        "video_info": {
            "title": video_info["title"],
            "author": video_info["author"]
        },
        "time_format": timestamp_format,
        "start_time": datetime.fromtimestamp(start_timestamp).strftime("%H:%M:%S") if start_timestamp else "00:00:00",
        "duration_seconds": max_second
    }

if __name__ == '__main__':
    app.run(debug=True)