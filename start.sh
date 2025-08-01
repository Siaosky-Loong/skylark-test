#!/bin/bash

# BytePlus ModelArk Chat Demo 启动脚本

echo "=== BytePlus ModelArk Chat Demo ==="
echo "正在启动应用..."

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖是否已安装
if [ ! -f "venv/pyvenv.cfg" ] || ! pip show flask > /dev/null 2>&1; then
    echo "安装依赖..."
    pip install -r requirements.txt
fi

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: .env文件不存在"
    echo "请复制.env.example为.env并设置您的API密钥:"
    echo "cp .env.example .env"
    echo "然后编辑.env文件设置ARK_API_KEY"
    echo ""
fi

echo "启动Flask应用..."
echo "应用将在 http://localhost:8000 启动"
echo "按 Ctrl+C 停止应用"
echo ""

python app.py