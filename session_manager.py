#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtCore import QObject, Signal, Slot, QSettings, Qt, QDateTime, QSize
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                              QPushButton, QMenu, QInputDialog, QMessageBox, 
                              QDialog, QFormLayout, QComboBox, QLineEdit, QDialogButtonBox,
                              QLabel, QHBoxLayout)
from PySide6.QtGui import QIcon

class AddSessionDialog(QDialog):
    """添加会话对话框"""
    
    def __init__(self, parent=None):
        """初始化添加会话对话框"""
        super().__init__(parent)
        
        self.setWindowTitle(self.tr("添加会话"))
        self.resize(400, 200)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 创建表单
        form_layout = QFormLayout()
        
        # 会话名称
        self.name_edit = QLineEdit()
        form_layout.addRow(self.tr("会话名称:"), self.name_edit)
        
        # 提供商选择
        self.provider_combo = QComboBox()
        self.provider_combo.addItem("OpenAI", "openai")
        self.provider_combo.addItem("Anthropic", "anthropic")
        self.provider_combo.addItem("DeepSeek", "deepseek")
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        form_layout.addRow(self.tr("提供商:"), self.provider_combo)
        
        # 模型选择
        self.model_combo = QComboBox()
        form_layout.addRow(self.tr("模型:"), self.model_combo)
        
        # 初始化模型列表
        self._update_model_list("openai")
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # 添加到主布局
        layout.addLayout(form_layout)
        layout.addWidget(button_box)
    
    @Slot(int)
    def _on_provider_changed(self, index):
        """提供商变更处理"""
        provider_id = self.provider_combo.currentData()
        self._update_model_list(provider_id)
    
    def _update_model_list(self, provider_id):
        """更新模型列表"""
        self.model_combo.clear()
        
        if provider_id == "openai":
            self.model_combo.addItems(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
        elif provider_id == "anthropic":
            self.model_combo.addItems(["claude-2", "claude-instant-1", "claude-3-opus", "claude-3-sonnet"])
        elif provider_id == "deepseek":
            self.model_combo.addItems(["deepseek-chat", "deepseek-coder"])
    
    def get_session_info(self):
        """获取会话信息"""
        return {
            "name": self.name_edit.text().strip(),
            "provider_id": self.provider_combo.currentData(),
            "model_id": self.model_combo.currentText()
        }

class SessionManager(QObject):
    """会话管理类，负责管理多个聊天会话"""
    
    # 信号
    session_added = Signal(str, str)  # 会话ID, 会话名称
    session_removed = Signal(str)  # 会话ID
    session_selected = Signal(str)  # 会话ID
    
    def __init__(self, parent=None):
        """初始化会话管理器"""
        super().__init__(parent)
        
        # 会话列表
        self._sessions = {}  # 会话ID -> 会话信息
        self._current_session_id = None
        
        # 加载会话
        self._load_sessions()
    
    def create_session_widget(self, parent=None):
        """创建会话列表部件
        
        Args:
            parent: 父部件
            
        Returns:
            QWidget: 会话列表部件
        """
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 创建会话管理标题
        title_label = QLabel(self.tr("会话管理"), widget)
        title_label.setObjectName("session_title")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 创建会话列表
        self._session_list = QListWidget(widget)
        self._session_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._session_list.customContextMenuRequested.connect(self._show_context_menu)
        self._session_list.itemClicked.connect(self._on_session_selected)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        # 创建添加会话按钮
        add_button = QPushButton("", widget)
        add_button.setObjectName("icon_button")
        add_button.setToolTip(self.tr("添加会话"))
        add_button.setIcon(QIcon(":/resources/images/add.png"))
        add_button.setIconSize(QSize(20, 20))
        add_button.clicked.connect(self._on_add_session)
        button_layout.addWidget(add_button)
        
        # 添加到布局
        layout.addWidget(self._session_list)
        layout.addLayout(button_layout)
        
        # 更新会话列表
        self._update_session_list()
        
        return widget
    
    def add_session(self, name, provider_id, model_id):
        """添加新会话
        
        Args:
            name: 会话名称
            provider_id: 提供商ID
            model_id: 模型ID
            
        Returns:
            str: 会话ID
        """
        import uuid
        session_id = str(uuid.uuid4())
        
        # 创建会话信息
        session_info = {
            "name": name,
            "provider_id": provider_id,
            "model_id": model_id,
            "created_at": QDateTime.currentDateTime().toString()
        }
        
        # 添加到会话列表
        self._sessions[session_id] = session_info
        
        # 保存会话
        self._save_sessions()
        
        # 发送信号
        self.session_added.emit(session_id, name)
        
        # 更新会话列表
        self._update_session_list()
        
        return session_id
    
    def copy_session(self, session_id):
        """复制会话
        
        Args:
            session_id: 要复制的会话ID
            
        Returns:
            str: 新会话ID
        """
        session_info = self._sessions.get(session_id)
        if not session_info:
            return None
        
        # 创建新会话名称
        new_name = f"{session_info['name']} (复制)"
        
        # 添加新会话
        return self.add_session(
            new_name,
            session_info["provider_id"],
            session_info["model_id"]
        )
    
    def remove_session(self, session_id):
        """删除会话
        
        Args:
            session_id: 会话ID
        """
        if session_id in self._sessions:
            # 从会话列表中删除
            del self._sessions[session_id]
            
            # 保存会话
            self._save_sessions()
            
            # 发送信号
            self.session_removed.emit(session_id)
            
            # 更新会话列表
            self._update_session_list()
    
    def get_session(self, session_id):
        """获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            dict: 会话信息
        """
        return self._sessions.get(session_id)
    
    def get_current_session_id(self):
        """获取当前会话ID
        
        Returns:
            str: 当前会话ID
        """
        return self._current_session_id
    
    def set_current_session(self, session_id):
        """设置当前会话
        
        Args:
            session_id: 会话ID
        """
        if session_id in self._sessions:
            self._current_session_id = session_id
            self.session_selected.emit(session_id)
    
    def get_all_sessions(self):
        """获取所有会话
        
        Returns:
            dict: 所有会话信息
        """
        return self._sessions
    
    def _load_sessions(self):
        """加载会话"""
        settings = QSettings()
        sessions_data = settings.value("Sessions/Data", "{}")
        
        try:
            import json
            self._sessions = json.loads(sessions_data)
        except:
            self._sessions = {}
    
    def _save_sessions(self):
        """保存会话"""
        settings = QSettings()
        import json
        settings.setValue("Sessions/Data", json.dumps(self._sessions))
    
    def _update_session_list(self):
        """更新会话列表"""
        self._session_list.clear()
        
        for session_id, session_info in self._sessions.items():
            item = QListWidgetItem(session_info["name"])
            item.setData(Qt.UserRole, session_id)
            self._session_list.addItem(item)
    
    @Slot()
    def _on_add_session(self):
        """添加会话按钮点击处理"""
        dialog = AddSessionDialog(self._session_list)
        
        if dialog.exec() == QDialog.Accepted:
            session_info = dialog.get_session_info()
            if session_info["name"]:
                # 创建新会话
                self.add_session(
                    session_info["name"],
                    session_info["provider_id"],
                    session_info["model_id"]
                )
    
    @Slot(QListWidgetItem)
    def _on_session_selected(self, item):
        """会话选择处理"""
        session_id = item.data(Qt.UserRole)
        self.set_current_session(session_id)
    
    @Slot()
    def _show_context_menu(self, pos):
        """显示上下文菜单"""
        item = self._session_list.itemAt(pos)
        if not item:
            return
        
        session_id = item.data(Qt.UserRole)
        
        menu = QMenu(self._session_list)
        
        # 重命名会话
        rename_action = menu.addAction(self.tr("重命名"))
        rename_action.triggered.connect(lambda: self._rename_session(session_id))
        
        # 复制会话
        copy_action = menu.addAction(self.tr("复制"))
        copy_action.triggered.connect(lambda: self.copy_session(session_id))
        
        # 删除会话
        delete_action = menu.addAction(self.tr("删除"))
        delete_action.triggered.connect(lambda: self._confirm_delete_session(session_id))
        
        menu.exec(self._session_list.mapToGlobal(pos))
    
    def _rename_session(self, session_id):
        """重命名会话
        
        Args:
            session_id: 会话ID
        """
        session_info = self._sessions.get(session_id)
        if not session_info:
            return
        
        # 创建重命名对话框
        dialog = QInputDialog(self._session_list)
        dialog.setWindowTitle(self.tr("重命名会话"))
        dialog.setLabelText(self.tr("请输入新名称:"))
        dialog.setTextValue(session_info["name"])
        
        if dialog.exec() == QInputDialog.Accepted:
            new_name = dialog.textValue().strip()
            if new_name:
                # 更新会话名称
                session_info["name"] = new_name
                
                # 保存会话
                self._save_sessions()
                
                # 更新会话列表
                self._update_session_list()
    
    def _confirm_delete_session(self, session_id):
        """确认删除会话
        
        Args:
            session_id: 会话ID
        """
        session_info = self._sessions.get(session_id)
        if not session_info:
            return
        
        # 创建确认对话框
        reply = QMessageBox.question(
            self._session_list,
            self.tr("确认删除"),
            self.tr(f"确定要删除会话 '{session_info['name']}' 吗？"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.remove_session(session_id) 