#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
from PySide6.QtWidgets import (QWidget, QDialog, QVBoxLayout, QFormLayout, 
                              QLineEdit, QComboBox, QGroupBox, QCheckBox, 
                              QSpinBox, QDoubleSpinBox, QPushButton, QTabWidget,
                              QDialogButtonBox, QLabel, QHBoxLayout, QStackedWidget,
                              QListWidget, QListWidgetItem, QFrame, QScrollArea,
                              QSplitter, QSizePolicy, QMessageBox)
from PySide6.QtCore import Qt, Signal, Slot, QSettings, QSize
from PySide6.QtGui import QIcon, QPixmap

from config_manager import ConfigManager
from llm_service import LlmService


class SettingsDialog(QWidget):
    """设置对话框"""
    
    # 信号
    settings_applied = Signal()
    
    def __init__(self, parent=None):
        """初始化设置对话框"""
        super().__init__(parent)
        
        self.setWindowTitle(self.tr("设置"))
        
        # 配置管理器
        self._config_manager = ConfigManager.instance()
        
        # 创建界面
        self._setup_ui()
        
        # 加载设置
        self._load_settings()
        
        # 连接设置信号，实现实时保存
        self._connect_settings_signals()
    
    def _setup_ui(self):
        """设置用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建左侧菜单
        self._create_left_menu()
        
        # 创建右侧内容区域
        self._create_content_area()
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(0)  # 移除分隔线
        splitter.addWidget(self._left_menu)
        splitter.addWidget(self._content_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([200, 700])
        
        # 添加到主布局
        main_layout.addWidget(splitter)
    
    def _create_left_menu(self):
        """创建左侧菜单"""
        self._left_menu = QWidget()
        self._left_menu.setObjectName("settings_left_menu")
        self._left_menu.setMinimumWidth(200)
        self._left_menu.setMaximumWidth(200)
        self._left_menu.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        
        menu_layout = QVBoxLayout(self._left_menu)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(0)
        
        # 创建菜单列表
        self._menu_list = QListWidget()
        self._menu_list.setObjectName("settings_menu_list")
        self._menu_list.setFrameShape(QFrame.NoFrame)
        self._menu_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._menu_list.currentRowChanged.connect(self._on_menu_changed)
        
        # 添加菜单项
        menu_items = [
            self.tr("模型服务"),
            self.tr("默认模型"),
            self.tr("网络搜索"),
            self.tr("MCP服务器"),
            self.tr("常规设置"),
            self.tr("显示设置"),
            self.tr("小程序设置"),
            self.tr("快捷方式"),
            self.tr("快捷助手"),
            self.tr("划到助手"),
            self.tr("快捷范围"),
            self.tr("数据设置"),
            self.tr("关于我们")
        ]
        
        for item in menu_items:
            list_item = QListWidgetItem(item)
            list_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self._menu_list.addItem(list_item)
        
        menu_layout.addWidget(self._menu_list)
    
    def _create_content_area(self):
        """创建右侧内容区域"""
        self._content_widget = QWidget()
        self._content_widget.setObjectName("settings_content")
        
        content_layout = QVBoxLayout(self._content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 创建标题栏
        self._title_bar = QWidget()
        self._title_bar.setObjectName("settings_title_bar")
        self._title_bar.setMinimumHeight(50)
        
        title_layout = QHBoxLayout(self._title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)
        
        self._title_label = QLabel(self.tr("模型服务"))
        self._title_label.setObjectName("settings_title")
        
        title_layout.addWidget(self._title_label)
        title_layout.addStretch()
        
        content_layout.addWidget(self._title_bar)
        
        # 创建内容区域
        self._content_stack = QStackedWidget()
        
        # 创建各个设置页
        self._create_model_service_page()
        self._create_default_model_page()
        self._create_web_search_page()
        self._create_mcp_server_page()
        self._create_general_settings_page()
        self._create_display_settings_page()
        self._create_mini_app_settings_page()
        self._create_shortcuts_page()
        self._create_quick_assistant_page()
        self._create_select_assistant_page()
        self._create_quick_range_page()
        self._create_data_settings_page()
        self._create_about_page()
        
        # 滚动区域包装内容
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self._content_stack)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        content_layout.addWidget(scroll_area)
    
    def _create_model_service_page(self):
        """创建模型服务设置页"""
        page = QWidget()
        page.setObjectName("settings_page")
        
        # 使用水平布局分为左右两部分
        main_layout = QHBoxLayout(page)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧模型平台列表区域
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 10, 5, 10)
        left_layout.setSpacing(10)
        
        # 搜索框
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        self._model_search_box = QLineEdit()
        self._model_search_box.setPlaceholderText(self.tr("搜索模型平台..."))
        self._model_search_box.setObjectName("model_search_box")
        self._model_search_box.textChanged.connect(self._filter_model_platforms)
        search_layout.addWidget(self._model_search_box)
        
        left_layout.addWidget(search_container)
        
        # 模型平台列表容器
        self._platforms_container = QWidget()
        self._platforms_layout = QVBoxLayout(self._platforms_container)
        self._platforms_layout.setContentsMargins(0, 0, 0, 0)
        self._platforms_layout.setSpacing(5)
        
        # 添加模型平台列表
        platform_names = [
            "硅基流动", "AltHubMix", "Oilama", "Anthropic", "OpenAI", 
            "Azure OpenAI", "PPIO 派数云", "Alaya New", "BurnCloud", 
            "无问芯湾", "Gemini", "七牛云", "深度求索", "TokenFlux", 
            "occoIAI", "GitHub Models", "零一万物"
        ]
        
        for platform in platform_names:
            platform_item = self._create_platform_item(platform)
            self._platforms_layout.addWidget(platform_item)
        
        # 使用滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._platforms_container)
        scroll.setFrameShape(QFrame.NoFrame)
        
        left_layout.addWidget(scroll)
        
        # 添加按钮
        add_button = QPushButton(self.tr("添加自定义平台"))
        add_button.setObjectName("add_platform_button")
        add_button.clicked.connect(self._on_add_custom_platform)
        left_layout.addWidget(add_button)
        
        # 右侧API配置区域
        right_widget = QWidget()
        self._right_layout = QVBoxLayout(right_widget)
        self._right_layout.setContentsMargins(10, 10, 10, 10)
        self._right_layout.setSpacing(10)
        
        # 右侧标题
        self._provider_title = QLabel(self.tr("选择一个模型平台"))
        self._provider_title.setObjectName("provider_title")
        self._right_layout.addWidget(self._provider_title)
        
        # 创建API配置堆栈
        self._api_config_stack = QStackedWidget()
        self._right_layout.addWidget(self._api_config_stack)
        
        # 添加占位页
        placeholder = QWidget()
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_label = QLabel(self.tr("请从左侧选择一个模型平台"))
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(placeholder_label)
        self._api_config_stack.addWidget(placeholder)
        
        # 添加到主布局
        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(right_widget, 2)
        
        self._content_stack.addWidget(page)
    
    def _create_platform_item(self, name):
        """创建模型平台项"""
        # 从配置管理器获取提供商ID
        providers = self._config_manager.get_all_providers()
        provider_id = None
        
        for pid, provider in providers.items():
            if provider.get("name") == name:
                provider_id = pid
                break
        
        # 如果没有找到，则使用名称作为ID
        if provider_id is None:
            provider_id = name.lower().replace(" ", "_")
        
        item = QPushButton(name)
        item.setObjectName("platform_item")
        item.setProperty("provider_id", provider_id)
        item.setProperty("provider_name", name)
        item.setCheckable(True)
        item.clicked.connect(lambda: self._on_platform_selected(provider_id, name))
        return item
    
    def _load_model_providers(self):
        """加载所有模型提供商"""
        # 清空现有列表
        self._clear_layout(self._platforms_layout)
        
        # 获取所有提供商
        providers = self._config_manager.get_all_providers()
        
        # 创建提供商项
        for provider_id, provider in providers.items():
            provider_name = provider.get("name", provider_id)
            platform_item = self._create_platform_item(provider_name)
            self._platforms_layout.addWidget(platform_item)
        
        # 添加额外的弹性空间
        self._platforms_layout.addStretch()
    
    def _clear_layout(self, layout):
        """清空布局中的所有控件"""
        if layout is None:
            return
        
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                # 递归清空子布局
                self._clear_layout(item.layout())
    
    def _on_platform_selected(self, provider_id, provider_name):
        """当模型平台被选中时调用"""
        # 获取提供商配置
        provider = self._config_manager.get_provider(provider_id)
        
        if not provider:
            # 如果提供商不存在，则创建一个
            self._config_manager.add_provider(provider_id, provider_name)
            provider = self._config_manager.get_provider(provider_id)
        
        # 更新标题
        self._provider_title.setText(provider.get("name", provider_name))
        
        # 创建API配置页（如果需要）
        if not hasattr(self, f"_api_config_page_{provider_id}"):
            api_config_page = self._create_api_config_page(provider_id, provider)
            self._api_config_stack.addWidget(api_config_page)
            setattr(self, f"_api_config_page_{provider_id}", api_config_page)
        
        # 显示对应的API配置页
        api_config_page = getattr(self, f"_api_config_page_{provider_id}")
        self._api_config_stack.setCurrentWidget(api_config_page)
        
        # 刷新模型列表
        self._refresh_model_list(provider_id)
    
    def _create_api_config_page(self, provider_id, provider):
        """创建API配置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # API设置区域
        api_group = QGroupBox(self.tr("API设置"))
        api_layout = QFormLayout(api_group)
        api_layout.setContentsMargins(10, 15, 10, 10)
        api_layout.setSpacing(10)
        
        # API密钥
        api_key_container = QWidget()
        api_key_layout = QVBoxLayout(api_key_container)
        api_key_layout.setContentsMargins(0, 0, 0, 0)
        api_key_layout.setSpacing(5)
        
        # 密钥输入框和按钮容器
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        api_key_input = QLineEdit()
        api_key_input.setEchoMode(QLineEdit.Password)
        api_key_input.setPlaceholderText(self.tr("输入API密钥，多个密钥用逗号分隔"))
        api_key_input.setText(provider.get("api_key", ""))
        api_key_input.setProperty("provider_id", provider_id)
        api_key_input.setProperty("field", "api_key")
        api_key_input.textChanged.connect(lambda text, pid=provider_id: self._on_provider_field_changed(pid, "api_key", text))
        
        # 显示/隐藏密钥按钮
        toggle_view_button = QPushButton()
        toggle_view_button.setCheckable(True)
        toggle_view_button.setIcon(QIcon(":/icons/eye_off.png"))
        toggle_view_button.setToolTip(self.tr("显示/隐藏密钥"))
        toggle_view_button.clicked.connect(lambda checked: self._toggle_password_view(api_key_input, toggle_view_button))
        
        detect_button = QPushButton(self.tr("检测"))
        detect_button.clicked.connect(lambda checked, pid=provider_id: self._on_test_api_key(pid))
        
        input_layout.addWidget(api_key_input)
        input_layout.addWidget(toggle_view_button)
        input_layout.addWidget(detect_button)
        
        api_key_layout.addWidget(input_container)
        
        # 添加获取密钥链接
        if provider_id == "deepseek":
            key_link = QLabel("<a href='https://platform.deepseek.com/api_keys'>点击这里获取密钥</a>")
            key_link.setOpenExternalLinks(True)
            api_key_layout.addWidget(key_link)
        elif provider_id == "openai":
            key_link = QLabel("<a href='https://platform.openai.com/api-keys'>点击这里获取密钥</a>")
            key_link.setOpenExternalLinks(True)
            api_key_layout.addWidget(key_link)
        
        api_layout.addRow(self.tr("API密钥:"), api_key_container)
        
        # API URL
        api_url_input = QLineEdit()
        api_url_input.setPlaceholderText(self.tr("API接口地址"))
        api_url_input.setText(provider.get("api_url", ""))
        api_url_input.setProperty("provider_id", provider_id)
        api_url_input.setProperty("field", "api_url")
        api_url_input.textChanged.connect(lambda text, pid=provider_id: self._on_provider_field_changed(pid, "api_url", text))
        
        api_layout.addRow(self.tr("API地址:"), api_url_input)
        
        layout.addWidget(api_group)
        
        # 模型列表区域
        models_group = QGroupBox(self.tr("模型列表"))
        models_layout = QVBoxLayout(models_group)
        models_layout.setContentsMargins(10, 15, 10, 10)
        models_layout.setSpacing(10)
        
        # 模型列表容器
        models_container = QWidget()
        models_container_layout = QVBoxLayout(models_container)
        models_container_layout.setContentsMargins(0, 0, 0, 0)
        models_container_layout.setSpacing(5)
        
        # 设置ID属性，用于后续刷新
        models_container.setObjectName(f"models_container_{provider_id}")
        
        # 使用滚动区域
        models_scroll = QScrollArea()
        models_scroll.setWidgetResizable(True)
        models_scroll.setWidget(models_container)
        models_scroll.setFrameShape(QFrame.NoFrame)
        
        models_layout.addWidget(models_scroll)
        
        # 添加模型按钮
        add_model_button = QPushButton(self.tr("添加模型"))
        add_model_button.setObjectName("add_model_button")
        add_model_button.clicked.connect(lambda checked, pid=provider_id: self._on_add_model(pid))
        models_layout.addWidget(add_model_button)
        
        layout.addWidget(models_group)
        
        # 添加弹性空间
        layout.addStretch()
        
        return page
    
    def _toggle_password_view(self, line_edit, button):
        """切换密码显示/隐藏状态"""
        if line_edit.echoMode() == QLineEdit.Password:
            line_edit.setEchoMode(QLineEdit.Normal)
            button.setIcon(QIcon(":/icons/eye.png"))
        else:
            line_edit.setEchoMode(QLineEdit.Password)
            button.setIcon(QIcon(":/icons/eye_off.png"))
    
    def _on_test_api_key(self, provider_id):
        """测试API密钥"""
        provider = self._config_manager.get_provider(provider_id)
        if not provider or not provider.get("api_key"):
            QMessageBox.warning(self, self.tr("提示"), self.tr("请先输入API密钥"))
            return
        
        # 获取模型列表
        models = self._config_manager.get_provider_models(provider_id)
        if not models:
            QMessageBox.warning(self, self.tr("提示"), self.tr("该提供商没有配置模型"))
            return
        
        # 创建模型选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("选择要测试的模型"))
        dialog.setMinimumWidth(300)
        
        dialog_layout = QVBoxLayout(dialog)
        
        # 添加模型选择下拉框
        model_label = QLabel(self.tr("选择模型:"))
        dialog_layout.addWidget(model_label)
        
        model_combo = QComboBox()
        for model in models:
            model_combo.addItem(model.get("name", model.get("id", "")), model.get("id"))
        
        dialog_layout.addWidget(model_combo)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addWidget(button_box)
        
        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            # 获取选择的模型
            model_id = model_combo.currentData()
            
            # 创建测试中对话框（使用QDialog而不是QMessageBox）
            progress_dialog = QDialog(self)
            progress_dialog.setWindowTitle(self.tr("正在测试"))
            progress_dialog.setMinimumWidth(300)
            progress_dialog.setMinimumHeight(100)
            progress_dialog.setModal(True)
            
            progress_layout = QVBoxLayout(progress_dialog)
            
            # 添加消息标签
            message_label = QLabel(self.tr("正在测试API连接，请稍候..."))
            message_label.setAlignment(Qt.AlignCenter)
            progress_layout.addWidget(message_label)
            
            # 添加取消按钮
            cancel_button = QPushButton(self.tr("取消"))
            cancel_button.clicked.connect(lambda: self._cancel_api_test(progress_dialog))
            
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(cancel_button)
            button_layout.addStretch()
            
            progress_layout.addLayout(button_layout)
            
            # 设置对话框属性，用于标识正在测试中
            progress_dialog.setProperty("testing", True)
            
            # 显示对话框
            progress_dialog.show()
            
            # 创建定时器，在超时后强制关闭对话框
            from PySide6.QtCore import QTimer
            self._test_timeout_timer = QTimer()
            self._test_timeout_timer.setSingleShot(True)
            self._test_timeout_timer.timeout.connect(lambda: self._handle_test_timeout(progress_dialog))
            self._test_timeout_timer.start(15000)  # 15秒超时
            
            # 使用QTimer以非阻塞方式运行测试
            QTimer.singleShot(100, lambda: self._show_test_result(provider_id, model_id, progress_dialog))
    
    def _cancel_api_test(self, progress_dialog):
        """取消API测试"""
        if hasattr(self, '_test_timeout_timer') and self._test_timeout_timer.isActive():
            self._test_timeout_timer.stop()
        
        if progress_dialog and progress_dialog.isVisible():
            progress_dialog.reject()
            progress_dialog.close()
    
    def _handle_test_timeout(self, progress_dialog):
        """处理测试超时"""
        if progress_dialog and progress_dialog.isVisible() and progress_dialog.property("testing"):
            progress_dialog.setProperty("testing", False)
            progress_dialog.close()
            QMessageBox.warning(self, self.tr("超时"), self.tr("API连接测试超时，请检查网络连接或API服务器状态"))
    
    def _show_test_result(self, provider_id, model_id, progress_dialog):
        """显示测试结果"""
        # 检查进度对话框是否仍然有效
        if progress_dialog is None or not progress_dialog.isVisible():
            return
            
        # 尝试关闭进度对话框
        try:
            progress_dialog.close()
        except:
            # 如果关闭失败，尝试另一种方式
            if hasattr(progress_dialog, 'reject'):
                progress_dialog.reject()
        
        # 创建LlmService实例进行测试
        llm_service = LlmService()
        success, message = llm_service.test_model_connection(provider_id, model_id)
        
        # 确保结果对话框有关闭按钮
        if success:
            result_dialog = QMessageBox(QMessageBox.Information, self.tr("测试结果"), 
                                         self.tr(f"API连接测试成功\n\n{message}"), 
                                         QMessageBox.Ok, self)
        else:
            result_dialog = QMessageBox(QMessageBox.Warning, self.tr("测试结果"), 
                                         self.tr(f"API连接测试失败\n\n{message}"), 
                                         QMessageBox.Ok, self)
        
        # 显示结果对话框
        result_dialog.exec_()
    
    def _refresh_model_list(self, provider_id):
        """刷新模型列表"""
        # 获取模型容器
        models_container = self.findChild(QWidget, f"models_container_{provider_id}")
        if not models_container:
            return
        
        # 清空现有列表
        self._clear_layout(models_container.layout())
        
        # 获取提供商的所有模型
        models = self._config_manager.get_provider_models(provider_id)
        
        # 创建模型项
        for model in models:
            model_item = self._create_model_item(provider_id, model)
            models_container.layout().addWidget(model_item)
        
        # 添加额外的弹性空间
        models_container.layout().addStretch()
    
    def _create_model_item(self, provider_id, model):
        """创建模型项"""
        item = QWidget()
        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(5, 5, 5, 5)
        
        # 模型名称
        model_name = QLabel(model.get("name", model.get("id", "")))
        model_name.setObjectName("model_name")
        item_layout.addWidget(model_name, 1)
        
        # 编辑按钮
        edit_button = QPushButton(self.tr("编辑"))
        edit_button.setObjectName("edit_model_button")
        edit_button.clicked.connect(lambda checked, pid=provider_id, mid=model.get("id"): self._on_edit_model(pid, mid))
        item_layout.addWidget(edit_button)
        
        # 删除按钮
        delete_button = QPushButton(self.tr("删除"))
        delete_button.setObjectName("delete_model_button")
        delete_button.clicked.connect(lambda checked, pid=provider_id, mid=model.get("id"): self._on_delete_model(pid, mid))
        item_layout.addWidget(delete_button)
        
        return item
    
    def _on_provider_field_changed(self, provider_id, field, value):
        """当提供商字段值改变时调用"""
        provider = self._config_manager.get_provider(provider_id)
        if not provider:
            return
        
        # 创建提供商配置副本
        provider_copy = copy.deepcopy(provider)
        provider_copy[field] = value
        
        # 更新提供商配置
        self._config_manager.set_provider(provider_id, provider_copy)
    
    def _on_add_model(self, provider_id):
        """添加模型"""
        # 创建模型配置对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("添加模型"))
        dialog.setMinimumWidth(400)
        
        dialog_layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        
        # 模型ID
        model_id_input = QLineEdit()
        model_id_input.setPlaceholderText(self.tr("模型的唯一标识符"))
        form_layout.addRow(self.tr("模型ID:"), model_id_input)
        
        # 模型名称
        model_name_input = QLineEdit()
        model_name_input.setPlaceholderText(self.tr("模型的显示名称"))
        form_layout.addRow(self.tr("模型名称:"), model_name_input)
        
        # 最大Token数
        max_tokens_input = QSpinBox()
        max_tokens_input.setRange(1, 100000)
        max_tokens_input.setValue(4096)
        form_layout.addRow(self.tr("最大Token数:"), max_tokens_input)
        
        # 是否支持流式输出
        supports_stream_check = QCheckBox()
        supports_stream_check.setChecked(True)
        form_layout.addRow(self.tr("支持流式输出:"), supports_stream_check)
        
        dialog_layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addWidget(button_box)
        
        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            # 获取表单数据
            model_id = model_id_input.text().strip()
            model_name = model_name_input.text().strip()
            max_tokens = max_tokens_input.value()
            supports_stream = supports_stream_check.isChecked()
            
            # 验证输入
            if not model_id:
                QMessageBox.warning(self, self.tr("错误"), self.tr("模型ID不能为空"))
                return
            
            if not model_name:
                model_name = model_id
            
            # 创建模型配置
            model_config = {
                "id": model_id,
                "name": model_name,
                "max_tokens": max_tokens,
                "supports_stream": supports_stream
            }
            
            # 添加到提供商
            if self._config_manager.add_model_to_provider(provider_id, model_config):
                # 刷新模型列表
                self._refresh_model_list(provider_id)
                QMessageBox.information(self, self.tr("成功"), self.tr("模型添加成功"))
            else:
                QMessageBox.warning(self, self.tr("错误"), self.tr("模型添加失败"))
    
    def _on_edit_model(self, provider_id, model_id):
        """编辑模型"""
        # 获取模型配置
        provider = self._config_manager.get_provider(provider_id)
        if not provider:
            return
        
        model = None
        for m in provider.get("models", []):
            if m.get("id") == model_id:
                model = m
                break
        
        if not model:
            QMessageBox.warning(self, self.tr("错误"), self.tr("未找到模型配置"))
            return
        
        # 创建模型配置对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("编辑模型"))
        dialog.setMinimumWidth(400)
        
        dialog_layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        
        # 模型ID（只读）
        model_id_input = QLineEdit()
        model_id_input.setText(model.get("id", ""))
        model_id_input.setReadOnly(True)
        form_layout.addRow(self.tr("模型ID:"), model_id_input)
        
        # 模型名称
        model_name_input = QLineEdit()
        model_name_input.setText(model.get("name", ""))
        form_layout.addRow(self.tr("模型名称:"), model_name_input)
        
        # 最大Token数
        max_tokens_input = QSpinBox()
        max_tokens_input.setRange(1, 100000)
        max_tokens_input.setValue(model.get("max_tokens", 4096))
        form_layout.addRow(self.tr("最大Token数:"), max_tokens_input)
        
        # 是否支持流式输出
        supports_stream_check = QCheckBox()
        supports_stream_check.setChecked(model.get("supports_stream", True))
        form_layout.addRow(self.tr("支持流式输出:"), supports_stream_check)
        
        dialog_layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addWidget(button_box)
        
        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            # 获取表单数据
            model_name = model_name_input.text().strip()
            max_tokens = max_tokens_input.value()
            supports_stream = supports_stream_check.isChecked()
            
            # 验证输入
            if not model_name:
                model_name = model_id
            
            # 创建模型配置
            model_config = {
                "id": model_id,
                "name": model_name,
                "max_tokens": max_tokens,
                "supports_stream": supports_stream
            }
            
            # 更新模型
            if self._config_manager.add_model_to_provider(provider_id, model_config):
                # 刷新模型列表
                self._refresh_model_list(provider_id)
                QMessageBox.information(self, self.tr("成功"), self.tr("模型更新成功"))
            else:
                QMessageBox.warning(self, self.tr("错误"), self.tr("模型更新失败"))
    
    def _on_delete_model(self, provider_id, model_id):
        """删除模型"""
        # 确认删除
        if QMessageBox.question(self, self.tr("确认"), self.tr("确定要删除此模型吗？")) != QMessageBox.Yes:
            return
        
        # 删除模型
        if self._config_manager.delete_model_from_provider(provider_id, model_id):
            # 刷新模型列表
            self._refresh_model_list(provider_id)
            QMessageBox.information(self, self.tr("成功"), self.tr("模型删除成功"))
        else:
            QMessageBox.warning(self, self.tr("错误"), self.tr("模型删除失败"))
    
    def _on_add_custom_platform(self):
        """添加自定义平台"""
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("添加自定义平台"))
        dialog.setMinimumWidth(400)
        
        dialog_layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        
        # 平台ID
        platform_id_input = QLineEdit()
        platform_id_input.setPlaceholderText(self.tr("平台的唯一标识符，英文小写"))
        form_layout.addRow(self.tr("平台ID:"), platform_id_input)
        
        # 平台名称
        platform_name_input = QLineEdit()
        platform_name_input.setPlaceholderText(self.tr("平台的显示名称"))
        form_layout.addRow(self.tr("平台名称:"), platform_name_input)
        
        # API URL
        api_url_input = QLineEdit()
        api_url_input.setPlaceholderText(self.tr("API接口地址"))
        form_layout.addRow(self.tr("API地址:"), api_url_input)
        
        dialog_layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addWidget(button_box)
        
        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            # 获取表单数据
            platform_id = platform_id_input.text().strip()
            platform_name = platform_name_input.text().strip()
            api_url = api_url_input.text().strip()
            
            # 验证输入
            if not platform_id:
                QMessageBox.warning(self, self.tr("错误"), self.tr("平台ID不能为空"))
                return
            
            if not platform_name:
                platform_name = platform_id
            
            # 添加平台
            if self._config_manager.add_provider(platform_id, platform_name, api_url):
                # 添加到UI
                platform_item = self._create_platform_item(platform_name)
                self._platforms_layout.insertWidget(self._platforms_layout.count()-1, platform_item)
                QMessageBox.information(self, self.tr("成功"), self.tr("平台添加成功"))
            else:
                QMessageBox.warning(self, self.tr("错误"), self.tr("平台添加失败"))
    
    def _filter_model_platforms(self, text):
        """根据搜索文本过滤模型平台"""
        # 遍历所有平台项
        for i in range(self._platforms_layout.count()):
            item = self._platforms_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QPushButton):
                    # 获取平台名称
                    platform_name = widget.text()
                    # 如果搜索文本为空或平台名称包含搜索文本，则显示；否则隐藏
                    widget.setVisible(not text or text.lower() in platform_name.lower())
    
    def _on_menu_changed(self, index):
        """菜单切换处理"""
        self._content_stack.setCurrentIndex(index)
        self._title_label.setText(self._menu_list.item(index).text())
    
    def _load_settings(self):
        """加载设置"""
        # 加载常规设置
        language = self._config_manager.get("general", "language", "zh_CN")
        if language in self._language_map:
            self._language_combo.setCurrentIndex(self._language_map[language])
        
        self._auto_start.setChecked(self._config_manager.get("general", "auto_start", False))
        self._check_updates.setChecked(self._config_manager.get("general", "check_updates", True))
    
    def _save_settings(self):
        """保存设置"""
        # 保存常规设置
        language_idx = self._language_combo.currentIndex()
        language = next((k for k, v in self._language_map.items() if v == language_idx), "zh_CN")
        self._config_manager.set("general", "language", language)
        
        self._config_manager.set("general", "auto_start", self._auto_start.isChecked())
        self._config_manager.set("general", "check_updates", self._check_updates.isChecked())
        
        # 保存到文件
        self._config_manager.save()
        
        # 发送设置应用信号
        self.settings_applied.emit()
    
    def _connect_settings_signals(self):
        """连接设置信号"""
        # 语言设置
        if hasattr(self, '_language_combo'):
            self._language_combo.currentIndexChanged.connect(self._on_language_changed)
        
        # 自动启动
        if hasattr(self, '_auto_start'):
            self._auto_start.stateChanged.connect(self._on_auto_start_changed)
        
        # 检查更新
        if hasattr(self, '_check_updates'):
            self._check_updates.stateChanged.connect(self._on_check_updates_changed)
    
    @Slot()
    def _on_reset_settings(self):
        """重置设置处理"""
        # 弹出确认对话框
        reply = QMessageBox.question(
            self,
            self.tr("确认重置"),
            self.tr("确定要将所有设置还原为默认值吗？此操作无法撤销。"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 重置设置
            if self._config_manager.reset():
                # 重新加载设置到UI
                self._load_settings()
                
                # 显示成功消息
                QMessageBox.information(
                    self, 
                    self.tr("重置成功"),
                    self.tr("所有设置已还原为默认值。")
                )
            else:
                # 显示错误消息
                QMessageBox.warning(
                    self,
                    self.tr("重置失败"),
                    self.tr("无法还原默认设置，请检查配置文件权限。")
                )
    
    @Slot(int)
    def _on_language_changed(self, index):
        """语言设置变更处理"""
        # 保存设置
        self._save_settings()
    
    @Slot(int)
    def _on_auto_start_changed(self, state):
        """自动启动设置变更处理"""
        # 保存设置
        self._save_settings()
    
    @Slot(int)
    def _on_check_updates_changed(self, state):
        """更新检查设置变更处理"""
        # 保存设置
        self._save_settings()
    
    @Slot(str)
    def _on_api_key_changed(self, text):
        """API密钥变更处理"""
        # 这里可以添加保存到配置的代码
        pass
    
    @Slot(str)
    def _on_api_url_changed(self, text):
        """API地址变更处理"""
        # 这里可以添加保存到配置的代码
        pass
    
    @Slot(str)
    def _on_model_binding_changed(self, text):
        """模型绑定变更处理"""
        # 这里可以添加保存到配置的代码
        pass
    
    def _create_default_model_page(self):
        """创建默认模型设置页"""
        page = QWidget()
        page.setObjectName("settings_page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加提示
        label = QLabel(self.tr("默认模型设置"))
        label.setObjectName("settings_section_title")
        layout.addWidget(label)
        
        # 添加到内容栈
        self._content_stack.addWidget(page)
    
    def _create_web_search_page(self):
        """创建网络搜索设置页"""
        page = QWidget()
        page.setObjectName("settings_page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加提示
        label = QLabel(self.tr("网络搜索设置"))
        label.setObjectName("settings_section_title")
        layout.addWidget(label)
        
        # 添加到内容栈
        self._content_stack.addWidget(page)
    
    def _create_mcp_server_page(self):
        """创建MCP服务器设置页"""
        page = QWidget()
        page.setObjectName("settings_page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加提示
        label = QLabel(self.tr("MCP服务器设置"))
        label.setObjectName("settings_section_title")
        layout.addWidget(label)
        
        # 添加到内容栈
        self._content_stack.addWidget(page)
    
    def _create_general_settings_page(self):
        """创建常规设置页"""
        page = QWidget()
        page.setObjectName("settings_page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 常规设置组
        general_group = QGroupBox(self.tr("常规设置"))
        general_layout = QFormLayout(general_group)
        
        # 语言设置
        self._language_combo = QComboBox()
        self._language_combo.addItem(self.tr("简体中文"), "zh_CN")
        self._language_combo.addItem(self.tr("English"), "en_US")
        self._language_map = {"zh_CN": 0, "en_US": 1}
        self._language_combo.currentIndexChanged.connect(self._on_language_changed)
        general_layout.addRow(self.tr("语言:"), self._language_combo)
        
        # 自动启动
        self._auto_start = QCheckBox()
        self._auto_start.stateChanged.connect(self._on_auto_start_changed)
        general_layout.addRow(self.tr("开机自动启动:"), self._auto_start)
        
        # 自动检查更新
        self._check_updates = QCheckBox()
        self._check_updates.stateChanged.connect(self._on_check_updates_changed)
        general_layout.addRow(self.tr("自动检查更新:"), self._check_updates)
        
        layout.addWidget(general_group)
        
        # 重置按钮
        reset_button = QPushButton(self.tr("还原默认设置"))
        reset_button.clicked.connect(self._on_reset_settings)
        layout.addWidget(reset_button)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 添加到内容栈
        self._content_stack.addWidget(page)
    
    def _create_display_settings_page(self):
        """创建显示设置页"""
        page = QWidget()
        page.setObjectName("settings_page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加提示
        label = QLabel(self.tr("显示设置"))
        label.setObjectName("settings_section_title")
        layout.addWidget(label)
        
        # 添加到内容栈
        self._content_stack.addWidget(page)
    
    def _create_mini_app_settings_page(self):
        """创建小程序设置页"""
        page = QWidget()
        page.setObjectName("settings_page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加提示
        label = QLabel(self.tr("小程序设置"))
        label.setObjectName("settings_section_title")
        layout.addWidget(label)
        
        # 添加到内容栈
        self._content_stack.addWidget(page)
    
    def _create_shortcuts_page(self):
        """创建快捷方式设置页"""
        page = QWidget()
        page.setObjectName("settings_page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加提示
        label = QLabel(self.tr("快捷方式设置"))
        label.setObjectName("settings_section_title")
        layout.addWidget(label)
        
        # 添加到内容栈
        self._content_stack.addWidget(page)
    
    def _create_quick_assistant_page(self):
        """创建快捷助手设置页"""
        page = QWidget()
        page.setObjectName("settings_page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加提示
        label = QLabel(self.tr("快捷助手设置"))
        label.setObjectName("settings_section_title")
        layout.addWidget(label)
        
        # 添加到内容栈
        self._content_stack.addWidget(page)
    
    def _create_select_assistant_page(self):
        """创建划到助手设置页"""
        page = QWidget()
        page.setObjectName("settings_page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加提示
        label = QLabel(self.tr("划到助手设置"))
        label.setObjectName("settings_section_title")
        layout.addWidget(label)
        
        # 添加到内容栈
        self._content_stack.addWidget(page)
    
    def _create_quick_range_page(self):
        """创建快捷范围设置页"""
        page = QWidget()
        page.setObjectName("settings_page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加提示
        label = QLabel(self.tr("快捷范围设置"))
        label.setObjectName("settings_section_title")
        layout.addWidget(label)
        
        # 添加到内容栈
        self._content_stack.addWidget(page)
    
    def _create_data_settings_page(self):
        """创建数据设置页"""
        page = QWidget()
        page.setObjectName("settings_page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加提示
        label = QLabel(self.tr("数据设置"))
        label.setObjectName("settings_section_title")
        layout.addWidget(label)
        
        # 添加到内容栈
        self._content_stack.addWidget(page)
    
    def _create_about_page(self):
        """创建关于我们页"""
        page = QWidget()
        page.setObjectName("settings_page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加提示
        label = QLabel(self.tr("关于我们"))
        label.setObjectName("settings_section_title")
        layout.addWidget(label)
        
        # 添加版本信息
        version_label = QLabel(self.tr("BerryLLM Studio 版本: 1.0.0"))
        layout.addWidget(version_label)
        
        # 添加到内容栈
        self._content_stack.addWidget(page) 