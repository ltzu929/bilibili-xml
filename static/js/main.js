document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const videoUrlInput = document.getElementById('videoUrl');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const searchQueryInput = document.getElementById('searchQuery');
    const searchBtn = document.getElementById('searchBtn');
    const searchResultsDiv = document.getElementById('searchResults');
    const videoTitleElement = document.getElementById('videoTitle');
    const videoAuthorElement = document.getElementById('videoAuthor');
    const startTimeInput = document.getElementById('startTimeInput');
    const chartOptionsForm = document.getElementById('chartOptionsForm');
    
    // 存储分析结果数据
    let analysisData = null;
    let densityChart = null;
    
    // 初始化图表
    function initChart() {
        if (densityChart) {
            densityChart.dispose();
        }
        densityChart = echarts.init(document.getElementById('density-chart'));
        window.addEventListener('resize', () => densityChart.resize());
    }
    
    // 绑定分析按钮点击事件
    analyzeBtn.addEventListener('click', function() {
        const inputText = videoUrlInput.value.trim();
        
        // 自动从输入文本中提取B站链接
        const extractedUrl = extractBilibiliUrl(inputText);
        
        if (!extractedUrl) {
            alert('未找到有效的B站视频链接！请检查输入内容。');
            return;
        }
        
        // 显示提取的链接
        videoUrlInput.value = extractedUrl;
        
        // 显示加载提示
        loadingDiv.classList.remove('d-none');
        resultsDiv.classList.add('d-none');
        
        // 发送分析请求
        fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ video_url: extractedUrl })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || '请求失败');
                });
            }
            return response.json();
        })
        .then(data => {
            // 保存分析数据
            analysisData = data;
            
            // 隐藏加载提示，显示结果
            loadingDiv.classList.add('d-none');
            resultsDiv.classList.remove('d-none');
            
            // 显示视频信息
            if (data.video_info) {
                videoTitleElement.textContent = data.video_info.title || '未知标题';
                videoAuthorElement.textContent = data.video_info.author || '未知UP主';
                videoTitleElement.parentElement.classList.remove('d-none');
            }
            
            // 显示图表属性设置区域
            document.getElementById('chartAttributesSection').classList.remove('d-none');
            
            // 初始化并渲染图表
            initChart();
            renderDensityChart();
        })
        .catch(error => {
            loadingDiv.classList.add('d-none');
            
            // 处理常见错误
            let errorMessage = error.message;
            if (errorMessage.includes('window_length')) {
                errorMessage = '该视频弹幕数据太少，无法进行分析。请尝试其他视频。';
            } else if (errorMessage.includes('无法获取视频信息')) {
                errorMessage = '无法获取视频信息，请确认视频链接正确且视频未被删除或设为私密。';
            } else if (errorMessage.includes('无法从URL中提取视频ID')) {
                errorMessage = '无效的B站视频链接，请检查输入内容。';
            }
            
            alert('分析失败: ' + errorMessage);
            console.error('分析错误:', error);
        });
    });
    
    // 从文本中提取B站链接
    function extractBilibiliUrl(text) {
        // 匹配B站链接的正则表达式，支持多种格式
        const patterns = [
            /https?:\/\/(www\.)?bilibili\.com\/video\/([^/?&#\s]+)/i,  // 完整链接
            /https?:\/\/(www\.)?b23\.tv\/([^/?&#\s]+)/i,  // 短链接
            /BV\w{10}/i,  // BV号
            /av\d+/i      // av号
        ];
        
        for (const pattern of patterns) {
            const match = text.match(pattern);
            if (match) {
                // 如果是完整链接或短链接
                if (match[0].startsWith('http')) {
                    // 去除问号后的参数
                    const url = match[0].split('?')[0];
                    return url;
                } 
                // 如果是BV号或av号，构造完整链接
                else {
                    return `https://www.bilibili.com/video/${match[0]}`;
                }
            }
        }
        
        return null;
    }
    
    // 绑定搜索按钮点击事件
    searchBtn.addEventListener('click', function() {
        const searchQuery = searchQueryInput.value.trim();
        if (!searchQuery || !analysisData) {
            return;
        }
        
        const results = [];
        
        // 在弹幕数据中搜索（现在comments是按秒索引的）
        for (const [second, comments] of Object.entries(analysisData.comments)) {
            for (const comment of comments) {
                if (comment.includes(searchQuery)) {
                    results.push({
                        second: parseInt(second),
                        text: comment
                    });
                }
            }
        }
        
        // 显示搜索结果
        renderSearchResults(results, searchQuery);
    });
    
    // 绑定图表属性选项变更事件
    if (chartOptionsForm) {
        chartOptionsForm.addEventListener('change', renderDensityChart);
    }
    
    // 标准化弹幕文本
    function normalizeComment(comment) {
        return comment
            .replace(/哈{2,}/g, '哈哈')
            .replace(/6{2,}/g, '66')
            .replace(/2{2,}3{2,}/g, '233')
            .replace(/[wW]{2,}/g, 'ww')
            .replace(/草{2,}/g, '草')
            .replace(/艹{2,}/g, '艹');
    }
    
    // 处理弹幕数据，计算热门弹幕
    function processComments(comments) {
        if (!comments || comments.length === 0) return [];
        
        const commentCounts = {};
        comments.forEach(comment => {
            const normalized = normalizeComment(comment);
            commentCounts[normalized] = (commentCounts[normalized] || 0) + 1;
        });
        
        return Object.entries(commentCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 3)
            .map(([text, count]) => ({ text, count }));
    }
    
    // 渲染弹幕密度图表
    function renderDensityChart() {
        if (!analysisData || !densityChart) return;
        
        const data = analysisData;
        
        // 获取图表选项
        const displayOption = document.querySelector('input[name="displayOption"]:checked')?.value || 'all';
        const startTime = document.getElementById('startTimeInput')?.value || '';
        
        // 使用秒级数据
        let xAxisData = data.density.x;
        let xAxisLabels = [];
        
        // 根据数据量动态调整标签间隔
        const labelInterval = xAxisData.length > 300 ? 30 : (xAxisData.length > 120 ? 15 : 5);
        
        // 格式化显示为 MM:SS 格式
        for (let i = 0; i < xAxisData.length; i++) {
            // 每labelInterval秒显示一个标签，避免过于密集
            if (i % labelInterval === 0 || i === xAxisData.length - 1) {
                const minutes = Math.floor(xAxisData[i] / 60);
                const seconds = xAxisData[i] % 60;
                xAxisLabels.push(`${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
            } else {
                xAxisLabels.push('');
            }
        }
        
        // 如果有起始时间，转换秒数到实际时间
        if (startTime && /^\d{2}:\d{2}:\d{2}$/.test(startTime)) {
            const [startHour, startMinute, startSecond] = startTime.split(':').map(Number);
            xAxisLabels = [];
            
            for (let i = 0; i < xAxisData.length; i++) {
                if (i % labelInterval === 0 || i === xAxisData.length - 1) {
                    const totalSeconds = startSecond + xAxisData[i];
                    const seconds = totalSeconds % 60;
                    const totalMinutes = startMinute + Math.floor(totalSeconds / 60);
                    const minutes = totalMinutes % 60;
                    const hours = startHour + Math.floor(totalMinutes / 60);
                    
                    xAxisLabels.push(`${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
                } else {
                    xAxisLabels.push('');
                }
            }
        }
        
        // 处理不同类型的密度数据
        let seriesData = data.density.smooth || data.density.total;
        let seriesLineColor = '#3E78B2';
        let seriesAreaColorStops = [
            { offset: 0, color: 'rgba(62, 120, 178, 0.7)' },
            { offset: 1, color: 'rgba(62, 120, 178, 0.1)' }
        ];
        let seriesName = '弹幕密度';
        
        if (displayOption === 'callOnly' && data.call_density) {
            seriesData = data.call_density;
            seriesName = '打call密度';
        } else if (displayOption === 'haOnly' && data.ha_density) {
            seriesData = data.ha_density;
            seriesName = '"哈"密度';
            seriesLineColor = '#FF9966';
            seriesAreaColorStops = [
                { offset: 0, color: 'rgba(255, 153, 102, 0.7)' },
                { offset: 1, color: 'rgba(255, 153, 102, 0.1)' }
            ];
        } else if (displayOption === 'questionOnly' && data.question_density) {
            seriesData = data.question_density;
            seriesName = '"？"密度';
            seriesLineColor = '#9966CC';
            seriesAreaColorStops = [
                { offset: 0, color: 'rgba(153, 102, 204, 0.7)' },
                { offset: 1, color: 'rgba(153, 102, 204, 0.1)' }
            ];
        }
        
        // 找出峰值点
        let peakPoints = findPeakPoints(seriesData, xAxisLabels);
        
        // 预处理弹幕数据，计算每个时间点的热门弹幕
        const popularComments = {};
        for (const [secondKey, comments] of Object.entries(data.comments)) {
            const second = parseInt(secondKey);
            popularComments[second] = processComments(comments);
        }
        
        // 格式化时间函数（用于显示在tooltip中）
        function formatTime(seconds) {
            const minutes = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        
        const option = {
            title: {
                text: '弹幕热度分析 (精确到秒)',
                left: 'center'
            },
            tooltip: {
                trigger: 'axis',
                formatter: function(params) {
                    const timeIndex = params[0].dataIndex;
                    const seconds = xAxisData[timeIndex];
                    const time = formatTime(seconds);
                    const value = params[0].value;
                    
                    let result = `<div style="font-weight: bold; margin-bottom: 5px;">${time} (${seconds}秒): ${value}条弹幕</div>`;
                    
                    // 获取该时间点的热门弹幕
                    const topComments = popularComments[seconds] || [];
                    
                    // 检查当前时间点是否有弹幕数据
                    const secondComments = data.comments[seconds.toString()] || [];
                    
                    if (topComments.length > 0) {
                        result += '<div style="margin-top: 8px;">热门弹幕：</div>';
                        
                        topComments.forEach((item, index) => {
                            result += `<div style="margin-top: 3px; font-size: 13px;">
                                <span style="display: inline-block; width: 16px; text-align: center; margin-right: 5px;">${index + 1}</span>
                                <span style="font-weight: bold;">${item.text}</span>
                                <span style="color: #888; margin-left: 5px;">(${item.count})</span>
                            </div>`;
                        });
                    } else if (secondComments.length > 0) {
                        // 如果没有热门弹幕但有原始弹幕，则显示原始弹幕
                        result += `<div style="margin-top: 8px;">原始弹幕(前3条)：</div>`;
                        
                        for (let i = 0; i < Math.min(3, secondComments.length); i++) {
                            result += `<div style="margin-top: 3px; font-size: 13px;">${secondComments[i]}</div>`;
                        }
                    } else {
                        result += '<div style="color: #888; margin-top: 5px;">此时间点无弹幕</div>';
                    }
                    
                    return result;
                },
                axisPointer: {
                    type: 'line',
                    lineStyle: {
                        color: 'rgba(0, 0, 0, 0.2)',
                        width: 1,
                        type: 'solid'
                    }
                },
                padding: 10,
                textStyle: {
                    fontSize: 13
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                data: xAxisData,
                axisLabel: {
                    formatter: function(value, index) {
                        return xAxisLabels[index];
                    },
                    fontSize: 10,
                    rotate: 45,
                    interval: 'auto' // 自动控制标签密度
                },
                axisLine: { lineStyle: { color: '#666' } }
            },
            yAxis: {
                type: 'value',
                name: '弹幕数量',
                nameLocation: 'middle',
                nameGap: 40,
                axisLine: { lineStyle: { color: '#666' } },
                splitLine: { lineStyle: { color: '#ddd', type: 'dashed' } }
            },
            dataZoom: [{
                type: 'inside',
                start: 0,
                end: 100
            }, {
                start: 0,
                end: 100
            }],
            series: [{
                name: seriesName,
                type: 'line',
                smooth: true,
                symbol: 'none', // 不显示数据点标记
                sampling: 'average', // 对数据进行抽样平均
                data: seriesData,
                lineStyle: { width: 2, color: seriesLineColor },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: seriesAreaColorStops
                    }
                },
                markPoint: {
                    symbolSize: 45,
                    data: peakPoints
                }
            }]
        };
        
        densityChart.setOption(option);
        
        // 添加图表点击事件
        densityChart.off('click');
        densityChart.on('click', function(params) {
            if (params.componentType === 'series') {
                const second = xAxisData[params.dataIndex];
                const time = formatTime(second);
                const comments = data.comments[second.toString()] || [];
                
                if (comments.length > 0) {
                    // 创建弹出层显示该时间点的所有弹幕
                    const modal = document.getElementById('commentModal') || createCommentModal();
                    const modalTitle = modal.querySelector('.modal-title');
                    const modalBody = modal.querySelector('.modal-body');
                    
                    modalTitle.textContent = `${time} (${second}秒) 的弹幕`;
                    modalBody.innerHTML = '';
                    
                    const list = document.createElement('ul');
                    list.className = 'list-group';
                    
                    comments.forEach(comment => {
                        const item = document.createElement('li');
                        item.className = 'list-group-item';
                        item.textContent = comment;
                        list.appendChild(item);
                    });
                    
                    modalBody.appendChild(list);
                    
                    // 显示模态框
                    const commentModal = new bootstrap.Modal(modal);
                    commentModal.show();
                }
            }
        });
    }
    
    // 创建评论模态框
    function createCommentModal() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'commentModal';
        modal.tabIndex = '-1';
        modal.setAttribute('aria-labelledby', 'commentModalLabel');
        modal.setAttribute('aria-hidden', 'true');
        
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="commentModalLabel">弹幕详情</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        return modal;
    }
    
    // 找出峰值点
    function findPeakPoints(data, xAxisLabels) {
        const maxValue = Math.max(...data);
        const threshold = maxValue * 0.6; // 60%的最大值作为阈值
        
        let peaks = [];
        for (let i = 1; i < data.length - 1; i++) {
            if (data[i] > threshold && 
                data[i] > data[i-1] && 
                data[i] >= data[i+1]) {
                
                // 查找局部区域内的最高点
                let isLocalMax = true;
                for (let j = Math.max(0, i - 5); j < Math.min(data.length, i + 6); j++) {
                    if (j !== i && data[j] > data[i]) {
                        isLocalMax = false;
                        break;
                    }
                }
                
                if (isLocalMax) {
                    peaks.push({
                        value: [i, data[i]],
                        xAxis: i,
                        yAxis: data[i],
                        name: '峰值',
                        label: { 
                            formatter: `峰值: ${xAxisLabels[i] || i}`,
                            position: 'top'
                        }
                    });
                }
            }
        }
        
        // 最多显示5个峰值
        if (peaks.length > 5) {
            peaks.sort((a, b) => b.yAxis - a.yAxis);
            peaks = peaks.slice(0, 5);
        }
        
        return peaks;
    }
    
    // 渲染搜索结果
    function renderSearchResults(results, query) {
        searchResultsDiv.innerHTML = '';
        
        if (results.length === 0) {
            searchResultsDiv.innerHTML = `
                <div class="alert alert-info">
                    未找到包含 "${query}" 的弹幕
                </div>
            `;
            return;
        }
        
        // 创建结果容器
        const resultsContainer = document.createElement('div');
        resultsContainer.className = 'search-results p-2';
        
        // 结果计数
        const countElement = document.createElement('div');
        countElement.className = 'mb-3 text-muted';
        countElement.textContent = `共找到 ${results.length} 条包含 "${query}" 的弹幕`;
        
        // 结果列表
        for (const result of results) {
            const item = document.createElement('div');
            item.className = 'result-item mb-2 p-3 bg-light';
            
            // 格式化时间显示（秒转为 MM:SS 格式）
            const minutes = Math.floor(result.second / 60);
            const seconds = result.second % 60;
            const timeFormatted = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            const timeSpan = document.createElement('span');
            timeSpan.className = 'badge bg-primary me-2';
            timeSpan.textContent = timeFormatted;
            
            const textSpan = document.createElement('span');
            textSpan.innerHTML = result.text.replace(new RegExp(query, 'g'), `<span class="fw-bold text-danger">${query}</span>`);
            
            item.appendChild(timeSpan);
            item.appendChild(textSpan);
            resultsContainer.appendChild(item);
        }
        
        searchResultsDiv.appendChild(countElement);
        searchResultsDiv.appendChild(resultsContainer);
    }
});