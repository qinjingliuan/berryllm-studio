#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QWidget, QDialog, QVBoxLayout, QFormLayout, 
                              QLineEdit, QComboBox, QGroupBox, QCheckBox, 
                              QSpinBox, QDoubleSpinBox, QPushButton, QTabWidget,
                              QDialogButtonBox, QLabel, QHBoxLayout)
from PySide6.QtCore import Qt, Signal, Slot, QSettings


class SettingsDialog(QDialog):
    """设置对话框"""
    
    # 信号
    settings_applied = Signal()
    
    def __init__(self, parent=None):
        """初始化设置对话框"""
        super().__init__(parent)
        
        self.setWindowTitle(self.tr("设置"))
        self.resize(500, 400)
        
        # 创建界面
        self._setup_ui()
        
        # 加载设置
        self._load_settings()
    
    def _setup_ui(self):
        """设置用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 创建标签页
        self._tab_widget = QTabWidget()
        
        # 创建各个设置页
        self._create_general_tab()
        self._create_api_tab()
        self._create_advanced_tab()
        self._create_about_tab()
        
        # 创建按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        
        # 添加到主布局
        main_layout.addWidget(self._tab_widget)
        main_layout.addWidget(button_box)
    
    def _create_general_tab(self):
        """创建常规设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 界面设置
        ui_group = QGroupBox(self.tr("界面设置"))
        ui_layout = QFormLayout(ui_group)
        
        # 语言选择
        self._language_combo = QComboBox()
        self._language_combo.addItem(self.tr("系统默认"), "system")
        self._language_combo.addItem(self.tr("简体中文"), "zh_CN")
        self._language_combo.addItem(self.tr("English"), "en_US")
        ui_layout.addRow(self.tr("语言:"), self._language_combo)
        
        # 添加到布局
        layout.addWidget(ui_group)
        layout.addStretch()
        
        # 添加标签页
        self._tab_widget.addTab(tab, self.tr("常规"))
    
    def _create_api_tab(self):
        """创建API设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 提供商选择
        provider_group = QGroupBox(self.tr("LLM提供商"))
        provider_layout = QFormLayout(provider_group)
        
        self._provider_combo = QComboBox()
        self._provider_combo.addItem("OpenAI", "openai")
        self._provider_combo.addItem("Anthropic", "anthropic")
        self._provider_combo.addItem("DeepSeek", "deepseek")
        self._provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_layout.addRow(self.tr("提供商:"), self._provider_combo)
        
        # OpenAI设置
        self._openai_group = QGroupBox("OpenAI")
        openai_layout = QFormLayout(self._openai_group)
        
        self._openai_api_url = QLineEdit()
        self._openai_api_key = QLineEdit()
        self._openai_api_key.setEchoMode(QLineEdit.Password)
        self._openai_model = QComboBox()
        self._openai_model.addItems(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
        
        openai_layout.addRow(self.tr("API URL:"), self._openai_api_url)
        openai_layout.addRow(self.tr("API Key:"), self._openai_api_key)
        openai_layout.addRow(self.tr("模型:"), self._openai_model)
        
        # Anthropic设置
        self._anthropic_group = QGroupBox("Anthropic")
        anthropic_layout = QFormLayout(self._anthropic_group)
        
        self._anthropic_api_url = QLineEdit()
        self._anthropic_api_key = QLineEdit()
        self._anthropic_api_key.setEchoMode(QLineEdit.Password)
        self._anthropic_model = QComboBox()
        self._anthropic_model.addItems(["claude-2", "claude-instant-1", "claude-3-opus", "claude-3-sonnet"])
        
        anthropic_layout.addRow(self.tr("API URL:"), self._anthropic_api_url)
        anthropic_layout.addRow(self.tr("API Key:"), self._anthropic_api_key)
        anthropic_layout.addRow(self.tr("模型:"), self._anthropic_model)
        
        # DeepSeek设置
        self._deepseek_group = QGroupBox("DeepSeek")
        deepseek_layout = QFormLayout(self._deepseek_group)
        
        self._deepseek_api_url = QLineEdit()
        self._deepseek_api_key = QLineEdit()
        self._deepseek_api_key.setEchoMode(QLineEdit.Password)
        self._deepseek_model = QComboBox()
        self._deepseek_model.addItems(["deepseek-chat", "deepseek-coder"])
        
        deepseek_layout.addRow(self.tr("API URL:"), self._deepseek_api_url)
        deepseek_layout.addRow(self.tr("API Key:"), self._deepseek_api_key)
        deepseek_layout.addRow(self.tr("模型:"), self._deepseek_model)
        
        # 添加到布局
        layout.addWidget(provider_group)
        layout.addWidget(self._openai_group)
        layout.addWidget(self._anthropic_group)
        layout.addWidget(self._deepseek_group)
        
        # 添加标签页
        self._tab_widget.addTab(tab, self.tr("API"))
    
    def _create_advanced_tab(self):
        """创建高级设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # LLM设置
        llm_group = QGroupBox(self.tr("LLM设置"))
        llm_layout = QFormLayout(llm_group)
        
        self._streaming_check = QCheckBox(self.tr("启用流式响应"))
        llm_layout.addRow("", self._streaming_check)
        
        self._max_tokens_spin = QSpinBox()
        self._max_tokens_spin.setRange(16, 8192)
        self._max_tokens_spin.setSingleStep(16)
        self._max_tokens_spin.setValue(2048)
        llm_layout.addRow(self.tr("最大Token数:"), self._max_tokens_spin)
        
        self._temperature_spin = QDoubleSpinBox()
        self._temperature_spin.setRange(0.0, 2.0)
        self._temperature_spin.setSingleStep(0.1)
        self._temperature_spin.setValue(0.7)
        llm_layout.addRow(self.tr("温度:"), self._temperature_spin)
        
        self._max_history_spin = QSpinBox()
        self._max_history_spin.setRange(1, 50)
        self._max_history_spin.setValue(10)
        llm_layout.addRow(self.tr("最大历史消息数:"), self._max_history_spin)
        
        # 上下文设置
        context_group = QGroupBox(self.tr("上下文设置"))
        context_layout = QFormLayout(context_group)
        
        self._auto_load_context = QCheckBox(self.tr("自动加载上次的上下文"))
        context_layout.addRow("", self._auto_load_context)
        
        # 添加到布局
        layout.addWidget(llm_group)
        layout.addWidget(context_group)
        layout.addStretch()
        
        # 添加标签页
        self._tab_widget.addTab(tab, self.tr("高级"))
    
    def _create_about_tab(self):
        """创建关于标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 应用信息
        about_label = QLabel(self.tr(
            "<h3>BerryLLM Studio</h3>"
            "<p>版本: 1.0.0</p>"
            "<p>一个简单易用的大语言模型聊天应用</p>"
            "<p>支持多种LLM提供商</p>"
        ))
        about_label.setAlignment(Qt.AlignCenter)
        about_label.setTextFormat(Qt.RichText)
        
        # 添加到布局
        layout.addWidget(about_label)
        layout.addStretch()
        
        # 添加标签页
        self._tab_widget.addTab(tab, self.tr("关于"))
    
    def _load_settings(self):
        """加载设置"""
        settings = QSettings()
        
        # 加载常规设置
        language = settings.value("UI/Language", "system")
        index = self._language_combo.findData(language)
        if index >= 0:
            self._language_combo.setCurrentIndex(index)
        
        # 加载API设置
        provider = settings.value("LLM/Provider", "openai")
        index = self._provider_combo.findData(provider)
        if index >= 0:
            self._provider_combo.setCurrentIndex(index)
        
        # OpenAI设置
        self._openai_api_url.setText(settings.value("LLM/openai/ApiUrl", "https://api.openai.com/v1/chat/completions"))
        self._openai_api_key.setText(settings.value("LLM/openai/ApiKey", ""))
        openai_model = settings.value("LLM/OpenAI/Model", "gpt-3.5-turbo")
        index = self._openai_model.findText(openai_model)
        if index >= 0:
            self._openai_model.setCurrentIndex(index)
        
        # Anthropic设置
        self._anthropic_api_url.setText(settings.value("LLM/anthropic/ApiUrl", "https://api.anthropic.com/v1/messages"))
        self._anthropic_api_key.setText(settings.value("LLM/anthropic/ApiKey", ""))
        anthropic_model = settings.value("LLM/Anthropic/Model", "claude-2")
        index = self._anthropic_model.findText(anthropic_model)
        if index >= 0:
            self._anthropic_model.setCurrentIndex(index)
        
        # DeepSeek设置
        self._deepseek_api_url.setText(settings.value("LLM/deepseek/ApiUrl", "https://api.deepseek.com/v1/chat/completions"))
        self._deepseek_api_key.setText(settings.value("LLM/deepseek/ApiKey", ""))
        deepseek_model = settings.value("LLM/DeepSeek/Model", "deepseek-chat")
        index = self._deepseek_model.findText(deepseek_model)
        if index >= 0:
            self._deepseek_model.setCurrentIndex(index)
        
        # 加载高级设置
        self._streaming_check.setChecked(settings.value("LLM/EnableStreaming", True, bool))
        self._max_tokens_spin.setValue(settings.value("LLM/MaxTokens", 2048, int))
        self._temperature_spin.setValue(settings.value("LLM/Temperature", 0.7, float))
        self._max_history_spin.setValue(settings.value("LLM/MaxHistoryMessages", 10, int))
        self._auto_load_context.setChecked(settings.value("Context/AutoLoadLastContext", False, bool))
        
        # 更新UI状态
        self._update_provider_ui()
    
    def _save_settings(self):
        """保存设置"""
        settings = QSettings()
        
        # 保存常规设置
        settings.setValue("UI/Language", self._language_combo.currentData())
        
        # 保存API设置
        settings.setValue("LLM/Provider", self._provider_combo.currentData())
        
        # OpenAI设置
        settings.setValue("LLM/openai/ApiUrl", self._openai_api_url.text())
        settings.setValue("LLM/openai/ApiKey", self._openai_api_key.text())
        settings.setValue("LLM/OpenAI/Model", self._openai_model.currentText())
        
        # Anthropic设置
        settings.setValue("LLM/anthropic/ApiUrl", self._anthropic_api_url.text())
        settings.setValue("LLM/anthropic/ApiKey", self._anthropic_api_key.text())
        settings.setValue("LLM/Anthropic/Model", self._anthropic_model.currentText())
        
        # DeepSeek设置
        settings.setValue("LLM/deepseek/ApiUrl", self._deepseek_api_url.text())
        settings.setValue("LLM/deepseek/ApiKey", self._deepseek_api_key.text())
        settings.setValue("LLM/DeepSeek/Model", self._deepseek_model.currentText())
        
        # 保存高级设置
        settings.setValue("LLM/EnableStreaming", self._streaming_check.isChecked())
        settings.setValue("LLM/MaxTokens", self._max_tokens_spin.value())
        settings.setValue("LLM/Temperature", self._temperature_spin.value())
        settings.setValue("LLM/MaxHistoryMessages", self._max_history_spin.value())
        settings.setValue("Context/AutoLoadLastContext", self._auto_load_context.isChecked())
    
    @Slot(int)
    def _on_provider_changed(self, index):
        """提供商变更处理"""
        self._update_provider_ui()
    
    def _update_provider_ui(self):
        """更新提供商UI"""
        current_provider = self._provider_combo.currentData()
        
        self._openai_group.setVisible(current_provider == "openai")
        self._anthropic_group.setVisible(current_provider == "anthropic")
        self._deepseek_group.setVisible(current_provider == "deepseek")
    
    @Slot()
    def _on_accept(self):
        """确认按钮处理"""
        self._save_settings()
        self.settings_applied.emit()
        self.accept() 