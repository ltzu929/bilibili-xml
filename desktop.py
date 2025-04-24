import webview
import threading
import sys
import os
import time
import logging
from app import app
from queue import Queue
from flask import request

# 创建一个线程安全的消息队列
message_queue = Queue()

# 添加Flask路由以支持进度报告
@app.route('/api/progress', methods=['GET'])
def get_progress():
    if not message_queue.empty():
        return {'status': 'processing', 'message': message_queue.get()}
    return {'status': 'idle', 'message': ''}

def start_server():
    """启动Flask服务器"""
    try:
        # 使用线程池处理请求，提高并发能力
        from werkzeug.serving import run_simple
        run_simple('127.0.0.1', 5000, app, threaded=True)
    except Exception as e:
        logging.error(f"服务器启动失败: {e}")
        sys.exit(1)

def create_window():
    """创建WebView窗口"""
    try:
        # 配置窗口属性，提升用户体验
        window = webview.create_window(
            '路灯 - B站弹幕分析工具', 
            'http://127.0.0.1:5000',
            width=1200, 
            height=800, 
            resizable=True,
            min_size=(800, 600),
            background_color='#FFFFFF',
            text_select=True
        )
        
        # 设置关闭处理函数
        window.events.closed += on_window_close
        
        webview.start(debug=False)
    except Exception as e:
        logging.error(f"窗口创建失败: {e}")
        sys.exit(1)

def on_window_close():
    """窗口关闭时的清理操作"""
    logging.info("应用程序正在关闭...")
    # 执行必要的清理操作
    sys.exit(0)

# 设置日志记录
def setup_logging():
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, f'app_{time.strftime("%Y%m%d_%H%M%S")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

if __name__ == '__main__':
    # 设置日志
    setup_logging()
    
    # 设置工作目录为应用程序所在目录
    if getattr(sys, 'frozen', False):
        # 如果是PyInstaller打包后的应用
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    os.chdir(application_path)
    logging.info(f"工作目录: {application_path}")
    
    # 启动Flask服务器线程
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()
    
    # 等待服务器启动
    time.sleep(1)
    
    # 创建WebView窗口
    create_window()