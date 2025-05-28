#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QMainWindow, QMenuBar, QMenu, 
                              QStatusBar, QMessageBox, QFileDialog,
                              QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QToolBar, QToolButton, QLabel, QSizePolicy, QStackedWidget,
                              QSplitter)
from PySide6.QtCore import Qt, Signal, Slot, QSettings, QSize, QFile, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QIcon, QKeySequence, QAction, QPixmap

from chat_view import ChatView
from llm_service import LlmService
from context_manager import ContextManager
from tool_manager import ToolManager
from theme_manager import ThemeManager, Theme
from settings_page import SettingsDialog
from session_manager import SessionManager


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
        self._session_manager = SessionManager(self)
        
        # 创建中央部件
        self._central_widget = QWidget(self)
        self.setCentralWidget(self._central_widget)
        
        # 创建主布局
        self._main_layout = QHBoxLayout(self._central_widget)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        
        # 创建分割器
        self._main_splitter = QSplitter(Qt.Horizontal)
        
        # 创建左侧设置菜单
        self._create_side_menu()
        
        # 创建会话管理菜单
        self._create_session_menu()
        
        # 创建聊天视图堆栈
        self._chat_stack = QStackedWidget(self)
        self._chat_views = {}  # 会话ID -> 聊天视图
        
        # 创建默认聊天视图
        self._create_default_chat_view()
        
        # 添加到分割器
        self._main_splitter.addWidget(self._chat_stack)
        
        # 设置分割器初始大小
        self._main_splitter.setSizes([200, 200, 600])
        
        # 添加到主布局
        self._main_layout.addWidget(self._main_splitter)
        
        # 创建动作
        self._create_actions()
        
        # 创建状态栏
        self._create_status_bar()
        
        # 连接信号和槽
        self._connect_signals()
        
        # 加载设置
        self._load_settings()
        
        # 显示欢迎消息
        self._show_welcome_message()
    
    def _create_side_menu(self):
        """创建左侧菜单"""
        # 创建左侧菜单容器
        self._side_menu = QWidget(self._central_widget)
        self._side_menu.setObjectName("side_menu")
        self._side_menu.setMinimumWidth(60)
        self._side_menu.setMaximumWidth(60)
        
        # 左侧菜单布局
        side_layout = QVBoxLayout(self._side_menu)
        side_layout.setContentsMargins(10, 10, 10, 10)
        side_layout.setSpacing(10)
        
        # 添加标题
        title_label = QLabel("", self._side_menu)
        title_label.setObjectName("side_menu_title")
        title_label.setAlignment(Qt.AlignCenter)
        side_layout.addWidget(title_label)
        
        # 添加分隔线
        separator = QWidget(self._side_menu)
        separator.setFixedHeight(1)
        separator.setObjectName("menu_separator")
        side_layout.addWidget(separator)
        
        # 保存聊天按钮 - 隐藏
        self._save_chat_button = QPushButton("", self._side_menu)
        self._save_chat_button.setObjectName("icon_button")
        self._save_chat_button.setToolTip(self.tr("保存聊天记录"))
        self._save_chat_button.setIcon(QIcon("resources/images/save.png"))
        self._save_chat_button.setIconSize(QSize(24, 24))
        self._save_chat_button.setVisible(False)  # 隐藏按钮
        side_layout.addWidget(self._save_chat_button)
        
        # 清除聊天按钮 - 隐藏
        self._clear_chat_button = QPushButton("", self._side_menu)
        self._clear_chat_button.setObjectName("icon_button")
        self._clear_chat_button.setToolTip(self.tr("清除聊天记录"))
        self._clear_chat_button.setIcon(QIcon("resources/images/clear.png"))
        self._clear_chat_button.setIconSize(QSize(24, 24))
        self._clear_chat_button.setVisible(False)  # 隐藏按钮
        side_layout.addWidget(self._clear_chat_button)
        
        # 添加弹性空间
        side_layout.addStretch(1)
        
        # 主题切换按钮 - 放在底部
        self._theme_button = QPushButton("", self._side_menu)
        self._theme_button.setObjectName("round_icon_button")  # 使用圆形按钮样式
        self._theme_button.setToolTip(self.tr("切换主题"))
        self._theme_button.setIconSize(QSize(24, 24))  # 调整图标大小
        self._theme_button.setFlat(True)  # 设置为平面按钮，移除边框
        side_layout.addWidget(self._theme_button)
        
        # 设置按钮 - 放在底部
        self._settings_button = QPushButton("", self._side_menu)
        self._settings_button.setObjectName("round_icon_button")  # 使用圆形按钮样式
        self._settings_button.setToolTip(self.tr("设置"))
        self._settings_button.setIconSize(QSize(24, 24))  # 调整图标大小
        self._settings_button.setFlat(True)  # 设置为平面按钮，移除边框
        side_layout.addWidget(self._settings_button)
        
        # 更新按钮图标
        self._update_theme_button_icon(ThemeManager.instance().current_theme())
        
        # 添加到分割器
        self._main_splitter.addWidget(self._side_menu)
    
    def _create_session_menu(self):
        """创建会话管理菜单"""
        # 创建会话管理容器
        self._session_menu = QWidget(self._central_widget)
        self._session_menu.setObjectName("session_menu")
        self._session_menu.setMinimumWidth(200)
        self._session_menu.setMaximumWidth(250)
        
        # 会话管理布局
        session_layout = QVBoxLayout(self._session_menu)
        session_layout.setContentsMargins(10, 10, 10, 10)
        session_layout.setSpacing(5)
        
        # 添加标题
        title_label = QLabel("BerryLLM Studio", self._session_menu)
        title_label.setObjectName("side_menu_title")
        title_label.setAlignment(Qt.AlignCenter)
        session_layout.addWidget(title_label)
        
        # 添加分隔线
        separator = QWidget(self._session_menu)
        separator.setFixedHeight(1)
        separator.setObjectName("menu_separator")
        session_layout.addWidget(separator)
        
        # 添加会话管理部件
        session_widget = self._session_manager.create_session_widget(self._session_menu)
        session_layout.addWidget(session_widget)
        
        # 添加到分割器
        self._main_splitter.addWidget(self._session_menu)
    
    def _create_default_chat_view(self):
        """创建默认聊天视图"""
        # 创建默认聊天视图
        default_chat_view = ChatView(self)
        self._chat_stack.addWidget(default_chat_view)
        
        # 显示欢迎消息
        default_chat_view.append_assistant_message(self.tr("欢迎使用BerryLLM Studio! 请输入您的问题。"))
    
    def _create_chat_view(self, session_id):
        """创建聊天视图
        
        Args:
            session_id: 会话ID
        """
        # 创建聊天视图
        chat_view = ChatView(self, session_id)
        chat_view.set_session_id(session_id)
        self._chat_stack.addWidget(chat_view)
        self._chat_views[session_id] = chat_view
        
        # 显示欢迎消息
        session_info = self._session_manager.get_session(session_id)
        if session_info:
            provider_name = session_info["provider_id"].capitalize()
            model_name = session_info["model_id"]
            chat_view.append_assistant_message(
                self.tr(f"欢迎使用 {provider_name} {model_name}! 请输入您的问题。")
            )
    
    def _create_actions(self):
        """创建动作"""
        # 连接按钮信号
        self._save_chat_button.clicked.connect(self._on_save_chat_action)
        self._clear_chat_button.clicked.connect(self._on_clear_chat_action)
        self._settings_button.clicked.connect(self._on_settings_action)
        self._theme_button.clicked.connect(self._on_toggle_theme_action)
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.statusBar().showMessage(self.tr("就绪"))
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 连接会话管理器信号
        self._session_manager.session_added.connect(self._on_session_added)
        self._session_manager.session_removed.connect(self._on_session_removed)
        self._session_manager.session_selected.connect(self._on_session_selected)
        
        # 连接主题管理器信号
        ThemeManager.instance().theme_changed.connect(self._on_theme_changed)
    
    def _update_theme_button_icon(self, theme):
        """更新主题按钮图标"""
        if theme == Theme.LIGHT:
            # 浅色主题 - 显示月亮图标
            self._theme_button.setIcon(QIcon("resources/images/moon.png"))
            self._theme_button.setToolTip(self.tr("切换到深色主题"))
            # 浅色主题下设置图标 - 使用图片
            self._settings_button.setText("")
            self._settings_button.setIcon(QIcon("resources/images/settings.png"))
        else:
            # 深色主题 - 显示太阳图标
            self._theme_button.setIcon(QIcon("resources/images/sun.png"))
            self._theme_button.setToolTip(self.tr("切换到浅色主题"))
            # 深色主题下设置图标
            self._settings_button.setText("")
            self._settings_button.setIcon(QIcon("resources/images/settings.png"))
        
        # 确保图标大小一致
        self._theme_button.setIconSize(QSize(24, 24))  # 调整图标大小
        self._settings_button.setIconSize(QSize(24, 24))  # 调整图标大小
    
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
        if dialog.exec() == SettingsDialog.Accepted:
            self._on_settings_applied()
    
    @Slot()
    def _on_toggle_theme_action(self):
        """切换主题动作处理"""
        theme_manager = ThemeManager.instance()
        current_theme = theme_manager.current_theme()
        
        # 直接切换主题，不使用缩放动画
        if current_theme == Theme.LIGHT:
            theme_manager.set_theme(Theme.DARK)
        else:
            theme_manager.set_theme(Theme.LIGHT)
        
        # 使用淡入淡出效果替代缩放
        self._theme_button.setEnabled(False)  # 暂时禁用按钮防止连续点击
        
        # 0.3秒后重新启用按钮
        QTimer.singleShot(300, lambda: self._theme_button.setEnabled(True))
    
    @Slot(Theme)
    def _on_theme_changed(self, theme):
        """主题变更处理"""
        self._update_theme_button_icon(theme)
    
    @Slot()
    def _on_save_chat_action(self):
        """保存聊天动作处理"""
        chat_view = self._get_current_chat_view()
        if not chat_view:
            return
        
        # 创建文件对话框
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilter(self.tr("文本文件 (*.txt);;HTML文件 (*.html)"))
        file_dialog.setDefaultSuffix("txt")
        
        if file_dialog.exec() == QFileDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            chat_view.save_chat(file_path)
    
    @Slot()
    def _on_clear_chat_action(self):
        """清除聊天动作处理"""
        chat_view = self._get_current_chat_view()
        if chat_view:
            chat_view.clear_chat()
    
    @Slot()
    def _on_settings_applied(self):
        """设置应用处理"""
        # 更新状态栏
        self.statusBar().showMessage(self.tr("设置已应用"), 3000)
    
    @Slot(str, str)
    def _on_session_added(self, session_id, name):
        """会话添加处理
        
        Args:
            session_id: 会话ID
            name: 会话名称
        """
        # 创建聊天视图
        self._create_chat_view(session_id)
        
        # 切换到新会话
        self._session_manager.set_current_session(session_id)
        
        # 更新状态栏
        self.statusBar().showMessage(self.tr(f"已添加会话: {name}"), 3000)
    
    @Slot(str)
    def _on_session_removed(self, session_id):
        """会话删除处理
        
        Args:
            session_id: 会话ID
        """
        # 删除聊天视图
        if session_id in self._chat_views:
            chat_view = self._chat_views[session_id]
            self._chat_stack.removeWidget(chat_view)
            del self._chat_views[session_id]
            
            # 如果删除的是当前会话,切换到默认视图
            if self._session_manager.get_current_session_id() == session_id:
                self._chat_stack.setCurrentIndex(0)
        
        # 更新状态栏
        self.statusBar().showMessage(self.tr("已删除会话"), 3000)
    
    @Slot(str)
    def _on_session_selected(self, session_id):
        """会话选择处理
        
        Args:
            session_id: 会话ID
        """
        # 切换到选中的会话视图
        if session_id in self._chat_views:
            self._chat_stack.setCurrentWidget(self._chat_views[session_id])
        else:
            # 如果视图不存在,创建新视图
            self._create_chat_view(session_id)
            self._chat_stack.setCurrentWidget(self._chat_views[session_id])
    
    def _get_current_chat_view(self):
        """获取当前聊天视图
        
        Returns:
            ChatView: 当前聊天视图
        """
        # 获取当前会话ID
        session_id = self._session_manager.get_current_session_id()
        
        if session_id and session_id in self._chat_views:
            return self._chat_views[session_id]
        else:
            # 如果没有当前会话,返回默认视图
            return self._chat_stack.widget(0)
    
    def _show_welcome_message(self):
        """显示欢迎消息"""
        # 更新状态栏
        self.statusBar().showMessage(self.tr("欢迎使用BerryLLM Studio"), 5000) 