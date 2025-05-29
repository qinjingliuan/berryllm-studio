#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QMainWindow, QMenuBar, QMenu, 
                              QStatusBar, QMessageBox, QFileDialog,
                              QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QToolBar, QToolButton, QLabel, QSizePolicy, QStackedWidget,
                              QSplitter)
from PySide6.QtCore import Qt, Signal, Slot, QSettings, QSize, QFile, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QIcon, QKeySequence, QAction, QPixmap
import sys
import os

from chat_view import ChatView
from llm_service import LlmService
from context_manager import ContextManager
from tool_manager import ToolManager
from theme_manager import ThemeManager, Theme
from settings_page import SettingsDialog
from session_manager import SessionManager
from config_manager import ConfigManager


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self, parent=None):
        """初始化主窗口"""
        super().__init__(parent)
        
        self.setWindowTitle(self.tr("BerryLLM Studio"))
        self.resize(1000, 600)  # 调整默认尺寸
        self.setMinimumSize(1000, 600)  # 设置最小尺寸
        
        # 设置应用程序图标
        # Windows平台需要特殊处理
        if sys.platform.startswith('win'):
            # 在Windows上优先使用.ico格式
            win_ico_path = "resources/images/berryllm_icon.ico"
            resource_ico_path = ":/resources/images/berryllm_icon.ico"
            
            if QFile.exists(resource_ico_path):
                self.setWindowIcon(QIcon(resource_ico_path))
                print(f"Windows: 主窗口从资源文件加载.ico图标")
            elif os.path.exists(win_ico_path):
                self.setWindowIcon(QIcon(win_ico_path))
                print(f"Windows: 主窗口从文件系统加载.ico图标")
            else:
                # 如果.ico不存在，尝试使用.png
                resource_icon_path = ":/resources/images/berryllm_icon.png"
                file_icon_path = "resources/images/berryllm_icon.png"
                
                if QFile.exists(resource_icon_path):
                    self.setWindowIcon(QIcon(resource_icon_path))
                    print(f"Windows: 主窗口从资源文件加载.png图标")
                elif os.path.exists(file_icon_path):
                    self.setWindowIcon(QIcon(file_icon_path))
                    print(f"Windows: 主窗口从文件系统加载.png图标")
        else:
            # 非Windows平台的处理方式
            # 首先尝试从资源文件加载
            resource_icon_path = ":/resources/images/berryllm_icon.png"
            file_icon_path = "resources/images/berryllm_icon.png"
            
            if QFile.exists(resource_icon_path):
                self.setWindowIcon(QIcon(resource_icon_path))
                print(f"从资源文件加载图标")
            elif QFile.exists(file_icon_path):
                self.setWindowIcon(QIcon(file_icon_path))
                print(f"从文件系统加载图标")
            else:
                print(f"警告: 无法找到图标文件")
        
        # 初始化配置管理器
        self._config_manager = ConfigManager.instance()
        
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
        
        # 所有部件先创建好
        # 创建左侧设置菜单
        self._create_side_menu()
        
        # 创建会话管理菜单
        self._create_session_menu()
        
        # 创建聊天视图堆栈
        self._chat_stack = QStackedWidget(self)
        self._chat_views = {}  # 会话ID -> 聊天视图
        
        # 创建默认聊天视图
        self._create_default_chat_view()
        
        # 按顺序添加到分割器，确保顺序正确
        # 1. 左侧菜单
        self._main_splitter.addWidget(self._side_menu)
        # 2. 会话管理菜单
        self._main_splitter.addWidget(self._session_menu)
        # 3. 聊天视图
        self._main_splitter.addWidget(self._chat_stack)
        
        # 设置分割器初始大小
        self._main_splitter.setSizes([60, 200, 740])  # 调整分割器大小比例
        
        # 添加到主布局
        self._main_layout.addWidget(self._main_splitter)
        
        # 创建动作
        self._create_actions()
        
        # 连接信号和槽
        self._connect_signals()
        
        # 加载设置
        self._load_settings()
        
        # 显示欢迎消息
        self._show_welcome_message()
        
        # 默认选中助手按钮
        self._assistant_button.setChecked(True)
        self._settings_button.setChecked(False)
        
        # 更新按钮图标状态
        self._update_button_icons()
    
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
        side_layout.setAlignment(Qt.AlignHCenter)  # 设置水平居中
        
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
        
        # 助手按钮 - 添加在顶部
        self._assistant_button = QPushButton("", self._side_menu)
        self._assistant_button.setObjectName("round_icon_button")
        self._assistant_button.setToolTip(self.tr("助手"))
        # 默认使用dark图标，选中状态由_update_button_icons管理
        # 修改为使用资源文件中的图标
        self._assistant_button.setIcon(QIcon(":/resources/images/AI_dark.png"))
        self._assistant_button.setIconSize(QSize(24, 24))
        self._assistant_button.setFlat(True)
        self._assistant_button.setCheckable(True)  # 设置为可选择
        side_layout.addWidget(self._assistant_button)
        
        # 保存聊天按钮 - 隐藏
        self._save_chat_button = QPushButton("", self._side_menu)
        self._save_chat_button.setObjectName("icon_button")
        self._save_chat_button.setToolTip(self.tr("保存聊天记录"))
        # 修改为使用资源文件中的图标
        self._save_chat_button.setIcon(QIcon(":/resources/images/save.png"))
        self._save_chat_button.setIconSize(QSize(24, 24))
        self._save_chat_button.setVisible(False)  # 隐藏按钮
        side_layout.addWidget(self._save_chat_button)
        
        # 清除聊天按钮 - 隐藏
        self._clear_chat_button = QPushButton("", self._side_menu)
        self._clear_chat_button.setObjectName("icon_button")
        self._clear_chat_button.setToolTip(self.tr("清除聊天记录"))
        # 修改为使用资源文件中的图标
        self._clear_chat_button.setIcon(QIcon(":/resources/images/clear.png"))
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
        # 默认使用dark图标，选中状态由_update_button_icons管理
        # 修改为使用资源文件中的图标
        self._settings_button.setIcon(QIcon(":/resources/images/settings_dark.png"))
        self._settings_button.setIconSize(QSize(24, 24))  # 调整图标大小
        self._settings_button.setFlat(True)  # 设置为平面按钮，移除边框
        self._settings_button.setCheckable(True)  # 设置为可选择
        side_layout.addWidget(self._settings_button)
        
        # 更新主题相关按钮图标
        self._update_theme_button_icon(ThemeManager.instance().current_theme())
    
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
        
        # 添加分隔线
        separator = QWidget(self._session_menu)
        separator.setFixedHeight(1)
        separator.setObjectName("menu_separator")
        session_layout.addWidget(separator)
        
        # 添加会话管理部件
        session_widget = self._session_manager.create_session_widget(self._session_menu)
        session_layout.addWidget(session_widget)
    
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
        self._assistant_button.clicked.connect(self._on_assistant_action)
    
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
            # 修改为使用资源文件中的图标
            self._theme_button.setIcon(QIcon(":/resources/images/moon.png"))
            self._theme_button.setToolTip(self.tr("切换到深色主题"))
        else:
            # 深色主题 - 显示太阳图标
            # 修改为使用资源文件中的图标
            self._theme_button.setIcon(QIcon(":/resources/images/sun.png"))
            self._theme_button.setToolTip(self.tr("切换到浅色主题"))
        
        # 确保图标大小一致
        self._theme_button.setIconSize(QSize(24, 24))  # 调整图标大小
    
    def _load_settings(self):
        """加载设置"""
        # 加载QSettings中的窗口设置
        settings = QSettings()
        
        # 加载窗口设置
        geometry = settings.value("MainWindow/Geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        state = settings.value("MainWindow/State")
        if state:
            self.restoreState(state)
            
        # 从配置管理器加载主题设置
        theme_name = self._config_manager.get("display", "theme", "light")
        if theme_name == "dark":
            ThemeManager.instance().set_theme(Theme.DARK)
        else:
            ThemeManager.instance().set_theme(Theme.LIGHT)
    
    def _save_settings(self):
        """保存设置"""
        # 保存窗口设置到QSettings
        settings = QSettings()
        settings.setValue("MainWindow/Geometry", self.saveGeometry())
        settings.setValue("MainWindow/State", self.saveState())
        
        # 保存主题设置到配置管理器
        current_theme = ThemeManager.instance().current_theme()
        theme_name = "dark" if current_theme == Theme.DARK else "light"
        self._config_manager.set("display", "theme", theme_name)
        self._config_manager.save()
    
    def closeEvent(self, event):
        """关闭事件处理"""
        self._save_settings()
        super().closeEvent(event)
    
    @Slot()
    def _on_settings_action(self):
        """设置动作处理"""
        # 如果设置视图已经存在并显示，则不需要操作
        if hasattr(self, '_settings_widget') and self._settings_widget.isVisible():
            return
        
        # 设置按钮选中状态
        self._settings_button.setChecked(True)
        self._assistant_button.setChecked(False)
        
        # 更新按钮图标
        self._update_button_icons()
            
        # 隐藏会话管理和聊天界面
        if self._session_menu.isVisible():
            self._session_menu.hide()
        
        # 获取当前聊天视图
        current_chat = self._get_current_chat_view()
        if current_chat:
            current_chat.hide()
        
        # 创建设置视图（如果不存在）
        if not hasattr(self, '_settings_widget'):
            self._settings_widget = QWidget()
            settings_layout = QVBoxLayout(self._settings_widget)
            settings_layout.setContentsMargins(0, 0, 0, 0)
            settings_layout.setSpacing(0)  # 移除内部间距
            
            self._settings_dialog = SettingsDialog(self)
            self._settings_dialog.setWindowFlags(Qt.Widget)  # 设置为普通Widget
            
            # 连接设置应用信号
            self._settings_dialog.settings_applied.connect(self._on_settings_applied)
            
            settings_layout.addWidget(self._settings_dialog)
        
        # 确保垂直菜单在正确的位置（第一位）
        if self._main_splitter.indexOf(self._side_menu) != 0:
            self._main_splitter.insertWidget(0, self._side_menu)
        
        # 确保设置视图在第二位置
        if self._main_splitter.indexOf(self._settings_widget) != 1:
            if self._main_splitter.indexOf(self._settings_widget) != -1:
                # 如果设置视图已在分割器中但不在正确位置，先移除
                self._main_splitter.replaceWidget(
                    self._main_splitter.indexOf(self._settings_widget), 
                    QWidget()
                )
            # 添加到正确位置
            self._main_splitter.insertWidget(1, self._settings_widget)
        
        # 显示设置视图
        self._settings_widget.show()
        
        # 调整分割器大小
        self._main_splitter.setSizes([60, self._main_splitter.width() - 60, 0])  # 左侧菜单保持60px宽度，设置页面占据剩余空间
    
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
        # 重新加载可能变更的设置
        # 从配置管理器加载语言设置
        language = self._config_manager.get("general", "language", "zh_CN")
        print(f"应用语言设置: {language}")
        
        # 应用主题
        theme_name = self._config_manager.get("display", "theme", "light")
        current_theme = ThemeManager.instance().current_theme()
        if theme_name == "dark" and current_theme != Theme.DARK:
            ThemeManager.instance().set_theme(Theme.DARK)
        elif theme_name == "light" and current_theme != Theme.LIGHT:
            ThemeManager.instance().set_theme(Theme.LIGHT)
    
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
        pass
    
    def _show_chat_view(self):
        """显示会话管理和聊天界面"""
        # 显示会话管理菜单
        if not self._session_menu.isVisible():
            self._session_menu.show()
        
        # 显示当前聊天视图
        current_chat = self._get_current_chat_view()
        if current_chat and not current_chat.isVisible():
            current_chat.show()
        
        # 需要重新调整分割器中部件的位置
        # 确保垂直菜单、会话管理和聊天视图的顺序正确
        if self._main_splitter.indexOf(self._side_menu) != 0:
            # 移除并重新添加部件，保持正确顺序
            self._main_splitter.insertWidget(0, self._side_menu)
        
        if self._main_splitter.indexOf(self._session_menu) != 1:
            # 确保会话菜单在第二位置
            self._main_splitter.insertWidget(1, self._session_menu)
        
        if self._main_splitter.indexOf(self._chat_stack) != 2:
            # 确保聊天视图在第三位置
            self._main_splitter.insertWidget(2, self._chat_stack)
            
        # 调整分割器大小
        self._main_splitter.setSizes([60, 200, self._main_splitter.width() - 260])  # 左侧菜单60px，会话管理200px，聊天视图占剩余空间 

    def _update_button_icons(self):
        """更新按钮图标状态"""
        # 设置按钮图标
        if self._settings_button.isChecked():
            # 修改为使用资源文件中的图标
            self._settings_button.setIcon(QIcon(":/resources/images/settings_light.png"))
        else:
            # 修改为使用资源文件中的图标
            self._settings_button.setIcon(QIcon(":/resources/images/settings_dark.png"))
            
        # 助手按钮图标
        if self._assistant_button.isChecked():
            # 修改为使用资源文件中的图标
            self._assistant_button.setIcon(QIcon(":/resources/images/AI_light.png"))
        else:
            # 修改为使用资源文件中的图标
            self._assistant_button.setIcon(QIcon(":/resources/images/AI_dark.png"))
            
        # 确保图标大小一致
        self._settings_button.setIconSize(QSize(24, 24))
        self._assistant_button.setIconSize(QSize(24, 24))
    
    @Slot()
    def _on_assistant_action(self):
        """助手按钮处理"""
        # 设置按钮选中状态
        self._assistant_button.setChecked(True)
        self._settings_button.setChecked(False)
        
        # 更新按钮图标
        self._update_button_icons()
        
        # 如果设置视图正在显示，则隐藏它
        if hasattr(self, '_settings_widget') and self._settings_widget.isVisible():
            self._settings_widget.hide()
            
            # 如果设置视图在分割器中，暂时移除它
            index = self._main_splitter.indexOf(self._settings_widget)
            if index != -1:
                # 创建一个临时占位符部件
                placeholder = QWidget()
                self._main_splitter.replaceWidget(index, placeholder)
                # 安全删除占位符
                placeholder.deleteLater()
        
        # 显示会话管理和聊天界面
        self._show_chat_view() 