
import React, { useState } from 'react';

interface InputFormProps {
    onAnalyze: (url: string) => void;
    error: string | null;
}

export const InputForm: React.FC<InputFormProps> = ({ onAnalyze, error }) => {
    const [url, setUrl] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (url.trim()) {
            onAnalyze(url.trim());
        }
    };

    return (
        <div className="w-full max-w-2xl mx-auto p-8 bg-slate-800 rounded-lg shadow-2xl shadow-cyan-500/10">
            <h2 className="text-2xl font-semibold text-center text-slate-100 mb-2">开始分析</h2>
            <p className="text-center text-slate-400 mb-6">粘贴B站视频链接或BV号，快速定位高能时刻！</p>
            <form onSubmit={handleSubmit}>
                <div className="flex flex-col sm:flex-row gap-4">
                    <input
                        type="text"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="例如: https://www.bilibili.com/video/BV1..."
                        className="flex-grow bg-slate-700 text-slate-200 border-2 border-slate-600 rounded-md px-4 py-3 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition duration-300"
                    />
                    <button
                        type="submit"
                        disabled={!url.trim()}
                        className="bg-cyan-600 text-white font-bold py-3 px-6 rounded-md hover:bg-cyan-500 disabled:bg-slate-600 disabled:cursor-not-allowed transition duration-300 transform hover:scale-105"
                    >
                        分析
                    </button>
                </div>
            </form>
            {error && (
                 <div className="mt-4 text-center bg-red-900/50 border border-red-700 text-red-300 p-3 rounded-md">
                    {error}
                </div>
            )}
        </div>
    );
};
