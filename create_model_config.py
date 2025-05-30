#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import toml

def create_model_config():
    # 配置目录
    config_dir = os.path.join(os.path.abspath('Data'), 'Files')
    os.makedirs(config_dir, exist_ok=True)
    
    # 配置文件路径
    model_file = os.path.join(config_dir, 'model.toml')
    
    # 配置内容
    config = {
        'providers': {
            'openai': {
                'name': 'OpenAI',
                'api_url': 'https://api.openai.com/v1/chat/completions',
                'api_key': '',
                'models': [
                    {
                        'id': 'gpt-3.5-turbo',
                        'name': 'GPT-3.5 Turbo',
                        'max_tokens': 4096,
                        'supports_stream': True
                    },
                    {
                        'id': 'gpt-4',
                        'name': 'GPT-4',
                        'max_tokens': 8192,
                        'supports_stream': True
                    }
                ]
            },
            'deepseek': {
                'name': '深度求索',
                'api_url': 'https://api.deepseek.com/v1/chat/completions',
                'api_key': '',
                'models': [
                    {
                        'id': 'deepseek-chat',
                        'name': 'DeepSeek Chat',
                        'max_tokens': 4096,
                        'supports_stream': True
                    },
                    {
                        'id': 'deepseek-coder',
                        'name': 'DeepSeek Coder',
                        'max_tokens': 8192,
                        'supports_stream': True
                    }
                ]
            }
        }
    }
    
    # 保存配置
    with open(model_file, 'w', encoding='utf-8') as f:
        toml.dump(config, f)
    
    print(f'已创建模型配置文件: {model_file}')

if __name__ == '__main__':
    create_model_config() 