#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import toml
import shutil
import copy

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
        self._model_config_file = os.path.join(self._config_dir, "model.toml")
        
        # 确保配置目录存在
        os.makedirs(self._config_dir, exist_ok=True)
        
        # 配置数据
        self._config = {}
        self._model_config = {}
        
        # 创建默认配置
        self._create_default_config()
        
        # 加载配置
        self.load()
        
        # 加载模型配置
        self.load_model_config()
    
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
    
    def load_model_config(self):
        """加载模型配置"""
        # 如果模型配置文件不存在，创建默认模型配置
        if not os.path.exists(self._model_config_file):
            self._create_default_model_config()
        
        # 加载模型配置
        try:
            self._model_config = toml.load(self._model_config_file)
            print(f"已加载模型配置文件: {self._model_config_file}")
        except Exception as e:
            print(f"加载模型配置文件失败: {e}")
            self._model_config = {"providers": {}}
    
    def _create_default_model_config(self):
        """创建默认模型配置文件"""
        # 如果文件已存在，不做任何操作
        if os.path.exists(self._model_config_file):
            return
            
        # 默认模型配置模板
        default_model_config = {
            "providers": {
                "openai": {
                    "name": "OpenAI",
                    "api_url": "https://api.openai.com/v1/chat/completions",
                    "api_key": "",
                    "models": [
                        {
                            "id": "gpt-3.5-turbo",
                            "name": "GPT-3.5 Turbo",
                            "max_tokens": 4096,
                            "supports_stream": True
                        },
                        {
                            "id": "gpt-4",
                            "name": "GPT-4",
                            "max_tokens": 8192,
                            "supports_stream": True
                        }
                    ]
                },
                "deepseek": {
                    "name": "深度求索",
                    "api_url": "https://api.deepseek.com/v1/chat/completions",
                    "api_key": "",
                    "models": [
                        {
                            "id": "deepseek-chat",
                            "name": "DeepSeek Chat",
                            "max_tokens": 4096,
                            "supports_stream": True
                        },
                        {
                            "id": "deepseek-coder",
                            "name": "DeepSeek Coder",
                            "max_tokens": 8192,
                            "supports_stream": True
                        }
                    ]
                }
            }
        }
        
        # 保存默认模型配置
        try:
            with open(self._model_config_file, "w", encoding="utf-8") as f:
                toml.dump(default_model_config, f)
            print(f"已创建默认模型配置文件: {self._model_config_file}")
        except Exception as e:
            print(f"创建默认模型配置文件失败: {e}")
    
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
    
    def save_model_config(self):
        """保存模型配置"""
        try:
            with open(self._model_config_file, "w", encoding="utf-8") as f:
                toml.dump(self._model_config, f)
            print(f"已保存模型配置文件: {self._model_config_file}")
            return True
        except Exception as e:
            print(f"保存模型配置文件失败: {e}")
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
    
    # 模型配置相关方法
    def get_all_providers(self):
        """获取所有模型提供商
        
        Returns:
            dict: 所有模型提供商配置
        """
        return self._model_config.get("providers", {})
    
    def get_provider(self, provider_id):
        """获取指定提供商的配置
        
        Args:
            provider_id: 提供商ID
        
        Returns:
            dict: 提供商配置
        """
        return self._model_config.get("providers", {}).get(provider_id, {})
    
    def set_provider(self, provider_id, provider_config):
        """设置提供商配置
        
        Args:
            provider_id: 提供商ID
            provider_config: 提供商配置
        
        Returns:
            bool: 是否成功
        """
        try:
            if "providers" not in self._model_config:
                self._model_config["providers"] = {}
            
            self._model_config["providers"][provider_id] = provider_config
            return self.save_model_config()
        except Exception as e:
            print(f"设置提供商配置失败: {e}")
            return False
    
    def delete_provider(self, provider_id):
        """删除提供商配置
        
        Args:
            provider_id: 提供商ID
        
        Returns:
            bool: 是否成功
        """
        try:
            if provider_id in self._model_config.get("providers", {}):
                del self._model_config["providers"][provider_id]
                return self.save_model_config()
            return False
        except:
            return False
    
    def get_provider_api_key(self, provider_id):
        """获取提供商API密钥
        
        Args:
            provider_id: 提供商ID
        
        Returns:
            str: API密钥
        """
        provider = self.get_provider(provider_id)
        return provider.get("api_key", "")
    
    def set_provider_api_key(self, provider_id, api_key):
        """设置提供商API密钥
        
        Args:
            provider_id: 提供商ID
            api_key: API密钥
        
        Returns:
            bool: 是否成功
        """
        try:
            provider = self.get_provider(provider_id)
            if not provider:
                return False
            
            provider_copy = copy.deepcopy(provider)
            provider_copy["api_key"] = api_key
            return self.set_provider(provider_id, provider_copy)
        except:
            return False
    
    def get_provider_models(self, provider_id):
        """获取提供商的所有模型
        
        Args:
            provider_id: 提供商ID
        
        Returns:
            list: 模型列表
        """
        provider = self.get_provider(provider_id)
        return provider.get("models", [])
    
    def add_model_to_provider(self, provider_id, model_config):
        """向提供商添加模型
        
        Args:
            provider_id: 提供商ID
            model_config: 模型配置
        
        Returns:
            bool: 是否成功
        """
        try:
            provider = self.get_provider(provider_id)
            if not provider:
                return False
            
            provider_copy = copy.deepcopy(provider)
            if "models" not in provider_copy:
                provider_copy["models"] = []
            
            # 检查模型是否已存在
            for i, model in enumerate(provider_copy["models"]):
                if model.get("id") == model_config.get("id"):
                    # 更新现有模型
                    provider_copy["models"][i] = model_config
                    return self.set_provider(provider_id, provider_copy)
            
            # 添加新模型
            provider_copy["models"].append(model_config)
            return self.set_provider(provider_id, provider_copy)
        except Exception as e:
            print(f"添加模型失败: {e}")
            return False
    
    def delete_model_from_provider(self, provider_id, model_id):
        """从提供商删除模型
        
        Args:
            provider_id: 提供商ID
            model_id: 模型ID
        
        Returns:
            bool: 是否成功
        """
        try:
            provider = self.get_provider(provider_id)
            if not provider:
                return False
            
            provider_copy = copy.deepcopy(provider)
            if "models" not in provider_copy:
                return False
            
            # 查找并删除模型
            for i, model in enumerate(provider_copy["models"]):
                if model.get("id") == model_id:
                    del provider_copy["models"][i]
                    return self.set_provider(provider_id, provider_copy)
            
            return False
        except:
            return False
    
    def add_provider(self, provider_id, name, api_url="", api_key="", models=None):
        """添加新的提供商
        
        Args:
            provider_id: 提供商ID
            name: 提供商名称
            api_url: API URL
            api_key: API密钥
            models: 模型列表
        
        Returns:
            bool: 是否成功
        """
        if models is None:
            models = []
        
        provider_config = {
            "name": name,
            "api_url": api_url,
            "api_key": api_key,
            "models": models
        }
        
        return self.set_provider(provider_id, provider_config) 