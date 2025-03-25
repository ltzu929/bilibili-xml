from collections import defaultdict, Counter
import json
import logging
from tkinter import messagebox

class DanmakuAnalyzer:
    def __init__(self, downloader):
        self.downloader = downloader
        self.json_data = None

    def process_danmaku(self, video_id, cids):
        total_cids = len(cids)
        completed_cids = 0

        aggregated_danmaku_per_minute = defaultdict(list)
        aggregated_hot_words = defaultdict(Counter)
        aggregated_comments = defaultdict(list)

        for cid in cids:
            if not self.downloader.download_danmaku(video_id, cid):
                continue

            json_data = self.xml_to_json(video_id, cid)
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

        if not aggregated_danmaku_per_minute:
            messagebox.showerror("错误", "未能下载任何弹幕文件。")
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

        self.json_data = {
            'density': merged_density,
            'hot_words': merged_hot_words,
            'comments': merged_comments
        }

        return self.json_data