# 🌳 ArborVista - 智能论文阅读助手

<div align="center">

![ArborVista Logo](https://img.shields.io/badge/ArborVista-智能文档处理平台-00C851?style=for-the-badge&logo=tree&logoColor=white)

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D.svg?style=flat-square&logo=vue.js&logoColor=white)](https://vuejs.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-red.svg?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-AGPL--3.0-orange.svg?style=flat-square)](LICENSE)

> 基于 MinerU API 的智能论文阅读助手，提供 PDF 文档解析、OCR 识别、表格提取等功能

[🚀 快速开始](#-快速开始) • [📖 使用指南](#-使用指南) • [🔧 开发指南](#-开发指南) • [❓ 常见问题](#-常见问题)

</div>

---

## ✨ 功能特性

<div align="center">

| 🎯 核心功能 | 📊 技术特性 | 🎨 用户体验 |
|------------|------------|------------|
| 📄 **智能PDF解析** | 🔍 **多语言OCR** | 🌐 **现代化界面** |
| 🖼️ **图片处理** | 📊 **表格自动提取** | 📱 **响应式设计** |
| ☁️ **云端处理** | 📝 **Markdown输出** | ⚡ **快速响应** |
| 📚 **文档管理** | 🔧 **API集成** | 🎯 **直观操作** |

</div>

### 🌟 主要亮点

- **🎯 一键上传** - 支持拖拽上传，批量处理多个文件
- **🔍 智能识别** - 自动识别文档结构，提取文本、图片、表格
- **🌍 多语言支持** - 支持中文、英文、韩文、日文等多种语言
- **📊 结构化输出** - 生成清晰的Markdown格式文档
- **☁️ 云端处理** - 基于MinerU API，无需本地复杂配置
- **📱 移动友好** - 响应式设计，支持各种设备访问

---

## 🚀 快速开始

### 📋 环境要求

<div align="center">

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| 🐍 **Python** | 3.10+ | 推荐使用conda管理环境 |
| 🟢 **Node.js** | 16+ | 用于前端开发 |
| 💾 **内存** | 4GB+ | 推荐8GB以上 |
| 🌐 **网络** | 稳定 | 需要访问MinerU API |

</div>

### 🔧 安装步骤

#### 1️⃣ 克隆项目
```bash
git clone <repository-url>
cd ArborVista
```

#### 2️⃣ 环境配置

**🐍 Python环境**
```bash
# 使用conda创建环境（推荐）
conda create -n arborvista python=3.10
conda activate arborvista

# 或使用venv
python -m venv arborvista
# Windows
arborvista\Scripts\activate
# Linux/Mac
source arborvista/bin/activate
```

**📦 安装依赖**
```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装前端依赖
cd arborvistavue
npm install
cd ..
```

#### 3️⃣ 配置API Token

**🔑 获取MinerU API Token**
1. 访问 [MinerU官网](https://mineru.net) 注册账号
2. 获取API Token

**⚙️ 设置环境变量**
```bash
# Windows PowerShell
$env:MINERU_API_TOKEN="your_token_here"

# Windows CMD
set MINERU_API_TOKEN=your_token_here

# Linux/Mac
export MINERU_API_TOKEN="your_token_here"

# 或创建.env文件
echo "MINERU_API_TOKEN=your_token_here" > .env
```

#### 4️⃣ 启动项目

**🚀 一键启动（推荐）**
```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

**🔧 手动启动**
```bash
# 终端1：启动后端服务
python app/app.py

# 终端2：启动前端服务
cd arborvistavue
npm run serve
```

### 🌐 访问应用

<div align="center">

| 服务 | 地址 | 说明 |
|------|------|------|
| 🌐 **前端界面** | http://127.0.0.1:8080 | 主要操作界面 |
| 🔧 **后端API** | http://127.0.0.1:5000 | API服务 |
| 📚 **API文档** | http://127.0.0.1:5000/api/docs | 接口文档 |

</div>

---

## 📖 使用指南

### 🎯 基本使用流程

<div align="center">

```mermaid
graph LR
    A[📁 上传文档] --> B[⚙️ 选择选项]
    B --> C[🔄 处理中]
    C --> D[📄 查看结果]
    D --> E[💾 下载保存]
```

</div>

#### 1️⃣ 上传文档
- **支持格式**：PDF、PNG、JPG、JPEG
- **文件大小**：最大100MB
- **上传方式**：拖拽上传或点击选择

#### 2️⃣ 选择处理选项
- **🔍 OCR识别** - 启用文字识别功能
- **📐 公式识别** - 启用数学公式识别
- **📊 表格识别** - 启用表格结构识别
- **🌍 语言选择** - 选择文档主要语言

#### 3️⃣ 查看结果
- **📄 Markdown预览** - 结构化文档展示
- **🖼️ 图片查看** - 提取的图片资源
- **📊 表格数据** - 识别的表格内容

### 🎨 界面预览

<div align="center">

| 功能页面 | 描述 | 特色 |
|----------|------|------|
| 🏠 **首页** | 文档上传和处理 | 拖拽上传、批量处理 |
| 📚 **文档库** | 文档管理和查看 | 分类管理、搜索过滤 |
| 👁️ **文档查看器** | 文档内容展示 | Markdown渲染、图片预览 |

</div>

---

## 🏗️ 项目结构

```
ArborVista/
├── 📁 app/                    # 后端 Flask 应用
│   ├── 📄 app.py             # 主应用文件
│   ├── 📄 config.py          # 配置文件
│   └── 📄 mineru_api.py      # MinerU API客户端
├── 📁 arborvistavue/         # 前端 Vue.js 应用
│   ├── 📁 src/               # 源代码
│   │   ├── 📁 components/    # 组件
│   │   ├── 📁 views/         # 页面
│   │   ├── 📁 router/        # 路由
│   │   └── 📁 config/        # 配置
│   ├── 📁 public/            # 静态资源
│   └── 📄 package.json       # 前端依赖
├── 📁 data/                  # 数据目录
│   ├── 📁 input/             # 输入文件
│   └── 📁 output/            # 输出结果
├── 📄 requirements.txt       # Python 依赖
├── 📄 .gitignore             # Git忽略规则
├── 📄 env.example            # 环境变量示例
├── 📄 start.bat              # Windows 启动脚本
└── 📄 README.md              # 项目说明
```

---

## ⚙️ 配置说明

### 🔧 API配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `MINERU_API_TOKEN` | MinerU API访问令牌 | 必需 |
| `API_BASE_URL` | API基础URL | MinerU官方API |
| `TIMEOUT` | 处理超时时间 | 5分钟 |

### 🎛️ 应用配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `MAX_FILE_SIZE` | 最大文件大小 | 100MB |
| `SUPPORTED_FORMATS` | 支持格式 | PDF, PNG, JPG, JPEG |
| `OUTPUT_FORMAT` | 输出格式 | Markdown + 图片 |

---

## 🔧 开发指南

### 🐍 后端开发

```bash
# 安装开发依赖
pip install -r requirements.txt

# 启动开发服务器
python app/app.py

```

### 🟢 前端开发

```bash
# 进入前端目录
cd arborvistavue

# 安装依赖
npm install

# 启动开发服务器
npm run serve

# 构建生产版本
npm run build
```

### 📡 API接口

#### 上传文件
```http
POST /api/upload
Content-Type: multipart/form-data

{
  "file": "文件内容",
  "is_ocr": true,
  "enable_formula": false
}
```

#### 获取文件列表
```http
GET /api/files
```

#### 获取文件内容
```http
GET /api/files/{file_id}/content
```

#### 获取图片
```http
GET /api/files/{file_id}/images/{image_path}
```

---

## ❓ 常见问题

<details>
<summary><strong>Q: 启动时提示 MINERU_API_TOKEN 未设置</strong></summary>

**A**: 确保已正确设置环境变量

```bash
# 检查环境变量
echo $MINERU_API_TOKEN

# 设置环境变量
export MINERU_API_TOKEN="your_token_here"
```

</details>

<details>
<summary><strong>Q: API连接失败</strong></summary>

**A**: 检查网络连接和Token有效性

```bash
# 运行API测试
python test_api.py

# 检查网络连接
ping mineru.net
```

</details>

<details>
<summary><strong>Q: 前端无法连接后端</strong></summary>

**A**: 检查后端服务是否正常启动，端口是否被占用

```bash
# 检查端口占用
netstat -ano | findstr :5000

# 重启服务
python app/app.py
```

</details>

<details>
<summary><strong>Q: 处理超时</strong></summary>

**A**: 检查文件大小和网络状况
- 确保文件小于100MB
- 检查网络连接稳定性
- 尝试重新上传

</details>

---

## 📊 性能优化

### 🌐 网络优化
- 使用稳定的网络连接
- 避免在网络高峰期处理大文件
- 考虑使用CDN加速

### 🚀 应用优化
- 定期清理临时文件
- 监控API使用配额
- 优化图片压缩

---

## 🤝 贡献指南

1. **Fork** 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 **Pull Request**

---

## 📄 许可证

本项目基于 MinerU 开源项目构建，遵循 [AGPL-3.0](LICENSE) 许可证。

---

## 🙏 致谢

- [MinerU](https://github.com/opendatalab/MinerU) - 核心PDF处理引擎
- [Vue.js](https://vuejs.org/) - 前端框架
- [Flask](https://flask.palletsprojects.com/) - 后端框架
- [Element Plus](https://element-plus.org/) - UI组件库

---

## 📞 联系我们

- 📧 **项目主页**: [GitHub Repository]
- 🐛 **问题反馈**: [Issues]
- 💬 **讨论交流**: [Discussions]

---

<div align="center">

### 🌟 如果这个项目对你有帮助，请给个 ⭐️ Star 支持一下！

**ArborVista** - 让文档处理更智能，让知识获取更高效

</div>
