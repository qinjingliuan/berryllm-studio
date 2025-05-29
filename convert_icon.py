#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from PIL import Image

def convert_png_to_ico(png_path, ico_path, sizes=None):
    """
    将PNG图像转换为ICO格式
    
    Args:
        png_path: PNG图像路径
        ico_path: 输出ICO文件路径
        sizes: 图标尺寸列表，如果为None则使用默认尺寸
    """
    if sizes is None:
        sizes = [16, 24, 32, 48, 64, 128, 256]
    
    try:
        # 打开PNG图像
        img = Image.open(png_path)
        
        # 创建不同尺寸的图像
        icon_images = []
        for size in sizes:
            # 调整大小并保持纵横比
            resized_img = img.resize((size, size), Image.LANCZOS)
            icon_images.append(resized_img)
        
        # 保存为ICO文件
        icon_images[0].save(ico_path, format='ICO', sizes=[(img.size[0], img.size[1]) for img in icon_images])
        
        print(f"成功将 {png_path} 转换为 {ico_path}")
        return True
    except Exception as e:
        print(f"转换失败: {e}")
        return False

def main():
    """主函数"""
    # 图标路径
    png_path = "resources/images/berryllm_icon.png"
    ico_path = "resources/images/berryllm_icon.ico"
    
    # 确保目录存在
    os.makedirs(os.path.dirname(ico_path), exist_ok=True)
    
    # 转换图标
    if convert_png_to_ico(png_path, ico_path):
        print("图标转换成功!")
    else:
        print("图标转换失败!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 