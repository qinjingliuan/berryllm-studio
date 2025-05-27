#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QMainWindow, QMenuBar, QMenu, 
                              QStatusBar, QMessageBox, QFileDialog,
                              QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QToolBar, QToolButton, QLabel, QSizePolicy)
from PySide6.QtCore import Qt, Signal, Slot, QSettings, QSize, QFile
from PySide6.QtGui import QIcon, QKeySequence, QAction, QPixmap

from chat_view import ChatView
from llm_service import LlmService
from context_manager import ContextManager
from tool_manager import ToolManager
from theme_manager import ThemeManager, Theme
from settings_page import SettingsDialog


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self, parent=None):
        """初始化主窗口"""
        super().__init__(parent)
        
        self.setWindowTitle(self.tr("BerryLLM Studio"))
        self.resize(1024, 768)
        
        # 设置应用程序图标 - 修复图标路径问题
        icon_path = ":/resources/images/berryllm_icon.png"
        print(f"尝试加载图标: {icon_path}")
        
        # 检查资源文件是否存在
        if QFile.exists(icon_path):
            print(f"资源文件存在: {icon_path}")
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"警告: 资源文件不存在: {icon_path}")
            # 尝试从文件系统加载
            fs_icon_path = "resources/images/berryllm_icon.png"
            if QFile.exists(fs_icon_path):
                print(f"从文件系统加载图标: {fs_icon_path}")
                self.setWindowIcon(QIcon(fs_icon_path))
            else:
                print(f"错误: 无法找到图标文件")
        
        # 创建核心组件
        self._llm_service = LlmService(self)
        self._context_manager = ContextManager(self)
        self._tool_manager = ToolManager(self)
        
        # 创建中央部件
        self._central_widget = QWidget(self)
        self.setCentralWidget(self._central_widget)
        
        # 创建主布局
        self._main_layout = QHBoxLayout(self._central_widget)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        
        # 创建左侧菜单
        self._create_side_menu()
        
        # 创建聊天视图
        self._chat_view = ChatView(self)
        self._main_layout.addWidget(self._chat_view, 1)
        
        # 创建动作
        self._create_actions()
        
        # 创建状态栏
        self._create_status_bar()
        
        # 连接信号和槽
        self._connect_signals()
        
        # 加载设置
        self._load_settings()
        
        # 显示欢迎消息
        self._chat_view.append_assistant_message(self.tr("欢迎使用BerryLLM Studio! 请输入您的问题。"))
    
    def _create_side_menu(self):
        """创建左侧菜单"""
        # 创建左侧菜单容器
        self._side_menu = QWidget(self._central_widget)
        self._side_menu.setObjectName("side_menu")
        self._side_menu.setMinimumWidth(200)
        self._side_menu.setMaximumWidth(250)
        
        # 左侧菜单布局
        side_layout = QVBoxLayout(self._side_menu)
        side_layout.setContentsMargins(10, 10, 10, 10)
        side_layout.setSpacing(5)
        
        # 添加标题
        title_label = QLabel("BerryLLM Studio", self._side_menu)
        title_label.setObjectName("side_menu_title")
        title_label.setAlignment(Qt.AlignCenter)
        side_layout.addWidget(title_label)
        
        # 添加分隔线
        separator = QWidget(self._side_menu)
        separator.setFixedHeight(1)
        separator.setObjectName("menu_separator")
        side_layout.addWidget(separator)
        
        # 保存聊天按钮
        self._save_chat_button = QPushButton(self.tr("保存聊天记录"), self._side_menu)
        self._save_chat_button.setObjectName("side_menu_button")
        side_layout.addWidget(self._save_chat_button)
        
        # 清除聊天按钮
        self._clear_chat_button = QPushButton(self.tr("清除聊天记录"), self._side_menu)
        self._clear_chat_button.setObjectName("side_menu_button")
        side_layout.addWidget(self._clear_chat_button)
        
        # 设置按钮
        self._settings_button = QPushButton(self.tr("设置"), self._side_menu)
        self._settings_button.setObjectName("side_menu_button")
        side_layout.addWidget(self._settings_button)
        
        # 主题切换按钮
        self._theme_button = QPushButton("", self._side_menu)
        self._theme_button.setObjectName("theme_button")
        self._theme_button.setMinimumWidth(120)  # 设置最小宽度
        self._theme_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 水平扩展，垂直固定
        self._update_theme_button_text(ThemeManager.instance().current_theme())
        side_layout.addWidget(self._theme_button)
        
        # 关于按钮
        self._about_button = QPushButton(self.tr("关于"), self._side_menu)
        self._about_button.setObjectName("side_menu_button")
        side_layout.addWidget(self._about_button)
        
        # 添加弹性空间
        side_layout.addStretch(1)
        
        # 添加到主布局
        self._main_layout.addWidget(self._side_menu)
    
    def _create_actions(self):
        """创建动作"""
        # 连接按钮信号
        self._save_chat_button.clicked.connect(self._on_save_chat_action)
        self._clear_chat_button.clicked.connect(self._on_clear_chat_action)
        self._settings_button.clicked.connect(self._on_settings_action)
        self._theme_button.clicked.connect(self._on_toggle_theme_action)
        self._about_button.clicked.connect(self._on_about_action)
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.statusBar().showMessage(self.tr("就绪"))
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 连接聊天视图信号
        self._chat_view.user_message_sent.connect(self._send_message_with_context)
        
        # 连接LLM服务信号
        self._llm_service.response_started.connect(self._on_response_started)
        self._llm_service.response_chunk.connect(self._on_response_chunk)
        self._llm_service.response_finished.connect(self._on_response_finished)
        self._llm_service.error_occurred.connect(self._on_error_occurred)
        
        # 连接主题管理器信号
        ThemeManager.instance().theme_changed.connect(self._on_theme_changed)
    
    def _update_theme_button_text(self, theme):
        """更新主题按钮文本"""
        if theme == Theme.LIGHT:
            self._theme_button.setText(self.tr("浅色主题"))
        elif theme == Theme.DARK:
            self._theme_button.setText(self.tr("深色主题"))
        else:
            self._theme_button.setText(self.tr("自动主题"))
    
    def _load_settings(self):
        """加载设置"""
        settings = QSettings()
        
        # 加载窗口设置
        geometry = settings.value("MainWindow/Geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        state = settings.value("MainWindow/State")
        if state:
            self.restoreState(state)
    
    def _save_settings(self):
        """保存设置"""
        settings = QSettings()
        
        # 保存窗口设置
        settings.setValue("MainWindow/Geometry", self.saveGeometry())
        settings.setValue("MainWindow/State", self.saveState())
    
    def closeEvent(self, event):
        """关闭事件处理"""
        self._save_settings()
        super().closeEvent(event)
    
    @Slot()
    def _on_settings_action(self):
        """设置动作处理"""
        dialog = SettingsDialog(self)
        dialog.settings_applied.connect(self._on_settings_applied)
        dialog.exec()
    
    @Slot()
    def _on_toggle_theme_action(self):
        """切换主题动作处理"""
        ThemeManager.instance().toggle_theme()
    
    @Slot(Theme)
    def _on_theme_changed(self, theme):
        """主题变更处理"""
        # 更新主题按钮文本
        self._update_theme_button_text(theme)
        
        # 确保侧边栏宽度保持一致
        self._side_menu.setMinimumWidth(200)
        self._side_menu.setMaximumWidth(250)
        self._side_menu.updateGeometry()
        self._main_layout.update()
    
    @Slot()
    def _on_about_action(self):
        """关于动作处理"""
        QMessageBox.about(
            self,
            self.tr("关于 BerryLLM Studio"),
            self.tr(
                "BerryLLM Studio v1.0.0\n\n"
                "一个基于PySide6的LLM聊天界面\n\n"
                "Copyright © 2023"
            )
        )
    
    @Slot()
    def _on_save_chat_action(self):
        """保存聊天记录动作处理"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("保存聊天记录"),
            "",
            self.tr("HTML文件 (*.html);;文本文件 (*.txt)")
        )
        
        if not file_path:
            return
        
        try:
            if file_path.endswith(".html"):
                # 保存为HTML
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self._chat_view._chat_display.toHtml())
            else:
                # 保存为纯文本
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self._chat_view._chat_display.toPlainText())
            
            self.statusBar().showMessage(self.tr("聊天记录已保存"), 3000)
        
        except Exception as e:
            QMessageBox.critical(
                self,
                self.tr("错误"),
                self.tr("保存聊天记录失败: {}").format(str(e))
            )
    
    @Slot()
    def _on_clear_chat_action(self):
        """清除聊天记录动作处理"""
        reply = QMessageBox.question(
            self,
            self.tr("确认"),
            self.tr("确定要清除所有聊天记录吗?"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._chat_view.clear_chat()
            self._llm_service.clear_conversation_history()
            self.statusBar().showMessage(self.tr("聊天记录已清除"), 3000)
    
    @Slot()
    def _on_settings_applied(self):
        """设置应用处理"""
        # 重新加载设置
        settings = QSettings()
        
        # 应用主题设置
        theme_value = settings.value("UI/Theme", 0, int)
        theme = Theme(theme_value)
        ThemeManager.instance().apply_theme(theme)
        
        # 更新状态栏
        self.statusBar().showMessage(self.tr("设置已更新"), 3000)
    
    @Slot(str)
    def _send_message_with_context(self, message):
        """发送带上下文的消息
        
        Args:
            message: 用户消息
        """
        # 获取上下文
        context = self._context_manager.get_context()
        
        # 发送消息到LLM服务
        self._llm_service.send_message(message, context)
    
    @Slot()
    def _on_response_started(self):
        """响应开始处理"""
        self.statusBar().showMessage(self.tr("正在生成回复..."))
    
    @Slot(str)
    def _on_response_chunk(self, chunk):
        """响应块处理
        
        Args:
            chunk: 响应文本块
        """
        self._chat_view.append_streaming_content(chunk)
    
    @Slot()
    def _on_response_finished(self):
        """响应完成处理"""
        self.statusBar().showMessage(self.tr("回复完成"), 3000)
    
    @Slot(str)
    def _on_error_occurred(self, error):
        """错误处理
        
        Args:
            error: 错误信息
        """
        self.statusBar().showMessage(self.tr("错误: {}").format(error), 5000)
        self._chat_view.append_assistant_message(self.tr("发生错误: {}").format(error)) 