#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QWidget, QDialog, QVBoxLayout, QFormLayout, 
                              QLineEdit, QComboBox, QGroupBox, QCheckBox, 
                              QSpinBox, QDoubleSpinBox, QPushButton, QTabWidget,
                              QDialogButtonBox, QLabel, QHBoxLayout, QStackedWidget,
                              QListWidget, QListWidgetItem, QFrame, QScrollArea,
                              QSplitter, QSizePolicy, QMessageBox)
from PySide6.QtCore import Qt, Signal, Slot, QSettings, QSize
from PySide6.QtGui import QIcon, QPixmap

from config_manager import ConfigManager


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
        
        search_box = QLineEdit()
        search_box.setPlaceholderText(self.tr("搜索模型平台..."))
        search_box.setObjectName("model_search_box")
        search_layout.addWidget(search_box)
        
        left_layout.addWidget(search_container)
        
        # 模型平台列表
        platforms_container = QWidget()
        platforms_layout = QVBoxLayout(platforms_container)
        platforms_layout.setContentsMargins(0, 0, 0, 0)
        platforms_layout.setSpacing(5)
        
        # 添加模型平台列表
        platform_names = [
            "硅基流动", "AltHubMix", "Oilama", "Anthropic", "OpenAI", 
            "Azure OpenAI", "PPIO 派数云", "Alaya New", "BurnCloud", 
            "无问芯湾", "Gemini", "七牛云", "深度求索", "TokenFlux", 
            "occoIAI", "GitHub Models", "零一万物"
        ]
        
        for platform in platform_names:
            platform_item = self._create_platform_item(platform)
            platforms_layout.addWidget(platform_item)
        
        # 添加按钮
        add_button = QPushButton(self.tr("添加"))
        add_button.setObjectName("add_platform_button")
        platforms_layout.addWidget(add_button)
        
        # 使用滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(platforms_container)
        scroll.setFrameShape(QFrame.NoFrame)
        
        left_layout.addWidget(scroll)
        
        # 右侧API配置区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)
        
        # API设置区域
        api_group = QGroupBox(self.tr("API设置"))
        api_layout = QFormLayout(api_group)
        api_layout.setContentsMargins(10, 15, 10, 10)
        api_layout.setSpacing(10)
        
        # API密钥
        api_key_container = QWidget()
        api_key_layout = QHBoxLayout(api_key_container)
        api_key_layout.setContentsMargins(0, 0, 0, 0)
        
        self._api_key_input = QLineEdit()
        self._api_key_input.setEchoMode(QLineEdit.Password)
        self._api_key_input.setPlaceholderText(self.tr("输入API密钥，多个密钥用逗号分隔"))
        detect_button = QPushButton(self.tr("检测"))
        
        api_key_layout.addWidget(self._api_key_input)
        api_key_layout.addWidget(detect_button)
        
        api_layout.addRow(self.tr("API密钥:"), api_key_container)
        
        # 模型密码
        password_label = QLabel(self.tr("<a href='#'>点击查看模型密码</a>"))
        password_label.setTextFormat(Qt.RichText)
        password_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        api_layout.addRow("", password_label)
        
        # API地址说明
        api_note = QLabel(self.tr("• 以\"/\"结尾的地址将忽略v1版本\n• 以\"#\"结尾的地址将强制使用输入的地址"))
        api_layout.addRow("", api_note)
        
        # API地址
        self._api_url1 = QLineEdit("https://api.siliconflow.cn")
        api_layout.addRow(self.tr("API地址:"), self._api_url1)
        
        self._api_url2 = QLineEdit("https://api.siliconflow.cn/v1/chat/completions")
        api_layout.addRow("", self._api_url2)
        
        # 配置
        model_binding_label = QLabel(self.tr("模型绑定:"))
        self._model_binding_input = QLineEdit("deepseek-ai/DeepSeek-R1")
        api_layout.addRow(model_binding_label, self._model_binding_input)
        
        # 账户管理
        account_group = QGroupBox(self.tr("账户管理"))
        account_layout = QVBoxLayout(account_group)
        account_layout.setContentsMargins(10, 15, 10, 10)
        account_layout.setSpacing(10)
        
        # 余额显示
        balance_container = QWidget()
        balance_layout = QHBoxLayout(balance_container)
        balance_layout.setContentsMargins(0, 0, 0, 0)
        
        balance_label = QLabel(self.tr("余额: ¥100.00"))
        recharge_button = QPushButton(self.tr("余额充值"))
        
        balance_layout.addWidget(balance_label)
        balance_layout.addStretch()
        balance_layout.addWidget(recharge_button)
        
        account_layout.addWidget(balance_container)
        
        # 费用账单
        bill_button = QPushButton(self.tr("费用账单"))
        account_layout.addWidget(bill_button)
        
        # 服务提供方
        provider_label = QLabel(self.tr("本服务由 siliconflow.cn 提供"))
        provider_label.setAlignment(Qt.AlignCenter)
        account_layout.addWidget(provider_label)
        
        # 添加到右侧布局
        right_layout.addWidget(api_group)
        right_layout.addWidget(account_group)
        right_layout.addStretch()
        
        # 添加左右两侧到主布局
        main_layout.addWidget(left_widget, 1)  # 左侧占比较小
        main_layout.addWidget(right_widget, 2)  # 右侧占比较大
        
        # 添加到堆栈
        self._content_stack.addWidget(page)
        
        # 连接信号
        self._api_key_input.textChanged.connect(self._on_api_key_changed)
        self._api_url1.textChanged.connect(self._on_api_url_changed)
        self._api_url2.textChanged.connect(self._on_api_url_changed)
        self._model_binding_input.textChanged.connect(self._on_model_binding_changed)
    
    def _create_platform_item(self, name):
        """创建平台项目"""
        item = QWidget()
        item.setObjectName("platform_item")
        
        layout = QHBoxLayout(item)
        layout.setContentsMargins(10, 5, 10, 5)
        
        label = QLabel(name)
        label.setObjectName("platform_name")
        
        layout.addWidget(label)
        layout.addStretch()
        
        # 添加点击效果
        item.mousePressEvent = lambda event, n=name: self._on_platform_selected(n)
        
        return item
    
    def _create_default_model_page(self):
        """创建默认模型设置页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 默认模型设置
        model_group = QGroupBox(self.tr("默认模型设置"))
        model_layout = QFormLayout(model_group)
        
        default_model = QComboBox()
        default_model.addItems(["GPT-4", "Claude 3 Opus", "DeepSeek", "Gemini"])
        model_layout.addRow(self.tr("默认模型:"), default_model)
        
        layout.addWidget(model_group)
        layout.addStretch()
        
        self._content_stack.addWidget(page)
    
    def _create_web_search_page(self):
        """创建网络搜索设置页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 网络搜索设置
        search_group = QGroupBox(self.tr("网络搜索设置"))
        search_layout = QFormLayout(search_group)
        
        enable_search = QCheckBox(self.tr("启用网络搜索"))
        search_layout.addRow("", enable_search)
        
        search_engine = QComboBox()
        search_engine.addItems(["Google", "Bing", "Baidu"])
        search_layout.addRow(self.tr("搜索引擎:"), search_engine)
        
        layout.addWidget(search_group)
        layout.addStretch()
        
        self._content_stack.addWidget(page)
    
    def _create_mcp_server_page(self):
        """创建MCP服务器设置页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # MCP服务器设置
        mcp_group = QGroupBox(self.tr("MCP服务器设置"))
        mcp_layout = QFormLayout(mcp_group)
        
        server_url = QLineEdit("https://mcp.example.com")
        mcp_layout.addRow(self.tr("服务器URL:"), server_url)
        
        api_key = QLineEdit()
        api_key.setEchoMode(QLineEdit.Password)
        mcp_layout.addRow(self.tr("API密钥:"), api_key)
        
        layout.addWidget(mcp_group)
        layout.addStretch()
        
        self._content_stack.addWidget(page)
    
    def _create_general_settings_page(self):
        """创建常规设置页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 常规设置
        general_group = QGroupBox(self.tr("常规设置"))
        general_layout = QFormLayout(general_group)
        
        # 语言设置
        self._language_combo = QComboBox()
        self._language_combo.addItems([self.tr("简体中文"), self.tr("English")])
        general_layout.addRow(self.tr("界面语言:"), self._language_combo)
        
        # 语言映射
        self._language_map = {
            "zh_CN": 0,  # 简体中文
            "en_US": 1,  # 英文
        }
        
        # 启动设置
        self._auto_start = QCheckBox(self.tr("开机自动启动"))
        general_layout.addRow("", self._auto_start)
        
        # 更新检查
        self._check_updates = QCheckBox(self.tr("启动时检查更新"))
        general_layout.addRow("", self._check_updates)
        
        # 还原默认设置按钮
        reset_button_container = QWidget()
        reset_button_layout = QHBoxLayout(reset_button_container)
        reset_button_layout.setContentsMargins(0, 10, 0, 0)
        
        reset_button = QPushButton(self.tr("还原默认设置"))
        reset_button.setObjectName("reset_settings_button")
        reset_button.clicked.connect(self._on_reset_settings)
        
        reset_button_layout.addStretch()
        reset_button_layout.addWidget(reset_button)
        
        # 添加到布局
        layout.addWidget(general_group)
        layout.addWidget(reset_button_container)
        layout.addStretch()
        
        # 连接信号
        self._language_combo.currentIndexChanged.connect(self._on_language_changed)
        self._auto_start.stateChanged.connect(self._on_auto_start_changed)
        self._check_updates.stateChanged.connect(self._on_check_updates_changed)
        
        self._content_stack.addWidget(page)
    
    def _create_display_settings_page(self):
        """创建显示设置页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 显示设置
        display_group = QGroupBox(self.tr("显示设置"))
        display_layout = QFormLayout(display_group)
        
        # 主题设置
        theme = QComboBox()
        theme.addItems([self.tr("浅色"), self.tr("深色"), self.tr("跟随系统")])
        display_layout.addRow(self.tr("主题:"), theme)
        
        # 字体大小
        font_size = QSpinBox()
        font_size.setRange(8, 24)
        font_size.setValue(12)
        display_layout.addRow(self.tr("字体大小:"), font_size)
        
        layout.addWidget(display_group)
        layout.addStretch()
        
        self._content_stack.addWidget(page)
    
    def _create_mini_app_settings_page(self):
        """创建小程序设置页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 小程序设置
        miniapp_group = QGroupBox(self.tr("小程序设置"))
        miniapp_layout = QFormLayout(miniapp_group)
        
        # 启用小程序
        enable_miniapp = QCheckBox(self.tr("启用小程序功能"))
        miniapp_layout.addRow("", enable_miniapp)
        
        layout.addWidget(miniapp_group)
        layout.addStretch()
        
        self._content_stack.addWidget(page)
    
    def _create_shortcuts_page(self):
        """创建快捷方式设置页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 快捷方式设置
        shortcuts_group = QGroupBox(self.tr("快捷方式设置"))
        shortcuts_layout = QFormLayout(shortcuts_group)
        
        # 全局快捷键
        global_shortcut = QLineEdit("Ctrl+Shift+Space")
        shortcuts_layout.addRow(self.tr("唤起应用:"), global_shortcut)
        
        layout.addWidget(shortcuts_group)
        layout.addStretch()
        
        self._content_stack.addWidget(page)
    
    def _create_quick_assistant_page(self):
        """创建快捷助手设置页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 快捷助手设置
        assistant_group = QGroupBox(self.tr("快捷助手设置"))
        assistant_layout = QFormLayout(assistant_group)
        
        # 启用快捷助手
        enable_assistant = QCheckBox(self.tr("启用快捷助手"))
        assistant_layout.addRow("", enable_assistant)
        
        layout.addWidget(assistant_group)
        layout.addStretch()
        
        self._content_stack.addWidget(page)
    
    def _create_select_assistant_page(self):
        """创建划到助手设置页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 划到助手设置
        select_group = QGroupBox(self.tr("划到助手设置"))
        select_layout = QFormLayout(select_group)
        
        # 启用划到助手
        enable_select = QCheckBox(self.tr("启用划到助手"))
        select_layout.addRow("", enable_select)
        
        layout.addWidget(select_group)
        layout.addStretch()
        
        self._content_stack.addWidget(page)
    
    def _create_quick_range_page(self):
        """创建快捷范围设置页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 快捷范围设置
        range_group = QGroupBox(self.tr("快捷范围设置"))
        range_layout = QFormLayout(range_group)
        
        # 默认范围
        default_range = QComboBox()
        default_range.addItems([self.tr("所有应用"), self.tr("指定应用")])
        range_layout.addRow(self.tr("默认范围:"), default_range)
        
        layout.addWidget(range_group)
        layout.addStretch()
        
        self._content_stack.addWidget(page)
    
    def _create_data_settings_page(self):
        """创建数据设置页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 数据设置
        data_group = QGroupBox(self.tr("数据设置"))
        data_layout = QFormLayout(data_group)
        
        # 数据存储位置
        data_location = QLineEdit()
        data_location.setReadOnly(True)
        browse_button = QPushButton(self.tr("浏览"))
        
        location_container = QWidget()
        location_layout = QHBoxLayout(location_container)
        location_layout.setContentsMargins(0, 0, 0, 0)
        location_layout.addWidget(data_location)
        location_layout.addWidget(browse_button)
        
        data_layout.addRow(self.tr("数据存储位置:"), location_container)
        
        # 清除数据
        clear_button = QPushButton(self.tr("清除所有数据"))
        clear_button.setObjectName("danger_button")
        data_layout.addRow("", clear_button)
        
        layout.addWidget(data_group)
        layout.addStretch()
        
        self._content_stack.addWidget(page)
    
    def _create_about_page(self):
        """创建关于我们页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 关于信息
        about_group = QGroupBox(self.tr("关于BerryLLM Studio"))
        about_layout = QVBoxLayout(about_group)
        
        # 应用信息
        app_info = QLabel(self.tr(
            "<h3>BerryLLM Studio</h3>"
            "<p>版本: 1.0.0</p>"
            "<p>一个简单易用的大语言模型聊天应用</p>"
            "<p>支持多种LLM提供商</p>"
        ))
        app_info.setTextFormat(Qt.RichText)
        app_info.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(app_info)
        
        layout.addWidget(about_group)
        layout.addStretch()
        
        self._content_stack.addWidget(page)
    
    def _on_menu_changed(self, index):
        """菜单切换处理"""
        self._content_stack.setCurrentIndex(index)
        self._title_label.setText(self._menu_list.item(index).text())
    
    def _on_platform_selected(self, platform_name):
        """平台选择处理"""
        # 更新API设置
        if platform_name == "硅基流动":
            self._api_url1.setText("https://api.siliconflow.cn")
            self._api_url2.setText("https://api.siliconflow.cn/v1/chat/completions")
            self._model_binding_input.setText("deepseek-ai/DeepSeek-R1")
        elif platform_name == "OpenAI":
            self._api_url1.setText("https://api.openai.com")
            self._api_url2.setText("https://api.openai.com/v1/chat/completions")
            self._model_binding_input.setText("gpt-4")
        # 其他平台可以根据需要添加
    
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
        # 这里会连接各种设置控件的信号到相应的处理函数
        # 每当设置变化时，调用_save_settings()来实时保存
        pass
    
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