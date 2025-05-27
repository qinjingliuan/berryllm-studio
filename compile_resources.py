#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys

def main():
    """编译Qt资源文件为Python模块"""
    print("正在编译资源文件...")
    
    # 检查pyside6-rcc命令是否可用
    try:
        # 在Windows上查找pyside6-rcc.exe
        if sys.platform == 'win32':
            rcc_cmd = 'pyside6-rcc.exe'
        else:
            rcc_cmd = 'pyside6-rcc'
        
        # 尝试运行命令
        subprocess.run([rcc_cmd, '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("错误: 找不到pyside6-rcc命令。请确保PySide6已正确安装。")
        return 1
    
    # 编译资源文件
    try:
        result = subprocess.run(
            [rcc_cmd, '-o', 'resources_rc.py', 'resources.qrc'],
            check=True
        )
        if result.returncode == 0:
            print("资源文件编译成功!")
        else:
            print(f"资源文件编译失败，返回代码: {result.returncode}")
            return 1
    except subprocess.CalledProcessError as e:
        print(f"资源文件编译失败: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 