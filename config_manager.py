#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import toml
import shutil

class ConfigManager:
    """配置管理类，负责加载、保存和重置配置"""
    
    _instance = None
    
    @classmethod
    def instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = ConfigManager()
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        # 确保是单例
        if ConfigManager._instance is not None:
            raise RuntimeError("ConfigManager是单例类，请使用ConfigManager.instance()获取实例")
        
        # 配置文件路径
        self._config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data", "Files")
        self._config_file = os.path.join(self._config_dir, "custom.toml")
        self._default_config_file = os.path.join(self._config_dir, "default.toml")
        
        # 确保配置目录存在
        os.makedirs(self._config_dir, exist_ok=True)
        
        # 配置数据
        self._config = {}
        
        # 创建默认配置
        self._create_default_config()
        
        # 加载配置
        self.load()
    
    def _create_default_config(self):
        """创建默认配置文件"""
        default_config = {
            "general": {
                "language": "zh_CN",
                "auto_start": False,
                "check_updates": True
            },
            "display": {
                "theme": "light",
                "font_size": 12,
                "show_toolbar": True
            },
            "model": {
                "default_model": "DeepSeek-R1",
                "default_provider": "硅基流动"
            },
            "network": {
                "enable_search": True,
                "search_engine": "Google",
                "proxy_enabled": False,
                "proxy_url": ""
            }
        }
        
        # 保存默认配置
        try:
            with open(self._default_config_file, "w", encoding="utf-8") as f:
                toml.dump(default_config, f)
            print(f"已创建默认配置文件: {self._default_config_file}")
        except Exception as e:
            print(f"创建默认配置文件失败: {e}")
    
    def load(self):
        """加载配置"""
        # 如果配置文件不存在，则使用默认配置
        if not os.path.exists(self._config_file):
            try:
                if os.path.exists(self._default_config_file):
                    shutil.copy(self._default_config_file, self._config_file)
                    print(f"已复制默认配置到: {self._config_file}")
                else:
                    # 如果默认配置文件也不存在，重新创建
                    self._create_default_config()
                    shutil.copy(self._default_config_file, self._config_file)
                    print(f"已创建并复制默认配置到: {self._config_file}")
            except Exception as e:
                print(f"复制配置文件失败: {e}")
        
        # 加载配置
        try:
            self._config = toml.load(self._config_file)
            print(f"已加载配置文件: {self._config_file}")
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            # 如果加载失败，使用默认配置
            if os.path.exists(self._default_config_file):
                try:
                    self._config = toml.load(self._default_config_file)
                    print(f"已加载默认配置文件: {self._default_config_file}")
                except Exception as e:
                    print(f"加载默认配置文件失败: {e}")
                    self._config = {}
            else:
                self._config = {}
    
    def save(self):
        """保存配置"""
        try:
            with open(self._config_file, "w", encoding="utf-8") as f:
                toml.dump(self._config, f)
            print(f"已保存配置文件: {self._config_file}")
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def reset(self):
        """重置为默认配置"""
        try:
            if os.path.exists(self._default_config_file):
                self._config = toml.load(self._default_config_file)
                self.save()
                print("已重置为默认配置")
                return True
            else:
                print("默认配置文件不存在，无法重置")
                return False
        except Exception as e:
            print(f"重置配置失败: {e}")
            return False
    
    def get(self, section, key, default=None):
        """获取配置值
        
        Args:
            section: 配置节
            key: 配置键
            default: 默认值
        
        Returns:
            配置值
        """
        try:
            return self._config.get(section, {}).get(key, default)
        except:
            return default
    
    def set(self, section, key, value):
        """设置配置值
        
        Args:
            section: 配置节
            key: 配置键
            value: 配置值
        
        Returns:
            bool: 是否成功
        """
        try:
            if section not in self._config:
                self._config[section] = {}
            
            self._config[section][key] = value
            return True
        except:
            return False
    
    def get_all(self):
        """获取所有配置
        
        Returns:
            dict: 所有配置
        """
        return self._config 