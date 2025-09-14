#!/bin/bash

# ArborVista Smart Paper Reader - Linux/Mac 启动脚本
# 作者: ArborVista Team
# 版本: 1.0.0

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo "========================================"
    print_message $CYAN "     ArborVista Smart Paper Reader"
    echo "========================================"
}

print_success() {
    print_message $GREEN "✅ $1"
}

print_warning() {
    print_message $YELLOW "⚠️  $1"
}

print_error() {
    print_message $RED "❌ $1"
}

print_info() {
    print_message $BLUE "ℹ️  $1"
}

# 切换到脚本所在目录
cd "$(dirname "$0")"

print_header

# 检查Python环境
print_info "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    print_error "Python3 未找到，请先安装Python 3.10+"
    exit 1
fi

# 检查Python版本
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_success "Python版本: $PYTHON_VERSION"

# 检查Node.js环境
print_info "检查Node.js环境..."
if ! command -v node &> /dev/null; then
    print_error "Node.js 未找到，请先安装Node.js 16+"
    exit 1
fi

NODE_VERSION=$(node --version)
print_success "Node.js版本: $NODE_VERSION"

# 检查npm
if ! command -v npm &> /dev/null; then
    print_error "npm 未找到，请先安装npm"
    exit 1
fi

# 检查必要文件
print_info "检查项目文件..."
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt 未找到，请在ArborVista根目录运行此脚本"
    exit 1
fi

if [ ! -f "app/app.py" ]; then
    print_error "app/app.py 未找到，请在ArborVista根目录运行此脚本"
    exit 1
fi

if [ ! -f "arborvistavue/package.json" ]; then
    print_error "arborvistavue/package.json 未找到，请在ArborVista根目录运行此脚本"
    exit 1
fi

print_success "项目文件检查完成"

# 检查环境变量
print_info "检查环境变量..."
if [ -z "$MINERU_API_TOKEN" ]; then
    print_warning "MINERU_API_TOKEN 未设置，请手动设置："
    echo "  export MINERU_API_TOKEN=\"your_token_here\""
    echo "  或创建 .env 文件："
    echo "  echo 'MINERU_API_TOKEN=your_token_here' > .env"
    echo ""
    read -p "是否继续启动？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "启动已取消"
        exit 0
    fi
else
    print_success "MINERU_API_TOKEN 已设置"
fi

# 安装Python依赖
print_info "安装Python依赖..."
if [ ! -d "venv" ]; then
    print_info "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 升级pip
python -m pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    print_error "Python依赖安装失败，请检查网络连接或Python环境"
    exit 1
fi

print_success "Python依赖安装完成"

# 启动后端服务
print_info "启动后端服务..."
python app/app.py &
BACKEND_PID=$!

# 等待后端启动
print_info "等待后端服务启动..."
sleep 3

# 检查后端是否启动成功
if ! curl -s http://127.0.0.1:5000 > /dev/null; then
    print_warning "后端服务可能未正常启动，继续启动前端..."
fi

# 检查前端依赖
print_info "检查前端依赖..."
cd arborvistavue

if [ ! -d "node_modules" ]; then
    print_info "安装前端依赖..."
    npm install
    if [ $? -ne 0 ]; then
        print_error "前端依赖安装失败，请检查网络连接或Node.js环境"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
fi

# 启动前端服务
print_info "启动前端服务..."
npm run serve &
FRONTEND_PID=$!

# 等待前端启动
sleep 5

# 获取本机IP地址
LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")

# 显示启动信息
echo ""
echo "========================================"
print_success "项目启动成功！"
echo ""
print_info "本地访问地址："
echo "  🌐 前端界面: http://127.0.0.1:8080"
echo "  🔧 后端API: http://127.0.0.1:5000"
echo ""
print_info "网络访问地址："
echo "  🌐 前端界面: http://$LOCAL_IP:8080"
echo "  🔧 后端API: http://$LOCAL_IP:5000"
echo ""
print_info "注意事项："
echo "  - MINERU_API_TOKEN 环境变量已设置"
echo "  - 需要稳定的网络连接访问MinerU API"
echo "  - 其他设备可通过网络地址访问"
echo "  - 确保防火墙允许端口5000和8080"
echo "========================================"
echo ""

# 创建清理函数
cleanup() {
    print_info "正在停止服务..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    print_success "服务已停止"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 等待用户输入
print_info "按 Ctrl+C 停止服务..."
wait
