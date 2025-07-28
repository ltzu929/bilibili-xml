# B站弹幕分析工具 (桌面版)

一个功能强大的B站弹幕数据分析工具，能够通过视频链接或BV号获取弹幕数据，生成直观的可视化图表，并展示关键时间点的热词分析，帮助用户快速定位视频精彩内容。


## ✨ 功能特点

- **弹幕数据可视化**：生成弹幕密度时间分布折线图，直观展示视频热度变化
- **智能热词分析**：自动提取各时间段弹幕热词Top 5，鼠标悬停即可查看
- **视频精准跳转**：点击图表任意位置，自动在浏览器中打开对应时间点视频
- **响应式设计**：完美适配不同屏幕尺寸，支持全屏显示
- **桌面应用体验**：基于Electron开发，支持Windows系统一键安装使用

## 📋 项目结构

```
├── README.md               # 项目说明文档
├── package.json            # 项目依赖配置
├── danmaku_server.py       # 后端弹幕数据处理服务
├── frontend/               # 前端Vue应用
│   ├── package.json        # 前端依赖配置
│   ├── src/                # 源代码目录
│   │   ├── App.vue         # 主应用组件
│   │   ├── assets/         # 静态资源
│   │   └── main.js         # 入口文件
│   └── vite.config.js      # Vite构建配置
└── .gitignore              # Git忽略文件配置
```

## 🚀 快速开始

### 环境要求
- Node.js v14+ 和 npm v6+
- Python 3.8+ (用于后端服务)

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/yourusername/bilibili-danmaku-analyzer.git
   cd bilibili-danmaku-analyzer
   ```

2. **安装依赖**
   ```bash
   # 安装后端依赖
   pip install -r requirements.txt
   
   # 安装前端依赖
   cd frontend
   npm install
   cd ..
   ```

3. **运行开发环境**
   ```bash
   npm run dev
   ```
   这将同时启动前端Vite开发服务器和Electron窗口

## 💻 使用方法

1. 在应用界面输入框中粘贴B站视频链接或BV号
2. 点击"开始分析"按钮
3. 等待数据加载完成后，查看生成的弹幕密度图表
4. 鼠标悬停在图表上查看对应时间点的热词
5. 点击图表任意位置可跳转到视频对应时间点

## 📦 打包成exe文件

1. **安装打包工具**
   ```bash
   cd frontend
   npm install electron-builder --save-dev
   ```

2. **执行打包命令**
   ```bash
   npm run build
   ```

3. 打包完成后，可在`frontend/dist_electron`目录下找到生成的exe安装文件

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开Pull Request

## 📄 许可证

本项目采用MIT许可证 - 详情参见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Electron](https://www.electronjs.org/) - 跨平台桌面应用开发框架
- [Vue.js](https://vuejs.org/) - 前端JavaScript框架
- [ECharts](https://echarts.apache.org/) - 数据可视化库
- [B站API](https://api.bilibili.com/) - 提供弹幕数据支持
