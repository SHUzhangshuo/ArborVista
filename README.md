# 🌳 ArborVista - 智能论文阅读助手

> 基于 MinerU 的智能论文阅读助手，提供 PDF 文档解析、OCR 识别、表格提取等功能。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.x-green.svg)](https://vuejs.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-red.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-AGPL--3.0-orange.svg)](LICENSE)

## ✨ 功能特性

- 📄 **智能PDF解析** - 自动识别文档结构，提取文本、图片、表格
- 🔍 **OCR文字识别** - 支持多语言OCR，包括中文、英文、韩文、日文等
- 📊 **表格自动提取** - 智能识别表格结构，转换为Markdown格式
- 🖼️ **图片处理** - 支持PNG、JPG、JPEG格式图片处理
- 🚀 **GPU加速** - 智能检测GPU，自动选择最佳处理模式
- 🌐 **现代化界面** - 基于Vue.js的响应式Web界面
- 📝 **Markdown输出** - 结构化输出，便于阅读和编辑

## 🚀 快速开始

### 1. 环境要求

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.10+ | 推荐使用conda管理环境 |
| Node.js | 16+ | 用于前端开发 |
| CUDA | 12.1+ | 可选，用于GPU加速 |
| 内存 | 8GB+ | 推荐16GB以上 |

### 2. 克隆项目
```bash
git clone <repository-url>
cd ArborVista
```

### 3. 环境配置

#### 3.1 创建Python环境
```bash
# 使用conda创建环境
conda create -n arborvista python=3.10
conda activate arborvista

# 或使用venv
python -m venv arborvista
# Windows
arborvista\Scripts\activate
# Linux/Mac
source arborvista/bin/activate
```

#### 3.2 安装依赖
```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装前端依赖
cd arborvistavue
npm install
cd ..
```

### 4. 启动项目

#### 方式一：一键启动（推荐）
```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

#### 方式二：手动启动
```bash
# 终端1：启动后端服务
python app/app.py

# 终端2：启动前端服务
cd arborvistavue
npm run serve
```

### 5. 访问应用
- 🌐 **前端界面**: http://localhost:8080
- 🔧 **后端API**: http://localhost:5000
- 📚 **API文档**: http://localhost:5000/api/docs

## 📖 使用指南

### 基本使用流程

1. **上传文档**
   - 支持格式：PDF、PNG、JPG、JPEG
   - 最大文件大小：100MB
   - 拖拽上传或点击选择文件

2. **选择处理方式**
   - `auto` - 自动检测最佳处理方式
   - `txt` - 文本提取模式
   - `ocr` - OCR识别模式

3. **选择语言**
   - `ch` - 中文（默认）
   - `en` - 英文
   - `korean` - 韩文
   - `japan` - 日文
   - 其他支持的语言

4. **查看结果**
   - 处理完成后自动跳转到结果页面
   - 支持Markdown格式预览
   - 可下载处理结果

### 高级配置

#### GPU配置
```python
# 在 app/config.py 中配置
MINERU_CONFIG = {
    'device_mode': 'cuda:0',  # 或 'cpu'
    'virtual_vram': 7168,     # GPU内存限制(MB)
    'model_source': 'huggingface'  # 模型源
}
```

#### 环境变量
```bash
# 设置设备模式
export MINERU_DEVICE_MODE=cuda:0

# 设置GPU内存限制
export MINERU_VIRTUAL_VRAM_SIZE=7168

# 设置模型源
export MINERU_MODEL_SOURCE=huggingface
```

## 🏗️ 项目结构

```
ArborVista/
├── 📁 app/                    # 后端 Flask 应用
│   ├── 📄 app.py             # 主应用文件
│   └── 📄 config.py          # 配置文件
├── 📁 arborvistavue/         # 前端 Vue.js 应用
│   ├── 📁 src/               # 源代码
│   ├── 📁 public/            # 静态资源
│   └── 📄 package.json       # 前端依赖
├── 📁 mineru/                # MinerU 核心模块
│   ├── 📁 cli/               # 命令行接口
│   ├── 📁 backend/           # 后端处理
│   ├── 📁 model/             # 模型相关
│   └── 📁 utils/             # 工具函数
├── 📁 data/                  # 数据目录
│   ├── 📁 input/             # 输入文件
│   └── 📁 output/            # 输出结果
├── 📄 requirements.txt       # Python 依赖
├── 📄 start.bat              # Windows 启动脚本
├── 📄 start.sh               # Linux/Mac 启动脚本
└── 📄 README.md              # 项目说明
```

## ⚙️ 配置说明

### 设备模式配置
- **GPU模式**: 自动检测CUDA，使用GPU加速
- **CPU模式**: 当GPU不可用时自动切换
- **显存管理**: 智能分配GPU显存使用

### 模型配置
- **模型源**: HuggingFace、ModelScope、本地
- **语言支持**: 多语言OCR模型
- **模型下载**: 首次使用时自动下载

## 🔧 开发指南

### 后端开发
```bash
# 安装开发依赖
pip install -r requirements.txt

# 启动开发服务器
python app/app.py

# 运行测试
python -m pytest tests/
```

### 前端开发
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

### API接口

#### 上传文件
```http
POST /api/upload
Content-Type: multipart/form-data

{
  "file": "文件内容",
  "method": "auto",
  "language": "ch"
}
```

#### 获取文件列表
```http
GET /api/files
```

#### 下载结果
```http
GET /api/download/{file_id}
```

## 🐛 常见问题

### Q: 启动时提示 MinerU 模块未找到
**A**: 确保已正确安装所有依赖，并检查 Python 路径设置
```bash
# 重新安装依赖
pip install -r requirements.txt

# 检查模块导入
python -c "import mineru; print('MinerU模块正常')"
```

### Q: GPU 内存不足
**A**: 在配置中降低 `virtual_vram` 值，或使用 CPU 模式
```python
# 修改 app/config.py
MINERU_CONFIG = {
    'device_mode': 'cpu',  # 使用CPU模式
    'virtual_vram': 1024,  # 降低内存使用
}
```

### Q: 前端无法连接后端
**A**: 检查后端服务是否正常启动，端口是否被占用
```bash
# 检查端口占用
netstat -ano | findstr :5000

# 重启服务
python app/app.py
```

### Q: 模型下载失败
**A**: 检查网络连接，或使用国内镜像源
```bash
# 设置HuggingFace镜像
export HF_ENDPOINT=https://hf-mirror.com

# 或使用ModelScope
export MINERU_MODEL_SOURCE=modelscope
```

### Q: 处理速度慢
**A**: 确保使用GPU模式，并检查显存使用情况
```bash
# 检查GPU状态
nvidia-smi

# 检查CUDA可用性
python -c "import torch; print(torch.cuda.is_available())"
```

## 📊 性能优化

### GPU优化
- 使用CUDA 12.1+版本
- 确保GPU显存充足（推荐8GB+）
- 调整batch_size参数

### CPU优化
- 增加系统内存
- 使用多核处理
- 调整并发数

### 网络优化
- 使用国内镜像源
- 配置代理设置
- 预下载模型

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目基于 MinerU 开源项目构建，遵循 [AGPL-3.0](LICENSE) 许可证。

## 🙏 致谢

- [MinerU](https://github.com/opendatalab/MinerU) - 核心PDF处理引擎
- [Vue.js](https://vuejs.org/) - 前端框架
- [Flask](https://flask.palletsprojects.com/) - 后端框架
- [PyTorch](https://pytorch.org/) - 深度学习框架

## 📞 联系我们

- 项目主页: [GitHub Repository]
- 问题反馈: [Issues]
- 讨论交流: [Discussions]

---

<div align="center">
  <p>如果这个项目对你有帮助，请给个 ⭐️ Star 支持一下！</p>
</div>