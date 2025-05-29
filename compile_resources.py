#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import shutil

def main():
    """编译Qt资源文件为Python模块"""
    print("正在编译资源文件...")
    
    # 查找pyside6-rcc命令
    rcc_cmd = None
    
    # 尝试在PATH中查找命令
    paths_to_check = [
        'pyside6-rcc',           # 默认PATH搜索
        'pyside6-rcc.exe',       # Windows
        os.path.expanduser('~/Library/Python/3.9/bin/pyside6-rcc'),  # macOS用户安装
        os.path.expanduser('~/.local/bin/pyside6-rcc'),              # Linux用户安装
        '/usr/local/bin/pyside6-rcc',                               # 系统安装
        '/opt/homebrew/bin/pyside6-rcc',                            # Homebrew安装
    ]
    
    # 如果在虚拟环境中，则优先检查虚拟环境中的命令
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        if sys.platform == 'win32':
            venv_rcc = os.path.join(venv_path, 'Scripts', 'pyside6-rcc.exe')
        else:
            venv_rcc = os.path.join(venv_path, 'bin', 'pyside6-rcc')
        paths_to_check.insert(0, venv_rcc)
    
    # 检查可能的路径
    for path in paths_to_check:
        if shutil.which(path):
            rcc_cmd = path
            print(f"找到pyside6-rcc: {rcc_cmd}")
            break
    
    # 如果找不到命令，尝试使用pip安装
    if not rcc_cmd:
        print("未找到pyside6-rcc命令，尝试安装PySide6...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'PySide6'], check=True)
            # 重新查找命令
            for path in paths_to_check:
                if shutil.which(path):
                    rcc_cmd = path
                    print(f"安装后找到pyside6-rcc: {rcc_cmd}")
                    break
        except subprocess.CalledProcessError:
            print("安装PySide6失败")
    
    # 如果仍然找不到命令，报错退出
    if not rcc_cmd:
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