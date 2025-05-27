#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys

def main():
    """编译Qt翻译文件"""
    print("正在编译翻译文件...")
    
    # 检查pyside6-lrelease命令是否可用
    try:
        # 在Windows上查找pyside6-lrelease.exe
        if sys.platform == 'win32':
            lrelease_cmd = 'pyside6-lrelease.exe'
        else:
            lrelease_cmd = 'pyside6-lrelease'
        
        # 尝试运行命令
        subprocess.run([lrelease_cmd, '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("错误: 找不到pyside6-lrelease命令。请确保PySide6已正确安装。")
        return 1
    
    # 获取翻译文件目录
    trans_dir = os.path.join(os.path.dirname(__file__), "resources", "trans")
    
    # 确保目录存在
    if not os.path.exists(trans_dir):
        print(f"错误: 翻译目录不存在: {trans_dir}")
        return 1
    
    # 查找所有.ts文件
    ts_files = [f for f in os.listdir(trans_dir) if f.endswith('.ts')]
    
    if not ts_files:
        print(f"错误: 在 {trans_dir} 中找不到.ts文件")
        return 1
    
    # 编译每个翻译文件
    success_count = 0
    for ts_file in ts_files:
        ts_path = os.path.join(trans_dir, ts_file)
        qm_path = os.path.join(trans_dir, ts_file.replace('.ts', '.qm'))
        
        try:
            result = subprocess.run(
                [lrelease_cmd, ts_path, '-qm', qm_path],
                check=True
            )
            if result.returncode == 0:
                print(f"已成功编译: {ts_file} -> {os.path.basename(qm_path)}")
                success_count += 1
            else:
                print(f"编译失败 {ts_file}, 返回代码: {result.returncode}")
        except subprocess.CalledProcessError as e:
            print(f"编译 {ts_file} 失败: {e}")
    
    print(f"编译完成: {success_count}/{len(ts_files)} 个文件成功")
    return 0 if success_count == len(ts_files) else 1

if __name__ == '__main__':
    sys.exit(main()) 