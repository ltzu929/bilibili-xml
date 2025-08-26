# BiliHighlight Finder (B站直播回放高能时刻探测器)

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
.
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

请确保你的电脑上已经安装了 [Node.js](https://nodejs.org/) (推荐 v18 或更高版本)。

### 第 1 步: 安装项目依赖

首先，在项目根目录下打开终端，运行一次 `npm install` 来安装所有需要的工具和库。

```bash
npm install
```

### 第 2 步: (可选) 开发模式

如果你想修改代码并实时查看效果，你需要同时运行前端的 Vite 开发服务器和 Electron 应用。

1.  **启动前端:** 在终端中运行 `npx vite`。
2.  **启动应用:** 打开 **另一个** 终端，运行 `npm start`。

> 注意：在开发模式下，应用可能会显示一片空白，直到你启动 Vite 服务器。

### 第 3 步: 打包成 .exe 文件

这是最重要的一步！当你完成了开发，想要生成可以分享给别人的 `.exe` 文件时，只需要在项目根目录下运行以下命令：

```bash
npm run package
```

这个命令会先使用 Vite 构建前端项目，然后用 `electron-builder` 将所有东西（包括Node.js运行时、后端服务、前端文件）打包成一个独立的安装程序。

完成后，你会在项目根目录下的 **`release`** 文件夹里找到生成的 `.exe` 文件。现在你可以把这个文件分享给任何人，或者在自己的电脑上一键启动了！
