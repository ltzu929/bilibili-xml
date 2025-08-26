import React from 'react';
import type { AnalysisResult } from '../types';
import { DanmakuChart } from './DanmakuChart';
import { HighlightList } from './HighlightList';
import { RefreshCw, Download } from './icons';

interface ResultsDisplayProps {
    result: AnalysisResult;
    videoUrl: string;
    onReset: () => void;
}

export const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ result, videoUrl, onReset }) => {
    
    const handleDownload = () => {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(result, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", `${result.bvId}_analysis.json`);
        document.body.appendChild(downloadAnchorNode); // required for firefox
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    };

    return (
        <div className="bg-slate-800/50 p-4 sm:p-6 rounded-lg shadow-lg w-full">
            <div className="flex justify-between items-center mb-4">
                <div>
                     <h2 className="text-xl sm:text-2xl font-bold text-slate-100">分析结果: {result.bvId}</h2>
                     <p className="text-slate-400 text-sm">弹幕热度与热词 (/1min)</p>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={onReset} className="p-2 text-slate-400 hover:text-cyan-400 transition-colors duration-200" aria-label="Analyze another">
                        <RefreshCw className="w-5 h-5" />
                    </button>
                    <button onClick={handleDownload} className="p-2 text-slate-400 hover:text-cyan-400 transition-colors duration-200" aria-label="Download data">
                        <Download className="w-5 h-5" />
                    </button>
                </div>
            </div>
            
            <div className="mb-6">
                <DanmakuChart data={result.chartData} />
            </div>

            <div>
                <h3 className="text-xl font-semibold mb-4 text-slate-200">高能时刻列表</h3>
                <HighlightList highlights={result.highlights} bvId={result.bvId} />
            </div>
        </div>
    );
};
