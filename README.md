# 🌳 ArborVista - 智能论文阅读助手

<div align="center">

![ArborVista Logo](https://img.shields.io/badge/ArborVista-智能文档处理平台-00C851?style=for-the-badge&logo=tree&logoColor=white)

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D.svg?style=flat-square&logo=vue.js&logoColor=white)](https://vuejs.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-red.svg?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-AGPL--3.0-orange.svg?style=flat-square)](LICENSE)

> 基于 MinerU API 的智能论文阅读助手，提供 PDF 文档解析、OCR 识别、表格提取、RAG 智能问答等功能

[🚀 快速开始](#-快速开始) • [📖 使用指南](#-使用指南) • [🤖 RAG 智能问答](#-rag-智能问答) • [🔧 开发指南](#-开发指南) • [❓ 常见问题](#-常见问题)

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
| 🤖 **RAG智能问答** | 🧠 **向量检索** | 📝 **查询日志** |

</div>

### 🌟 主要亮点

- **🎯 一键上传** - 支持拖拽上传，批量处理多个文件
- **🔍 智能识别** - 自动识别文档结构，提取文本、图片、表格
- **🌍 多语言支持** - 支持中文、英文、韩文、日文等多种语言
- **📊 结构化输出** - 生成清晰的Markdown格式文档
- **☁️ 云端处理** - 基于MinerU API，无需本地复杂配置
- **💻 本地调用** - 支持本地MinerU vLLM后端，可完全离线使用
- **🤖 RAG智能问答** - 基于向量检索的文档问答系统，支持单篇论文和整个文档库查询
- **📝 查询日志** - 自动记录所有RAG查询，便于追踪和分析
- **📱 移动友好** - 响应式设计，支持各种设备访问

---

## 🚀 快速开始

### 📋 环境要求

<div align="center">

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| 🐍 **Python** | 3.10+ | 推荐使用conda管理环境 |
| 🟢 **Node.js** | 16+ | 用于前端开发 |
| 💾 **内存** | 4GB+ | 推荐8GB以上（RAG功能需要额外内存） |
| 🌐 **网络** | 稳定 | 需要访问MinerU API和OpenAI API（RAG功能） |

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

# 注意：RAG功能需要额外的依赖，如果安装时间过长，可以手动安装：
# pip install langchain langchain-openai langchain-community faiss-gpu sentence-transformers

# 安装前端依赖
cd arborvistavue
npm install
cd ..
```

#### 3️⃣ 配置环境变量

**📝 方式一：使用 .env 文件（推荐）**

1. 复制环境变量示例文件：
```bash
# Windows
copy env.example .env

# Linux/Mac
cp env.example .env
```

2. 编辑 `.env` 文件，填入实际值：

**方式A：使用在线API（默认）**
```bash
# MinerU API配置（在线模式必需）
MINERU_API_TOKEN=your-mineru-api-token-here
MINERU_USE_LOCAL=false

# RAG/LLM配置（RAG功能必需）
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_BASE_URL=http://your-api-server-url/v1/
OPENAI_MODEL=gpt-5
OPENAI_TEMPERATURE=0.7

# Flask配置（可选）
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

**方式B：使用本地调用（离线模式）**
```bash
# MinerU本地配置（本地模式必需）
MINERU_USE_LOCAL=true
MINERU_LOCAL_URL=http://127.0.0.1:30000

# RAG/LLM配置（RAG功能必需）
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_BASE_URL=http://your-api-server-url/v1/
OPENAI_MODEL=gpt-5
OPENAI_TEMPERATURE=0.7

# Flask配置（可选）
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

**⚙️ 方式二：临时设置环境变量（当前终端会话）**

**Windows PowerShell:**
```powershell
# 方式A：使用在线API（默认）
$env:MINERU_API_TOKEN="your_token_here"
$env:MINERU_USE_LOCAL="false"

# 方式B：使用本地调用
$env:MINERU_USE_LOCAL="true"
$env:MINERU_LOCAL_URL="http://127.0.0.1:30000"

# RAG功能配置
$env:OPENAI_API_KEY="your_openai_api_key_here"
$env:OPENAI_BASE_URL="http://your-api-server-url/v1/"
$env:OPENAI_MODEL="gpt-5"
$env:OPENAI_TEMPERATURE="0.7"
```

**Windows CMD:**
```cmd
REM 方式A：使用在线API（默认）
set MINERU_API_TOKEN=your_token_here
set MINERU_USE_LOCAL=false

REM 方式B：使用本地调用
set MINERU_USE_LOCAL=true
set MINERU_LOCAL_URL=http://127.0.0.1:30000

set OPENAI_API_KEY=your_openai_api_key_here
set OPENAI_BASE_URL=http://your-api-server-url/v1/
set OPENAI_MODEL=gpt-5
set OPENAI_TEMPERATURE=0.7
```

**Linux/Mac:**
```bash
# 方式A：使用在线API（默认）
export MINERU_API_TOKEN="your_token_here"
export MINERU_USE_LOCAL="false"

# 方式B：使用本地调用
export MINERU_USE_LOCAL="true"
export MINERU_LOCAL_URL="http://127.0.0.1:30000"

export OPENAI_API_KEY="your_openai_api_key_here"
export OPENAI_BASE_URL="http://your-api-server-url/v1/"
export OPENAI_MODEL="gpt-5"
export OPENAI_TEMPERATURE="0.7"
```

**🔧 方式三：永久设置环境变量（系统级）**

**Windows:**
1. 右键"此电脑" → 属性 → 高级系统设置
2. 点击"环境变量"
3. 在"用户变量"或"系统变量"中添加上述变量

**Linux/Mac:**
将上述 `export` 命令添加到 `~/.bashrc` 或 `~/.zshrc`：
```bash
echo 'export MINERU_API_TOKEN="your_token_here"' >> ~/.bashrc
echo 'export OPENAI_API_KEY="your_openai_api_key_here"' >> ~/.bashrc
echo 'export OPENAI_BASE_URL="http://your-api-server-url/v1/"' >> ~/.bashrc
source ~/.bashrc
```

**📋 必需的环境变量说明**

| 环境变量 | 说明 | 是否必需 | 默认值 | 获取方式 |
|---------|------|---------|--------|---------|
| `MINERU_API_TOKEN` | MinerU API访问令牌 | ⚠️ 在线模式必需 | 无 | 访问 [MinerU官网](https://mineru.net) 注册获取 |
| `MINERU_USE_LOCAL` | 是否使用本地调用 | ⚪ 可选 | `false` | 设置为 `true` 启用本地模式 |
| `MINERU_LOCAL_URL` | 本地vLLM后端URL | ⚠️ 本地模式必需 | `http://127.0.0.1:30000` | 本地MinerU vLLM服务地址 |
| `OPENAI_API_KEY` | OpenAI API密钥 | ✅ RAG功能必需 | 无 | 访问 OpenAI 或你的API服务提供商获取 |
| `OPENAI_BASE_URL` | LLM API基础URL | ✅ RAG功能必需 | 无 | 你的API服务地址，例如：`http://your-server/v1/` |
| `OPENAI_MODEL` | 模型名称 | ⚪ 可选 | `gpt-5` | 使用的LLM模型名称 |
| `OPENAI_TEMPERATURE` | 模型温度参数 | ⚪ 可选 | `0.7` | 范围：0.0-2.0 |
| `SECRET_KEY` | Flask密钥 | ⚪ 可选 | `dev-secret-key-change-in-production` | 用于生产环境，建议使用随机字符串 |

**💡 使用模式说明：**
- **在线模式**（默认）：需要设置 `MINERU_API_TOKEN`，`MINERU_USE_LOCAL=false` 或不设置
- **本地模式**：需要设置 `MINERU_USE_LOCAL=true` 和 `MINERU_LOCAL_URL`，需要先安装并启动本地MinerU vLLM服务

#### 4️⃣ 验证环境变量配置

在启动前，建议验证环境变量是否正确配置：

**使用 .env 文件（推荐方式）**
```bash
# 检查 .env 文件是否存在
# Windows
if exist .env (echo .env file exists) else (echo .env file not found)

# Linux/Mac
test -f .env && echo ".env file exists" || echo ".env file not found"
```

**验证环境变量**
```bash
# Windows PowerShell
if ($env:MINERU_API_TOKEN) { echo "✅ MINERU_API_TOKEN is set" } else { echo "❌ MINERU_API_TOKEN is not set" }
if ($env:OPENAI_API_KEY) { echo "✅ OPENAI_API_KEY is set" } else { echo "⚠️ OPENAI_API_KEY is not set (RAG功能需要)" }
if ($env:OPENAI_BASE_URL) { echo "✅ OPENAI_BASE_URL is set" } else { echo "⚠️ OPENAI_BASE_URL is not set (RAG功能需要)" }

# Linux/Mac
[ -n "$MINERU_API_TOKEN" ] && echo "✅ MINERU_API_TOKEN is set" || echo "❌ MINERU_API_TOKEN is not set"
[ -n "$OPENAI_API_KEY" ] && echo "✅ OPENAI_API_KEY is set" || echo "⚠️ OPENAI_API_KEY is not set (RAG功能需要)"
[ -n "$OPENAI_BASE_URL" ] && echo "✅ OPENAI_BASE_URL is set" || echo "⚠️ OPENAI_BASE_URL is not set (RAG功能需要)"
```

#### 5️⃣ 启动项目

**🚀 一键启动（推荐）**
```bash
# Windows
start.bat # 第一次需要运行两次，前端需要安装依赖
# 前端报错使用下面的语句修复
cd arborvistavue
npm run lint -- --fix

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
| 🤖 **AI问答** | RAG智能问答 | 单篇论文/整个文档库查询 |

</div>

---

## 🤖 RAG 智能问答

### 📋 功能说明

ArborVista 集成了基于 LangChain 和 FAISS 的 RAG（检索增强生成）系统，支持对文档进行智能问答。

### 🎯 主要特性

- **📚 文档库管理** - 支持多个文档库，每个文档库独立管理
- **🔍 向量检索** - 基于语义相似度的智能检索
- **📄 单篇论文查询** - 针对特定论文进行问答
- **📚 全文档库查询** - 跨论文检索和问答
- **📝 查询日志** - 自动记录所有查询，保存到 `data/logs/{library_id}_query.log`

### 🚀 使用流程

#### 1️⃣ 构建向量数据库

1. 进入文档库页面，选择要构建向量数据库的文档库
2. 点击"构建向量数据库"按钮
3. 系统会自动：
   - 加载文档库中的所有论文
   - 切分文档为小片段
   - 生成向量嵌入
   - 构建FAISS向量索引
   - 保存到 `data/vectorDatabase/{library_id}_faiss/`

#### 2️⃣ 开始问答

在文档查看器中：
1. 点击"AI问答"按钮
2. 选择查询模式：
   - **当前论文** - 仅查询当前打开的论文
   - **整个文档库** - 查询整个文档库中的所有论文
3. 输入问题，点击"提问"
4. 系统会返回基于文档内容的答案和相关来源片段

#### 3️⃣ 查看查询日志

所有RAG查询都会自动记录到日志文件：
- 位置：`data/logs/{library_id}_query.log`
- 格式：包含时间戳、级别、文档库ID、问题、完整答案等信息
- 日志轮转：单个文件最大10MB，保留30天，自动压缩

### 📊 日志格式示例

```
2025-11-05 14:13:43.453 | INFO     | library_d8fd90da | 📝 RAG Query
   📚 Library: library_d8fd90da
   📄 File ID: ubicomp25_FarSight.pdf-33b9be5a-899a-484e-b182-d482b47ce26f
   🔍 Scope: single_paper
   ❓ Question: lora感知的局限性
   💬 Answer:
基于提供的文档，LoRa 感知主要存在以下局限性：
- 带宽窄，分辨率受限
- 硬件诱发的相位/频率漂移
- 空间可分性弱（少天线）
...
```

### ⚙️ 技术细节

- **嵌入模型**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **向量数据库**: FAISS (Facebook AI Similarity Search)
- **LLM**: OpenAI GPT（通过 `OPENAI_API_KEY` 配置）
- **检索方式**: 语义相似度检索 + 元数据过滤

---

## 🏗️ 项目结构

```
ArborVista/
├── 📁 app/                    # 后端 Flask 应用
│   ├── 📄 app.py             # 主应用文件
│   ├── 📄 config.py          # 配置文件
│   └── 📄 mineru_api.py      # MinerU API客户端
├── 📁 agent/                  # RAG智能问答系统
│   ├── 📄 RAG.py             # RAG核心实现
│   ├── 📄 download_model.py  # 模型下载脚本
│   └── 📄 test_longchain.py  # LangChain测试
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
│   ├── 📁 output/            # 输出结果
│   ├── 📁 vectorDatabase/    # 向量数据库存储
│   │   └── 📁 models/        # 嵌入模型缓存
│   └── 📁 logs/              # 查询日志
│       └── 📄 {library_id}_query.log  # 各文档库的查询日志
├── 📄 requirements.txt       # Python 依赖
├── 📄 .gitignore             # Git忽略规则
├── 📄 env.example            # 环境变量示例
├── 📄 start.bat              # Windows 启动脚本
└── 📄 README.md              # 项目说明
```

---

## ⚙️ 配置说明

### 🔧 环境变量配置

| 环境变量 | 说明 | 是否必需 | 默认值 |
|---------|------|---------|--------|
| `MINERU_API_TOKEN` | MinerU API访问令牌 | ⚠️ 在线模式必需 | 无 |
| `MINERU_USE_LOCAL` | 是否使用本地调用 | ⚪ 可选 | `false` |
| `MINERU_LOCAL_URL` | 本地vLLM后端URL | ⚠️ 本地模式必需 | `http://127.0.0.1:30000` |
| `OPENAI_API_KEY` | OpenAI API密钥（RAG功能） | ✅ RAG功能必需 | 无 |
| `OPENAI_BASE_URL` | LLM API基础URL | ✅ RAG功能必需 | 无 |
| `OPENAI_MODEL` | 模型名称 | ⚪ 可选 | `gpt-5` |
| `OPENAI_TEMPERATURE` | 模型温度参数（0.0-2.0） | ⚪ 可选 | `0.7` |
| `SECRET_KEY` | Flask应用密钥 | ⚪ 可选 | `dev-secret-key-change-in-production` |
| `FLASK_ENV` | Flask环境模式 | ⚪ 可选 | `development` |

### 💻 本地调用配置

ArborVista 支持两种 MinerU 调用方式：

#### 🌐 在线API模式（默认）

使用 MinerU 云端API服务，无需本地安装：

```bash
# 设置环境变量
export MINERU_API_TOKEN="your-api-token"
export MINERU_USE_LOCAL="false"  # 或不设置，默认为false
```

**优点：**
- ✅ 无需本地安装 MinerU
- ✅ 无需配置本地服务
- ✅ 自动获得 MinerU 最新功能更新

**缺点：**
- ❌ 需要网络连接
- ❌ 需要 API Token
- ❌ 可能有使用配额限制

#### 💻 本地调用模式

使用本地 MinerU vLLM 后端，完全离线使用：

**1. 安装 MinerU（如果尚未安装）**

```bash
# 首先安装 uv（如果尚未安装）
pip install uv

# 使用 conda 创建环境（推荐）
conda create -n mineru python=3.12 -y
conda activate mineru

# 或使用 venv（可选）
python -m venv mineru_env
# Windows
mineru_env\Scripts\activate
# Linux/Mac
source mineru_env/bin/activate

# 安装 MinerU
uv pip install mineru

# 验证安装
mineru -v
```

**2. 启动本地 vLLM 服务**

```bash
# 启动 MinerU vLLM 后端（默认端口 30000）
# 具体启动命令请参考 MinerU 官方文档
```

**3. 配置环境变量**

```bash
# 设置本地模式
export MINERU_USE_LOCAL="true"
export MINERU_LOCAL_URL="http://127.0.0.1:30000"  # 根据实际服务地址调整
```

**优点：**
- ✅ 完全离线使用
- ✅ 无需 API Token
- ✅ 无使用配额限制
- ✅ 数据隐私更好

**缺点：**
- ❌ 需要本地安装 MinerU
- ❌ 需要配置和启动本地服务
- ❌ 需要本地计算资源（GPU推荐）

**💡 切换模式：**

只需修改 `MINERU_USE_LOCAL` 环境变量即可在两种模式间切换，无需修改代码。

### 🎛️ 应用配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `MAX_FILE_SIZE` | 最大文件大小 | 100MB |
| `SUPPORTED_FORMATS` | 支持格式 | PDF, PNG, JPG, JPEG |
| `OUTPUT_FORMAT` | 输出格式 | Markdown + 图片 |
| `LOGS_DIR` | 日志目录 | `data/logs` |
| `VECTOR_DB_DIR` | 向量数据库目录 | `data/vectorDatabase` |

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

#### RAG查询（单篇论文）
```http
POST /api/libraries/{library_id}/files/{file_id}/rag
Content-Type: application/json

{
  "question": "这篇论文的主要贡献是什么？",
  "query_mode": "single_paper"
}
```

#### RAG查询（整个文档库）
```http
POST /api/libraries/{library_id}/rag
Content-Type: application/json

{
  "question": "哪些论文提到了transformer？",
  "query_mode": "all_papers"
}
```

#### 构建向量数据库
```http
POST /api/libraries/{library_id}/build_vector_store
```

#### 获取向量数据库状态
```http
GET /api/libraries/{library_id}/vector_store_status
```

---

## ❓ 常见问题

<details>
<summary><strong>Q: 启动时提示 MINERU_API_TOKEN 未设置</strong></summary>

**A**: 有两种解决方案

**方案一：使用在线API模式（需要API Token）**

```bash
# 1. 复制示例文件
cp env.example .env

# 2. 编辑 .env 文件，填入实际的 MINERU_API_TOKEN
# MINERU_API_TOKEN=your-actual-token-here
# MINERU_USE_LOCAL=false
```

**方案二：使用本地调用模式（无需API Token）**

```bash
# 1. 确保已安装 MinerU
# 如果尚未安装，先安装 uv
pip install uv

# 创建环境并安装 MinerU
conda create -n mineru python=3.12 -y
conda activate mineru
uv pip install mineru

# 验证安装
mineru -v

# 2. 启动本地 vLLM 服务（参考 MinerU 文档）

# 3. 设置环境变量
export MINERU_USE_LOCAL="true"
export MINERU_LOCAL_URL="http://127.0.0.1:30000"
```

**检查环境变量是否设置成功**
```bash
# Windows PowerShell
echo $env:MINERU_USE_LOCAL
echo $env:MINERU_API_TOKEN  # 在线模式需要
echo $env:MINERU_LOCAL_URL  # 本地模式需要

# Windows CMD
echo %MINERU_USE_LOCAL%
echo %MINERU_API_TOKEN%
echo %MINERU_LOCAL_URL%

# Linux/Mac
echo $MINERU_USE_LOCAL
echo $MINERU_API_TOKEN
echo $MINERU_LOCAL_URL
```

</details>

<details>
<summary><strong>Q: 如何使用本地调用模式？</strong></summary>

**A**: 按照以下步骤配置本地调用：

**1. 安装 MinerU**

```bash
# 首先安装 uv（如果尚未安装）
pip install uv

# 创建 conda 环境（推荐）
conda create -n mineru python=3.12 -y
conda activate mineru

# 或使用 venv（可选）
python -m venv mineru_env
# Windows
mineru_env\Scripts\activate
# Linux/Mac
source mineru_env/bin/activate

# 安装 MinerU
uv pip install mineru

# 验证安装
mineru -v
```

**2. 启动本地 vLLM 服务**

根据 MinerU 官方文档启动 vLLM 后端服务（默认端口 30000）

**3. 配置环境变量**

```bash
# 方式一：使用 .env 文件
# 编辑 .env 文件，添加：
MINERU_USE_LOCAL=true
MINERU_LOCAL_URL=http://127.0.0.1:30000

# 方式二：临时设置
export MINERU_USE_LOCAL="true"
export MINERU_LOCAL_URL="http://127.0.0.1:30000"
```

**4. 验证配置**

启动应用后，查看控制台输出：
- ✅ 如果看到 "MinerU 本地模式已启用"，说明配置成功
- ❌ 如果看到 "MinerU command not found"，说明 MinerU 未正确安装

**常见问题：**
- **MinerU command not found**: 
  - 确保已安装 uv: `pip install uv`
  - 确保已安装 MinerU: `uv pip install mineru`
  - 确保在正确的 conda/venv 环境中
  - 验证安装: `mineru -v`
- **连接失败**: 检查本地 vLLM 服务是否已启动，端口是否正确
- **处理超时**: 检查本地服务资源是否充足（GPU/内存）

</details>

<details>
<summary><strong>Q: API连接失败 / 本地调用失败</strong></summary>

**A**: 根据使用的模式进行排查

**在线API模式：**
```bash
# 检查网络连接
ping mineru.net

# 验证 Token 有效性
# 访问 MinerU 官网检查 Token 状态

# 检查环境变量
echo $MINERU_API_TOKEN
echo $MINERU_USE_LOCAL  # 应该为 false 或不设置
```

**本地调用模式：**
```bash
# 1. 检查 MinerU 是否安装
# 如果使用 conda 环境
conda activate mineru
# 或如果使用 venv
# source mineru_env/bin/activate  # Linux/Mac
# mineru_env\Scripts\activate     # Windows

mineru -v

# 2. 检查本地服务是否运行
# 检查端口 30000 是否被占用
netstat -ano | findstr :30000  # Windows
lsof -i :30000  # Linux/Mac

# 3. 检查环境变量
echo $MINERU_USE_LOCAL  # 应该为 true
echo $MINERU_LOCAL_URL  # 应该指向正确的服务地址

# 4. 测试本地服务连接
curl http://127.0.0.1:30000/health  # 如果服务提供健康检查接口
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

<details>
<summary><strong>Q: RAG功能无法使用</strong></summary>

**A**: 检查以下配置

**1. 检查必需的环境变量**
```bash
# Windows PowerShell
echo $env:OPENAI_API_KEY
echo $env:OPENAI_BASE_URL

# Windows CMD
echo %OPENAI_API_KEY%
echo %OPENAI_BASE_URL%

# Linux/Mac
echo $OPENAI_API_KEY
echo $OPENAI_BASE_URL
```

如果未设置，请配置：
```bash
# 方式一：使用 .env 文件（推荐）
# 编辑 .env 文件，添加：
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=http://your-api-server-url/v1/

# 方式二：临时设置
export OPENAI_API_KEY="your-api-key-here"
export OPENAI_BASE_URL="http://your-api-server-url/v1/"
```

**2. 检查依赖安装**
```bash
# 手动安装RAG依赖
pip install langchain langchain-openai langchain-community faiss-gpu sentence-transformers
```

**3. 检查向量数据库**
- 确保已为文档库构建向量数据库
- 查看日志文件了解详细错误信息：`data/logs/{library_id}_query.log`

**4. 常见错误**
- `OPENAI_API_KEY 未设置`：需要设置环境变量或配置 .env 文件
- `OPENAI_BASE_URL 未设置`：需要设置 API 服务器地址
- `向量数据库不存在`：需要先构建向量数据库

</details>

<details>
<summary><strong>Q: 向量数据库构建失败</strong></summary>

**A**: 可能的原因和解决方案
- **内存不足**: 确保有足够的内存（推荐8GB+）
- **模型下载失败**: 检查网络连接，或手动运行 `python agent/download_model.py`
- **文档格式问题**: 确保文档已正确解析，包含有效文本内容

</details>

<details>
<summary><strong>Q: 查询日志在哪里查看？</strong></summary>

**A**: 查询日志自动保存到 `data/logs/` 目录
- 每个文档库有独立的日志文件：`{library_id}_query.log`
- 日志包含时间戳、问题、完整答案等信息
- 日志文件自动轮转（最大10MB），保留30天

</details>

<details>
<summary><strong>Q: 如何正确配置 .env 文件？</strong></summary>

**A**: 按照以下步骤配置：

**1. 创建 .env 文件**
```bash
# 复制示例文件
cp env.example .env
```

**2. 编辑 .env 文件**
使用文本编辑器打开 `.env` 文件，填入实际值：
```bash
# 必需配置
MINERU_API_TOKEN=your-actual-mineru-token-here
OPENAI_API_KEY=your-actual-openai-key-here
OPENAI_BASE_URL=http://your-actual-api-server/v1/

# 可选配置（有默认值）
OPENAI_MODEL=gpt-5
OPENAI_TEMPERATURE=0.7
SECRET_KEY=your-secret-key-here
```

**3. 验证配置**
```bash
# 确保 .env 文件在项目根目录
# 确保 .env 文件已添加到 .gitignore（不会提交到 Git）
```

**4. 注意事项**
- ⚠️ **不要**将 `.env` 文件提交到 Git（已在 .gitignore 中）
- ✅ 使用 `env.example` 作为模板
- ✅ 每个环境（开发/生产）使用不同的 `.env` 文件
- ✅ 定期更新 API Token，避免过期

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
- [LangChain](https://www.langchain.com/) - RAG框架
- [FAISS](https://github.com/facebookresearch/faiss) - 向量相似度搜索
- [Sentence Transformers](https://www.sbert.net/) - 文本嵌入模型
- [Loguru](https://github.com/Delgan/loguru) - 日志库

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
