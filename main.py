# 导入必要的库
import customtkinter as ctk  # 用于创建自定义Tkinter图形界面
import xml.etree.ElementTree as ET  # 用于解析XML文件
from collections import defaultdict, Counter  # 用于统计数据和计数
import matplotlib.pyplot as plt  # 用于绘制图形
import numpy as np  # 数学计算库，用于处理数组等
from scipy.interpolate import make_interp_spline  # 用于平滑数据曲线
from tkinter import filedialog  # 用于文件对话框选择文件
import requests  # 用于网络请求

# 设置界面的外观模式和默认颜色主题
ctk.set_appearance_mode("System")  # 自动选择系统主题
ctk.set_default_color_theme("blue")  # 设置默认主题为蓝色

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体显示中文
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 从输入的文本中提取Bilibili视频的URL
def extract_url_from_input(input_text):
    import re
    # 匹配Bilibili视频URL的正则表达式
    pattern = r'https?://www\.bilibili\.com/video/(BV[0-9A-Za-z]+|av\d+)(\?.*)?'
    match = re.search(pattern, input_text)
    return match.group(0) if match else None  # 如果匹配成功，返回URL

# 提取视频ID（BV号或者av号）
def get_video_id(url):
    import re
    # 正则表达式匹配视频ID
    match = re.search(r'/video/(BV[0-9A-Za-z]+|av\d+)', url)
    return match.group(1) if match else None  # 返回匹配到的视频ID

# 根据视频ID获取弹幕的XML文件URL
def get_danmaku_url(video_id):
    try:
        # 根据视频ID（BV号或av号）构造API URL
        api_url = f"https://api.bilibili.com/x/player/pagelist?bvid={video_id}" if video_id.startswith("BV") else f"https://api.bilibili.com/x/player/pagelist?aid={video_id[2:]}"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com"}
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()  # 解析JSON数据
        if data['code'] == 0:  # 如果返回的数据正常
            cid = data['data'][0]['cid']
            return f"https://comment.bilibili.com/{cid}.xml"  # 返回弹幕文件的URL
    except requests.RequestException as e:
        print(f"请求弹幕API时出错: {e}")
    return None  # 如果出错，返回None

# 下载弹幕文件
def download_danmaku(danmaku_url, output_path):
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com"}
        response = requests.get(danmaku_url, headers=headers, timeout=10)
        response.raise_for_status()
        # 将下载的弹幕内容保存到指定的文件路径
        with open(output_path, "wb") as file:
            file.write(response.content)
        return output_path  # 返回保存路径
    except requests.RequestException as e:
        print(f"下载弹幕文件时出错: {e}")
    return None  # 如果出错，返回None

# 绘制弹幕统计图
def plot_danmaku_statistics(xml_file_path):
    tree = ET.parse(xml_file_path)  # 解析XML文件
    root = tree.getroot()  # 获取根节点
    danmaku_per_minute = defaultdict(list)  # 使用defaultdict存储每分钟的弹幕内容

    # 遍历所有弹幕，按分钟分组
    for d in root.findall('d'):
        p = d.get('p').split(',')  # 获取每条弹幕的属性
        time = float(p[0])  # 弹幕出现的时间（秒）
        content = d.text  # 弹幕内容
        minute = int(time // 60)  # 将时间转换为分钟
        danmaku_per_minute[minute].append(content)  # 将弹幕按分钟分组

    # 计算每分钟弹幕的数量
    minutes = sorted(danmaku_per_minute.keys())
    danmaku_counts = [len(danmaku_per_minute[minute]) for minute in minutes]

    # 使用三次样条插值平滑曲线
    x_new = np.linspace(min(minutes), max(minutes), 300)  # 生成新的x轴数据
    spline = make_interp_spline(minutes, danmaku_counts, k=3)  # 三次样条插值
    y_smooth = spline(x_new)  # 计算平滑后的y值

    # 找出弹幕最多的5分钟
    top_5_minutes = sorted(zip(minutes, danmaku_counts), key=lambda x: x[1], reverse=True)[:5]
    top_danmaku_info = []
    for minute, count in top_5_minutes:
        counter = Counter(danmaku_per_minute[minute])  # 统计该分钟最常出现的弹幕
        most_common_danmaku, most_common_count = counter.most_common(1)[0]
        top_danmaku_info.append((minute, count, most_common_danmaku, most_common_count))

    # 绘制弹幕数量的统计图
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(8, 6))  # 设置图表尺寸
    ax.plot(x_new, y_smooth, color='blue', label='弹幕数量', linewidth=2)  # 绘制平滑曲线
    ax.set_title('弹幕数量每分钟统计', fontsize=16, fontweight='bold')  # 设置标题
    ax.set_xlabel('分钟', fontsize=14)  # 设置x轴标签
    ax.set_ylabel('弹幕数量', fontsize=14)  # 设置y轴标签
    ax.legend(fontsize=12)  # 显示图例

    # 用于显示弹幕数量突增点的标注框
    annotation = ax.annotate("", xy=(0, 0), xytext=(20, 20),
                             textcoords="offset points",
                             bbox=dict(boxstyle="round", fc="w"),
                             arrowprops=dict(arrowstyle="->"))
    annotation.set_visible(False)  # 初始时标注不可见

    # 用于拖动功能的状态变量
    drag_start_pos = [0, 0]

    # 鼠标移动事件，用于显示当前分钟弹幕内容的统计
    def on_move(event):
        if event.inaxes is None:
            return
        x, y = event.xdata, event.ydata
        if x is not None:
            minute = int(round(x))
            if minute in danmaku_per_minute:
                contents = danmaku_per_minute[minute]
                counter = Counter(contents)
                top_three = counter.most_common(3)
                text = f"第{minute}分钟:\n" + "\n".join([f"{content}: {count}" for content, count in top_three])
                annotation.xy = (x, y)
                annotation.set_text(text)
                annotation.set_visible(True)  # 显示标注框
            else:
                annotation.set_visible(False)  # 如果没有数据，隐藏标注框
        fig.canvas.draw_idle()

    # 鼠标滚轮事件，用于缩放图表
    def on_scroll(event):
        base_scale = 1.2
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()

        # 缩放范围
        if event.button == 'up':
            scale_factor = 1 / base_scale
        elif event.button == 'down':
            scale_factor = base_scale
        else:
            return

        new_x_min = x_min + (x_max - x_min) * (1 - scale_factor) / 2
        new_x_max = x_max - (x_max - x_min) * (1 - scale_factor) / 2
        new_y_min = y_min + (y_max - y_min) * (1 - scale_factor) / 2
        new_y_max = y_max - (y_max - y_min) * (1 - scale_factor) / 2

        # 避免超出范围
        if new_x_min < 0:
            new_x_min = 0
        if new_y_min < 0:
            new_y_min = 0

        ax.set_xlim(new_x_min, new_x_max)
        ax.set_ylim(new_y_min, new_y_max)
        fig.canvas.draw()

    # 鼠标按下事件，用于记录拖动起始点
    def on_press(event):
        if event.inaxes:
            drag_start_pos[0] = event.xdata
            drag_start_pos[1] = event.ydata

    # 鼠标拖动事件，用于平移图表
    def on_drag(event):
        if event.inaxes and event.button == 1:  # 鼠标左键拖动
            dx = drag_start_pos[0] - event.xdata
            dy = drag_start_pos[1] - event.ydata

            x_min, x_max = ax.get_xlim()
            y_min, y_max = ax.get_ylim()

            # 更新图像显示的范围
            ax.set_xlim(x_min + dx, x_max + dx)
            ax.set_ylim(y_min + dy, y_max + dy)
            fig.canvas.draw()

    # 连接事件
    fig.canvas.mpl_connect("motion_notify_event", on_move)
    fig.canvas.mpl_connect("scroll_event", on_scroll)
    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("motion_notify_event", on_drag)

    # 显示弹幕最多的5分钟的内容
    info_text = "\n".join([ 
        f"第{minute}分钟:  最多的弹幕是'{danmaku}' ({danmaku_count}次)"
        for minute, count, danmaku, danmaku_count in top_danmaku_info
    ])
    fig.text(0.02, 0.02, info_text, fontsize=12, verticalalignment='bottom', bbox=dict(boxstyle="round,pad=0.5", edgecolor='black', facecolor='white'))

    # 显示图表
    plt.show()

# 处理URL的函数，获取并下载弹幕文件
def process_url():
    url = url_entry.get()
    if not url:
        print("错误: 请输入视频URL")
        return
    url = extract_url_from_input(url)
    if not url:
        print("错误: 无效的视频URL")
        return
    video_id = get_video_id(url)
    if not video_id:
        print("错误: 无法提取视频ID")
        return
    danmaku_url = get_danmaku_url(video_id)
    if not danmaku_url:
        return
    output_path = f"{video_id}.xml"
    downloaded_file = download_danmaku(danmaku_url, output_path)
    if downloaded_file:
        plot_danmaku_statistics(downloaded_file)

# 处理本地文件的函数，选择XML文件并绘制统计图
def process_local_file():
    file_path = filedialog.askopenfilename(filetypes=[("XML 文件", "*.xml")])
    if file_path:
        plot_danmaku_statistics(file_path)

# 创建主窗口
root = ctk.CTk()
root.title("哔哩哔哩弹幕分析工具")  # 设置窗口标题
root.geometry("700x500")  # 设置窗口尺寸
root.resizable(True, True)  # 允许用户动态调整窗口大小

# 窗口居中显示
root.update_idletasks()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width // 2) - (700 // 2)
y = (screen_height // 2) - (500 // 2)
root.geometry(f"+{x}+{y}")

# URL 输入部分
url_label = ctk.CTkLabel(root, text="请输入哔哩哔哩视频URL:", font=("Arial", 14))
url_label.pack(pady=10)
url_entry = ctk.CTkEntry(root, width=500)  # 输入框
url_entry.pack(pady=5)
url_button = ctk.CTkButton(root, text="处理URL", command=process_url, corner_radius=20)  # 按钮
url_button.pack(pady=10)

# 文件选择部分
file_button = ctk.CTkButton(root, text="选择本地弹幕文件", command=process_local_file, corner_radius=20)  # 按钮
file_button.pack(pady=20)

# 启动Tkinter主循环
root.mainloop()
