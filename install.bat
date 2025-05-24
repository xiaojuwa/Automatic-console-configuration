@echo off
echo 网络设备自动化助手 - 安装脚本
echo ================================

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境，请先安装Python 3.7或更高版本
    pause
    exit /b 1
)

echo Python环境检查通过

echo 正在安装依赖包...
pip install -r requirements.txt

if errorlevel 1 (
    echo 错误: 依赖包安装失败
    pause
    exit /b 1
)

echo 依赖包安装完成

echo 正在启动程序...
python main.py

pause
