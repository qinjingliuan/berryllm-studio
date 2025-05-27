# BerryLLM Studio

BerryLLM Studio 是一个基于 PySide6 开发的现代化 LLM 聊天界面，提供了简洁易用的用户体验和丰富的功能，支持连接多种大语言模型服务。

![BerryLLM Studio](resources/images/berryllm_icon.png)

## 功能特点

- **多模型支持**：集成 OpenAI、Anthropic Claude 和 DeepSeek 等多种 LLM 服务
- **流式响应**：实时显示 AI 回复，提供更自然的对话体验
- **主题切换**：内置浅色/深色主题，自动适配系统主题或手动切换
- **上下文管理**：智能维护对话上下文，支持长对话
- **多语言支持**：支持中文和英文界面
- **聊天记录**：支持保存和导出聊天历史
- **参数调节**：可自定义模型参数如温度、最大 token 数等
- **简洁界面**：直观的用户界面，操作简单

## 系统要求

- Python 3.8 或更高版本
- 支持 Windows、macOS 和 Linux

## 安装

### 安装依赖

```bash
# 安装必要的依赖
pip install PySide6 requests

### 直接运行

```bash
# 运行主程序
python main.py
```

### 打包应用（可选）

```bash
# 使用 PyInstaller 打包（需要先安装 PyInstaller）
pip install pyinstaller
pyinstaller --windowed --icon=resources/images/berryllm_icon.png main.py
```

## 使用指南

1. **首次启动**：
   - 启动应用后，会显示默认的欢迎消息
   - 点击左侧菜单中的"设置"按钮进行初始配置

2. **配置 API**：
   - 在设置页面中选择你想使用的 LLM 提供商（OpenAI、Anthropic 或 DeepSeek）
   - 输入相应的 API 密钥和其他必要参数
   - 选择模型和设置其他参数

3. **开始对话**：
   - 在底部输入框中输入你的问题或指令
   - 按下回车键或点击发送按钮
   - AI 将以流式方式返回回答

4. **管理聊天**：
   - 使用"保存聊天记录"功能将对话保存为 HTML 或纯文本
   - 使用"清除聊天记录"功能开始新的对话

5. **切换主题**：
   - 点击"主题"按钮在浅色、深色和自动主题之间切换

## 开发指南

### 项目结构

```
berryllm-studio/
├── main.py              # 程序入口
├── main_window.py       # 主窗口实现
├── chat_view.py         # 聊天视图组件
├── llm_service.py       # LLM 服务接口
├── context_manager.py   # 上下文管理器
├── tool_manager.py      # 工具管理器
├── theme_manager.py     # 主题管理器
├── settings_page.py     # 设置页面
├── resources/           # 资源文件夹
│   ├── images/          # 图像资源
│   ├── styles/          # 样式表
│   └── trans/           # 翻译文件
└── README.md            # 项目说明
```

### 扩展指南

#### 添加新的 LLM 提供商

1. 在 `llm_service.py` 中添加新的 API 客户端类
2. 在 `settings_page.py` 中添加相应的设置界面
3. 更新配置保存和加载逻辑

#### 自定义主题

1. 在 `resources/styles/` 目录下创建新的 .qss 样式表文件
2. 在 `theme_manager.py` 中添加新主题的加载逻辑

## 贡献

欢迎提交 Pull Request 或创建 Issue 来帮助改进 BerryLLM Studio。在贡献代码前，请确保：

1. 代码风格符合项目规范
2. 新功能有适当的测试
3. 文档已更新

## 许可证

BerryLLM Studio 采用区分用户的双重许可模式：

- **个人用户和 10 人及以下组织**：GNU Affero 通用公共许可证 v3.0 (AGPLv3)
- **超过 10 人的组织**：需获取商业许可证

详细许可条款请参阅 [LICENSE](LICENSE) 文件。

## 联系方式

- 项目主页：[https://github.com/qinjingliuan/berryllm-studio](https://github.com/qinjingliuan/berryllm-studio)
- 问题反馈：请在 GitHub 上创建 Issue
- 商业合作：liuanqinjing@gmail.com
