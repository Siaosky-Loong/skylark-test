# BytePlus ModelArk Chat Demo

这是一个基于BytePlus ModelArk API的聊天演示应用，提供了完整的Web界面来与AI模型进行交互。

## 功能特性

- ✅ 支持System和User消息输入
- ✅ 实时调用BytePlus ModelArk API
- ✅ 美观的现代化Web界面
- ✅ 自动保存模型端点配置
- ✅ 显示Token使用统计
- ✅ 错误处理和加载状态
- ✅ 响应式设计，支持移动端

## 技术栈

- **后端**: Flask + OpenAI Python SDK
- **前端**: HTML5 + CSS3 + JavaScript
- **API**: BytePlus ModelArk Chat API

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制环境变量示例文件并配置您的API密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入您的BytePlus ModelArk API密钥：

```env
ARK_API_KEY=your_actual_api_key_here
```

### 3. 获取API密钥和端点ID

1. 访问 [BytePlus控制台](https://console.byteplus.com/)
2. 创建或选择一个ModelArk项目
3. 获取您的API密钥 (ARK_API_KEY)
4. 创建模型端点并获取端点ID

### 4. 运行应用

```bash
python app.py
```

应用将在 `http://localhost:8000` 启动。

### 5. 使用应用

1. 在浏览器中打开 `http://localhost:8000`
2. 输入您的模型端点ID
3. 可选：输入System消息来设定AI的角色或行为
4. 输入User消息
5. 点击"发送消息"按钮

## API参数配置

本demo按照要求配置了以下参数：

### 推理参数
- `temperature`: 1.0
- `top_p`: 0.7

### Logit Bias
```python
logit_bias = {
    "861": -100,
    "854": -100,
    "135": -100,
    "136": -100,
}
```

## 项目结构

```
skylark-test/
├── app.py                 # Flask后端应用
├── requirements.txt       # Python依赖
├── .env.example          # 环境变量示例
├── README.md             # 项目说明
├── templates/
│   └── index.html        # 前端HTML页面
└── static/
    ├── style.css         # CSS样式文件
    └── script.js         # JavaScript逻辑
```

## 接口文档

本项目基于BytePlus ModelArk Chat API开发，详细的API文档请参考：
https://docs.byteplus.com/en/docs/ModelArk/Chat

## 注意事项

1. **API密钥安全**: 请妥善保管您的API密钥，不要将其提交到版本控制系统
2. **端点ID**: 每个模型端点都有唯一的ID，请确保使用正确的端点ID
3. **网络连接**: 确保您的网络可以访问BytePlus API服务
4. **Token限制**: 注意您的API配额和Token使用限制

## 故障排除

### 常见错误

1. **AuthenticationError**: 检查API密钥是否正确设置
2. **模型端点错误**: 确认端点ID是否正确且已激活
3. **网络连接错误**: 检查网络连接和防火墙设置

### 调试模式

应用默认以调试模式运行，您可以在控制台查看详细的错误信息。

## 许可证

本项目仅供学习和演示使用。

## 支持

如有问题，请参考：
- [BytePlus ModelArk文档](https://docs.byteplus.com/en/docs/ModelArk/)
- [OpenAI Python SDK文档](https://github.com/openai/openai-python)