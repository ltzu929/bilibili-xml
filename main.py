# 导入必要的模块
import customtkinter as ctk
import xml.etree.ElementTree as ET
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
from tkinter import messagebox
import requests
import json
import logging
import os
from tkinter import StringVar, Radiobutton

# 设置日志记录，记录弹幕分析过程中的信息和错误
logging.basicConfig(filename="danmaku_analysis.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 配置界面的外观
ctk.set_appearance_mode("System")  # 设置外观模式为系统模式
ctk.set_default_color_theme("blue")  # 设置默认主题颜色为蓝色

# 配置 Matplotlib 中文字体支持，确保显示中文字符
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置字体为 SimHei
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 提取 Bilibili 视频 URL 的函数
def extract_url_from_input(input_text):
    """
    从输入的文本中提取 Bilibili 视频 URL。
    使用正则表达式匹配合法的 URL 格式。
    """
    import re
    pattern = r'https?://www\.bilibili\.com/video/(BV[0-9A-Za-z]+|av\d+)(\?.*)?'
    match = re.search(pattern, input_text)
    return match.group(0) if match else None

# 提取视频 ID 的函数
def get_video_id(url):
    """
    从 Bilibili 视频 URL 中提取视频 ID。
    支持 BV 号和 av 号两种格式。
    """
    import re
    match = re.search(r'/video/(BV[0-9A-Za-z]+|av\d+)', url)
    return match.group(1) if match else None

# 获取弹幕的 URL
def get_danmaku_url(video_id):
    """
    根据视频 ID 获取对应的弹幕文件 URL。
    调用 Bilibili API 获取视频的弹幕 cid 信息。
    """
    try:
        # 根据视频 ID 构造 API 请求 URL
        api_url = f"https://api.bilibili.com/x/player/pagelist?bvid={video_id}" if video_id.startswith("BV") else f"https://api.bilibili.com/x/player/pagelist?aid={video_id[2:]}"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com"}
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data['code'] == 0:
            # 返回弹幕文件的 URL
            cid = data['data'][0]['cid']
            return f"https://comment.bilibili.com/{cid}.xml"
    except requests.RequestException as e:
        # 捕获请求异常并记录日志
        messagebox.showerror("错误", f"请求弹幕 API 时出错: {e}")
        logging.error(f"获取弹幕 URL 出错: {e}")
    return None

# 下载弹幕文件
def download_danmaku(danmaku_url, output_path):
    """
    下载弹幕文件并保存到指定路径。
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com"}
        response = requests.get(danmaku_url, headers=headers, timeout=10)
        response.raise_for_status()
        # 将弹幕内容写入文件
        with open(output_path, "wb") as file:
            file.write(response.content)
        logging.info(f"弹幕文件已下载: {output_path}")
        return output_path
    except requests.RequestException as e:
        # 捕获下载异常并记录日志
        messagebox.showerror("错误", f"下载弹幕文件时出错: {e}")
        logging.error(f"下载弹幕文件时出错: {e}")
    return None

# XML 转 JSON 的转换函数
def xml_to_json(xml_file_path, output_json_path):
    """
    将 XML 格式的弹幕文件转换为 JSON 格式。
    """
    try:
        # 解析 XML 文件
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        # 按分钟统计弹幕
        danmaku_per_minute = defaultdict(list)
        for d in root.findall('d'):
            p = d.get('p').split(',')  # 提取弹幕的参数信息
            time = float(p[0])  # 获取弹幕发送的时间
            content = d.text  # 弹幕内容

            # 处理特定弹幕内容为统一格式
            if content.strip() == "哈" or all(char == "哈" for char in content.strip()):
                content = "哈"
            elif content.strip() == "？" or all(char == "？" for char in content.strip()):
                content = "？"
            elif content.strip() == "艹" or content.strip() == "草":
                content = "草"
            minute = int(time // 60)  # 按分钟归类弹幕
            danmaku_per_minute[minute].append(content)

        # 生成 JSON 数据
        json_data = {
            'density': {
                'x': list(danmaku_per_minute.keys()),
                'total': [len(danmaku_per_minute[m]) for m in danmaku_per_minute.keys()]
            },
            'hot_words': [
                [minute, Counter(danmaku_per_minute[minute]).most_common(10)]
                for minute in danmaku_per_minute.keys()
            ]
        }

        # 写入 JSON 文件
        with open(output_json_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)
        logging.info(f"XML 文件已成功转换为 JSON: {output_json_path}")
        return json_data
    except ET.ParseError as e:
        # 捕获 XML 解析错误
        messagebox.showerror("错误", f"XML 文件解析错误: {e}")
        logging.error(f"XML 文件解析错误: {e}")
    except Exception as e:
        # 捕获其他异常
        messagebox.showerror("错误", f"转换 XML 为 JSON 时失败: {e}")
        logging.error(f"转换 XML 为 JSON 时失败: {e}")

# 根据用户选择的过滤条件筛选弹幕数据
def filter_data_by_option(density_data, hot_words, option):
    """
    根据用户选择的过滤条件筛选弹幕密度数据。
    参数：
        density_data: 包含弹幕密度（x: 时间, total: 数量）的数据字典
        hot_words: 包含热词统计的列表
        option: 筛选条件（"all"、"ha"、"cao" 或 "?"）
    返回：
        筛选后的数据字典
    """
    filtered_data = {'x': [], 'total': []}  # 初始化筛选后的数据
    for i, minute in enumerate(density_data['x']):
        if option == "all":
            # 显示全部数据
            filtered_data['x'].append(minute)
            filtered_data['total'].append(density_data['total'][i])
        else:
            # 按热词进行筛选
            words_at_minute = [word for word, _ in hot_words[i][1]]  # 当前分钟的热词列表
            if option == "ha" and "哈" in words_at_minute:
                filtered_data['x'].append(minute)
                filtered_data['total'].append(density_data['total'][i])
            elif option == "cao" and "草" in words_at_minute:
                filtered_data['x'].append(minute)
                filtered_data['total'].append(density_data['total'][i])
            elif option == "?" and "？" in words_at_minute:
                filtered_data['x'].append(minute)
                filtered_data['total'].append(density_data['total'][i])
    return filtered_data

# 根据用户选择更新图表显示
def update_plot():
    """
    根据用户选择的过滤条件更新图表。
    使用全局变量 json_data 作为数据源。
    """
    option = display_option.get()  # 获取用户当前选择的过滤条件
    filtered_density = filter_data_by_option(json_data['density'], json_data['hot_words'], option)

    # 在绘制新图表前关闭旧图表窗口，避免生成多个窗口
    plt.close('all')

    # 调用绘制弹幕密度图的函数
    plot_density_with_hover_and_line(filtered_density, json_data['hot_words'])

# 绘制弹幕密度图，并支持鼠标悬停交互
def plot_density_with_hover_and_line(density_data, hot_words):
    """
    绘制弹幕密度图，支持鼠标悬停显示热词和弹幕数量，并添加垂直指示线。
    参数：
        density_data: 包含弹幕密度的字典数据
        hot_words: 包含热词统计的列表
    """
    # 提取时间轴（x）和弹幕总数（y）
    x = np.array(density_data['x'])
    y = np.array(density_data['total'])

    # 对时间轴数据进行排序并去重
    if len(x) > 1:
        sorted_indices = np.argsort(x)
        x = x[sorted_indices]
        y = y[sorted_indices]
        unique_x, unique_indices = np.unique(x, return_index=True)
        x = unique_x
        y = y[unique_indices]

    # 使用样条插值平滑曲线（仅当数据点数大于 2 时）
    if len(x) > 2:
        x_new = np.linspace(min(x), max(x), 300)
        spline = make_interp_spline(x, y, k=3)  # 样条插值
        y_smooth = spline(x_new)
    else:
        x_new, y_smooth = x, y

    # 设置图表样式和绘制曲线
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.fill_between(x_new, y_smooth, color='skyblue', alpha=0.4)
    ax.plot(x_new, y_smooth, color='blue', label='弹幕密度', linewidth=2)

    # 添加图表标题和轴标签
    ax.set_title("弹幕热度与热词 (/5min)", fontsize=16)
    ax.set_xlabel("时间（分钟）", fontsize=14)
    ax.set_ylabel("弹幕数量", fontsize=14)

    # 构建热词信息字典，仅保留前 5 个热词
    hot_words_dict = {minute: words[:5] for minute, words in hot_words}

    # 配置鼠标悬停时显示的注释框
    annotation = ax.annotate("", xy=(0, 0), xytext=(20, 20),
                             textcoords="offset points",
                             bbox=dict(boxstyle="round", fc="w"),
                             arrowprops=dict(arrowstyle="->"))
    annotation.set_visible(False)  # 初始状态隐藏注释框

    # 配置垂直指示线，用于高亮当前时间点
    vertical_line = ax.axvline(x=0, color='gray', linestyle='--', linewidth=1)
    vertical_line.set_visible(False)

    # 鼠标悬停事件处理函数
    def on_hover(event):
        if event.inaxes == ax:  # 确保鼠标在绘图区内
            if event.xdata is not None:  # 鼠标的 x 坐标有效
                # 找到与鼠标最近的时间点
                nearest_index = min(range(len(x)), key=lambda i: abs(x[i] - event.xdata))
                nearest_minute = x[nearest_index]

                # 更新垂直指示线的位置
                vertical_line.set_xdata([nearest_minute])
                vertical_line.set_visible(True)

                # 更新注释框的内容
                annotation.xy = (nearest_minute, y[nearest_index])
                text = f"时间: {nearest_minute} 分钟\n弹幕数量: {y[nearest_index]}"
                if nearest_minute in hot_words_dict:
                    text += "\n热词:\n" + "\n".join([f"{word}: {count}" for word, count in hot_words_dict[nearest_minute]])

                annotation.set_text(text)
                annotation.set_visible(True)

                # 调整注释框的位置，避免超出边界
                fig.canvas.draw_idle()  # 渲染文本
                renderer = fig.canvas.get_renderer()
                bbox = annotation.get_window_extent(renderer)  # 获取注释框的像素边界
                annotation_width = bbox.width
                annotation_height = bbox.height

                # 默认偏移量
                x_offset, y_offset = 20, 20

                # 判断是否超出右边界
                if event.x + x_offset + annotation_width > fig.bbox.width:
                    x_offset = -annotation_width - 20

                # 判断是否超出上边界
                if event.y + y_offset + annotation_height > fig.bbox.height:
                    y_offset = -annotation_height - 20

                annotation.xytext = (x_offset, y_offset)
                annotation.set_visible(True)
                fig.canvas.draw_idle()
            else:
                # 鼠标不在有效区域时隐藏注释框和垂直线
                annotation.set_visible(False)
                vertical_line.set_visible(False)
                fig.canvas.draw_idle()

    # 连接鼠标悬停事件到绘图区
    fig.canvas.mpl_connect("motion_notify_event", on_hover)

    # 显示图表
    plt.legend()
    plt.show()

# 主流程：处理 URL 并开始分析
def process_url_and_analyze():
    """
    处理用户输入的 URL，完成弹幕下载、转换和分析。
    """
    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("错误", "请输入视频 URL！")
        return

    video_id = get_video_id(url)
    if not video_id:
        messagebox.showerror("错误", "无效的视频 URL！")
        return

    danmaku_url = get_danmaku_url(video_id)
    if not danmaku_url:
        return

    xml_file_path = f"{video_id}.xml"
    downloaded_file = download_danmaku(danmaku_url, xml_file_path)
    if not downloaded_file:
        return

    json_file_path = xml_file_path.replace('.xml', '.json')
    global json_data
    json_data = xml_to_json(xml_file_path, json_file_path)  # 将数据存储为全局变量
    if not json_data:
        return

    try:
        update_plot()  # 绘制图表
    except Exception as e:
        messagebox.showerror("错误", f"绘图失败: {e}")

# 创建主窗口
root = ctk.CTk()
root.title("哔哩哔哩弹幕分析工具")
root.geometry("700x500")
root.resizable(True, True)

# 窗口居中显示
root.update_idletasks()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width // 2) - (700 // 2)
y = (screen_height // 2) - (500 // 2)
root.geometry(f"+{x}+{y}")

# 创建一个变量，用于存储用户选择的选项
display_option = StringVar(value="all")  # 默认值为显示全部

url_label = ctk.CTkLabel(root, text="请输入哔哩哔哩视频 URL:", font=("Arial", 14))
url_label.pack(pady=10)
url_entry = ctk.CTkEntry(root, width=500)
url_entry.pack(pady=5)


url_button = ctk.CTkButton(root, text="处理 URL 并分析", command=process_url_and_analyze, corner_radius=20)
url_button.pack(pady=20)

root.mainloop()
