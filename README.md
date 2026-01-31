# BiliHighlight Finder (B站直播回放高能时刻探测器)

该项目已弃，如有需要，请前往https://github.com/ltzu929/bili-danmaku-analyzer

这是一个桌面应用，旨在帮助B站UP主通过分析直播回放的弹幕数据，快速定位和剪辑“高能时刻”。

本应用使用 Electron 打包，将前端界面与后端分析服务整合为一个独立的 `.exe` 文件，无需安装 Node.js 环境即可运行。

## 技术栈

-   **应用框架:**
    -   Electron (用于构建跨平台桌面应用)
-   **前端:**
    -   React 18 + TypeScript
    -   Vite (构建工具)
    -   Tailwind CSS (样式)
    -   Recharts (数据可视化图表)
-   **后端:**
    -   Node.js + Express (内置的本地API服务)
    -   axios / xml-js (用于获取和解析B站弹幕)
-   **打包工具:**
    -   `electron-builder` (用于将应用打包成安装文件)

## 项目结构

```
。
├── electron/           # Electron 主进程脚本
│   └── main.js
├── release/            # 打包后生成的 .exe 文件会在这里
├── server/             # 后端 Node.js Express 服务
│   └── index.js
├── src/                # 前端 React 源码
│   ├── components/
│   ├── services/
│   ├── App.tsx
│   └── index.tsx
├── dist/               # 前端代码编译后的静态文件
├── index.html          # HTML 入口
├── package.json        # 项目配置和依赖
└── vite.config.ts      # Vite 配置文件
```

---

## 如何在你的电脑上运行和打包

直接下载安装release中的安装包
