#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtCore import QObject, Signal, Slot, QSettings
import json
import os
import importlib.util
import inspect


class Tool:
    """工具类,表示一个可以被LLM调用的工具"""
    
    def __init__(self, name, description, function=None):
        """初始化工具
        
        Args:
            name: 工具名称
            description: 工具描述
            function: 工具函数
        """
        self.name = name
        self.description = description
        self.function = function
        self.enabled = True
    
    def execute(self, *args, **kwargs):
        """执行工具函数
        
        Returns:
            工具函数的返回值
        """
        if not self.function or not callable(self.function):
            return {"error": "工具函数未定义"}
        
        try:
            return self.function(*args, **kwargs)
        except Exception as e:
            return {"error": f"执行工具时出错: {str(e)}"}
    
    def to_dict(self):
        """转换为字典
        
        Returns:
            dict: 工具信息字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled
        }


class ToolManager(QObject):
    """工具管理器,负责管理和执行LLM可用的工具"""
    
    # 信号
    tool_registered = Signal(str)
    tool_unregistered = Signal(str)
    tool_executed = Signal(str, dict)
    
    def __init__(self, parent=None):
        """初始化工具管理器"""
        super().__init__(parent)
        
        # 工具字典
        self._tools = {}
        
        # 加载内置工具
        self._load_builtin_tools()
        
        # 加载自定义工具
        self._load_custom_tools()
    
    def register_tool(self, tool):
        """注册工具
        
        Args:
            tool: Tool对象
            
        Returns:
            bool: 是否成功注册
        """
        if not isinstance(tool, Tool):
            return False
        
        self._tools[tool.name] = tool
        self.tool_registered.emit(tool.name)
        return True
    
    def unregister_tool(self, tool_name):
        """注销工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 是否成功注销
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            self.tool_unregistered.emit(tool_name)
            return True
        
        return False
    
    def get_tool(self, tool_name):
        """获取工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Tool: 工具对象,如果不存在则返回None
        """
        return self._tools.get(tool_name)
    
    def get_all_tools(self):
        """获取所有工具
        
        Returns:
            list: 工具对象列表
        """
        return list(self._tools.values())
    
    def get_enabled_tools(self):
        """获取所有启用的工具
        
        Returns:
            list: 启用的工具对象列表
        """
        return [tool for tool in self._tools.values() if tool.enabled]
    
    def execute_tool(self, tool_name, *args, **kwargs):
        """执行工具
        
        Args:
            tool_name: 工具名称
            *args, **kwargs: 工具函数参数
            
        Returns:
            工具函数的返回值
        """
        tool = self.get_tool(tool_name)
        if not tool:
            result = {"error": f"工具 '{tool_name}' 不存在"}
        elif not tool.enabled:
            result = {"error": f"工具 '{tool_name}' 已禁用"}
        else:
            result = tool.execute(*args, **kwargs)
        
        self.tool_executed.emit(tool_name, result)
        return result
    
    def enable_tool(self, tool_name):
        """启用工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 是否成功启用
        """
        tool = self.get_tool(tool_name)
        if tool:
            tool.enabled = True
            return True
        
        return False
    
    def disable_tool(self, tool_name):
        """禁用工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 是否成功禁用
        """
        tool = self.get_tool(tool_name)
        if tool:
            tool.enabled = False
            return True
        
        return False
    
    def get_tools_as_json(self):
        """获取工具列表的JSON表示
        
        Returns:
            str: JSON字符串
        """
        tools_dict = {name: tool.to_dict() for name, tool in self._tools.items()}
        return json.dumps(tools_dict)
    
    def _load_builtin_tools(self):
        """加载内置工具"""
        # 注册内置工具示例
        
        # 日期时间工具
        def get_current_datetime():
            import datetime
            now = datetime.datetime.now()
            return {
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": int(now.timestamp())
            }
        
        self.register_tool(Tool(
            "get_current_datetime",
            "获取当前日期和时间",
            get_current_datetime
        ))
        
        # 计算器工具
        def calculate(expression):
            try:
                # 安全的eval
                allowed_names = {"abs": abs, "round": round, "min": min, "max": max}
                code = compile(expression, "<string>", "eval")
                for name in code.co_names:
                    if name not in allowed_names:
                        raise NameError(f"使用了不允许的名称: {name}")
                return {"result": eval(code, {"__builtins__": {}}, allowed_names)}
            except Exception as e:
                return {"error": f"计算错误: {str(e)}"}
        
        self.register_tool(Tool(
            "calculate",
            "计算数学表达式",
            calculate
        ))
    
    def _load_custom_tools(self):
        """加载自定义工具"""
        # 从插件目录加载自定义工具
        plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")
        if not os.path.exists(plugin_dir):
            return
        
        for filename in os.listdir(plugin_dir):
            if filename.endswith(".py"):
                try:
                    module_path = os.path.join(plugin_dir, filename)
                    module_name = os.path.splitext(filename)[0]
                    
                    # 动态导入模块
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 查找并注册工具
                    for name, obj in inspect.getmembers(module):
                        if isinstance(obj, Tool):
                            self.register_tool(obj)
                
                except Exception as e:
                    print(f"加载插件 {filename} 失败: {str(e)}")
    
    def save_settings(self):
        """保存工具设置"""
        settings = QSettings()
        
        # 保存工具启用状态
        tool_states = {}
        for name, tool in self._tools.items():
            tool_states[name] = tool.enabled
        
        settings.setValue("Tools/EnabledState", json.dumps(tool_states))
    
    def load_settings(self):
        """加载工具设置"""
        settings = QSettings()
        
        # 加载工具启用状态
        tool_states = json.loads(settings.value("Tools/EnabledState", "{}"))
        for name, enabled in tool_states.items():
            tool = self.get_tool(name)
            if tool:
                tool.enabled = enabled 