@echo off
echo 正在准备打包BerryLLM Studio...

rem 设置虚拟环境
echo 正在激活虚拟环境...
call .venv\Scripts\activate.bat

rem 确保依赖库已安装
echo 正在安装依赖...
pip install -r requirements.txt

rem 确保资源文件已编译
echo 正在编译资源文件...
python compile_resources.py

rem 创建ICO图标文件
echo 正在转换图标...
python convert_icon.py

rem 使用spec文件打包
echo 正在使用spec文件打包应用程序...
pyinstaller berryllm.spec

rem 创建自解压安装包
echo 正在创建安装包...
cd dist
powershell Compress-Archive -Path "BerryLLM Studio" -DestinationPath "BerryLLM-Studio-Windows.zip" -Force
cd ..

echo 打包完成！
echo 安装包位置: dist\BerryLLM-Studio-Windows.zip
echo 应用程序位置: dist\BerryLLM Studio
pause 