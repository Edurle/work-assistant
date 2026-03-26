#!/bin/bash
# Work Assistant 安装脚本

echo "================================"
echo "Work Assistant 安装脚本"
echo "================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

echo "Python 版本: $(python3 --version)"

# 检查 pip
if ! python3 -m pip --version &> /dev/null; then
    echo "警告: pip 未安装，正在尝试安装..."
    sudo apt-get update && sudo apt-get install -y python3-pip
fi

# 安装依赖
echo ""
echo "正在安装依赖..."
python3 -m pip install -r requirements.txt

# Linux 特定依赖
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo ""
    echo "检测到 Linux 系统，安装额外依赖..."

    # notify2 需要 libgirepository
    if ! dpkg -l | grep -q libgirepository1.0-dev; then
        echo "安装 libgirepository1.0-dev (notify2 依赖)..."
        sudo apt-get install -y libgirepository1.0-dev
    fi

    # PyGObject
    python3 -m pip install PyGObject
fi

echo ""
echo "================================"
echo "安装完成!"
echo ""
echo "运行应用:"
echo "  cd /home/wang/work-assistant"
echo "  python3 src/main.py"
echo "================================"
