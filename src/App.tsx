import React, { useState, useCallback } from 'react';
import { InputForm } from './components/InputForm';
import { ResultsDisplay } from './components/ResultsDisplay';
import { LoadingSpinner } from './components/LoadingSpinner';
import { fetchAndAnalyzeVideo } from './services/bilibiliService';
import type { AnalysisResult } from './types';

const App: React.FC = () => {
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
    const [videoUrl, setVideoUrl] = useState<string>('');

    const handleAnalyze = useCallback(async (url: string) => {
        setIsLoading(true);
        setError(null);
        setAnalysisResult(null);
        setVideoUrl(url);

        try {
            const result = await fetchAndAnalyzeVideo(url);
            setAnalysisResult(result);
        } catch (e) {
            if (e instanceof Error) {
                setError(e.message);
            } else {
                setError('An unknown error occurred.');
            }
        } finally {
            setIsLoading(false);
        }
    }, []);

    const handleReset = useCallback(() => {
        setIsLoading(false);
        setError(null);
        setAnalysisResult(null);
        setVideoUrl('');
    }, []);

    return (
        <div className="min-h-screen bg-slate-900 text-slate-200 flex flex-col items-center p-4 sm:p-6 lg:p-8 font-sans">
            <header className="w-full max-w-5xl text-center mb-8">
                <h1 className="text-4xl sm:text-5xl font-bold text-cyan-400">BiliHighlight Finder</h1>
                <p className="text-slate-400 mt-2">B站直播回放高能时刻探测器</p>
            </header>

            <main className="w-full max-w-5xl flex-grow">
                {!analysisResult && !isLoading && (
                    <InputForm onAnalyze={handleAnalyze} error={error} />
                )}
                
                {isLoading && (
                    <div className="flex flex-col items-center justify-center text-center p-8 bg-slate-800/50 rounded-lg">
                         <LoadingSpinner />
                         <p className="mt-4 text-lg text-slate-300">正在分析弹幕数据，请稍候...</p>
                         <p className="text-sm text-slate-500">（这可能需要一点时间，取决于视频长度）</p>
                    </div>
                )}

                {analysisResult && (
                    <ResultsDisplay 
                        result={analysisResult} 
                        videoUrl={videoUrl}
                        onReset={handleReset}
                    />
                )}
            </main>

            <footer className="w-full max-w-5xl text-center mt-8 py-4 border-t border-slate-700">
                <p className="text-slate-500 text-sm">
                    Created with React, TypeScript, and Tailwind CSS.
                </p>
            </footer>
        </div>
    );
};

export default App;
