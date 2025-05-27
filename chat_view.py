#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QWidget, QTextEdit, QLineEdit, QPushButton,
                              QVBoxLayout, QHBoxLayout, QMenu, QScrollBar)
from PySide6.QtCore import Qt, Signal, Slot, QDateTime
from PySide6.QtGui import QAction, QTextCursor


class ChatView(QWidget):
    """聊天视图组件,用于显示用户和AI助手的对话"""
    
    # 信号
    user_message_sent = Signal(str)
    
    def __init__(self, parent=None):
        """初始化聊天视图"""
        super().__init__(parent)
        self._is_streaming = False
        self._setup_ui()
    
    def append_user_message(self, message):
        """添加用户消息到聊天窗口"""
        self._chat_display.append(self._format_user_message(message))
        self._chat_display.verticalScrollBar().setValue(
            self._chat_display.verticalScrollBar().maximum()
        )
    
    def append_assistant_message(self, message):
        """添加助手消息到聊天窗口"""
        self._is_streaming = False
        self._chat_display.append(self._format_assistant_message(message))
        self._chat_display.verticalScrollBar().setValue(
            self._chat_display.verticalScrollBar().maximum()
        )
    
    def append_streaming_content(self, content):
        """添加流式内容到聊天窗口"""
        if not self._is_streaming:
            # 开始新的流式响应
            self._is_streaming = True
            self._chat_display.append(self._format_assistant_message(""))
        
        # 获取当前文本
        cursor = self._chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(content)
        
        # 滚动到底部
        self._chat_display.verticalScrollBar().setValue(
            self._chat_display.verticalScrollBar().maximum()
        )
    
    def clear_chat(self):
        """清空聊天内容"""
        self._chat_display.clear()
        self._is_streaming = False
    
    @Slot()
    def _on_send_button_clicked(self):
        """发送按钮点击处理"""
        message = self._input_field.text().strip()
        if not message:
            return
        
        # 添加用户消息到聊天窗口
        self.append_user_message(message)
        
        # 发送消息信号
        self.user_message_sent.emit(message)
        
        # 清空输入框
        self._input_field.clear()
    
    @Slot()
    def _on_input_return_pressed(self):
        """输入框回车键处理"""
        self._on_send_button_clicked()
    
    @Slot()
    def _on_clear_button_clicked(self):
        """清除按钮点击处理"""
        self.clear_chat()
    
    def _setup_ui(self):
        """设置用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建聊天显示区域
        self._chat_display = QTextEdit(self)
        self._chat_display.setReadOnly(True)
        self._chat_display.setContextMenuPolicy(Qt.CustomContextMenu)
        self._chat_display.customContextMenuRequested.connect(self._show_context_menu)
        
        # 创建输入区域
        input_widget = QWidget(self)
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        self._input_field = QLineEdit(input_widget)
        self._input_field.setPlaceholderText(self.tr("输入消息..."))
        self._input_field.returnPressed.connect(self._on_input_return_pressed)
        
        self._send_button = QPushButton(self.tr("发送"), input_widget)
        self._send_button.clicked.connect(self._on_send_button_clicked)
        
        self._clear_button = QPushButton(self.tr("清除"), input_widget)
        self._clear_button.clicked.connect(self._on_clear_button_clicked)
        
        input_layout.addWidget(self._input_field)
        input_layout.addWidget(self._send_button)
        input_layout.addWidget(self._clear_button)
        
        # 添加到主布局
        main_layout.addWidget(self._chat_display)
        main_layout.addWidget(input_widget)
        
        # 设置初始大小
        self.setMinimumSize(400, 300)
    
    def _show_context_menu(self, pos):
        """显示上下文菜单"""
        menu = self._chat_display.createStandardContextMenu()
        menu.addSeparator()
        clear_action = QAction(self.tr("清除聊天"), self)
        clear_action.triggered.connect(self.clear_chat)
        menu.addAction(clear_action)
        menu.exec(self._chat_display.mapToGlobal(pos))
    
    def _format_user_message(self, message):
        """格式化用户消息"""
        now = QDateTime.currentDateTime()
        timestamp = now.toString("HH:mm:ss")
        
        return f"<p style='margin-top:10px;'><b>{self.tr('用户')} [{timestamp}]:</b><br>{message}</p>"
    
    def _format_assistant_message(self, message):
        """格式化助手消息"""
        now = QDateTime.currentDateTime()
        timestamp = now.toString("HH:mm:ss")
        
        return f"<p style='margin-top:10px;'><b>{self.tr('AI助手')} [{timestamp}]:</b><br>{message}</p>" 