@echo off
echo 正在启动 BerryLLM Studio...

rem 判断是否安装了虚拟环境
if exist ".venv" (
    rem 激活虚拟环境
    call .venv\Scripts\activate.bat
    rem 运行应用
    python main.py
) else (
    echo 未找到虚拟环境，正在创建...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo 正在安装依赖...
    pip install -r requirements.txt
    echo 正在编译资源文件...
    python compile_resources.py
    rem 运行应用
    python main.py
)
pause 