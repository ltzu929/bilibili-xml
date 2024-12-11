import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from collections import defaultdict, Counter
import tkinter as tk
from tkinter import filedialog
import requests
import re
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 选择中文字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def extract_url_from_input(input_text):
    """
    从用户输入的文本中提取Bilibili视频URL。
    """
    pattern = r'https?://www\.bilibili\.com/video/(BV[0-9A-Za-z]+|av\d+)(\?.*)?'
    match = re.search(pattern, input_text)
    return match.group(0) if match else None

def is_valid_bilibili_url(url):
    """
    验证URL是否为有效的Bilibili视频URL。
    """
    pattern = r'^https?://www\.bilibili\.com/video/(BV[0-9A-Za-z]+|av\d+)(\?.*)?$'
    return re.match(pattern, url) is not None

def get_video_id(url):
    """
    从URL中提取视频ID。
    """
    match = re.search(r'/video/(BV[0-9A-Za-z]+|av\d+)', url)
    return match.group(1) if match else None

def get_danmaku_url(video_id):
    """
    根据视频ID获取弹幕文件的URL。
    """
    try:
        api_url = f"https://api.bilibili.com/x/player/pagelist?bvid={video_id}" if video_id.startswith("BV") else f"https://api.bilibili.com/x/player/pagelist?aid={video_id[2:]}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
            "Referer": "https://www.bilibili.com",
        }
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data['code'] == 0:
            cid = data['data'][0]['cid']  # 默认取第一个分P的CID
            return f"https://comment.bilibili.com/{cid}.xml"
        else:
            print("无法获取CID:", data['message'])
    except requests.RequestException as e:
        print(f"请求弹幕API时出错: {e}")
    return None

def download_danmaku(danmaku_url, output_path):
    """
    下载弹幕文件到本地。
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
            "Referer": "https://www.bilibili.com",
        }
        response = requests.get(danmaku_url, headers=headers, timeout=10)
        response.raise_for_status()

        with open(output_path, "wb") as file:
            file.write(response.content)
        print(f"弹幕文件已成功下载到: {output_path}")
    except requests.RequestException as e:
        print(f"下载弹幕文件时出错: {e}")

def preprocess_danmaku(content):
    """
    预处理弹幕内容，将只包含“哈”的弹幕视为“哈”，只包含“?”的弹幕视为“?”，
    只包含“草”的弹幕视为“草”，只包含“艹”的弹幕视为“艹”。忽略包含“晚安”的弹幕。
    只包含数字'1'的弹幕视为'1'。

    Args:
        content (str): 弹幕内容。

    Returns:
        str: 预处理后的弹幕内容，如果弹幕包含“晚安”则返回空字符串。
    """
    if "晚安" in content or "晚上好" in content:
        return ""  # 忽略包含“晚安”的弹幕

    # 检查是否只包含某个特定字符
    if len(set(content)) == 1:
        char = content[0]
        if char == '哈' or char == '?' or char == '草' or char == '艹' or char == '1':
            return char

    return content

def plot_danmaku_statistics(xml_file_path):
    """
    解析XML文件中的弹幕数据，并绘制弹幕数量每分钟的统计图表。

    Args:
        xml_file_path (str): XML文件的路径。
    """
    # 解析XML文件
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # 存储每分钟的弹幕数量和内容
    danmaku_per_minute = defaultdict(list)

    # 遍历所有弹幕元素
    for d in root.findall('d'):
        # 获取属性p并拆分
        p = d.get('p').split(',')
        time = float(p[0])  # 弹幕出现时间（秒）
        content = d.text  # 弹幕内容
        
        # 预处理弹幕内容
        content = preprocess_danmaku(content)
        
        # 忽略被标记为空字符串的弹幕
        if not content:
            continue
        
        # 计算分钟数
        minute = int(time // 60)
        
        # 存储弹幕内容到对应的分钟
        danmaku_per_minute[minute].append(content)

    # 统计每分钟的弹幕数量
    minutes = sorted(danmaku_per_minute.keys())
    danmaku_counts = [len(danmaku_per_minute[minute]) for minute in minutes]

    # 找出弹幕数量最多的5个分钟
    top_5_minutes = sorted(zip(minutes, danmaku_counts), key=lambda x: x[1], reverse=True)[:5]

    # 获取每个分钟内弹幕数量最多的弹幕内容
    top_danmaku_info = []
    for minute, count in top_5_minutes:
        counter = Counter(danmaku_per_minute[minute])
        most_common_danmaku, most_common_count = counter.most_common(1)[0]
        top_danmaku_info.append((minute, count, most_common_danmaku, most_common_count))

    # 设置图表样式
    plt.style.use('ggplot')  # 使用ggplot风格

    # 创建图表
    fig, ax = plt.subplots(figsize=(14, 7))

    # 绘制弹幕数量曲线
    line, = ax.plot(minutes, danmaku_counts, marker='o', linestyle='-', color='blue', label='弹幕数量')

    # 添加标题和轴标签
    ax.set_title('弹幕数量每分钟统计', fontsize=16, fontweight='bold')
    ax.set_xlabel('分钟', fontsize=14)
    ax.set_ylabel('弹幕数量', fontsize=14)

    # 调整刻度标签字体大小
    ax.tick_params(axis='both', which='major', labelsize=12)

    # 添加网格
    ax.grid(True, linestyle='--', alpha=0.7)

    # 设置刻度间隔
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    # 添加图例
    ax.legend(fontsize=12)

    # 标记弹幕数量突增的点
    threshold = 10  # 增加阈值以减少标记的突增点
    previous_count = 0
    spike_minutes = []

    for i, count in enumerate(danmaku_counts):
        if count > previous_count + threshold:
            spike_minutes.append(minutes[i])
        previous_count = count

    # 在突增点添加红色圆圈标记
    for minute in spike_minutes:
        idx = minutes.index(minute)
        ax.plot(minute, danmaku_counts[idx], marker='o', markersize=10, color='red')

    # 显示图表
    plt.tight_layout(rect=[0, 0.2, 1, 1])  # 留出更多空间给文本框

    # 添加鼠标移动事件监听器
    def on_move(event):
        if event.inaxes is None:
            return
        x, y = event.xdata, event.ydata
        minute = int(round(x))
        if minute in danmaku_per_minute:
            contents = danmaku_per_minute[minute]
            counter = Counter(contents)
            top_three = counter.most_common(3)
            text = "\n".join([f"{content}: {count}" for content, count in top_three])
            
            # 调整xytext以防止超出窗口边界
            annotation.xy = (x, y)
            annotation.set_text(text)
            annotation.set_visible(True)
            
            # 获取当前轴的边界
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            
            # 调整xytext位置
            if x > xlim[1] - 10:
                annotation.xytext = (-20, 20)  # 移动到左侧
            elif x < xlim[0] + 10:
                annotation.xytext = (20, 20)   # 移动到右侧
            else:
                annotation.xytext = (20, 20)   # 默认位置
            
            if y > ylim[1] - 10:
                annotation.xytext = (annotation.xytext[0], -20)  # 移动到底部
            elif y < ylim[0] + 10:
                annotation.xytext = (annotation.xytext[0], 20)   # 移动到顶部
            
        else:
            annotation.set_visible(False)
        fig.canvas.draw_idle()

    annotation = ax.annotate("", xy=(0, 0), xytext=(20, 20),
                             textcoords="offset points",
                             bbox=dict(boxstyle="round", fc="w"),
                             arrowprops=dict(arrowstyle="->"))
    annotation.set_visible(False)

    fig.canvas.mpl_connect("motion_notify_event", on_move)

    # 在左下角显示弹幕最多的5个点的弹幕数量最多的弹幕
    info_text = "\n".join([
        f"第{minute}分钟: {count}条弹幕, 最多的弹幕是'{danmaku}' ({danmaku_count}次)"
        for minute, count, danmaku, danmaku_count in top_danmaku_info
    ])
    fig.text(0.02, 0.02, info_text, fontsize=12, verticalalignment='bottom', bbox=dict(boxstyle="round,pad=0.5", edgecolor='black', facecolor='white'))

    plt.show()

def main():
    # 获取用户输入的文本
    input_text = input("请输入包含Bilibili视频URL的文本: ")
    
    # 提取URL
    url = extract_url_from_input(input_text)
    
    if not url:
        print("未找到有效的Bilibili视频URL")
        return
    
    if not is_valid_bilibili_url(url):
        print("无效的Bilibili视频URL")
        return
    
    video_id = get_video_id(url)
    if not video_id:
        print("无法提取视频ID")
        return
    
    danmaku_url = get_danmaku_url(video_id)
    if not danmaku_url:
        print("无法获取弹幕文件URL")
        return
    
    # 下载弹幕文件
    output_path = f"{video_id}.xml"
    download_danmaku(danmaku_url, output_path)
    
    # 解析并绘制弹幕统计图表
    plot_danmaku_statistics(output_path)

if __name__ == "__main__":
    main()