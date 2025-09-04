#!/bin/bash

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================"
echo -e "    ArborVista 智能论文阅读助手"
echo -e "========================================${NC}"

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo -e "${RED}[错误] 未找到Python环境，请先安装Python${NC}"
    exit 1
fi

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo -e "${RED}[错误] 未找到Node.js环境，请先安装Node.js${NC}"
    exit 1
fi

# 检查必要文件
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}[错误] 未找到requirements.txt文件，请确保在ArborVista项目根目录下运行${NC}"
    exit 1
fi

if [ ! -f "app/app.py" ]; then
    echo -e "${RED}[错误] 未找到app/app.py文件，请确保在ArborVista项目根目录下运行${NC}"
    exit 1
fi

if [ ! -f "arborvistavue/package.json" ]; then
    echo -e "${RED}[错误] 未找到arborvistavue/package.json文件，请确保在ArborVista项目根目录下运行${NC}"
    exit 1
fi

# 显示环境信息
echo -e "${GREEN}[信息] 当前Python环境: $(which python)${NC}"
echo -e "${GREEN}[信息] 当前工作目录: $(pwd)${NC}"

# 安装Python依赖
echo -e "${YELLOW}[信息] 安装Python依赖...${NC}"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[警告] 依赖安装可能有问题，但继续启动...${NC}"
fi

# 安装mineru模块
echo -e "${YELLOW}[信息] 安装MinerU模块...${NC}"
pip install -e ./mineru
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[警告] MinerU模块安装可能有问题，但继续启动...${NC}"
fi

# 启动后端服务
echo -e "${YELLOW}[信息] 启动后端服务...${NC}"
python app/app.py &
BACKEND_PID=$!

# 等待后端启动
echo -e "${YELLOW}[信息] 等待后端服务启动...${NC}"
sleep 3

# 检查前端依赖
echo -e "${YELLOW}[信息] 检查前端依赖...${NC}"
cd arborvistavue
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}[信息] 安装前端依赖...${NC}"
    npm install
fi

# 启动前端服务
echo -e "${YELLOW}[信息] 启动前端服务...${NC}"
npm run serve &
FRONTEND_PID=$!

# 回到根目录
cd ..

echo ""
echo -e "${GREEN}========================================"
echo -e "项目启动完成！"
echo -e "后端服务: http://localhost:5000"
echo -e "前端服务: http://localhost:8080"
echo -e "注意: 服务仅限本地访问"
echo -e "========================================${NC}"
echo -e "${BLUE}按 Ctrl+C 停止所有服务${NC}"

# 等待用户中断
trap "echo -e '\n${YELLOW}[信息] 正在停止服务...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT

# 保持脚本运行
wait
