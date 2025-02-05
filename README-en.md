# Bilibili Danmaku Analysis Tool

## Project Overview
Welcome to the `Bilibili Danmaku Analysis Tool`! This is a Python script designed to parse and analyze XML-formatted danmaku data from Bilibili videos. With this tool, you can easily understand the danmaku activity per minute of a video and identify the most popular danmaku content, helping you gain deeper insights into viewer interaction patterns.

## Tech Stack
- **Python**: The main programming language.
- **Matplotlib**: Used to create charts to visualize the danmaku data.
- **Tkinter**: Provides a simple file selection GUI.
- **ElementTree**: Used to parse XML-format danmaku files.
- **Requests**: Used to download danmaku data from the internet.

## Features
- **Automated URL Handling**: Supports direct input of Bilibili video links, automatically extracting and validating the video link's validity.
- **Intuitive Data Visualization**: Generates line charts showing the trend of danmaku counts per minute and marks the points where the danmaku count spikes.
- **Simplified Text Processing**: Pre-processes danmaku content, standardizes specific characters (such as "Ha", "?", "Cao", "草", "艹", "1"), and ignores danmaku containing "Good night".
- **Interactive Information Tooltip**: When hovering over a point on the chart, the top three most frequent danmaku at that minute will be displayed.
- **Automatic Danmaku File Download**: Just provide the video link, and the tool will automatically download and analyze the danmaku file.

## Usage Guide
1. **Download the File**: Simply download the `.exe` file.
2. **Run**: Double-click to run the program.
3. **Input URL**: Enter the sharing link of the video you want to analyze.
4. **View Results**: The program will automatically parse the danmaku data and generate a chart that visually displays how the danmaku count changes over time, along with the popular danmaku content.

## Future Plans
I plan to further expand the functionality of this tool, including:
- Supporting emoji analysis.
- Supporting SC (Super Chat) search.
