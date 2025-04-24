import os
import sys
import webbrowser
import time
import threading
from app import app

def open_browser():
    """在应用启动后打开浏览器"""
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # 创建数据目录
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists('data/cache'):
        os.makedirs('data/cache')
    
    # 启动浏览器线程
    threading.Thread(target=open_browser).start()
    
    # 启动Flask应用
    app.run(debug=False) 