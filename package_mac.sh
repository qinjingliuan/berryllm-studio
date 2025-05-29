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

# 如果资源文件存在，确保图标已转换
echo "正在转换图标..."
if [ -f "create_mac_icon.sh" ]; then
    bash create_mac_icon.sh
else
    python convert_icon.py
fi

# 使用PyInstaller打包应用
echo "正在打包应用程序..."
pyinstaller --name="BerryLLM Studio" \
            --windowed \
            --icon=resources/images/berryllm_icon.icns \
            --add-data="resources:resources" \
            --add-data="Data:Data" \
            --noupx \
            --clean \
            --onedir \
            main.py

# 创建DMG安装包
echo "正在创建DMG安装包..."
DMG_NAME="BerryLLM-Studio-macOS.dmg"
APP_NAME="BerryLLM Studio.app"
VOL_NAME="BerryLLM Studio"
SOURCE_DIR="dist/BerryLLM Studio"

# 确保源目录存在
if [ ! -d "$SOURCE_DIR" ]; then
    echo "错误: 找不到打包后的应用程序目录 $SOURCE_DIR"
    exit 1
fi

# 创建临时工作目录
DMG_TEMP="dist/dmg_temp"
mkdir -p "$DMG_TEMP"

# 创建.app包结构
mkdir -p "$DMG_TEMP/$APP_NAME/Contents/MacOS"
mkdir -p "$DMG_TEMP/$APP_NAME/Contents/Resources"

# 复制应用程序文件
cp -R "$SOURCE_DIR/"* "$DMG_TEMP/$APP_NAME/Contents/MacOS/"

# 复制图标
if [ -f "resources/images/berryllm_icon.icns" ]; then
    cp "resources/images/berryllm_icon.icns" "$DMG_TEMP/$APP_NAME/Contents/Resources/"
fi

# 创建Info.plist
cat > "$DMG_TEMP/$APP_NAME/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>BerryLLM Studio</string>
    <key>CFBundleExecutable</key>
    <string>BerryLLM Studio</string>
    <key>CFBundleIconFile</key>
    <string>berryllm_icon.icns</string>
    <key>CFBundleIdentifier</key>
    <string>cn.berryllm.studio</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>BerryLLM Studio</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# 创建DMG
echo "创建DMG镜像文件..."
if [ -f "dist/$DMG_NAME" ]; then
    rm "dist/$DMG_NAME"
fi

hdiutil create -volname "$VOL_NAME" \
               -srcfolder "$DMG_TEMP" \
               -ov -format UDZO \
               "dist/$DMG_NAME"

# 清理临时文件
rm -rf "$DMG_TEMP"

echo "打包完成！"
echo "安装包位置: dist/$DMG_NAME"
echo "应用程序位置: $SOURCE_DIR" 