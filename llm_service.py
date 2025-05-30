#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
from PySide6.QtCore import QObject, Signal, Slot, QSettings, QByteArray, QUrl, QEventLoop, QTimer
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply, QSsl, QSslConfiguration

from config_manager import ConfigManager


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
        
        # 配置管理器
        self._config_manager = ConfigManager.instance()
        
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
        
        # 获取API URL和密钥
        provider_id = session_info["provider_id"]
        provider = self._config_manager.get_provider(provider_id)
        
        if not provider:
            self.error_occurred.emit(session_id, f"未找到提供商配置: {provider_id}")
            return
        
        provider_api_url = provider.get("api_url", "")
        api_key = provider.get("api_key", "")
        
        if not provider_api_url:
            self.error_occurred.emit(session_id, "API URL未配置")
            return
        
        # 验证URL格式
        if not self._validate_url(provider_api_url):
            self.error_occurred.emit(session_id, f"API URL格式无效: {provider_api_url}")
            return
        
        # 检查API密钥
        if not api_key:
            self.error_occurred.emit(session_id, f"{provider_id} API密钥未配置")
            return
        
        # 获取模型配置
        model_id = session_info["model_id"]
        model_config = None
        
        for model in provider.get("models", []):
            if model.get("id") == model_id:
                model_config = model
                break
        
        if not model_config:
            self.error_occurred.emit(session_id, f"未找到模型配置: {model_id}")
            return
        
        # 创建请求
        request = self._create_request(provider_api_url, provider_id, api_key)
        
        # 构建请求体
        request_body = self._build_request_body(provider_id, model_id, message, context)
        
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
        providers = self._config_manager.get_all_providers()
        return list(providers.keys())
    
    def get_provider_api_url(self, provider_id):
        """获取提供商API URL"""
        provider = self._config_manager.get_provider(provider_id)
        return provider.get("api_url", "")
    
    def set_provider_api_url(self, provider_id, url):
        """设置提供商API URL"""
        provider = self._config_manager.get_provider(provider_id)
        if not provider:
            return False
        
        provider_copy = provider.copy()
        provider_copy["api_url"] = url
        return self._config_manager.set_provider(provider_id, provider_copy)
    
    def test_connection(self, provider_id=None):
        """测试与API提供商的连接
        
        Args:
            provider_id: 提供商ID,如果为None则使用当前提供商
        """
        if provider_id is None:
            provider_id = self._current_provider
        
        # 获取提供商配置
        provider = self._config_manager.get_provider(provider_id)
        if not provider:
            self.connection_test_result.emit(False, f"未找到提供商配置: {provider_id}")
            return
        
        # 获取API URL
        api_url = provider.get("api_url", "")
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
        api_key = provider.get("api_key", "")
        
        if not api_key:
            self.connection_test_result.emit(False, f"{provider_id} API密钥未配置")
            return
        
        # 根据不同提供商设置请求头
        self._set_provider_headers(request, provider_id, api_key)
        
        # 发送HEAD请求测试连接
        reply = self._network_manager.head(request)
        reply.setProperty("provider_id", provider_id)
        reply.finished.connect(lambda: self._on_connection_test_finished(reply, provider_id))
    
    def test_model_connection(self, provider_id, model_id):
        """测试与特定模型的连接
        
        Args:
            provider_id: 提供商ID
            model_id: 模型ID
            
        Returns:
            (bool, str): 测试结果和消息
        """
        # 获取提供商配置
        provider = self._config_manager.get_provider(provider_id)
        if not provider:
            return False, f"未找到提供商配置: {provider_id}"
        
        # 获取API URL和密钥
        api_url = provider.get("api_url", "")
        api_key = provider.get("api_key", "")
        
        if not api_url:
            return False, "API URL未配置"
        
        # 验证URL格式
        if not self._validate_url(api_url):
            return False, f"API URL格式无效: {api_url}"
        
        # 检查API密钥
        if not api_key:
            return False, f"{provider_id} API密钥未配置"
        
        # 构建简单的测试请求
        request = QNetworkRequest(QUrl(api_url))
        
        # 设置SSL配置
        request.setSslConfiguration(self._ssl_config)
        
        # 设置请求头
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        self._set_provider_headers(request, provider_id, api_key)
        
        # 构建极简请求体，只用于测试连接
        test_message = "Hello, this is a connection test."
        
        # 根据不同提供商构建请求体
        if provider_id == "openai":
            request_data = {
                "model": model_id,
                "messages": [{"role": "user", "content": test_message}],
                "max_tokens": 5  # 只请求少量token以快速测试
            }
        elif provider_id == "anthropic":
            request_data = {
                "model": model_id,
                "messages": [{"role": "user", "content": test_message}],
                "max_tokens": 5
            }
        elif provider_id == "deepseek":
            request_data = {
                "model": model_id,
                "messages": [{"role": "user", "content": test_message}],
                "max_tokens": 5
            }
        else:
            # 默认使用OpenAI格式
            request_data = {
                "model": model_id,
                "messages": [{"role": "user", "content": test_message}],
                "max_tokens": 5
            }
        
        # 发送POST请求测试连接
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        
        reply = self._network_manager.post(request, json.dumps(request_data).encode())
        
        # 连接信号
        reply.finished.connect(loop.quit)
        
        # 设置超时
        timer.start(10000)  # 10秒超时
        loop.exec_()
        
        # 检查结果
        if timer.isActive():
            # 请求完成，检查响应
            timer.stop()
            
            if reply.error() == QNetworkReply.NoError:
                response_data = reply.readAll().data().decode("utf-8")
                try:
                    json_data = json.loads(response_data)
                    reply.deleteLater()
                    return True, f"连接成功: {provider_id}/{model_id}"
                except json.JSONDecodeError:
                    reply.deleteLater()
                    return False, f"无法解析响应: {response_data[:100]}..."
            else:
                error = reply.errorString()
                reply.deleteLater()
                return False, f"连接错误: {error}"
        else:
            # 请求超时
            reply.abort()
            reply.deleteLater()
            return False, "连接超时，请检查网络或API服务器状态"
    
    def _validate_url(self, url):
        """验证URL格式"""
        if not url:
            return False
        
        # 简单验证URL格式
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return re.match(pattern, url) is not None
    
    def clear_conversation_history(self, session_id):
        """清除会话历史"""
        if session_id in self._conversation_histories:
            del self._conversation_histories[session_id]
    
    def _load_settings(self):
        """加载设置"""
        # 默认提供商
        default_provider = self._config_manager.get("model", "default_provider", "openai")
        if default_provider:
            self._current_provider = default_provider
    
    def _create_request(self, url, provider_id, api_key):
        """创建请求"""
        request = QNetworkRequest(QUrl(url))
        
        # 设置SSL配置
        request.setSslConfiguration(self._ssl_config)
        
        # 设置请求头
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        
        # 设置提供商特定的请求头
        self._set_provider_headers(request, provider_id, api_key)
        
        return request
    
    def _set_provider_headers(self, request, provider_id, api_key):
        """设置提供商特定的请求头"""
        if provider_id == "openai":
            request.setRawHeader(b"Authorization", f"Bearer {api_key}".encode())
        elif provider_id == "anthropic":
            request.setRawHeader(b"x-api-key", api_key.encode())
            request.setRawHeader(b"anthropic-version", b"2023-06-01")
        elif provider_id == "deepseek":
            request.setRawHeader(b"Authorization", f"Bearer {api_key}".encode())
        else:
            # 默认使用Bearer认证
            request.setRawHeader(b"Authorization", f"Bearer {api_key}".encode())
    
    def _build_request_body(self, provider_id, model_id, message, context):
        """构建请求体"""
        # 获取对话历史
        session_id = context.get("session_id", "")
        history = self._get_conversation_history(session_id)
        
        # 根据不同提供商构建请求体
        if provider_id == "openai":
            messages = []
            
            # 系统提示
            system_prompt = context.get("system_prompt", "")
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # 对话历史
            for entry in history:
                messages.append({"role": entry["role"], "content": entry["content"]})
            
            # 当前消息
            messages.append({"role": "user", "content": message})
            
            request_data = {
                "model": model_id,
                "messages": messages,
                "stream": True,
                "temperature": context.get("temperature", 0.7),
                "max_tokens": context.get("max_tokens", 1000),
                "top_p": context.get("top_p", 1.0)
            }
            
        elif provider_id == "anthropic":
            # 构建消息数组
            messages = []
            
            # 系统提示
            system_prompt = context.get("system_prompt", "")
            
            # 对话历史
            for entry in history:
                messages.append({"role": entry["role"], "content": entry["content"]})
            
            # 当前消息
            messages.append({"role": "user", "content": message})
            
            request_data = {
                "model": model_id,
                "messages": messages,
                "stream": True,
                "max_tokens": context.get("max_tokens", 1000),
                "temperature": context.get("temperature", 0.7),
                "top_p": context.get("top_p", 1.0)
            }
            
            if system_prompt:
                request_data["system"] = system_prompt
            
        elif provider_id == "deepseek":
            # 深度求索使用与OpenAI相同的接口格式
            messages = []
            
            # 系统提示
            system_prompt = context.get("system_prompt", "")
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # 对话历史
            for entry in history:
                messages.append({"role": entry["role"], "content": entry["content"]})
            
            # 当前消息
            messages.append({"role": "user", "content": message})
            
            request_data = {
                "model": model_id,
                "messages": messages,
                "stream": True,
                "temperature": context.get("temperature", 0.7),
                "max_tokens": context.get("max_tokens", 1000),
                "top_p": context.get("top_p", 1.0)
            }
        else:
            # 默认使用OpenAI格式
            messages = []
            
            # 系统提示
            system_prompt = context.get("system_prompt", "")
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # 对话历史
            for entry in history:
                messages.append({"role": entry["role"], "content": entry["content"]})
            
            # 当前消息
            messages.append({"role": "user", "content": message})
            
            request_data = {
                "model": model_id,
                "messages": messages,
                "stream": True,
                "temperature": context.get("temperature", 0.7),
                "max_tokens": context.get("max_tokens", 1000),
                "top_p": context.get("top_p", 1.0)
            }
        
        return json.dumps(request_data).encode()
    
    def _get_session_info(self, session_id):
        """获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            dict: 会话信息
        """
        if not session_id:
            return None
        
        # 会话ID格式: provider_id.model_id.uuid
        parts = session_id.split(".", 2)
        if len(parts) != 3:
            return None
        
        return {
            "provider_id": parts[0],
            "model_id": parts[1],
            "uuid": parts[2]
        }
    
    def _store_conversation_history(self, session_id, role, content):
        """存储对话历史
        
        Args:
            session_id: 会话ID
            role: 角色(user/assistant)
            content: 内容
        """
        if not session_id:
            return
        
        # 确保对话历史存在
        if session_id not in self._conversation_histories:
            self._conversation_histories[session_id] = []
        
        # 添加到对话历史
        self._conversation_histories[session_id].append({
            "role": role,
            "content": content
        })
    
    def _get_conversation_history(self, session_id):
        """获取对话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            list: 对话历史
        """
        if not session_id or session_id not in self._conversation_histories:
            return []
        
        return self._conversation_histories[session_id]
    
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