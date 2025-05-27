#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
from PySide6.QtCore import QObject, Signal, Slot, QSettings, QByteArray, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply, QSsl, QSslConfiguration


class LlmService(QObject):
    """LLM服务类,负责与AI提供商的API通信"""
    
    # 信号
    response_started = Signal()
    response_chunk = Signal(str)
    response_finished = Signal()
    error_occurred = Signal(str)
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
        
        # 对话历史
        self._conversation_history = []
        
        # 初始化SSL配置
        self._ssl_config = QSslConfiguration.defaultConfiguration()
        self._ssl_config.setProtocol(QSsl.TlsV1_2OrLater)
        
        # 加载设置
        self._load_settings()
    
    def send_message(self, message, context=None):
        """发送消息到LLM
        
        Args:
            message: 用户消息
            context: 上下文信息,可选
        """
        if context is None:
            context = {}
        
        # 取消任何活跃的请求
        self.cancel_request()
        
        # 获取API URL
        provider_api_url = self.get_provider_api_url(self._current_provider)
        if not provider_api_url:
            self.error_occurred.emit("API URL未配置")
            return
        
        # 验证URL格式
        if not self._validate_url(provider_api_url):
            self.error_occurred.emit(f"API URL格式无效: {provider_api_url}")
            return
        
        # 检查API密钥
        settings = QSettings()
        api_key = settings.value(f"LLM/{self._current_provider}/ApiKey", "")
        if not api_key:
            self.error_occurred.emit(f"{self._current_provider} API密钥未配置")
            return
        
        # 创建请求
        request = self._create_request(provider_api_url)
        
        # 构建请求体
        request_body = self._build_request_body(message, context)
        
        # 存储对话历史
        self._store_conversation_history("user", message)
        
        # 发送请求
        self._active_requests += 1
        self._current_reply = self._network_manager.post(request, request_body)
        
        # 连接信号
        self._current_reply.finished.connect(self._on_network_reply_finished)
        self._current_reply.readyRead.connect(self._on_network_reply_ready_read)
        self._current_reply.errorOccurred.connect(self._on_network_reply_error)
        
        # 发送开始响应信号
        self.response_started.emit()
    
    def cancel_request(self):
        """取消当前请求"""
        if self._current_reply and self._current_reply.isRunning():
            self._current_reply.abort()
            self._current_reply = None
    
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
    
    def clear_conversation_history(self):
        """清空对话历史"""
        self._conversation_history = []
    
    def _load_settings(self):
        """加载设置"""
        settings = QSettings()
        provider = settings.value("LLM/Provider", "openai")
        self._current_provider = provider
    
    def _create_request(self, url):
        """创建请求
        
        Args:
            url: API URL
            
        Returns:
            QNetworkRequest: 网络请求对象
        """
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        
        # 设置SSL配置
        request.setSslConfiguration(self._ssl_config)
        
        # 设置API密钥
        settings = QSettings()
        api_key = settings.value(f"LLM/{self._current_provider}/ApiKey", "")
        
        if self._current_provider == "openai":
            request.setRawHeader(b"Authorization", f"Bearer {api_key}".encode())
        elif self._current_provider == "anthropic":
            request.setRawHeader(b"x-api-key", api_key.encode())
            request.setRawHeader(b"anthropic-version", b"2023-06-01")
        elif self._current_provider == "deepseek":
            request.setRawHeader(b"Authorization", f"Bearer {api_key}".encode())
        
        return request
    
    def _build_request_body(self, message, context):
        """构建请求体
        
        Args:
            message: 用户消息
            context: 上下文信息
            
        Returns:
            QByteArray: 请求体数据
        """
        settings = QSettings()
        streaming = settings.value("LLM/EnableStreaming", True, bool)
        max_tokens = settings.value("LLM/MaxTokens", 2048, int)
        temperature = settings.value("LLM/Temperature", 0.7, float)
        
        request_data = {}
        
        if self._current_provider == "openai":
            # 构建OpenAI请求
            model = settings.value("LLM/OpenAI/Model", "gpt-3.5-turbo")
            
            messages = self._get_conversation_history()
            messages.append({"role": "user", "content": message})
            
            request_data = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": streaming
            }
            
            # 添加上下文
            if context:
                for key, value in context.items():
                    request_data[key] = value
                
        elif self._current_provider == "anthropic":
            # 构建Anthropic请求
            model = settings.value("LLM/Anthropic/Model", "claude-2")
            
            # 构建消息历史
            messages = []
            for msg in self._conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            request_data = {
                "model": model,
                "messages": messages + [{"role": "user", "content": message}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": streaming
            }
            
        elif self._current_provider == "deepseek":
            # 构建DeepSeek请求
            model = settings.value("LLM/DeepSeek/Model", "deepseek-chat")
            
            messages = self._get_conversation_history()
            messages.append({"role": "user", "content": message})
            
            request_data = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": streaming
            }
        
        # 转换为JSON
        return QByteArray(json.dumps(request_data).encode())
    
    def _store_conversation_history(self, role, content):
        """存储对话历史
        
        Args:
            role: 角色 (user/assistant)
            content: 消息内容
        """
        self._conversation_history.append({
            "role": role,
            "content": content
        })
        
        # 限制历史记录长度
        settings = QSettings()
        max_history = settings.value("LLM/MaxHistoryMessages", 10, int)
        if len(self._conversation_history) > max_history:
            self._conversation_history = self._conversation_history[-max_history:]
    
    def _get_conversation_history(self):
        """获取对话历史
        
        Returns:
            list: 对话历史列表
        """
        return self._conversation_history.copy()
    
    @Slot()
    def _on_network_reply_finished(self):
        """网络响应完成处理"""
        if not self._current_reply:
            return
        
        if self._current_reply.error() == QNetworkReply.NoError:
            # 处理最后的响应数据
            data = self._current_reply.readAll()
            if data:
                self._process_streaming_response(data)
            
            # 处理非流式响应
            settings = QSettings()
            streaming = settings.value("LLM/EnableStreaming", True, bool)
            
            if not streaming:
                try:
                    response_json = json.loads(str(self._response_buffer, 'utf-8'))
                    
                    if self._current_provider == "openai":
                        content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")
                    elif self._current_provider == "anthropic":
                        content = response_json.get("content", [{}])[0].get("text", "")
                    elif self._current_provider == "deepseek":
                        content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")
                    else:
                        content = ""
                    
                    if content:
                        self.response_chunk.emit(content)
                        self._store_conversation_history("assistant", content)
                except Exception as e:
                    self.error_occurred.emit(f"解析响应失败: {str(e)}")
        
        # 减少活跃请求计数
        self._active_requests -= 1
        if self._active_requests <= 0:
            self._active_requests = 0
            self.all_requests_finished.emit()
        
        # 发送响应完成信号
        self.response_finished.emit()
        
        # 清理
        self._current_reply.deleteLater()
        self._current_reply = None
        self._response_buffer.clear()
    
    @Slot()
    def _on_network_reply_ready_read(self):
        """网络响应数据可读处理"""
        if not self._current_reply:
            return
        
        # 读取数据
        data = self._current_reply.readAll()
        if not data:
            return
        
        # 处理流式响应
        self._process_streaming_response(data)
    
    @Slot(QNetworkReply.NetworkError)
    def _on_network_reply_error(self, error):
        """网络错误处理
        
        Args:
            error: 错误代码
        """
        if not self._current_reply:
            return
        
        error_msg = self._current_reply.errorString()
        status_code = self._current_reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        
        # 构建更详细的错误信息
        if status_code:
            if status_code == 404:
                error_detail = f"API端点不存在 (HTTP 404)。请检查API URL是否正确。"
            elif status_code == 401:
                error_detail = f"认证失败 (HTTP 401)。请检查API密钥是否正确。"
            elif status_code == 403:
                error_detail = f"访问被拒绝 (HTTP 403)。请检查API密钥权限。"
            elif status_code >= 500:
                error_detail = f"服务器错误 (HTTP {status_code})。请稍后重试。"
            else:
                error_detail = f"HTTP错误 {status_code}"
            
            self.error_occurred.emit(f"网络错误: {error_detail} - {error_msg}")
        else:
            # 没有状态码的错误，可能是连接问题
            if "not found" in error_msg.lower():
                error_detail = f"无法连接到服务器。请检查API URL是否正确，以及网络连接是否正常。"
                self.error_occurred.emit(f"网络错误: {error_detail}")
            else:
                self.error_occurred.emit(f"网络错误: {error_msg}")
        
        # 减少活跃请求计数
        self._active_requests -= 1
        if self._active_requests <= 0:
            self._active_requests = 0
            self.all_requests_finished.emit()
    
    def _process_streaming_response(self, data):
        """处理流式响应
        
        Args:
            data: 响应数据
        """
        # 添加到缓冲区
        self._response_buffer.append(data)
        
        # 检查是否是流式响应
        settings = QSettings()
        streaming = settings.value("LLM/EnableStreaming", True, bool)
        
        if not streaming:
            return
        
        try:
            # 处理数据
            content = ""
            data_str = str(data, 'utf-8')
            
            # 处理不同提供商的流式响应格式
            if self._current_provider == "openai":
                # OpenAI格式: data: {...}\n\ndata: {...}\n\n
                for line in data_str.split('\n'):
                    if line.startswith('data: ') and line != 'data: [DONE]':
                        json_str = line[6:]  # 去掉 'data: '
                        try:
                            chunk = json.loads(json_str)
                            delta = chunk.get('choices', [{}])[0].get('delta', {})
                            if 'content' in delta:
                                content += delta['content']
                        except:
                            pass
            
            elif self._current_provider == "anthropic":
                # Anthropic格式: event: content_block_delta\ndata: {...}\n\n
                for line in data_str.split('\n'):
                    if line.startswith('data: '):
                        json_str = line[6:]  # 去掉 'data: '
                        try:
                            chunk = json.loads(json_str)
                            delta = chunk.get('delta', {})
                            if 'text' in delta:
                                content += delta['text']
                        except:
                            pass
            
            elif self._current_provider == "deepseek":
                # DeepSeek格式: data: {...}\n\ndata: {...}\n\n
                for line in data_str.split('\n'):
                    if line.startswith('data: ') and line != 'data: [DONE]':
                        json_str = line[6:]  # 去掉 'data: '
                        try:
                            chunk = json.loads(json_str)
                            delta = chunk.get('choices', [{}])[0].get('delta', {})
                            if 'content' in delta:
                                content += delta['content']
                        except:
                            pass
            
            # 发送内容块
            if content:
                self.response_chunk.emit(content)
                # 不要在这里存储对话历史,因为流式响应会分多次接收
                # 最终的完整响应会在响应结束时存储
        
        except Exception as e:
            self.error_occurred.emit(f"处理流式响应失败: {str(e)}")
    
    @Slot()
    def _on_connection_test_finished(self, reply, provider_id):
        """连接测试完成处理
        
        Args:
            reply: 网络响应
            provider_id: 提供商ID
        """
        error = reply.error()
        
        if error == QNetworkReply.NoError:
            self.connection_test_result.emit(True, f"成功连接到{provider_id} API")
        else:
            error_msg = reply.errorString()
            status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            if status_code:
                self.connection_test_result.emit(False, f"连接失败: HTTP {status_code} - {error_msg}")
            else:
                self.connection_test_result.emit(False, f"连接失败: {error_msg}")
        
        reply.deleteLater() 