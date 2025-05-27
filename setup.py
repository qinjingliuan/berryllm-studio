#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil

def main():
    """初始化BerryLLM Studio环境"""
    print("正在初始化BerryLLM Studio环境...")
    
    # 安装依赖
    print("正在安装依赖...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"安装依赖失败: {e}")
        return 1
    
    # 编译资源
    print("正在编译资源文件...")
    try:
        subprocess.run([sys.executable, "compile_resources.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"编译资源文件失败: {e}")
        print("警告: 资源文件编译失败，但程序仍然可以运行")
    
    # 编译翻译
    print("正在编译翻译文件...")
    try:
        subprocess.run([sys.executable, "compile_translations.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"编译翻译文件失败: {e}")
        print("警告: 翻译文件编译失败，但程序仍然可以运行")
    
    # 创建插件目录
    plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
    if not os.path.exists(plugins_dir):
        os.makedirs(plugins_dir)
        print(f"已创建插件目录: {plugins_dir}")
    
    print("\n初始化完成！")
    print("您可以通过运行以下命令启动BerryLLM Studio:")
    if sys.platform == 'win32':
        print("  run.bat")
    else:
        print("  ./run.sh")
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 