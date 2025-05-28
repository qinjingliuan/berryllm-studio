#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QWidget, QTextEdit, QLineEdit, QPushButton,
                              QVBoxLayout, QHBoxLayout, QMenu, QScrollBar, QMessageBox)
from PySide6.QtCore import Qt, Signal, Slot, QDateTime
from PySide6.QtGui import QAction, QTextCursor


class ChatView(QWidget):
    """聊天视图组件,用于显示用户和AI助手的对话"""
    
    # 信号
    user_message_sent = Signal(str, str)  # 会话ID, 用户消息
    
    def __init__(self, parent=None, session_id=None):
        """初始化聊天视图"""
        super().__init__(parent)
        self._is_streaming = False
        self._session_id = session_id
        self._setup_ui()
        self._connect_signals()
    
    def set_session_id(self, session_id):
        """设置会话ID"""
        self._session_id = session_id
    
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
    
    def save_chat(self, file_path):
        """保存聊天记录
        
        Args:
            file_path: 文件路径
        """
        try:
            if file_path.endswith(".html"):
                # 保存为HTML
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self._chat_display.toHtml())
            else:
                # 保存为纯文本
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self._chat_display.toPlainText())
            
            # 显示成功消息
            QMessageBox.information(
                self,
                self.tr("成功"),
                self.tr("聊天记录已保存")
            )
        
        except Exception as e:
            # 显示错误消息
            QMessageBox.critical(
                self,
                self.tr("错误"),
                self.tr("保存聊天记录失败: {}").format(str(e))
            )
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 获取LLM服务
        main_window = self.parent()
        if main_window and hasattr(main_window, "_llm_service"):
            llm_service = main_window._llm_service
            
            # 连接LLM服务信号
            llm_service.response_started.connect(self._on_response_started)
            llm_service.response_chunk.connect(self._on_response_chunk)
            llm_service.response_finished.connect(self._on_response_finished)
            llm_service.error_occurred.connect(self._on_error_occurred)
    
    @Slot()
    def _on_send_button_clicked(self):
        """发送按钮点击处理"""
        message = self._input_field.text().strip()
        if not message or not self._session_id:
            return
        
        # 添加用户消息到聊天窗口
        self.append_user_message(message)
        
        # 发送消息信号
        self.user_message_sent.emit(self._session_id, message)
        
        # 发送消息到LLM服务
        main_window = self.parent()
        if main_window and hasattr(main_window, "_llm_service"):
            main_window._llm_service.send_message(self._session_id, message)
        
        # 清空输入框
        self._input_field.clear()
    
    @Slot()
    def _on_input_return_pressed(self):
        """输入框回车键处理"""
        self._on_send_button_clicked()
    
    @Slot()
    def _on_clear_button_clicked(self):
        """清除按钮点击处理"""
        # 创建确认对话框
        reply = QMessageBox.question(
            self,
            self.tr("确认"),
            self.tr("确定要清除所有聊天记录吗?"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.clear_chat()
            
            # 清除LLM服务中的对话历史
            main_window = self.parent()
            if main_window and hasattr(main_window, "_llm_service") and self._session_id:
                main_window._llm_service.clear_conversation_history(self._session_id)
    
    @Slot(str)
    def _on_response_started(self, session_id):
        """响应开始处理"""
        if session_id != self._session_id:
            return
        
        # 禁用发送按钮
        self._send_button.setEnabled(False)
    
    @Slot(str, str)
    def _on_response_chunk(self, session_id, content):
        """响应块处理"""
        if session_id != self._session_id:
            return
        
        # 添加流式内容
        self.append_streaming_content(content)
    
    @Slot(str)
    def _on_response_finished(self, session_id):
        """响应完成处理"""
        if session_id != self._session_id:
            return
        
        # 启用发送按钮
        self._send_button.setEnabled(True)
        
        # 重置流式状态
        self._is_streaming = False
    
    @Slot(str, str)
    def _on_error_occurred(self, session_id, error_message):
        """错误处理"""
        if session_id != self._session_id:
            return
        
        # 显示错误消息
        self.append_assistant_message(f"错误: {error_message}")
        
        # 启用发送按钮
        self._send_button.setEnabled(True)
    
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