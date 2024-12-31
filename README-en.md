# Bilibili Danmaku Analysis Tool  

## Project Overview  
Welcome to the **Bilibili Danmaku Analysis Tool**! This is a Python script designed for parsing and analyzing XML-format danmaku (commentary subtitles) data from Bilibili videos. With this tool, you can visually understand danmaku activity for each minute of a video and identify the most popular comments, providing deeper insights into audience interaction patterns.  

## Technology Stack  
- **Python**: The primary programming language.  
- **Matplotlib**: Used to create charts for visualizing danmaku data.  
- **Tkinter**: Provides a simple graphical interface for file selection (optional).  
- **ElementTree**: Parses XML-format danmaku files.  
- **Requests**: Downloads danmaku data from the internet.  

## Features  
- **Automated URL Processing**: Accepts plain text containing Bilibili video links, automatically extracting and validating video URLs.  
- **Intuitive Data Visualization**: Generates line charts showing changes in danmaku volume over time, highlighting significant spikes in activity.  
- **Hot Danmaku Tracking**: Lists the five moments with the highest danmaku volume and their associated comments in the bottom-left corner of the chart for quick identification of high-interaction periods.  
- **Simplified Text Processing**: Preprocesses danmaku content by standardizing specific characters (e.g., "ha," "?", "草," "艹," "1") and ignoring comments containing "goodnight."  
- **Interactive Tooltips**: Displays the top three most common comments for a specific minute when hovering over a point on the chart.  
- **Automatic Danmaku File Download**: Simply provide a video link, and the tool will automatically download and analyze the danmaku file.  

## Usage Guide  
1. **Download the File**: Download the `.exe` file.  
2. **Run the Tool**: Double-click to launch it.  
3. **Input the URL**: Enter the share link of the video you want to analyze.  
4. **View the Results**: The program will automatically parse the danmaku data and generate a chart, visually presenting the danmaku volume over time and highlighting popular comments.  

## Future Plans  
I plan to further enhance the tool with additional features, including:  
- Developing a user-friendly frontend interface for easier operation. (Completed)  
