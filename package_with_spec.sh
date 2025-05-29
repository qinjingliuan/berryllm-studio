#!/bin/bash

# 设置虚拟环境
echo "正在激活虚拟环境..."
source .venv/bin/activate

# 确保依赖库已安装
echo "正在安装依赖..."
pip install -r requirements.txt

# 确保资源文件已编译
echo "正在编译资源文件..."
python compile_resources.py

# 检测平台并执行对应的图标转换
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "检测到 macOS 平台，创建 .icns 图标文件..."
    bash create_mac_icon.sh
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "检测到 Windows 平台，创建 .ico 图标文件..."
    python convert_icon.py
else
    echo "未知平台: $OSTYPE"
    echo "仅创建 PNG 图标文件..."
    python convert_icon.py
fi

# 使用spec文件打包
echo "正在使用spec文件打包应用程序..."
pyinstaller berryllm.spec

# 根据平台创建安装包
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "正在创建 macOS DMG 安装包..."
    
    # 变量定义
    DMG_NAME="BerryLLM-Studio-macOS.dmg"
    APP_PATH="dist/BerryLLM Studio.app"
    VOL_NAME="BerryLLM Studio"
    
    # 确保应用程序存在
    if [ ! -d "$APP_PATH" ]; then
        echo "错误: 找不到打包后的应用程序 $APP_PATH"
        exit 1
    fi
    
    # 创建DMG
    echo "创建DMG镜像文件..."
    if [ -f "dist/$DMG_NAME" ]; then
        rm "dist/$DMG_NAME"
    fi
    
    # 创建临时文件夹
    DMG_TEMP="dist/dmg_temp"
    mkdir -p "$DMG_TEMP"
    cp -R "$APP_PATH" "$DMG_TEMP/"
    
    # 创建DMG文件
    hdiutil create -volname "$VOL_NAME" \
                  -srcfolder "$DMG_TEMP" \
                  -ov -format UDZO \
                  "dist/$DMG_NAME"
    
    # 清理临时文件
    rm -rf "$DMG_TEMP"
    
    echo "DMG 安装包已创建: dist/$DMG_NAME"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "正在创建 Windows ZIP 安装包..."
    cd dist
    zip -r "BerryLLM-Studio-Windows.zip" "BerryLLM Studio"
    cd ..
    echo "ZIP 安装包已创建: dist/BerryLLM-Studio-Windows.zip"
fi

echo "打包完成！" 