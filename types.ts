
export interface Danmaku {
    timestamp: number; // in seconds from video start
    content: string;
}

export interface ChartDataPoint {
    time: number; // Start time of the window in seconds
    displayTime: string; // Formatted time string (HH:MM:SS)
    count: number;
    hotWords: string[];
}

export interface Highlight {
    timestamp: number; // in seconds
    count: number;
}

export interface AnalysisResult {
    chartData: ChartDataPoint[];
    highlights: Highlight[];
    bvId: string;
    videoDuration: number;
}
