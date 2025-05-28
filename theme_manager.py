#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtCore import QObject, Signal, Slot, QSettings
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette
from enum import Enum
import os


class Theme(Enum):
    LIGHT = 0
    DARK = 1
    AUTO = 2


class ThemeManager(QObject):
    """主题管理器,负责应用和切换应用程序主题"""
    
    # 单例实例
    _instance = None
    
    # 信号
    theme_changed = Signal(Theme)
    
    @classmethod
    def instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance
    
    def __init__(self):
        """初始化主题管理器"""
        super().__init__()
        
        # 从设置中加载上次使用的主题
        settings = QSettings()
        saved_theme = settings.value("UI/Theme", Theme.AUTO.value, int)
        self._current_theme = Theme(saved_theme)
        
        # 应用保存的主题
        self.apply_theme(self._current_theme)
        
        # 确保主题设置立即生效
        QApplication.instance().processEvents()
    
    def apply_theme(self, theme):
        """应用指定主题"""
        style_sheet = ""
        
        if theme == Theme.LIGHT:
            style_sheet = self._load_style_sheet("light_theme.qss")
        elif theme == Theme.DARK:
            style_sheet = self._load_style_sheet("dark_theme.qss")
        elif theme == Theme.AUTO:
            # 根据系统主题自动选择
            if self._is_system_dark_theme():
                style_sheet = self._load_style_sheet("dark_theme.qss")
            else:
                style_sheet = self._load_style_sheet("light_theme.qss")
        
        if style_sheet:
            print(f"正在应用主题: {theme.name}, 样式表长度: {len(style_sheet)}")
            
            QApplication.instance().setStyleSheet(style_sheet)
            self._current_theme = theme
            
            # 保存当前主题设置
            settings = QSettings()
            settings.setValue("UI/Theme", theme.value)
            
            # 发送主题变更信号
            self.theme_changed.emit(theme)
        else:
            print(f"警告: 无法加载主题样式表: {theme.name}")
    
    def current_theme(self):
        """获取当前主题"""
        return self._current_theme
    
    def set_theme(self, theme):
        """设置主题
        
        Args:
            theme: 要设置的主题
        """
        if theme != self._current_theme:
            print(f"设置主题: {theme.name}")
            self.apply_theme(theme)
    
    @Slot()
    def toggle_theme(self):
        """切换主题"""
        if self._current_theme == Theme.LIGHT:
            new_theme = Theme.DARK
        else:
            new_theme = Theme.LIGHT
        print(f"切换主题: {self._current_theme.name} -> {new_theme.name}")
        self.apply_theme(new_theme)
    
    def _is_system_dark_theme(self):
        """检测系统是否使用深色主题"""
        # 使用QPalette检测系统颜色
        app = QApplication.instance()
        if app:
            palette = app.palette()
            bg_color = palette.color(QPalette.Window)
            # 如果背景色较暗，认为是深色主题
            return bg_color.lightness() < 128
        return False
    
    def _load_style_sheet(self, file_name):
        """加载样式表文件"""
        # 尝试从多个位置加载样式表
        paths = [
            os.path.join(os.path.dirname(__file__), "resources", "styles", file_name),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "styles", file_name),
            os.path.join(os.getcwd(), "resources", "styles", file_name)
        ]
        
        for path in paths:
            try:
                print(f"尝试加载样式表: {path}")
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
                    print(f"成功加载样式表: {path}, 长度: {len(content)}")
                    return content
            except (IOError, FileNotFoundError) as e:
                print(f"无法打开样式表文件: {path}, 错误: {e}")
                continue
        
        print(f"错误: 无法找到样式表文件: {file_name}")
        return "" 