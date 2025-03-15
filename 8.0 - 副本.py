import customtkinter as ctk
import xml.etree.ElementTree as ET
from collections import defaultdict, Counter
import matplotlib
matplotlib.use('TkAgg')  # 使用 TkAgg 后端
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from scipy.interpolate import make_interp_spline
from tkinter import messagebox
import requests
import json
import logging
import os
from tkinter import StringVar
import atexit
import threading
import re

# 配置日志
logging.basicConfig(level=logging.ERROR)  # 设置为ERROR级别

# 全局变量用于存储下载的文件路径
downloaded_files = []

# 配置界面的外观
ctk.set_appearance_mode("System")  # 设置外观模式为系统模式
ctk.set_default_color_theme("blue")  # 设置默认主题颜色为蓝色

# 配置 Matplotlib 中文字体支持，确保显示中文字符
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置字体为 SimHei
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


class DanmakuAnalyzer:
    def __init__(self, root):
        self.root = root
        self.json_data = None  # 存储当前分析的数据
        self.pagelist = []     # 存储所有分P的信息
        self.plot_frame = None       # 图表容器占位
        self.p_selection_frame = None # 分P选择容器占位
        self.memory_cache = {}  # 新增内存缓存字典

        # 用户选择的过滤选项变量
        self.display_option = StringVar(value="all")  # 默认值为显示全部
        # 用户选择的分P
        self.selected_p = StringVar()
        # 搜索框变量
        self.search_var = StringVar()

        self.create_widgets()

    def create_widgets(self):
        # ===== 主容器 =====
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # ===== 标题栏 =====
        header_frame = ctk.CTkFrame(self.main_container, height=80, corner_radius=16,
                                   fg_color=("#EBF5FF", "#2B2B2B"),
                                   border_width=1, border_color="#E0E0E0")
        header_frame.pack(fill="x", pady=(0,20))
        
        # 标题文字
        ctk.CTkLabel(header_frame, text="路灯", 
                    font=("Microsoft YaHei", 24, "bold"),
                    text_color=("#1E90FF", "#7EC8FF")).pack(side="left", padx=30)
        
        # 主题切换
        self.theme_btn = ctk.CTkButton(header_frame, text="☀️", width=40, height=40,
                                      corner_radius=20, command=self.toggle_theme)
        self.theme_btn.pack(side="right", padx=20)

        # ===== 控制面板 =====
        control_frame = ctk.CTkFrame(self.main_container, corner_radius=16,
                                    fg_color=("#FFFFFF", "#363636"),
                                    border_width=1, border_color="#E0E0E0")
        control_frame.pack(fill="x", pady=10)
        
        # URL输入组
        url_group = ctk.CTkFrame(control_frame, fg_color="transparent")
        url_group.pack(fill="x", pady=8)
        
        ctk.CTkLabel(url_group, text="视频URL：", 
                    font=("Microsoft YaHei", 14)).pack(side="left", padx=5)
        self.url_entry = ctk.CTkEntry(
            url_group, 
            width=500,
            placeholder_text="请输入B站视频链接...",
            corner_radius=20,
            border_color="#1E90FF",
            font=("Microsoft YaHei", 13)
        )
        self.url_entry.pack(side="left", expand=True, fill="x")
        
        # 动态输入验证
        self.url_entry.bind("<KeyRelease>", self.validate_url)

        # 功能按钮组
        btn_group = ctk.CTkFrame(control_frame, fg_color="transparent")
        btn_group.pack(fill="x", pady=10)
        
        self.analyze_btn = ctk.CTkButton(
            btn_group,
            text="开始分析",
            command=self.process_url_and_analyze,
            width=120,
            height=40,
            corner_radius=20,
            fg_color=("#1E90FF", "#004E98"),
            hover_color=("#0066CC", "#003366"),
            font=("Microsoft YaHei", 14, "bold"),
            state="disabled"
        )
        self.analyze_btn.pack(side="left", padx=10)
        
        # 过滤选项改为现代切换按钮组
        filter_frame = ctk.CTkFrame(btn_group, fg_color="transparent")
        filter_frame.pack(side="left", padx=20)
        
        filters = [
            ("全部", "all", "#4CAF50"),
            ("😄 哈", "ha", "#FFC107"), 
            ("🌿 草", "cao", "#8BC34A"),
            ("❓ ？", "?", "#9E9E9E")
        ]
        for text, value, color in filters:
            btn = ctk.CTkButton(
                filter_frame,
                text=text,
                command=lambda v=value: self.set_filter(v),
                fg_color=color,
                hover_color=self.adjust_color(color, -20),
                width=80,
                height=32,
                corner_radius=16
            )
            btn.pack(side="left", padx=5)

        # ===== 可视化区域 =====
        self.viz_frame = ctk.CTkFrame(
            self.main_container,
            corner_radius=16,
            fg_color=("#FFFFFF", "#2B2B2B")
        )
        self.viz_frame.pack(fill="both", expand=True, pady=10)
        
        # 加载动画
        self.loading_label = ctk.CTkLabel(
            self.viz_frame, 
            text="", 
            font=("Microsoft YaHei", 16),
            text_color=("#1E90FF", "#7EC8FF")
        )
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")
            # ===== 进度条组件 =====
        self.progress_frame = ctk.CTkFrame(self.main_container)
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="", font=("Arial", 12))
        self.progress_label.pack(side="top", fill="x", padx=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=400)
        self.progress_bar.set(0)
        self.progress_bar.pack(side="top", fill="x", padx=10, pady=5)
        
        # 初始时隐藏进度条
        self.progress_frame.pack_forget()

    def set_loading(self, active=True, text="分析中..."):
        if active:
            self.loading_label.configure(text=text)
            self.animate_loading()
        else:
            self.loading_label.configure(text="")
            self.root.after_cancel(self.anim_id) if hasattr(self, 'anim_id') else None

    def animate_loading(self):
        dots = [".  ", ".. ", "..."]
        def update(idx):
            self.loading_label.configure(text=f"分析中{dots[idx%3]}")
            self.anim_id = self.root.after(500, lambda: update(idx+1))
        update(0)

    def validate_url(self, event):
        url = self.url_entry.get()
        if re.match(r"^https?://(www\.)?bilibili\.com/video/", url):
            self.analyze_btn.configure(state="normal", fg_color="#1E90FF")
            self.url_entry.configure(border_color="#4CAF50")
        else:
            self.analyze_btn.configure(state="disabled", fg_color="#CCCCCC")
            self.url_entry.configure(border_color="#FF5252")

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "Dark" if current == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)
        self.theme_btn.configure(text="🌙" if new_mode == "Dark" else "☀️")

    def adjust_color(self, hex_color, amount):
        """动态调整颜色亮度"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = [min(255, max(0, c + amount)) for c in rgb]
        return f'#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}'
    def search_danmaku(self):
        """
        从 self.json_data['comments'] 中搜索弹幕文本，弹出结果
        """
        if not self.json_data:
            messagebox.showerror("错误", "无可搜索的弹幕，请先分析视频弹幕！")
            return

        search_query = self.search_var.get().strip()
        if not search_query:
            messagebox.showerror("错误", "请输入搜索关键词！")
            return

        results = []
        comments_dict = self.json_data.get('comments', {})
        for minute_str, comment_list in comments_dict.items():
            for comment_text in comment_list:
                if search_query in comment_text:
                    results.append((minute_str, comment_text))

        if not results:
            messagebox.showinfo("提示", f"未找到包含「{search_query}」的弹幕。")
            return

        result_window = ctk.CTkToplevel(self.root)
        result_window.title("搜索结果")

        text_box = ctk.CTkTextbox(result_window, width=600, height=400)
        text_box.pack(padx=10, pady=10, fill='both', expand=True)

        text_box.insert("end", f"搜索关键词: {search_query}\n\n")
        for minute_str, comment_text in results:
            text_box.insert("end", f"[{minute_str} 分钟] {comment_text}\n")
        text_box.configure(state="disabled")  # 禁止编辑

    def get_video_id(self, url):
        match = re.search(r'/video/(BV[0-9A-Za-z]+|av\d+)', url)
        return match.group(1) if match else None

    def get_pagelist(self, video_id):
        """
        获取分P信息
        """
        try:
            if video_id.startswith("BV"):
                api_url = f"https://api.bilibili.com/x/player/pagelist?bvid={video_id}"
            else:
                api_url = f"https://api.bilibili.com/x/player/pagelist?aid={video_id[2:]}"
            headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com"}
            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data['code'] == 0 and data['data']:
                self.pagelist = data['data']
                return self.pagelist
            else:
                messagebox.showerror("错误", "无法获取视频分P信息。")
        except requests.RequestException as e:
            messagebox.showerror("错误", f"请求分P信息时出错: {e}")
            logging.error(f"获取分P信息出错: {e}")
        return None

    def get_danmaku_url(self, cid):
        """
        根据 cid 获取弹幕url
        """
        try:
            return f"https://comment.bilibili.com/{cid}.xml"
        except Exception as e:
            messagebox.showerror("错误", f"构造弹幕 URL 时出错: {e}")
            logging.error(f"构造弹幕 URL 出错: {e}")
        return None

    def download_danmaku(self, danmaku_url, video_id, cid):
        """下载弹幕到内存缓存"""
        try:
            headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com"}
            response = requests.get(danmaku_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 存储到内存缓存
            self.memory_cache[(video_id, cid)] = {
                "xml": response.content,
                "json": None
            }
            logging.info(f"弹幕已缓存: {video_id}_cid{cid}")
            return True
        except requests.RequestException as e:
            messagebox.showerror("错误", f"下载弹幕时出错: {e}")
            logging.error(f"下载弹幕时出错: {e}")
            return False

    def cleanup_cache(self):
        """替代原来的文件清理"""
        self.memory_cache.clear()
        logging.info("内存缓存已清空")

    def on_closing(self):
        self.cleanup_cache()  # 替代原cleanup_downloaded_files
        self.root.destroy()

    def xml_to_json(self, video_id, cid):
        """直接从内存缓存转换XML到JSON"""
        cache_key = (video_id, cid)
        if cache_key not in self.memory_cache or not self.memory_cache[cache_key]["xml"]:
            return None

        try:
            # 从内存获取XML内容
            xml_content = self.memory_cache[cache_key]["xml"]
            
            # 使用fromstring解析内存数据
            root = ET.fromstring(xml_content.decode('utf-8'))

            danmaku_per_minute = defaultdict(list)
            for d in root.findall('d'):
                p = d.get('p').split(',')
                time = float(p[0])
                content = d.text if d.text else ""

                # 简单归一化某些常见弹幕
                if content.strip() == "哈" or all(char == "哈" for char in content.strip()):
                    content = "哈"
                elif content.strip() == "？" or all(char == "？" for char in content.strip()):
                    content = "？"
                elif content.strip() in ["艹", "草"]:
                    content = "草"
                minute = int(time // 60)
                danmaku_per_minute[minute].append(content)

            json_data = {
                'density': {
                'x': sorted(danmaku_per_minute.keys()),
                'total': [len(danmaku_per_minute[m]) for m in sorted(danmaku_per_minute.keys())]
            },
            'hot_words': [
                [minute, Counter(danmaku_per_minute[minute]).most_common(10)]
                for minute in sorted(danmaku_per_minute.keys())
            ],
            'comments': {
                str(m): danmaku_per_minute[m]
                for m in sorted(danmaku_per_minute.keys())
            }
        }

            # 更新内存缓存
            self.memory_cache[cache_key]["json"] = json_data
            return json_data
        
        except ET.ParseError as e:
            messagebox.showerror("错误", f"XML 解析错误: {e}")
        except Exception as e:
            messagebox.showerror("错误", f"转换失败: {e}")

    def filter_data_by_option(self, density_data, hot_words, option):
        filtered_data = {'x': [], 'total': []}
        hot_words_dict = {minute: dict(words) for minute, words in hot_words}

        for i, minute in enumerate(density_data['x']):
            if option == "all":
                filtered_data['x'].append(minute)
                filtered_data['total'].append(density_data['total'][i])
            elif option == "ha":
                # 只要某分钟热词里有"哈"就算
                if hot_words_dict.get(minute, {}).get("哈", 0) > 0:
                    filtered_data['x'].append(minute)
                    filtered_data['total'].append(density_data['total'][i])
            elif option == "cao":
                # 只要有"草"或"艹"就算
                if (hot_words_dict.get(minute, {}).get("草", 0) > 0 or
                        hot_words_dict.get(minute, {}).get("艹", 0) > 0):
                    filtered_data['x'].append(minute)
                    filtered_data['total'].append(density_data['total'][i])
            elif option == "?":
                if hot_words_dict.get(minute, {}).get("？", 0) > 0:
                    filtered_data['x'].append(minute)
                    filtered_data['total'].append(density_data['total'][i])
        return filtered_data

    def enable_navigation(self, fig, ax):
        """启用图表缩放和拖拽功能"""
        # 保存初始视图限制
        ax._original_view = (ax.get_xlim(), ax.get_ylim())
        
        # 状态变量
        self._drag_start = None
        self._current_ax = ax
        
        # 绑定事件
        fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        fig.canvas.mpl_connect('button_press_event', self.on_press)
        fig.canvas.mpl_connect('button_release_event', self.on_release)
        fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        fig.canvas.mpl_connect('key_press_event', self.on_key_press)

    def on_scroll(self, event):
        """处理滚轮缩放"""
        if event.inaxes != self._current_ax:
            return
        
        base_scale = 1.1
        cur_xlim = self._current_ax.get_xlim()
        cur_ylim = self._current_ax.get_ylim()
        
        xdata = event.xdata
        ydata = event.ydata
        
        if event.button == 'up':
            scale_factor = 1 / base_scale
        elif event.button == 'down':
            scale_factor = base_scale
        else:
            return
        
        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
        
        relx = (cur_xlim[1] - xdata)/(cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata)/(cur_ylim[1] - cur_ylim[0])
        
        self._current_ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
        self._current_ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])
        self._current_ax.figure.canvas.draw()

    def on_press(self, event):
        """记录拖拽起始位置"""
        if event.button == 1 and event.inaxes == self._current_ax:  # 左键
            self._drag_start = (event.xdata, event.ydata)

    def on_release(self, event):
        """清除拖拽状态"""
        self._drag_start = None

    def on_motion(self, event):
        """处理拖拽平移"""
        if self._drag_start is None or event.inaxes != self._current_ax:
            return
        
        dx = event.xdata - self._drag_start[0]
        dy = event.ydata - self._drag_start[1]
        
        cur_xlim = self._current_ax.get_xlim()
        cur_ylim = self._current_ax.get_ylim()
        
        self._current_ax.set_xlim(cur_xlim[0] - dx, cur_xlim[1] - dx)
        self._current_ax.set_ylim(cur_ylim[0] - dy, cur_ylim[1] - dy)
        self._current_ax.figure.canvas.draw()

    def on_key_press(self, event):
        """重置视图（按R键）"""
        if event.key.lower() == 'r':
            self._current_ax.set_xlim(self._current_ax._original_view[0])
            self._current_ax.set_ylim(self._current_ax._original_view[1])
            self._current_ax.figure.canvas.draw()

    def plot_density_with_hover_and_line(self, density_data, hot_words, parent_frame):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import numpy as np
        from scipy.interpolate import make_interp_spline

        x = np.array(density_data['x'])
        y = np.array(density_data['total'])

        # 数据预处理：去重并排序
        if len(x) > 1:
            sorted_indices = np.argsort(x)
            x = x[sorted_indices]
            y = y[sorted_indices]
            unique_x, unique_indices = np.unique(x, return_index=True)
            x = unique_x
            y = y[unique_indices]

        # 样条插值
        if len(x) > 2:
            x_new = np.linspace(x.min(), x.max(), 300)
            spline = make_interp_spline(x, y, k=3)
            y_smooth = spline(x_new)
        else:
            x_new, y_smooth = x, y

        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(14, 8))
        ax.fill_between(x_new, y_smooth, color='skyblue', alpha=0.4)
        ax.plot(x_new, y_smooth, color='blue', label='弹幕密度', linewidth=2)

        ax.set_xlim(left=0, right=x.max() if len(x) > 0 else 1)
        ax.set_ylim(bottom=0)
        ax.set_title("弹幕热度与热词 (/分钟)", fontsize=16)
        ax.set_xlabel("时间（分钟）", fontsize=14)
        ax.set_ylabel("弹幕数量", fontsize=14)

        # 只取前 5 个热词
        hot_words_dict = {minute: words[:5] for minute, words in hot_words}

        # 创建注释对象
        annotation = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(0, 0),
            textcoords="offset pixels",
            bbox=dict(boxstyle="round", fc="w"),
            arrowprops=dict(arrowstyle="->")
        )
        annotation.set_visible(False)

        # 创建垂直参考线
        vertical_line = ax.axvline(x=0, color='gray', linestyle='--', linewidth=1)
        vertical_line.set_visible(False)

        # 定义边缘检测参数
        EDGE_MARGIN_RATIO = 0.2  # 20%的画布宽度作为边缘检测区域

        self.enable_navigation(fig, ax)  # 启用导航功能

        def on_hover(event):
            if event.inaxes == ax and event.xdata is not None and event.ydata is not None and len(x) > 0:
                # 找到最近的时间点
                nearest_index = min(range(len(x)), key=lambda i: abs(x[i] - event.xdata))
                nearest_minute = x[nearest_index]
                nearest_value = y[nearest_index]

                # 更新垂直线
                vertical_line.set_xdata([nearest_minute])
                vertical_line.set_visible(True)

                # 构建注释文字
                text = f"时间: {nearest_minute} 分钟\n弹幕数量: {nearest_value}"
                if nearest_minute in hot_words_dict:
                    text += "\n热词:\n" + "\n".join(
                        f"{word}: {count}" for word, count in hot_words_dict[nearest_minute]
                    )
                annotation.set_text(text)

                # 获取画布和鼠标的像素坐标
                fig_width, fig_height = fig.canvas.get_width_height()
                mouse_x, mouse_y = event.x, event.y

                # 动态计算注释框预估尺寸
                approx_lines = text.count('\n') + 2  # 估算行数
                approx_box_height = approx_lines * 20  # 每行约20像素
                approx_box_width = 200 + (len(text) // 20) * 10  # 基础宽度+动态扩展

                # 计算安全边界
                safe_right_margin = fig_width - approx_box_width - 50  # 右侧保留50px余量
                safe_left_margin = 50  # 左侧保留50px
                near_right_edge = mouse_x > safe_right_margin
                near_left_edge = mouse_x < safe_left_margin

                # 初步定位
                if near_right_edge:
                    offset_x = -approx_box_width - 20  # 左侧偏移
                    offset_y = -approx_box_height // 2
                elif near_left_edge:
                    offset_x = safe_left_margin + 20  # 右侧偏移
                    offset_y = -approx_box_height // 2
                else:
                    offset_x = 20  # 默认右侧
                    offset_y = -20 if mouse_y > fig_height/2 else 20

                annotation.xy = (mouse_x, mouse_y)
                annotation.xycoords = "figure pixels"
                annotation.xytext = (offset_x, offset_y)
                annotation.set_visible(True)

                # 强制立即渲染获取真实尺寸
                fig.canvas.draw()
                renderer = fig.canvas.get_renderer()
                bbox = annotation.get_window_extent(renderer=renderer)

                # 精确边界修正
                new_offset_x, new_offset_y = offset_x, offset_y
                if bbox.xmax > fig_width:  # 右侧越界
                    new_offset_x = offset_x - (bbox.xmax - fig_width) - 10
                elif bbox.xmin < 0:        # 左侧越界
                    new_offset_x = offset_x - bbox.xmin + 10
                    
                if bbox.ymax > fig_height:  # 顶部越界
                    new_offset_y = offset_y - (bbox.ymax - fig_height) - 10
                elif bbox.ymin < 0:         # 底部越界
                    new_offset_y = offset_y - bbox.ymin + 10

                # 应用修正
                if (new_offset_x, new_offset_y) != (offset_x, offset_y):
                    annotation.xytext = (new_offset_x, new_offset_y)
                    fig.canvas.draw()

            else:
                annotation.set_visible(False)
                vertical_line.set_visible(False)
                fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_hover)

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        ax.legend()

    def update_plot(self, json_data):
        # 清空旧图表容器
        if self.plot_frame:  # 如果已有图表容器，先销毁
            self.plot_frame.destroy()
        
        # 创建新的图表容器
        self.plot_frame = ctk.CTkFrame(self.viz_frame)
        self.plot_frame.pack(fill="both", expand=True)  # 填充整个可视化区域
        
        # 过滤数据（原有逻辑）
        option = self.display_option.get()
        filtered_density = self.filter_data_by_option(
            json_data['density'], 
            json_data['hot_words'], 
            option
        )
        
        # 绘制新图表（原有逻辑）
        self.plot_density_with_hover_and_line(
            filtered_density, 
            json_data['hot_words'], 
            self.plot_frame
        )

    def update_plot_if_data(self):
        if self.json_data:
            self.update_plot(self.json_data)

    def show_p_selection(self, pagelist, p_titles, video_id):
        # 销毁旧的分P选择界面（如果存在）
        if self.p_selection_frame:
            self.p_selection_frame.destroy()
        
        # 创建新的分P选择容器
        self.p_selection_frame = ctk.CTkFrame(self.main_container)
        self.p_selection_frame.pack(pady=10, fill='x')  # 只保留一次pack
        
        # 清空容器内的旧组件
        for widget in self.p_selection_frame.winfo_children():
            widget.destroy()
        
        # 添加标签和下拉框
        p_label = ctk.CTkLabel(self.p_selection_frame, text="请选择要分析的分P:", font=("Arial", 14))
        p_label.pack(side="left", padx=10)  # 确保调用pack

        self.p_selection_frame.pack(pady=10, fill='x')

        p_label = ctk.CTkLabel(self.p_selection_frame, text="请选择要分析的分P:", font=("Arial", 14))

        p_dropdown = ctk.CTkComboBox(
            self.p_selection_frame, 
            values=p_titles, 
            variable=self.selected_p, 
            width=300,
            dropdown_font=("Arial", 12)
        )
        p_dropdown.pack(side="left", padx=10)
        p_dropdown.set(p_titles[0])

        p_confirm_button = ctk.CTkButton(
            self.p_selection_frame, 
            text="确认选择", 
            command=lambda: self.on_p_selected(pagelist, p_titles, video_id), 
            corner_radius=10
        )
        p_confirm_button.pack(side="left", padx=10)

    def on_p_selected(self, pagelist, p_titles, video_id):
        selected_index = p_titles.index(self.selected_p.get())
        self.p_selection_frame.pack_forget()

        selected_p_data = pagelist[selected_index]
        cids = [selected_p_data['cid']]

        if 'cids' in selected_p_data and isinstance(selected_p_data['cids'], list):
            cids.extend([cid_info['cid'] for cid_info in selected_p_data['cids']])

        self.progress_label.configure(text="开始下载弹幕文件...")
        self.progress_bar.set(0)
        self.progress_frame.pack(pady=10, fill='x')

        threading.Thread(
            target=self.download_and_process_danmaku, 
            args=(video_id, cids), 
            daemon=True
        ).start()

    def download_and_process_danmaku(self, video_id, cids):
        total_cids = len(cids)
        completed_cids = 0

        aggregated_danmaku_per_minute = defaultdict(list)
        aggregated_hot_words = defaultdict(Counter)
        aggregated_comments = defaultdict(list)

        for cid in cids:
            danmaku_url = self.get_danmaku_url(cid)
            if not danmaku_url:
                continue

            # 修改为内存下载
            if not self.download_danmaku(danmaku_url, video_id, cid):
                continue

            # 直接从缓存转换
            json_data = self.xml_to_json(video_id, cid)
            if not json_data:
                continue


            if not json_data:
                continue

            # 合并弹幕密度
            for minute, total in zip(json_data['density']['x'], json_data['density']['total']):
                aggregated_danmaku_per_minute[minute].append(total)

            # 合并热词
            for minute, words in json_data['hot_words']:
                for word, count in words:
                    aggregated_hot_words[minute][word] += count

            # 合并评论文本
            for minute_str, comments_list in json_data['comments'].items():
                minute_int = int(minute_str)
                aggregated_comments[minute_int].extend(comments_list)

            completed_cids += 1
            progress = completed_cids / total_cids
            self.update_progress(progress, f"已下载并处理 {completed_cids}/{total_cids} 个CID的弹幕文件...")

        if not aggregated_danmaku_per_minute:
            self.update_progress(1.0, "未能下载任何弹幕文件。")
            return

        merged_density = {
            'x': sorted(aggregated_danmaku_per_minute.keys()),
            'total': [sum(aggregated_danmaku_per_minute[m]) for m in sorted(aggregated_danmaku_per_minute.keys())]
        }

        merged_hot_words = []
        for minute in sorted(aggregated_hot_words.keys()):
            merged_hot_words.append([minute, aggregated_hot_words[minute].most_common(10)])

        merged_comments = {
            str(m): aggregated_comments[m]
            for m in sorted(aggregated_comments.keys())
        }

        merged_json_data = {
            'density': merged_density,
            'hot_words': merged_hot_words,
            'comments': merged_comments
        }

        self.root.after(0, lambda: self.update_plot(merged_json_data))
        self.root.after(0, lambda: self.progress_frame.pack_forget())

    def update_progress(self, progress, message):
        self.root.after(0, lambda: self.progress_bar.set(progress))
        self.root.after(0, lambda: self.progress_label.configure(text=message))

    def process_url_and_analyze(self):
        threading.Thread(target=self.process_url_and_analyze_thread, daemon=True).start()

    def process_url_and_analyze_thread(self):
        try:
            # 1. 重置关键变量
            self.json_data = None
            self.pagelist = []
            
            # 2. 隐藏分P选择界面（如果存在）
            if self.p_selection_frame:
                self.p_selection_frame.pack_forget()
            
            # 3. 禁用分析按钮防止重复点击
            self.root.after(0, lambda: self.analyze_btn.configure(state="disabled"))
            url = self.url_entry.get().strip()
            if not url:
                messagebox.showerror("错误", "请输入视频 URL！")
                return

            video_id = self.get_video_id(url)
            if not video_id:
                messagebox.showerror("错误", "无效的视频 URL！")
                return

            pagelist = self.get_pagelist(video_id)
            if not pagelist:
                return

            if len(pagelist) == 1:
                p_data = pagelist[0]
                cids = [p_data['cid']]

                if 'cids' in p_data and isinstance(p_data['cids'], list):
                    cids.extend([cid_info['cid'] for cid_info in p_data['cids']])

                self.progress_label.configure(text="开始下载弹幕文件...")
                self.progress_bar.set(0)
                self.progress_frame.pack(pady=10, fill='x')

                threading.Thread(
                    target=self.download_and_process_danmaku, 
                    args=(video_id, cids), 
                    daemon=True
                ).start()
            else:
                p_titles = [f"P{index + 1}: {p['part']}" for index, p in enumerate(pagelist)]
                self.root.after(0, lambda: self.show_p_selection(pagelist, p_titles, video_id))
        finally:
        # 无论成功或失败，最后重新启用分析按钮
            self.root.after(0, lambda: self.analyze_btn.configure(state="normal"))

    def on_closing(self):
        self.cleanup_cache()
        self.root.destroy()


if __name__ == "__main__":
    root = ctk.CTk()
    root.title("哔哩哔哩弹幕分析工具")
    # 初始窗口设置大一些
    root.geometry("1200x800")
    root.resizable(True, True)

    # 窗口居中
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (1200 // 2)
    y = (screen_height // 2) - (800 // 2)
    root.geometry(f"+{x}+{y}")

    analyzer = DanmakuAnalyzer(root)
    root.protocol("WM_DELETE_WINDOW", analyzer.on_closing)
    root.mainloop()