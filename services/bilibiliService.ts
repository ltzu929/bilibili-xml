import type { AnalysisResult } from '../types';

function extractBvId(url: string): string | null {
    const patterns = [
        /bilibili\.com\/video\/(BV[a-zA-Z0-9]+)/,
        /^(BV[a-zA-Z0-9]+)$/
    ];
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match && match[1]) {
            return match[1];
        }
    }
    return null;
}

export const fetchAndAnalyzeVideo = async (url: string): Promise<AnalysisResult> => {
    const bvId = extractBvId(url);
    if (!bvId) {
        throw new Error('无效的B站链接或BV号。请输入正确的URL或BV号。');
    }

    // The frontend now calls our local backend server
    const serverUrl = `http://localhost:3001/api/analyze?url=${encodeURIComponent(url)}`;

    try {
        const response = await fetch(serverUrl);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `服务器错误: ${response.status}`);
        }

        const result: AnalysisResult = await response.json();
        return result;

    } catch (error) {
        if (error instanceof TypeError) {
             // This typically happens if the server is not running or there's a network issue.
             throw new Error('无法连接到分析服务器。请确保后端服务正在运行。');
        }
        // Re-throw other errors (like the one from the server response)
        throw error;
    }
};
