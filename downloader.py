import requests
import logging
from tkinter import messagebox

class DanmakuDownloader:
    def __init__(self):
        self.memory_cache = {}

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