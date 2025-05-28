#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
from PySide6.QtCore import QObject, Signal, Slot, QSettings, QByteArray, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply, QSsl, QSslConfiguration


class LlmService(QObject):
    """LLM服务类,负责与AI提供商的API通信"""
    
    # 信号
    response_started = Signal(str)  # 会话ID
    response_chunk = Signal(str, str)  # 会话ID, 响应块
    response_finished = Signal(str)  # 会话ID
    error_occurred = Signal(str, str)  # 会话ID, 错误信息
    all_requests_finished = Signal()
    connection_test_result = Signal(bool, str)
    
    def __init__(self, parent=None):
        """初始化LLM服务"""
        super().__init__(parent)
        
        # 初始化网络管理器
        self._network_manager = QNetworkAccessManager(self)
        self._current_reply = None
        self._current_provider = "openai"  # 默认使用OpenAI
        
        # 缓存响应数据
        self._response_buffer = QByteArray()
        
        # 活跃请求计数
        self._active_requests = 0
        
        # 会话历史
        self._conversation_histories = {}  # 会话ID -> 对话历史
        
        # 当前活跃会话的请求
        self._active_session_replies = {}  # 会话ID -> QNetworkReply
        
        # 初始化SSL配置
        self._ssl_config = QSslConfiguration.defaultConfiguration()
        self._ssl_config.setProtocol(QSsl.TlsV1_2OrLater)
        
        # 加载设置
        self._load_settings()
    
    def send_message(self, session_id, message, context=None):
        """发送消息到LLM
        
        Args:
            session_id: 会话ID
            message: 用户消息
            context: 上下文信息,可选
        """
        if context is None:
            context = {}
        
        # 取消任何活跃的请求
        self.cancel_request(session_id)
        
        # 获取会话信息
        session_info = self._get_session_info(session_id)
        if not session_info:
            self.error_occurred.emit(session_id, "会话不存在")
            return
        
        # 获取API URL
        provider_api_url = self.get_provider_api_url(session_info["provider_id"])
        if not provider_api_url:
            self.error_occurred.emit(session_id, "API URL未配置")
            return
        
        # 验证URL格式
        if not self._validate_url(provider_api_url):
            self.error_occurred.emit(session_id, f"API URL格式无效: {provider_api_url}")
            return
        
        # 检查API密钥
        settings = QSettings()
        api_key = settings.value(f"LLM/{session_info['provider_id']}/ApiKey", "")
        if not api_key:
            self.error_occurred.emit(session_id, f"{session_info['provider_id']} API密钥未配置")
            return
        
        # 创建请求
        request = self._create_request(provider_api_url, session_info["provider_id"], api_key)
        
        # 构建请求体
        request_body = self._build_request_body(session_info["provider_id"], session_info["model_id"], message, context)
        
        # 存储对话历史
        self._store_conversation_history(session_id, "user", message)
        
        # 发送请求
        self._active_requests += 1
        reply = self._network_manager.post(request, request_body)
        
        # 存储会话ID
        reply.setProperty("session_id", session_id)
        
        # 保存到活跃会话请求
        self._active_session_replies[session_id] = reply
        
        # 连接信号
        reply.finished.connect(self._on_network_reply_finished)
        reply.readyRead.connect(self._on_network_reply_ready_read)
        reply.errorOccurred.connect(self._on_network_reply_error)
        
        # 发送开始响应信号
        self.response_started.emit(session_id)
    
    def cancel_request(self, session_id):
        """取消当前请求
        
        Args:
            session_id: 会话ID
        """
        if session_id in self._active_session_replies:
            reply = self._active_session_replies[session_id]
            if reply and reply.isRunning():
                reply.abort()
            del self._active_session_replies[session_id]
    
    def has_active_requests(self):
        """检查是否有活跃请求"""
        return self._active_requests > 0
    
    def set_provider(self, provider_id):
        """设置当前使用的提供商"""
        self._current_provider = provider_id
    
    def available_providers(self):
        """获取支持的提供商列表"""
        return ["openai", "anthropic", "deepseek"]
    
    def get_provider_api_url(self, provider_id):
        """获取提供商API URL"""
        settings = QSettings()
        
        # 获取默认URL
        default_urls = {
            "openai": "https://api.openai.com/v1/chat/completions",
            "anthropic": "https://api.anthropic.com/v1/messages",
            "deepseek": "https://api.deepseek.com/v1/chat/completions"
        }
        
        # 从设置中获取URL,如果没有则使用默认值
        return settings.value(f"LLM/{provider_id}/ApiUrl", default_urls.get(provider_id, ""))
    
    def set_provider_api_url(self, provider_id, url):
        """设置提供商API URL"""
        settings = QSettings()
        settings.setValue(f"LLM/{provider_id}/ApiUrl", url)
    
    def test_connection(self, provider_id=None):
        """测试与API提供商的连接
        
        Args:
            provider_id: 提供商ID,如果为None则使用当前提供商
        """
        if provider_id is None:
            provider_id = self._current_provider
        
        # 获取API URL
        api_url = self.get_provider_api_url(provider_id)
        if not api_url:
            self.connection_test_result.emit(False, "API URL未配置")
            return
        
        # 验证URL格式
        if not self._validate_url(api_url):
            self.connection_test_result.emit(False, f"API URL格式无效: {api_url}")
            return
        
        # 创建请求
        request = QNetworkRequest(QUrl(api_url))
        
        # 设置SSL配置
        request.setSslConfiguration(self._ssl_config)
        
        # 设置API密钥
        settings = QSettings()
        api_key = settings.value(f"LLM/{provider_id}/ApiKey", "")
        
        if not api_key:
            self.connection_test_result.emit(False, f"{provider_id} API密钥未配置")
            return
        
        if provider_id == "openai":
            request.setRawHeader(b"Authorization", f"Bearer {api_key}".encode())
        elif provider_id == "anthropic":
            request.setRawHeader(b"x-api-key", api_key.encode())
            request.setRawHeader(b"anthropic-version", b"2023-06-01")
        elif provider_id == "deepseek":
            request.setRawHeader(b"Authorization", f"Bearer {api_key}".encode())
        
        # 发送HEAD请求测试连接
        reply = self._network_manager.head(request)
        reply.finished.connect(lambda: self._on_connection_test_finished(reply, provider_id))
    
    def _validate_url(self, url):
        """验证URL格式
        
        Args:
            url: URL字符串
            
        Returns:
            bool: URL是否有效
        """
        # 简单的URL格式验证
        pattern = r'^https?://[\w\-.]+(:\d+)?(/[\w\-.~!$&\'()*+,;=:@/%]*)?$'
        return bool(re.match(pattern, url))
    
    def clear_conversation_history(self, session_id):
        """清空对话历史
        
        Args:
            session_id: 会话ID
        """
        if session_id in self._conversation_histories:
            self._conversation_histories[session_id] = []
    
    def _load_settings(self):
        """加载设置"""
        settings = QSettings()
        provider = settings.value("LLM/Provider", "openai")
        self._current_provider = provider
    
    def _create_request(self, url, provider_id, api_key):
        """创建请求
        
        Args:
            url: API URL
            provider_id: 提供商ID
            api_key: API密钥
            
        Returns:
            QNetworkRequest: 网络请求对象
        """
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        
        # 设置SSL配置
        request.setSslConfiguration(self._ssl_config)
        
        if provider_id == "openai":
            request.setRawHeader(b"Authorization", f"Bearer {api_key}".encode())
        elif provider_id == "anthropic":
            request.setRawHeader(b"x-api-key", api_key.encode())
            request.setRawHeader(b"anthropic-version", b"2023-06-01")
        elif provider_id == "deepseek":
            request.setRawHeader(b"Authorization", f"Bearer {api_key}".encode())
        
        return request
    
    def _build_request_body(self, provider_id, model_id, message, context):
        """构建请求体
        
        Args:
            provider_id: 提供商ID
            model_id: 模型ID
            message: 用户消息
            context: 上下文信息
            
        Returns:
            bytes: 请求体数据
        """
        settings = QSettings()
        max_tokens = settings.value("LLM/MaxTokens", 2048, int)
        temperature = settings.value("LLM/Temperature", 0.7, float)
        
        # 构建请求体
        if provider_id == "openai":
            data = {
                "model": model_id,
                "messages": [
                    {"role": "user", "content": message}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True
            }
        elif provider_id == "anthropic":
            data = {
                "model": model_id,
                "messages": [
                    {"role": "user", "content": message}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True
            }
        elif provider_id == "deepseek":
            data = {
                "model": model_id,
                "messages": [
                    {"role": "user", "content": message}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True
            }
        else:
            # 默认使用OpenAI格式
            data = {
                "model": model_id,
                "messages": [
                    {"role": "user", "content": message}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True
            }
        
        # 转换为JSON字符串并编码为UTF-8
        return json.dumps(data).encode("utf-8")
    
    def _get_session_info(self, session_id):
        """获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            dict: 会话信息
        """
        # 从SessionManager获取会话信息
        parent = self.parent()
        if parent and hasattr(parent, "_session_manager"):
            session_manager = parent._session_manager
            return session_manager.get_session(session_id)
        return None
    
    def _store_conversation_history(self, session_id, role, content):
        """存储对话历史
        
        Args:
            session_id: 会话ID
            role: 角色(user/assistant)
            content: 内容
        """
        # 初始化会话历史
        if session_id not in self._conversation_histories:
            self._conversation_histories[session_id] = []
        
        # 添加消息
        self._conversation_histories[session_id].append({
            "role": role,
            "content": content
        })
        
        # 限制历史记录长度
        settings = QSettings()
        max_history = settings.value("LLM/MaxHistoryMessages", 10, int)
        
        if len(self._conversation_histories[session_id]) > max_history * 2:
            # 保留最新的历史记录
            self._conversation_histories[session_id] = self._conversation_histories[session_id][-max_history*2:]
    
    def _get_conversation_history(self, session_id):
        """获取对话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            list: 对话历史
        """
        return self._conversation_histories.get(session_id, [])
    
    @Slot()
    def _on_network_reply_finished(self):
        """网络响应完成处理"""
        reply = self.sender()
        if not reply:
            return
        
        # 获取会话ID
        session_id = reply.property("session_id")
        
        # 减少活跃请求计数
        self._active_requests -= 1
        
        # 从活跃会话请求中移除
        if session_id in self._active_session_replies:
            del self._active_session_replies[session_id]
        
        # 发送完成信号
        self.response_finished.emit(session_id)
        
        # 如果所有请求都完成了,发送信号
        if self._active_requests <= 0:
            self._active_requests = 0
            self.all_requests_finished.emit()
        
        # 释放资源
        reply.deleteLater()
    
    @Slot()
    def _on_network_reply_ready_read(self):
        """网络响应数据可读处理"""
        reply = self.sender()
        if not reply:
            return
        
        # 获取会话ID
        session_id = reply.property("session_id")
        
        # 读取数据
        data = reply.readAll()
        
        # 处理流式响应
        self._process_streaming_response(session_id, data)
    
    @Slot(QNetworkReply.NetworkError)
    def _on_network_reply_error(self, error):
        """网络错误处理
        
        Args:
            error: 错误码
        """
        reply = self.sender()
        if not reply:
            return
        
        # 获取会话ID
        session_id = reply.property("session_id")
        
        # 获取错误信息
        error_string = reply.errorString()
        
        # 发送错误信号
        self.error_occurred.emit(session_id, f"网络错误: {error_string}")
        
        # 减少活跃请求计数
        self._active_requests -= 1
        
        # 从活跃会话请求中移除
        if session_id in self._active_session_replies:
            del self._active_session_replies[session_id]
        
        # 如果所有请求都完成了,发送信号
        if self._active_requests <= 0:
            self._active_requests = 0
            self.all_requests_finished.emit()
    
    def _process_streaming_response(self, session_id, data):
        """处理流式响应
        
        Args:
            session_id: 会话ID
            data: 响应数据
        """
        # 将数据添加到缓冲区
        self._response_buffer.append(data)
        
        # 获取会话信息
        session_info = self._get_session_info(session_id)
        if not session_info:
            return
        
        provider_id = session_info["provider_id"]
        
        # 处理不同提供商的流式响应
        if provider_id == "openai":
            # 处理OpenAI流式响应
            buffer_str = self._response_buffer.data().decode("utf-8", errors="ignore")
            
            # 查找完整的数据行
            lines = buffer_str.split("\n")
            processed_lines = 0
            
            for line in lines:
                line = line.strip()
                if not line or line == "data: [DONE]":
                    processed_lines += 1
                    continue
                
                if line.startswith("data: "):
                    try:
                        # 解析JSON数据
                        json_str = line[6:]  # 去除"data: "前缀
                        data = json.loads(json_str)
                        
                        # 提取内容
                        if "choices" in data and len(data["choices"]) > 0:
                            choice = data["choices"][0]
                            if "delta" in choice and "content" in choice["delta"]:
                                content = choice["delta"]["content"]
                                
                                # 发送内容块
                                self.response_chunk.emit(session_id, content)
                                
                                # 存储助手回复
                                self._store_conversation_history(session_id, "assistant", content)
                        
                        processed_lines += 1
                    except json.JSONDecodeError:
                        # 不完整的JSON,等待更多数据
                        break
                else:
                    processed_lines += 1
            
            # 移除已处理的行
            if processed_lines > 0:
                remaining = "\n".join(lines[processed_lines:])
                self._response_buffer = QByteArray(remaining.encode("utf-8"))
        
        elif provider_id == "anthropic":
            # 处理Anthropic流式响应
            buffer_str = self._response_buffer.data().decode("utf-8", errors="ignore")
            
            # 查找完整的数据行
            lines = buffer_str.split("\n")
            processed_lines = 0
            
            for line in lines:
                line = line.strip()
                if not line or line == "data: [DONE]":
                    processed_lines += 1
                    continue
                
                if line.startswith("data: "):
                    try:
                        # 解析JSON数据
                        json_str = line[6:]  # 去除"data: "前缀
                        data = json.loads(json_str)
                        
                        # 提取内容
                        if "type" in data and data["type"] == "content_block_delta":
                            if "delta" in data and "text" in data["delta"]:
                                content = data["delta"]["text"]
                                
                                # 发送内容块
                                self.response_chunk.emit(session_id, content)
                                
                                # 存储助手回复
                                self._store_conversation_history(session_id, "assistant", content)
                        
                        processed_lines += 1
                    except json.JSONDecodeError:
                        # 不完整的JSON,等待更多数据
                        break
                else:
                    processed_lines += 1
            
            # 移除已处理的行
            if processed_lines > 0:
                remaining = "\n".join(lines[processed_lines:])
                self._response_buffer = QByteArray(remaining.encode("utf-8"))
        
        else:
            # 默认处理方式(类似OpenAI)
            buffer_str = self._response_buffer.data().decode("utf-8", errors="ignore")
            
            # 查找完整的数据行
            lines = buffer_str.split("\n")
            processed_lines = 0
            
            for line in lines:
                line = line.strip()
                if not line or line == "data: [DONE]":
                    processed_lines += 1
                    continue
                
                if line.startswith("data: "):
                    try:
                        # 解析JSON数据
                        json_str = line[6:]  # 去除"data: "前缀
                        data = json.loads(json_str)
                        
                        # 提取内容(通用格式)
                        if "choices" in data and len(data["choices"]) > 0:
                            choice = data["choices"][0]
                            if "delta" in choice and "content" in choice["delta"]:
                                content = choice["delta"]["content"]
                                
                                # 发送内容块
                                self.response_chunk.emit(session_id, content)
                                
                                # 存储助手回复
                                self._store_conversation_history(session_id, "assistant", content)
                        
                        processed_lines += 1
                    except json.JSONDecodeError:
                        # 不完整的JSON,等待更多数据
                        break
                else:
                    processed_lines += 1
            
            # 移除已处理的行
            if processed_lines > 0:
                remaining = "\n".join(lines[processed_lines:])
                self._response_buffer = QByteArray(remaining.encode("utf-8"))
    
    @Slot()
    def _on_connection_test_finished(self, reply, provider_id):
        """连接测试完成处理
        
        Args:
            reply: 网络响应
            provider_id: 提供商ID
        """
        # 检查响应状态
        if reply.error() == QNetworkReply.NoError:
            self.connection_test_result.emit(True, f"{provider_id} API连接成功")
        else:
            self.connection_test_result.emit(False, f"{provider_id} API连接失败: {reply.errorString()}")
        
        # 释放资源
        reply.deleteLater() 