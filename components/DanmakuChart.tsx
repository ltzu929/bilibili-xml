
import React from 'react';
import { ResponsiveContainer, AreaChart, XAxis, YAxis, Tooltip, Area, Brush, CartesianGrid } from 'recharts';
import type { ChartDataPoint } from '../types';

interface DanmakuChartProps {
    data: ChartDataPoint[];
}

const CustomTooltip: React.FC<any> = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        const dataPoint = payload[0].payload;
        return (
            <div className="bg-slate-700/80 backdrop-blur-sm p-4 border border-slate-600 rounded-lg shadow-lg">
                <p className="text-slate-200 font-bold">{`时间: ${dataPoint.displayTime}`}</p>
                <p className="text-cyan-400">{`弹幕数: ${dataPoint.count}`}</p>
                 {dataPoint.hotWords && dataPoint.hotWords.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-slate-600">
                        <p className="text-slate-300 font-semibold mb-1">弹幕热词:</p>
                        <ul className="list-none p-0 m-0">
                           {dataPoint.hotWords.map((word: string, index: number) => (
                               <li key={index} className="text-slate-400">{word}</li>
                           ))}
                        </ul>
                    </div>
                 )}
            </div>
        );
    }
    return null;
};

export const DanmakuChart: React.FC<DanmakuChartProps> = ({ data }) => {
    return (
        <div style={{ width: '100%', height: 400 }}>
             <ResponsiveContainer>
                <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                        <linearGradient id="colorUv" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.8}/>
                            <stop offset="95%" stopColor="#22d3ee" stopOpacity={0}/>
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis 
                        dataKey="displayTime"
                        stroke="#94a3b8"
                        tick={{ fontSize: 12 }}
                        tickFormatter={(timeStr, index) => {
                            // Display fewer ticks to avoid clutter
                            if (data.length > 30 && index % Math.floor(data.length / 15) !== 0) {
                                return '';
                            }
                            return timeStr.substring(0, 5);
                        }}
                    />
                    <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Area type="monotone" dataKey="count" stroke="#67e8f9" fillOpacity={1} fill="url(#colorUv)" />
                    <Brush 
                        dataKey="displayTime" 
                        height={30} 
                        stroke="#0891b2" 
                        fill="#1e293b"
                        travellerWidth={15}
                        tickFormatter={(index) => data[index]?.displayTime.substring(0, 5) || ''}
                    >
                         <AreaChart>
                            <Area dataKey="count" stroke="#67e8f9" fill="#0e7490" />
                        </AreaChart>
                    </Brush>
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
};
