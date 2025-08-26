const express = require('express');
const cors = require('cors');
const axios = require('axios');
const xmlJs = require('xml-js');
const path = require('path');

const app = express();
const PORT = 3001;

// Middlewares
app.use(cors());
app.use(express.json());

// Serve static files from the 'dist' directory
const staticPath = path.join(__dirname, '..', 'dist');
app.use(express.static(staticPath));


// --- Bilibili API Logic ---

function extractBvId(url) {
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

async function getVideoInfo(bvId) {
    const url = `https://api.bilibili.com/x/web-interface/view?bvid=${bvId}`;
    const response = await axios.get(url, {
        headers: { 'User-Agent': 'Mozilla/5.0' }
    });
    if (response.data.code !== 0) {
        throw new Error('无法获取视频信息，请检查BV号是否正确。');
    }
    return {
        cid: response.data.data.cid,
        duration: response.data.data.duration,
    };
}

async function getDanmakuData(cid) {
    const url = `https://api.bilibili.com/x/v1/dm/list.so?oid=${cid}`;
    const response = await axios.get(url, { 
        responseType: 'arraybuffer',
        headers: { 'User-Agent': 'Mozilla/5.0' } 
    });
    const xmlData = new TextDecoder('utf-8').decode(response.data); // Use UTF-8 to prevent garbled text
    const jsonData = xmlJs.xml2js(xmlData, { compact: true });
    
    if (!jsonData.i || !jsonData.i.d) {
        return [];
    }

    const danmakus = Array.isArray(jsonData.i.d) ? jsonData.i.d : [jsonData.i.d];

    return danmakus.map(d => {
        const p = d._attributes.p.split(',');
        return {
            timestamp: parseFloat(p[0]),
            content: d._text || '',
        };
    });
}

function normalizeWord(word) {
    if (/^h+a+$/.test(word) || /^哈+$/.test(word)) {
        return '哈哈';
    }
    if (/^c+a+o+$/.test(word) || /^草+$/.test(word)) {
        return '草';
    }
    return word.replace(/\s/g, '');
}

function analyzeDanmakuData(danmakuData, durationSeconds, intervalSeconds = 60, thresholdMultiplier = 2.5) {
    const numIntervals = Math.ceil(durationSeconds / intervalSeconds);
    const buckets = Array.from({ length: numIntervals }, () => ({ danmaku: [] }));

    for (const d of danmakuData) {
        const index = Math.floor(d.timestamp / intervalSeconds);
        if (index < numIntervals) {
            buckets[index].danmaku.push(d);
        }
    }

    const chartData = buckets.map((bucket, i) => {
        const time = i * intervalSeconds;
        const h = Math.floor(time / 3600).toString().padStart(2, '0');
        const m = Math.floor((time % 3600) / 60).toString().padStart(2, '0');
        const s = Math.floor(time % 60).toString().padStart(2, '0');
        
        const hotWordCounts = {};
        bucket.danmaku.forEach(d => {
            if (d.content) {
                const normalized = normalizeWord(d.content.trim());
                if (normalized) {
                    hotWordCounts[normalized] = (hotWordCounts[normalized] || 0) + 1;
                }
            }
        });
        
        const sortedHotWords = Object.entries(hotWordCounts)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 5)
            .map(([word]) => word);

        return {
            time,
            displayTime: `${h}:${m}:${s}`,
            count: bucket.danmaku.length,
            hotWords: sortedHotWords,
        };
    });

    const highlights = [];
    const movingAverageWindow = 5;
    for (let i = 0; i < chartData.length; i++) {
        const currentPoint = chartData[i];
        if (currentPoint.count === 0) continue;

        const start = Math.max(0, i - movingAverageWindow);
        const end = Math.min(chartData.length - 1, i + movingAverageWindow);
        
        let sum = 0;
        let count = 0;
        for (let j = start; j <= end; j++) {
            if (i !== j) {
                sum += chartData[j].count;
                count++;
            }
        }
        const avg = count > 0 ? sum / count : 0;
        
        if (currentPoint.count > Math.max(10, avg * thresholdMultiplier)) {
            const lastHighlight = highlights[highlights.length - 1];
            if (!lastHighlight || Math.abs(currentPoint.time - lastHighlight.timestamp) > intervalSeconds * 2) {
                highlights.push({ timestamp: currentPoint.time, count: currentPoint.count });
            }
        }
    }

    return { chartData, highlights };
}


// --- API Endpoint ---

app.get('/api/analyze', async (req, res) => {
    const videoUrl = req.query.url;
    if (!videoUrl) {
        return res.status(400).json({ message: 'URL is required' });
    }

    try {
        console.log(`[Server] Received request for URL: ${videoUrl}`);
        
        const bvId = extractBvId(videoUrl);
        if (!bvId) {
            return res.status(400).json({ message: '无效的B站链接或BV号。' });
        }
        console.log(`[Server] Extracted BV ID: ${bvId}`);
        
        console.log('[Server] Fetching video info...');
        const { cid, duration } = await getVideoInfo(bvId);
        console.log(`[Server] Got CID: ${cid}, Duration: ${duration}s`);
        
        console.log('[Server] Fetching danmaku data...');
        const danmakuData = await getDanmakuData(cid);
        console.log(`[Server] Fetched ${danmakuData.length} danmakus.`);

        console.log('[Server] Analyzing data...');
        const { chartData, highlights } = analyzeDanmakuData(danmakuData, duration);
        console.log(`[Server] Analysis complete. Found ${highlights.length} highlights.`);

        const result = {
            chartData,
            highlights,
            bvId,
            videoDuration: duration,
        };

        res.status(200).json(result);

    } catch (error) {
        console.error('[Server] An error occurred:', error.message);
        res.status(500).json({ message: error.message || '分析过程中发生未知错误。' });
    }
});


// Catch-all to serve index.html for any other request
app.get('*', (req, res) => {
    res.sendFile(path.join(staticPath, 'index.html'));
});


app.listen(PORT, () => {
    console.log(`[Server] Server listening on port ${PORT}`);
});
