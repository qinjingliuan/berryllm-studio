#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtCore import QObject, Signal, Slot, QSettings
import json


class ContextManager(QObject):
    """上下文管理器,负责管理LLM对话的上下文信息"""
    
    # 信号
    context_updated = Signal(dict)
    
    def __init__(self, parent=None):
        """初始化上下文管理器"""
        super().__init__(parent)
        
        # 当前上下文
        self._current_context = {}
        
        # 加载设置
        self._load_settings()
    
    def get_context(self):
        """获取当前上下文
        
        Returns:
            dict: 当前上下文
        """
        return self._current_context.copy()
    
    def set_context(self, context):
        """设置上下文
        
        Args:
            context: 新的上下文
        """
        if not isinstance(context, dict):
            return
        
        self._current_context = context.copy()
        self.context_updated.emit(self._current_context)
    
    def update_context(self, key, value):
        """更新上下文中的特定键值
        
        Args:
            key: 键名
            value: 键值
        """
        self._current_context[key] = value
        self.context_updated.emit(self._current_context)
    
    def remove_from_context(self, key):
        """从上下文中移除特定键
        
        Args:
            key: 要移除的键名
        """
        if key in self._current_context:
            del self._current_context[key]
            self.context_updated.emit(self._current_context)
    
    def clear_context(self):
        """清空上下文"""
        self._current_context = {}
        self.context_updated.emit(self._current_context)
    
    def save_context(self, name):
        """保存当前上下文到设置
        
        Args:
            name: 上下文名称
        """
        settings = QSettings()
        saved_contexts = json.loads(settings.value("Context/SavedContexts", "{}"))
        saved_contexts[name] = self._current_context
        settings.setValue("Context/SavedContexts", json.dumps(saved_contexts))
    
    def load_saved_context(self, name):
        """加载保存的上下文
        
        Args:
            name: 上下文名称
            
        Returns:
            bool: 是否成功加载
        """
        settings = QSettings()
        saved_contexts = json.loads(settings.value("Context/SavedContexts", "{}"))
        
        if name in saved_contexts:
            self._current_context = saved_contexts[name]
            self.context_updated.emit(self._current_context)
            return True
        
        return False
    
    def get_saved_context_names(self):
        """获取所有保存的上下文名称
        
        Returns:
            list: 上下文名称列表
        """
        settings = QSettings()
        saved_contexts = json.loads(settings.value("Context/SavedContexts", "{}"))
        return list(saved_contexts.keys())
    
    def delete_saved_context(self, name):
        """删除保存的上下文
        
        Args:
            name: 上下文名称
            
        Returns:
            bool: 是否成功删除
        """
        settings = QSettings()
        saved_contexts = json.loads(settings.value("Context/SavedContexts", "{}"))
        
        if name in saved_contexts:
            del saved_contexts[name]
            settings.setValue("Context/SavedContexts", json.dumps(saved_contexts))
            return True
        
        return False
    
    def _load_settings(self):
        """加载设置"""
        settings = QSettings()
        
        # 检查是否自动加载上次的上下文
        auto_load = settings.value("Context/AutoLoadLastContext", False, bool)
        if auto_load:
            last_context_name = settings.value("Context/LastContextName", "")
            if last_context_name:
                self.load_saved_context(last_context_name)
    
    def save_settings(self):
        """保存设置"""
        # 如果需要,可以在这里保存额外的设置 