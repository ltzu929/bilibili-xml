from collections import defaultdict, Counter
import xml.etree.ElementTree as ET
from dataclasses import dataclass

@dataclass
class DanmakuData:
    x: list
    total: list
    hot_words: list
    comments: dict

class DanmakuAnalyzer:
    @staticmethod
    def xml_to_json(xml_content: str) -> DanmakuData:
        try:
            root = ET.fromstring(xml_content)
            danmaku_per_minute = defaultdict(list)

            for d in root.findall('d'):
                p = d.get('p').split(',')
                time = float(p[0])
                content = d.text if d.text else ""
                
                # 弹幕归一化处理
                content = DanmakuAnalyzer._normalize_danmaku(content)
                minute = int(time // 60)
                danmaku_per_minute[minute].append(content)

            return DanmakuData(
                x=sorted(danmaku_per_minute.keys()),
                total=[len(danmaku_per_minute[m]) for m in sorted(danmaku_per_minute.keys())],
                hot_words=[[m, Counter(danmaku_per_minute[m]).most_common(10)] 
                          for m in sorted(danmaku_per_minute.keys())],
                comments={str(m): danmaku_per_minute[m] 
                         for m in sorted(danmaku_per_minute.keys())}
            )
        except Exception as e:
            raise ValueError(f"XML解析失败: {str(e)}")

    @staticmethod
    def _normalize_danmaku(content: str) -> str:
        # 统一常见弹幕格式
        normalized = content.strip()
        if all(char in "哈" for char in normalized):
            return "哈"
        if all(char in "？?" for char in normalized):
            return "？"
        if normalized in ["艹", "草"]:
            return "草"
        return normalized