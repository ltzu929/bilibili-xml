<script setup>
import { ref, computed, watchEffect, onMounted } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent, DataZoomComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

echarts.use([LineChart, TitleComponent, TooltipComponent, GridComponent, DataZoomComponent, CanvasRenderer])

const videoUrl = ref('')
const loading = ref(false)
const error = ref('')
const chartData = ref([])
const wordMap = ref({}) // 每分钟Top5热词
const totalDanmaku = ref(0)
const countedDanmaku = ref(0)

const isDark = ref(false)

function detectSystemTheme() {
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
}
function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}
// 自动检测系统主题
onMounted(() => {
  const saved = localStorage.getItem('theme')
  if (saved) {
    isDark.value = saved === 'dark'
  } else {
    isDark.value = detectSystemTheme()
  }
})

function formatTime(sec) {
  const h = String(Math.floor(sec / 3600)).padStart(2, '0')
  const m = String(Math.floor((sec % 3600) / 60)).padStart(2, '0')
  const s = String(sec % 60).padStart(2, '0')
  return `${h}:${m}:${s}`
}

// 弹幕内容归一化
function normalizeDanmaku(text) {
  if (/^哈+$/.test(text)) return '哈哈';
  if (/^2+3+$/.test(text)) return '233';
  if (/^晚安+.*$/.test(text)) return '晚安';
  if (/^oh+$/i.test(text)) return 'oh';
  return text;
}

const chartOption = computed(() => {
// 在暗色模式下使用更柔和的颜色
const areaColor = isDark.value ? 'rgba(102, 177, 255, 0.2)' : 'rgba(64, 158, 255, 0.18)';
const lineColor = isDark.value ? '#5a9ee0' : '#409EFF';
const textColor = isDark.value ? '#c9d1d9' : '#333';
const tooltipBgColor = isDark.value ? '#1c2128' : '#fff';
const tooltipBorderColor = isDark.value ? '#30363d' : '#e4e7ed';
const axisLineColor = isDark.value ? '#484f58' : '#dcdfe6';
const splitLineColor = isDark.value ? '#30363d' : '#e4e7ed';

return {
    title: { text: '弹幕热度（每分钟）', textStyle: { color: textColor } },
  tooltip: {
    trigger: 'axis',
    backgroundColor: tooltipBgColor,
    borderColor: tooltipBorderColor,
    textStyle: { color: textColor },
    formatter: (params) => {
      const p = params[0]
      const time = p.axisValue
      const count = p.data
      // 只显示Top5热词
      const words = wordMap.value[params[0].dataIndex] || []
      return `时间：${time}<br/>弹幕数：${count}` + (words.length ? `<br/>热词：${words.map(w => `<span style='color:#409EFF'>${w.word}</span>(${w.count})`).join('<br/>')}` : '')
    }
  },
  grid: { left: 60, right: 30, top: 60, bottom: 80 },
  xAxis: {
    type: 'category',
    data: chartData.value.map((d) => formatTime(d.time)),
    axisLabel: { rotate: 0, color: textColor },
    axisLine: { lineStyle: { color: axisLineColor } },
    splitLine: { show: false }
  },
  yAxis: {
    type: 'value',
    name: '弹幕数',
    nameTextStyle: { color: textColor },
    axisLabel: { color: textColor },
    axisLine: { lineStyle: { color: axisLineColor } },
    splitLine: { lineStyle: { color: splitLineColor } }
  },
  dataZoom: [
    { type: 'slider', show: true, xAxisIndex: 0, height: 24, bottom: 20, backgroundColor: tooltipBgColor, borderColor: tooltipBorderColor, fillerColor: 'rgba(102, 177, 255, 0.2)' },
    { type: 'inside', xAxisIndex: 0 }
  ],
  series: [
    {
      type: 'line',
      data: chartData.value.map((d) => d.count),
      areaStyle: { color: areaColor },
      smooth: true,
      symbol: 'none',
      lineStyle: { color: lineColor, width: 2 },
      itemStyle: { color: lineColor }
      }
    ]
  };
});

const chartOptionNoTitle = computed(() => {
  const opt = chartOption.value
  // 去掉 ECharts 内置标题
  return { ...opt, title: undefined }
})

async function analyzeDanmaku() {
  error.value = ''
  chartData.value = []
  wordMap.value = {}
  totalDanmaku.value = 0
  countedDanmaku.value = 0
  if (!videoUrl.value) {
    error.value = '请输入B站视频链接或BV号'
    return
  }
  loading.value = true
  try {
    // 请求本地 Flask 后端
    const res = await fetch(`http://127.0.0.1:5000/danmaku?url=${encodeURIComponent(videoUrl.value)}`)
    if (!res.ok) throw new Error('后端接口请求失败')
    const xmlText = await res.text()
    // 解析 XML，统计每分钟弹幕数和热词
    const parser = new DOMParser()
    const xmlDoc = parser.parseFromString(xmlText, 'text/xml')
    const danmakus = Array.from(xmlDoc.getElementsByTagName('d'))
    totalDanmaku.value = danmakus.length
    const heatMap = {}
    const wordStat = {}
    let validCount = 0
    danmakus.forEach((d) => {
      const p = d.getAttribute('p')
      if (!p) return
      const fields = p.split(',')
      if (fields.length < 1) return
      const appearTime = parseFloat(fields[0])
      if (isNaN(appearTime)) return
      // 以1分钟为统计单位
      const minute = Math.floor(appearTime / 60) * 60
      heatMap[minute] = (heatMap[minute] || 0) + 1
      // 归一化弹幕内容
      const text = normalizeDanmaku(d.textContent.trim())
      if (!wordStat[minute]) wordStat[minute] = []
      wordStat[minute].push(text)
      validCount++
    })
    countedDanmaku.value = validCount
    // 转为数组并排序
    const arr = Object.entries(heatMap).map(([time, count]) => ({ time: Number(time), count }))
    arr.sort((a, b) => a.time - b.time)
    chartData.value = arr
    // 统计每分钟Top5热词
    wordMap.value = arr.map(d => {
      const list = wordStat[d.time] || []
      const freq = {}
      list.forEach(t => { freq[t] = (freq[t] || 0) + 1 })
      // 排序取Top5
      return Object.entries(freq)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([word, count]) => ({ word, count }))
    })
  } catch (e) {
    error.value = '分析失败：' + (e.message || e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div :class="['app-bg', isDark ? 'dark' : 'light']">
    <div class="main-card">
      <div class="theme-toggle">
        <button class="theme-btn" @click="toggleTheme">
          <span v-if="isDark">🌙 暗色</span>
          <span v-else>☀️ 亮色</span>
        </button>
      </div>
      <h1 class="main-title">路灯 - B站弹幕分析工具 <span class="subtitle">（桌面版）</span></h1>
      <div class="input-group">
        <input v-model="videoUrl" :class="isDark ? 'input-dark' : ''" placeholder="请输入B站视频链接或BV号" />
        <button @click="analyzeDanmaku" :disabled="loading">{{ loading ? '分析中...' : '开始分析' }}</button>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <div class="stat-row" v-if="totalDanmaku > 0">
        <span class="stat-label">总弹幕数</span><span class="stat-value">{{ totalDanmaku }}</span>
        <span class="stat-label">已统计弹幕数</span><span class="stat-value">{{ countedDanmaku }}</span>
      </div>
      <div v-if="chartData.length > 0" class="chart-card">
        <div class="chart-title">弹幕热度（每分钟）</div>
        <div class="chart-container">
          <v-chart :option="chartOptionNoTitle" autoresize />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-bg {
  min-height: 100vh;
  width: 100vw;
  background: #f6f7fb;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s;
  margin: 0;
  padding: 0;
}
.app-bg.dark {
  background: #181c23;
}
.main-card {
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.08);
  padding: 48px 48px 36px 48px;
  max-width: 95%;
  width: 100%;
  margin: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: background 0.3s, box-shadow 0.3s;
}
.app-bg.dark .main-card {
  background: #23262e;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
}
.theme-toggle {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}
.theme-btn {
  background: none;
  border: none;
  color: #409EFF;
  font-size: 1.1rem;
  cursor: pointer;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 8px;
  transition: background 0.2s;
}
.theme-btn:hover {
  background: #eaf4ff;
}
.app-bg.dark .theme-btn {
  color: #6eb6ff;
}
.app-bg.dark .theme-btn:hover {
  background: #232f3e;
}
.main-title {
  font-size: 2.3rem;
  font-weight: 700;
  color: #222;
  margin-bottom: 22px;
  letter-spacing: 1px;
  transition: color 0.3s;
}
.app-bg.dark .main-title {
  color: #e6e6e6;
}
.subtitle {
  font-size: 1.1rem;
  color: #8a97b1;
  font-weight: 400;
  transition: color 0.3s;
}
.app-bg.dark .subtitle {
  color: #b3bedc;
}
.input-group {
  display: flex;
  gap: 12px;
  width: 100%;
  margin-bottom: 22px;
}
input {
  flex: 1;
  padding: 12px 18px;
  font-size: 17px;
  border: 1.5px solid #e3e8f0;
  border-radius: 10px;
  background: #f8fafc;
  transition: border 0.2s, box-shadow 0.2s, background 0.3s, color 0.3s;
  outline: none;
  box-shadow: 0 2px 8px rgba(64,158,255,0.03);
  color: #222;
}
input:focus {
  border-color: #409EFF;
  background: #fff;
  box-shadow: 0 2px 12px rgba(64,158,255,0.08);
}
.input-dark {
  background: #23262e;
  color: #e6e6e6;
  border: 1.5px solid #444;
}
input.input-dark:focus {
  background: #23262e;
  border-color: #6eb6ff;
  color: #fff;
}
button {
  padding: 0 32px;
  font-size: 17px;
  background: linear-gradient(90deg, #6eb6ff 0%, #409EFF 100%);
  color: #fff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(64,158,255,0.08);
  transition: background 0.2s, box-shadow 0.2s;
  height: 44px;
}
button:disabled {
  background: #b3d8ff;
  cursor: not-allowed;
  box-shadow: none;
}
.app-bg.dark button {
  background: linear-gradient(90deg, #3a6fae 0%, #6eb6ff 100%);
  color: #e6e6e6;
}
.error {
  color: #e74c3c;
  margin-bottom: 12px;
  font-size: 15px;
  width: 100%;
  text-align: left;
}
.stat-row {
  display: flex;
  gap: 24px;
  margin-bottom: 22px;
  width: 100%;
  justify-content: flex-start;
  align-items: center;
}
.stat-label {
  color: #8a97b1;
  font-size: 15px;
  margin-right: 4px;
  transition: color 0.3s;
}
.stat-value {
  color: #409EFF;
  font-size: 17px;
  font-weight: 600;
  margin-right: 18px;
  transition: color 0.3s;
}
.app-bg.dark .stat-label {
  color: #b3bedc;
}
.app-bg.dark .stat-value {
  color: #6eb6ff;
}
.chart-card {
  background: #f8fafc;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(64,158,255,0.06);
  padding: 28px 24px 22px 24px;
  width: 100%;
  margin-top: 10px;
    display: flex;
  flex-direction: column;
  align-items: stretch;
  transition: background 0.3s, box-shadow 0.3s;
}
.app-bg.dark .chart-card {
  background: #23262e;
  box-shadow: 0 2px 12px rgba(64,158,255,0.13);
}
.chart-title {
  font-size: 1.15rem;
  color: #222;
  font-weight: 600;
  margin-bottom: 12px;
  letter-spacing: 0.5px;
  transition: color 0.3s;
}
.app-bg.dark .chart-title {
  color: #e6e6e6;
}
.chart-container {
  width: 100%;
  height: 420px;
}
.chart-container :deep(.echarts) {
  width: 100% !important;
  height: 100% !important;
}
@media (max-width: 1100px) {
  .main-card {
    max-width: 98vw;
    padding: 18px 2vw 12px 2vw;
  }
  .chart-card {
    padding: 10px 1vw 8px 1vw;
  }
}
</style>
