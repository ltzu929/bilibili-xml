import customtkinter as ctk
import xml.etree.ElementTree as ET
from collections import defaultdict, Counter
import matplotlib
matplotlib.use('TkAgg')
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
from downloader import DanmakuDownloader
from analyzer import DanmakuAnalyzer
from plotter import DanmakuPlotter

# 配置日志
logging.basicConfig(level=logging.ERROR)

# 全局变量用于存储下载的文件路径
downloaded_files = []

# 配置界面的外观
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# 配置 Matplotlib 中文字体支持，确保显示中文字符
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


class DanmakuApp:
    def __init__(self, root):
        self.root = root
        self.downloader = DanmakuDownloader()
        self.analyzer = DanmakuAnalyzer(self.downloader)
        self.plotter = DanmakuPlotter(self.root)
        self.json_data = None
        self.pagelist = []
        self.plot_frame = None
        self.p_selection_frame = None
        self.memory_cache = {}

        # 用户选择的过滤选项变量
        self.display_option = StringVar(value="all")
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
                                   border_width=1, border_color="#E0E0E0",
                                   bg_color="#1E90FF")
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
            corner_radius=20,
            border_width=2,
            border_color="#FFFFFF",
            fg_color=("#1E90FF", "#004E98"),
            hover_color=("#0066CC", "#003366"),
            font=("Microsoft YaHei", 14, "bold"),
            command=self.process_url_and_analyze,
            width=120,
            height=40,
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
            corner_radius=24,
            fg_color=("#FFFFFF", "#2B2B2B"),
            border_width=1,
            border_color="#E0E0E0"
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
    def process_url_and_analyze(self):
        """
        处理URL并开始分析弹幕数据
        """
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("错误", "请输入有效的B站视频链接！")
            return
        
        # 设置加载状态
        self.set_loading(True)
        
        try:
            # 这里添加实际的URL处理和弹幕分析逻辑
            pass
        except Exception as e:
            messagebox.showerror("错误", f"分析失败: {str(e)}")
        finally:
            self.set_loading(False)

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
        for minute, comment in results:
            text_box.insert("end", f"[{minute}] {comment}\n")

        text_box.configure(state="disabled")

if __name__ == "__main__":
    root = ctk.CTk()
    root.geometry('1200x800')
    app = DanmakuApp(root)
    root.mainloop()