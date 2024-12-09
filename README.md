# Bilibili 弹幕分析工具

## 项目简介
欢迎来到 `bilibili-xml`！这是一个用于解析和分析B站直播间的XML格式弹幕数据的Python脚本。通过这个工具，你可以直观地了解直播间内每一分钟的弹幕活动情况，并获取最热门的弹幕内容，帮助你更深入地理解观众的互动模式。

## 技术栈
- **Python**：作为主要编程语言。
- **Matplotlib**：用于创建图表以可视化弹幕数据。
- **Tkinter**：用于提供简单的文件选择图形界面。
- **ElementTree**：用于解析XML格式的弹幕文件。

## 功能特性
- **中文字体支持**：使用SimHei字体确保中文字符正确显示，并解决负号显示问题。
- **直观的数据可视化**：生成折线图展示每分钟的弹幕数量变化趋势，并在图表上标记出弹幕数量突增的点。
- **热点弹幕追踪**：在图表右下角列出弹幕数量最多的五个时刻及其对应的弹幕内容，便于快速定位高互动时段。
- **简化文本处理**：预处理弹幕内容，标准化特定字符（如“哈”、“?”、“草”、“艹”）并忽略包含“晚安”的弹幕。
- **交互式信息提示**：当鼠标悬停在图表上的某一点时，会显示该分钟内最常见的三个弹幕内容。

## 使用指南
1. **环境准备**：请确保已安装Python 3.x版本，并且安装了`matplotlib`库。可以通过pip命令安装：
   ```bash
   pip install matplotlib
2. **文件选择**：运行 路灯.py 后，程序会弹出一个文件选择对话框，让你选择要分析的XML弹幕文件。
3. **查看结果**：选择文件后，程序会自动解析弹幕数据并生成一张图表，直观展示弹幕数量随时间的变化及热门弹幕内容。

## 未来规划
我们计划进一步扩展此工具的功能，包括但不限于：
~ 开发用户友好的前端界面，让用户能够更方便地操作。
~ 实现直接从B站下载视频对应XML文件的功能，仅需提供视频链接即可完成全部流程
