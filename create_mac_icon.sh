#!/bin/bash

# 确保脚本在macOS平台运行
if [[ "$OSTYPE" != "darwin"* ]]; then
  echo "此脚本只能在 macOS 平台运行"
  exit 1
fi

echo "开始创建macOS图标文件..."

# 设置文件路径
PNG_ICON="resources/images/berryllm_icon.png"
ICON_SET="berryllm.iconset"
ICNS_FILE="resources/images/berryllm_icon.icns"

# 确保图标PNG存在
if [ ! -f "$PNG_ICON" ]; then
  echo "错误: 找不到图标文件 $PNG_ICON"
  exit 1
fi

# 创建临时图标集目录
mkdir -p "$ICON_SET"

# 创建不同尺寸的图标
echo "生成不同尺寸的图标..."
sips -z 16 16 "$PNG_ICON" --out "${ICON_SET}/icon_16x16.png"
sips -z 32 32 "$PNG_ICON" --out "${ICON_SET}/icon_16x16@2x.png"
sips -z 32 32 "$PNG_ICON" --out "${ICON_SET}/icon_32x32.png"
sips -z 64 64 "$PNG_ICON" --out "${ICON_SET}/icon_32x32@2x.png"
sips -z 128 128 "$PNG_ICON" --out "${ICON_SET}/icon_128x128.png"
sips -z 256 256 "$PNG_ICON" --out "${ICON_SET}/icon_128x128@2x.png"
sips -z 256 256 "$PNG_ICON" --out "${ICON_SET}/icon_256x256.png"
sips -z 512 512 "$PNG_ICON" --out "${ICON_SET}/icon_256x256@2x.png"
sips -z 512 512 "$PNG_ICON" --out "${ICON_SET}/icon_512x512.png"
sips -z 1024 1024 "$PNG_ICON" --out "${ICON_SET}/icon_512x512@2x.png"

# 创建.icns文件
echo "转换为 .icns 格式..."
mkdir -p "$(dirname "$ICNS_FILE")"
iconutil -c icns "$ICON_SET" -o "$ICNS_FILE"

# 清理临时文件
rm -rf "$ICON_SET"

echo "macOS图标文件创建完成: $ICNS_FILE" 