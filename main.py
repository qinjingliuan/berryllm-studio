#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTranslator, QLocale, QLibraryInfo, QFile, Qt
from PySide6.QtGui import QIcon

# 导入资源文件
try:
    import resources_rc
    print("成功导入资源文件")
except ImportError as e:
    print(f"警告: 资源文件未编译，将使用文件系统中的资源: {e}")
    print("请运行 python compile_resources.py 编译资源文件")

from main_window import MainWindow
from theme_manager import ThemeManager
from config_manager import ConfigManager


def main():
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("BerryLLM Studio")
    app.setOrganizationName("BerryLLM")
    app.setApplicationVersion("1.0.0")
    
    # 禁用使用系统应用程序菜单
    app.setAttribute(Qt.AA_DontUseNativeMenuBar, True)
    
    # 设置应用程序图标
    # Windows平台需要特殊处理
    if sys.platform.startswith('win'):
        # 首先尝试从资源文件加载
        resource_icon_path = ":/resources/images/berryllm_icon.png"
        file_icon_path = "resources/images/berryllm_icon.png"
        
        # 在Windows上优先使用.ico格式
        win_ico_path = "resources/images/berryllm_icon.ico"
        if os.path.exists(win_ico_path):
            app.setWindowIcon(QIcon(win_ico_path))
            print(f"Windows: 从文件系统加载.ico图标")
        elif QFile.exists(resource_icon_path):
            app.setWindowIcon(QIcon(resource_icon_path))
            print(f"Windows: 从资源文件加载图标")
        elif os.path.exists(file_icon_path):
            app.setWindowIcon(QIcon(file_icon_path))
            print(f"Windows: 从文件系统加载图标")
        
        # 设置进程ID，使Windows正确识别图标
        try:
            import ctypes
            app_id = "BerryLLM.Studio.App.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            print(f"已设置Windows应用程序ID: {app_id}")
        except:
            print("无法设置Windows应用程序ID")
    else:
        # 非Windows平台的处理方式
        resource_icon_path = ":/resources/images/berryllm_icon.png"
        file_icon_path = "resources/images/berryllm_icon.png"
        
        icon_set = False
        
        # 尝试从资源文件加载
        try:
            if QFile.exists(resource_icon_path):
                app.setWindowIcon(QIcon(resource_icon_path))
                print(f"从资源文件加载图标")
                icon_set = True
        except:
            pass
        
        # 如果资源文件加载失败，从文件系统加载
        if not icon_set and os.path.exists(file_icon_path):
            app.setWindowIcon(QIcon(file_icon_path))
            print(f"从文件系统加载图标")
    
    # 初始化配置管理器
    config_manager = ConfigManager.instance()
    print("配置管理器初始化完成")
    
    # 初始化主题管理器
    ThemeManager.instance()
    
    # 加载翻译
    qt_translator = QTranslator()
    app_translator = QTranslator()
    
    # 获取系统语言 - 使用配置中的语言设置
    locale = config_manager.get("general", "language", "zh_CN")
    print(f"使用语言: {locale}")
    
    # 加载Qt自带的翻译
    qt_trans_path = QLibraryInfo.path(QLibraryInfo.TranslationsPath)
    print(f"Qt翻译路径: {qt_trans_path}")
    if qt_translator.load("qt_" + locale, qt_trans_path):
        app.installTranslator(qt_translator)
        print(f"已加载Qt翻译: qt_{locale}")
    else:
        print(f"无法加载Qt翻译: qt_{locale}")
    
    # 尝试从不同位置加载应用程序翻译
    translation_paths = [
        os.path.join(os.path.dirname(__file__), "resources", "trans"),
        os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "resources", "trans"),
        os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "translations"),
        os.path.join(os.path.dirname(os.path.abspath(sys.argv[0]))),
        os.getcwd(),
        os.path.join(os.getcwd(), "resources", "trans")
    ]
    
    translation_loaded = False
    for path in translation_paths:
        print(f"尝试从 {path} 加载翻译")
        trans_file = f"berryllm_{locale}"
        if app_translator.load(trans_file, path):
            app.installTranslator(app_translator)
            translation_loaded = True
            print(f"翻译已从以下位置加载: {path}/{trans_file}")
            break
    
    if not translation_loaded:
        print(f"无法为 {locale} 加载翻译，尝试加载中文翻译")
        # 尝试加载中文翻译作为备选
        for path in translation_paths:
            if app_translator.load("berryllm_zh_CN", path):
                app.installTranslator(app_translator)
                print(f"已加载中文翻译: {path}/berryllm_zh_CN")
                translation_loaded = True
                break
        
        if not translation_loaded:
            print(f"警告: 无法加载任何翻译文件")
    
    # 创建主窗口
    main_window = MainWindow()
    main_window.show()
    
    # 运行应用程序
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 