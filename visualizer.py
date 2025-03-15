import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from scipy.interpolate import make_interp_spline

class DanmakuVisualizer:
    @staticmethod
    def create_density_plot(density_data, hot_words, parent_frame):
        fig, ax = plt.subplots(figsize=(14, 8))
        x = np.array(density_data['x'])
        y = np.array(density_data['total'])
        
        # 数据预处理和插值逻辑
        if len(x) > 1:
            sorted_indices = np.argsort(x)
            x = x[sorted_indices]
            y = y[sorted_indices]
            unique_x, unique_indices = np.unique(x, return_index=True)
            x = unique_x
            y = y[unique_indices]

        if len(x) > 2:
            x_new = np.linspace(x.min(), x.max(), 300)
            spline = make_interp_spline(x, y, k=3)
            y_smooth = spline(x_new)
        else:
            x_new, y_smooth = x, y

        # 绘制图表
        ax.fill_between(x_new, y_smooth, color='skyblue', alpha=0.4)
        ax.plot(x_new, y_smooth, color='blue', linewidth=2)
        
        # 配置图表样式
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        ax.set_title("弹幕热度与热词 (/分钟)", fontsize=16)
        ax.set_xlabel("时间（分钟）", fontsize=14)
        ax.set_ylabel("弹幕数量", fontsize=14)
        
        # 创建画布并返回
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        return canvas, ax

    @staticmethod
    def setup_zoom(ax, canvas):
        def on_scroll(event):
            if event.inaxes != ax:
                return
            
            base_scale = 1.1
            cur_xlim = ax.get_xlim()
            cur_ylim = ax.get_ylim()
            
            # 处理滚轮缩放逻辑
            if event.button == 'up':
                scale_factor = 1 / base_scale
            elif event.button == 'down':
                scale_factor = base_scale
            else:
                return

            # 计算新范围并更新视图
            new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
            new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
            
            relx = (cur_xlim[1] - event.xdata)/(cur_xlim[1] - cur_xlim[0])
            rely = (cur_ylim[1] - event.ydata)/(cur_ylim[1] - cur_ylim[0])
            
            ax.set_xlim([event.xdata - new_width * (1 - relx), 
                        event.xdata + new_width * relx])
            ax.set_ylim([event.ydata - new_height * (1 - rely), 
                        event.ydata + new_height * rely])
            canvas.draw()
        
        canvas.mpl_connect('scroll_event', on_scroll)