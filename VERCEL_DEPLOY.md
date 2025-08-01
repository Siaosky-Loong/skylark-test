# Vercel部署指南

本项目已经配置为支持Vercel部署。以下是部署步骤和注意事项。

## 部署步骤

### 1. 准备工作

确保你已经：
- 拥有Vercel账号
- 安装了Vercel CLI（可选）
- 准备好BytePlus ModelArk API密钥

### 2. 环境变量配置

在Vercel控制台中设置以下环境变量：

```bash
# Flask环境
FLASK_ENV=vercel
SECRET_KEY=your-secret-key-for-production

# BytePlus ModelArk API配置
ARK_API_KEY=your-ark-api-key
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# 模型默认参数
DEFAULT_TEMPERATURE=1.0
DEFAULT_MAX_TOKENS=1000
DEFAULT_TOP_P=0.7
DEFAULT_FREQUENCY_PENALTY=0.1
DEFAULT_PRESENCE_PENALTY=0.1

# Logit Bias配置（JSON格式）
LOGIT_BIAS_JSON={"861": -100, "854": -100, "135": -100, "136": -100}

# 日志级别
LOG_LEVEL=INFO
```

### 3. 部署方式

#### 方式一：通过Vercel控制台
1. 登录Vercel控制台
2. 点击"New Project"
3. 导入你的GitHub仓库
4. 选择这个分支（vercel-deploy）
5. 配置环境变量
6. 点击"Deploy"

#### 方式二：通过Vercel CLI
```bash
# 安装Vercel CLI
npm i -g vercel

# 登录Vercel
vercel login

# 部署项目
vercel --prod
```

## 项目结构说明

### 关键文件

- `vercel.json` - Vercel部署配置
- `api/index.py` - Serverless函数入口
- `config.py` - 包含Vercel专用配置
- `logger_utils_vercel.py` - 适用于Serverless的日志工具
- `.env.vercel` - 环境变量示例

### 主要修改

1. **移除文件系统依赖**
   - 日志系统改为仅控制台输出
   - Excel文件生成改为内存处理并返回Base64数据

2. **配置优化**
   - 添加VercelConfig配置类
   - 禁用文件日志功能
   - 优化Serverless环境设置

3. **前端适配**
   - 修改批量请求处理逻辑
   - 支持Base64 Excel文件下载

## 功能支持情况

### ✅ 完全支持的功能
- 单轮对话
- 多轮对话
- 批量请求（Excel下载）
- 参数配置
- 健康检查

### ⚠️ 有限支持的功能
- 日志查看（仅控制台输出，无文件存储）

### ❌ 不支持的功能
- 日志文件下载（Vercel无持久化存储）

## 注意事项

1. **环境变量安全**
   - 确保在Vercel控制台中正确设置所有环境变量
   - 不要在代码中硬编码敏感信息

2. **函数超时**
   - Vercel免费版函数执行时间限制为10秒
   - Pro版本限制为30秒
   - 批量请求可能需要Pro版本

3. **内存限制**
   - 注意批量请求的数量，避免超出内存限制
   - 建议单次批量请求不超过50次

4. **冷启动**
   - 首次访问可能有冷启动延迟
   - 可以通过定期访问保持函数热启动

## 测试部署

部署完成后，访问你的Vercel域名测试以下功能：
1. 主页加载
2. 单轮对话
3. 多轮对话
4. 批量请求
5. 健康检查 (`/health`)

## 故障排除

### 常见问题

1. **API密钥错误**
   - 检查Vercel环境变量中的ARK_API_KEY是否正确设置

2. **函数超时**
   - 减少批量请求数量
   - 考虑升级到Vercel Pro版本

3. **模块导入错误**
   - 确保所有依赖都在requirements.txt中
   - 检查Python版本兼容性

### 调试方法

1. 查看Vercel函数日志
2. 使用浏览器开发者工具检查网络请求
3. 检查环境变量配置

## 性能优化建议

1. **减少冷启动**
   - 使用Vercel的预热功能
   - 定期访问保持函数活跃

2. **优化响应时间**
   - 减少不必要的依赖导入
   - 使用异步处理

3. **监控使用情况**
   - 关注Vercel的使用统计
   - 监控函数执行时间和内存使用

## 更新部署

当需要更新代码时：
1. 推送代码到GitHub仓库
2. Vercel会自动重新部署
3. 或者使用`vercel --prod`手动部署

## 支持

如果遇到问题，请检查：
1. Vercel部署日志
2. 浏览器控制台错误
3. 网络连接状态
4. API密钥有效性