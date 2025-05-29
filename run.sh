#!/bin/bash
echo "正在启动 BerryLLM Studio..."

# 判断是否安装了虚拟环境
if [ -d ".venv" ]; then
    # 激活虚拟环境
    source .venv/bin/activate
    # 运行应用
    python main.py
else
    echo "未找到虚拟环境，正在创建..."
    python -m venv .venv
    source .venv/bin/activate
    echo "正在安装依赖..."
    pip install -r requirements.txt
    echo "正在编译资源文件..."
    python compile_resources.py
    # 运行应用
    python main.py
fi 