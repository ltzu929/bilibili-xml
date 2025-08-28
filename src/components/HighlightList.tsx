import React from 'react';
import type { Highlight } from '../types';

interface HighlightListProps {
    highlights: Highlight[];
    bvId: string;
}

const formatTimestamp = (totalSeconds: number): string => {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = Math.floor(totalSeconds % 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
};

export const HighlightList: React.FC<HighlightListProps> = ({ highlights, bvId }) => {
    if (highlights.length === 0) {
        return (
            <div className="text-center p-6 bg-slate-700/50 rounded-lg">
                <p className="text-slate-400">未能根据当前阈值检测到明显的高能时刻。</p>
                <p className="text-slate-500 text-sm mt-1">可以尝试调整分析算法的灵敏度。</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
            {highlights.map((highlight, index) => {
                const url = `https://www.bilibili.com/video/${bvId}?t=${highlight.timestamp}`;
                return (
                    <div
                        key={index}
                        onClick={() => {
                            try {
                                if (window.electronAPI && window.electronAPI.openExternal) {
                                    window.electronAPI.openExternal(url);
                                } else {
                                    // Fallback: open in new tab if electronAPI is not available
                                    window.open(url, '_blank');
                                }
                            } catch (error) {
                                console.error('Failed to open external link:', error);
                                // Last resort fallback
                                window.open(url, '_blank');
                            }
                        }}
                        className="group block text-center p-3 bg-slate-700 rounded-md hover:bg-cyan-800/50 border border-slate-600 hover:border-cyan-600 transition-all duration-300 transform hover:-translate-y-1 cursor-pointer"
                        title={`点击将在系统默认浏览器中打开视频 ${formatTimestamp(highlight.timestamp)} 处`}
                    >
                        <p className="font-mono text-lg font-semibold text-cyan-400 group-hover:text-cyan-300">
                            {formatTimestamp(highlight.timestamp)}
                        </p>
                        <p className="text-xs text-slate-400 group-hover:text-slate-300">
                            弹幕: {highlight.count}
                        </p>
                    </div>
                );
            })}
        </div>
    );
};
