@echo off
chcp 65001 >nul

REM 切换到脚本所在目录
cd /d "%~dp0"

echo ========================================
echo     ArborVista 智能论文阅读助手
echo ========================================

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python环境，请先安装Python
    pause
    exit /b 1
)

REM 检查是否在虚拟环境中
echo [信息] 当前Python环境: %CONDA_DEFAULT_ENV%
echo [信息] 当前工作目录: %CD%

REM 检查必要文件是否存在
if not exist "requirements.txt" (
    echo [错误] 未找到requirements.txt文件，请确保在ArborVista项目根目录下运行
    pause
    exit /b 1
)

if not exist "app\app.py" (
    echo [错误] 未找到app\app.py文件，请确保在ArborVista项目根目录下运行
    pause
    exit /b 1
)

if not exist "arborvistavue\package.json" (
    echo [错误] 未找到arborvistavue\package.json文件，请确保在ArborVista项目根目录下运行
    pause
    exit /b 1
)

REM 安装依赖
echo [信息] 安装Python依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [警告] 依赖安装可能有问题，但继续启动...
)

REM 安装mineru模块
echo [信息] 安装MinerU模块...
pip install -e ./mineru
if %errorlevel% neq 0 (
    echo [警告] MinerU模块安装可能有问题，但继续启动...
)

REM 启动后端服务
echo [信息] 启动后端服务...
start "ArborVista Backend" cmd /k "cd /d %~dp0 && python app\app.py"

REM 等待后端启动
echo [信息] 等待后端服务启动...
timeout /t 3 /nobreak >nul

REM 检查前端依赖
echo [信息] 检查前端依赖...
cd arborvistavue
if not exist "node_modules" (
    echo [信息] 安装前端依赖...
    npm install
)

REM 启动前端服务
echo [信息] 启动前端服务...
start "ArborVista Frontend" cmd /k "cd /d \"%~dp0arborvistavue\" & npm run serve"

echo.
echo ========================================
echo 项目启动完成！
echo 后端服务: http://localhost:5000
echo 前端服务: http://localhost:8080
echo 注意: 服务仅限本地访问
echo ========================================
echo 按任意键退出...
pause >nul