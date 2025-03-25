import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from scipy.interpolate import make_interp_spline
import customtkinter as ctk

class DanmakuPlotter:
    def __init__(self, root):
        self.root = root
        self.fig = None
        self.ax = None
        self.canvas = None

    def create_plot_frame(self, parent):
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        return self.canvas.get_tk_widget()

    def update_plot(self, json_data):
        if not json_data:
            return

        self.ax.clear()

        # 绘制弹幕密度图
        x = json_data['density']['x']
        y = json_data['density']['total']
        self.ax.plot(x, y, label='弹幕密度')

        # 设置图表样式
        self.ax.set_title('弹幕密度分析')
        self.ax.set_xlabel('时间（分钟）')
        self.ax.set_ylabel('弹幕数量')
        self.ax.legend()
        self.ax.grid(True)

        self.canvas.draw()

    def enable_navigation(self):
        """启用图表缩放和拖拽功能"""
        if not self.fig or not self.ax:
            return

        # 保存初始视图限制
        self.ax._original_view = (self.ax.get_xlim(), self.ax.get_ylim())

        # 绑定事件
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)

    def on_scroll(self, event):
        if event.inaxes != self.ax:
            return
        base_scale = 1.1
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        xdata = event.xdata
        ydata = event.ydata
        if event.button == 'up':
            scale_factor = 1 / base_scale
        elif event.button == 'down':
            scale_factor = base_scale
        else:
            scale_factor = 1
        self.ax.set_xlim([xdata - (xdata - cur_xlim[0]) * scale_factor,
                         xdata + (cur_xlim[1] - xdata) * scale_factor])
        self.ax.set_ylim([ydata - (ydata - cur_ylim[0]) * scale_factor,
                         ydata + (cur_ylim[1] - ydata) * scale_factor])
        self.canvas.draw()

    def on_press(self, event):
        if event.inaxes != self.ax:
            return
        self._drag_start = (event.xdata, event.ydata)

    def on_release(self, event):
        self._drag_start = None

    def on_motion(self, event):
        if not self._drag_start or event.inaxes != self.ax:
            return
        dx = event.xdata - self._drag_start[0]
        dy = event.ydata - self._drag_start[1]
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        self.ax.set_xlim(xlim[0] - dx, xlim[1] - dx)
        self.ax.set_ylim(ylim[0] - dy, ylim[1] - dy)
        self.canvas.draw()

    def on_key_press(self, event):
        if event.key == 'r':
            self.ax.set_xlim(self.ax._original_view[0])
            self.ax.set_ylim(self.ax._original_view[1])
            self.canvas.draw()