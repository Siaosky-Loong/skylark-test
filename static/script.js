// 多轮对话相关变量
let conversationHistory = [];
let isMultiTurnEnabled = false;
let contextRounds = 5;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 从localStorage恢复配置
    const savedApiKey = localStorage.getItem('apiKey');
    const savedBaseUrl = localStorage.getItem('baseUrl');
    const savedEndpoint = localStorage.getItem('modelEndpoint');
    const savedModelId = localStorage.getItem('modelId');
    const savedLogitBias = localStorage.getItem('logitBias');
    const savedMultiTurn = localStorage.getItem('multiTurnEnabled');
    const savedContextRounds = localStorage.getItem('contextRounds');
    
    if (savedApiKey) {
        document.getElementById('api-key').value = savedApiKey;
    }
    if (savedBaseUrl) {
        document.getElementById('base-url').value = savedBaseUrl;
    } else {
        // 设置默认值
        document.getElementById('base-url').value = 'https://ark.cn-beijing.volces.com/api/v3';
    }
    if (savedEndpoint) {
        document.getElementById('model-endpoint').value = savedEndpoint;
    }
    if (savedModelId) {
        document.getElementById('model-id').value = savedModelId;
    }
    if (savedLogitBias) {
        document.getElementById('logit-bias').value = savedLogitBias;
    } else {
        // 设置默认的logit_bias值
        document.getElementById('logit-bias').value = '{"861": -100, "854": -100, "135": -100, "136": -100}';
    }
    
    // 恢复多轮对话设置
    if (savedMultiTurn === 'true') {
        document.getElementById('multi-turn-enabled').checked = true;
        isMultiTurnEnabled = true;
        toggleMultiTurn();
    }
    if (savedContextRounds) {
        contextRounds = parseInt(savedContextRounds);
        document.getElementById('context-rounds').value = contextRounds;
    }
    
    // 为输入框添加回车键监听
    document.getElementById('user-input').addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // 为API密钥、base_url、端点、模型ID和logit_bias添加自动保存
    document.getElementById('api-key').addEventListener('input', function(e) {
        localStorage.setItem('apiKey', e.target.value);
    });
    
    document.getElementById('base-url').addEventListener('input', function(e) {
        localStorage.setItem('baseUrl', e.target.value);
    });
    
    document.getElementById('model-endpoint').addEventListener('input', function(e) {
        localStorage.setItem('modelEndpoint', e.target.value);
    });
    
    document.getElementById('model-id').addEventListener('input', function(e) {
        localStorage.setItem('modelId', e.target.value);
    });
    
    document.getElementById('logit-bias').addEventListener('input', function(e) {
        localStorage.setItem('logitBias', e.target.value);
    });
    
    // 为多轮对话设置添加自动保存
    document.getElementById('context-rounds').addEventListener('input', function(e) {
        contextRounds = parseInt(e.target.value) || 5;
        localStorage.setItem('contextRounds', contextRounds);
    });
});

// 切换多轮对话模式
function toggleMultiTurn() {
    const checkbox = document.getElementById('multi-turn-enabled');
    const contextConfig = document.getElementById('context-config');
    const conversationControls = document.getElementById('conversation-controls');
    const conversationHistory = document.getElementById('conversation-history');
    
    isMultiTurnEnabled = checkbox.checked;
    localStorage.setItem('multiTurnEnabled', isMultiTurnEnabled);
    
    if (isMultiTurnEnabled) {
        contextConfig.style.display = 'block';
        conversationControls.style.display = 'block';
        conversationHistory.style.display = 'block';
        // 立即更新历史记录显示
        updateHistoryDisplay();
    } else {
        contextConfig.style.display = 'none';
        conversationControls.style.display = 'none';
        conversationHistory.style.display = 'none';
    }
}

// 清空对话历史
function clearConversationHistory() {
    conversationHistory = [];
    updateHistoryDisplay();
}

// 添加消息到对话历史
function addToHistory(role, content, timestamp = null) {
    if (!isMultiTurnEnabled) return;
    
    const message = {
        role: role,
        content: content,
        timestamp: timestamp || new Date().toLocaleString()
    };
    
    conversationHistory.push(message);
    
    // 限制历史记录长度（保留最近的轮次）
    // 注意：这里按消息对计算，一轮对话包含用户消息和助手回复
    const maxMessages = contextRounds * 2; // 用户+助手消息对
    if (conversationHistory.length > maxMessages) {
        conversationHistory = conversationHistory.slice(-maxMessages);
    }
    
    // 立即更新历史记录显示
    updateHistoryDisplay();
}

// 更新历史记录显示
function updateHistoryDisplay() {
    const historyContainer = document.getElementById('history-container');
    
    if (!isMultiTurnEnabled) {
        return;
    }
    
    if (conversationHistory.length === 0) {
        historyContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">暂无对话历史</div>';
        return;
    }
    
    historyContainer.innerHTML = conversationHistory.map(message => `
        <div class="history-message ${message.role}">
            <div class="message-role">${getRoleDisplayName(message.role)}</div>
            <div class="message-content">${escapeHtml(message.content)}</div>
            <div class="message-timestamp">${message.timestamp}</div>
        </div>
    `).join('');
    
    // 滚动到底部显示最新消息
    historyContainer.scrollTop = historyContainer.scrollHeight;
}

// 获取角色显示名称
function getRoleDisplayName(role) {
    const roleNames = {
        'user': '用户',
        'assistant': '助手',
        'system': '系统'
    };
    return roleNames[role] || role;
}

// HTML转义函数，防止XSS攻击
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 构建包含历史记录的消息列表
function buildMessagesWithHistory(systemContent, userContent) {
    const messages = [];
    
    // 添加系统消息（如果有）
    if (systemContent) {
        messages.push({
            role: 'system',
            content: systemContent
        });
    }
    
    // 如果启用多轮对话，添加历史记录
    if (isMultiTurnEnabled && conversationHistory.length > 0) {
        // 过滤掉系统消息，避免重复
        const historyMessages = conversationHistory.filter(msg => msg.role !== 'system');
        messages.push(...historyMessages.map(msg => ({
            role: msg.role,
            content: msg.content
        })));
    }
    
    // 添加当前用户消息
    messages.push({
        role: 'user',
        content: userContent
    });
    
    return messages;
}

async function sendMessage() {
    const sendBtn = document.getElementById('send-btn');
    const btnText = document.getElementById('btn-text');
    const loadingSpinner = document.getElementById('loading-spinner');
    const responseContent = document.getElementById('response-content');
    const usageInfo = document.getElementById('usage-info');
    
    // 获取输入值
    const apiKey = document.getElementById('api-key').value.trim();
    const baseUrl = document.getElementById('base-url').value.trim();
    const modelEndpoint = document.getElementById('model-endpoint').value.trim();
    const modelId = document.getElementById('model-id').value.trim();
    const systemContent = document.getElementById('system-input').value.trim();
    const userContent = document.getElementById('user-input').value.trim();
    const logitBiasText = document.getElementById('logit-bias').value.trim();
    
    // 验证输入
    if (!apiKey) {
        showError('请输入API密钥');
        return;
    }
    
    if (!baseUrl) {
        showError('请输入模型请求地址');
        return;
    }
    
    // 验证URL格式
    try {
        new URL(baseUrl);
    } catch (e) {
        showError('请输入有效的URL地址，例如：https://ark.cn-beijing.volces.com/api/v3');
        return;
    }
    
    if (!modelEndpoint) {
        showError('请输入模型端点ID');
        return;
    }
    
    if (!userContent) {
        showError('请输入用户消息');
        return;
    }
    
    // 验证logit_bias格式（如果提供）
    let logitBias = null;
    if (logitBiasText) {
        try {
            logitBias = JSON.parse(logitBiasText);
            if (typeof logitBias !== 'object' || logitBias === null || Array.isArray(logitBias)) {
                showError('logit_bias必须是一个JSON对象，例如：{"861": -100, "854": -100}');
                return;
            }
        } catch (e) {
            showError('logit_bias格式错误，请输入有效的JSON格式，例如：{"861": -100, "854": -100}');
            return;
        }
    }
    
    // 保存配置到localStorage
    localStorage.setItem('apiKey', apiKey);
    localStorage.setItem('baseUrl', baseUrl);
    localStorage.setItem('modelEndpoint', modelEndpoint);
    localStorage.setItem('modelId', modelId);
    localStorage.setItem('logitBias', logitBiasText);
    
    // 禁用发送按钮并显示加载状态
    sendBtn.disabled = true;
    btnText.style.display = 'none';
    loadingSpinner.style.display = 'inline-block';
    
    // 清除之前的响应
    responseContent.innerHTML = '<p class="placeholder">正在处理您的请求...</p>';
    responseContent.className = '';
    usageInfo.style.display = 'none';
    
    // 如果启用多轮对话，先将用户消息添加到历史记录
    if (isMultiTurnEnabled) {
        addToHistory('user', userContent);
    }
    
    try {
        // 构建包含历史记录的消息列表
        const messages = buildMessagesWithHistory(systemContent, userContent);
        
        const requestData = {
            api_key: apiKey,
            base_url: baseUrl,
            model_endpoint: modelEndpoint,
            model_id: modelId,
            messages: messages,  // 发送完整的消息列表而不是单独的字段
            multi_turn: isMultiTurnEnabled
        };
        
        // 只有在提供了logit_bias时才添加到请求中
        if (logitBias) {
            requestData.logit_bias = logitBias;
        }
        
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 显示成功响应
            responseContent.textContent = data.response;
            responseContent.className = 'success';
            
            // 如果启用多轮对话，将助手回复添加到历史记录
            if (isMultiTurnEnabled) {
                addToHistory('assistant', data.response);
                // 清空用户输入框，准备下一轮对话
                document.getElementById('user-input').value = '';
            }
            
            // 显示token使用情况
            if (data.usage) {
                document.getElementById('prompt-tokens').textContent = data.usage.prompt_tokens;
                document.getElementById('completion-tokens').textContent = data.usage.completion_tokens;
                document.getElementById('total-tokens').textContent = data.usage.total_tokens;
                usageInfo.style.display = 'block';
            }
        } else {
            // 显示错误
            showError(data.error || '请求失败');
        }
        
    } catch (error) {
        console.error('请求错误:', error);
        showError('网络请求失败，请检查网络连接');
    } finally {
        // 恢复发送按钮状态
        sendBtn.disabled = false;
        btnText.style.display = 'inline';
        loadingSpinner.style.display = 'none';
    }
}

function showError(message) {
    const responseContent = document.getElementById('response-content');
    const usageInfo = document.getElementById('usage-info');
    
    responseContent.textContent = `错误: ${message}`;
    responseContent.className = 'error';
    usageInfo.style.display = 'none';
}

function clearInputs() {
    // 询问是否清除API密钥和端点配置
    const clearConfig = confirm('是否同时清除API密钥、请求地址、端点和模型配置？\n\n点击"确定"清除所有内容\n点击"取消"仅清除消息内容');
    
    if (clearConfig) {
        document.getElementById('api-key').value = '';
        document.getElementById('base-url').value = '';
        document.getElementById('model-endpoint').value = '';
        document.getElementById('model-id').value = '';
        localStorage.removeItem('apiKey');
        localStorage.removeItem('baseUrl');
        localStorage.removeItem('modelEndpoint');
        localStorage.removeItem('modelId');
    }
    
    document.getElementById('system-input').value = '';
    document.getElementById('user-input').value = '';
    document.getElementById('response-content').innerHTML = '<p class="placeholder">点击"发送消息"按钮开始对话...</p>';
    document.getElementById('response-content').className = '';
    document.getElementById('usage-info').style.display = 'none';
}

// 添加一些示例提示
function showExamples() {
    const examples = [
        {
            system: "你是一个专业的翻译助手，擅长中英文翻译。",
            user: "请将以下中文翻译成英文：人工智能正在改变我们的世界。"
        },
        {
            system: "你是一个创意写作助手，能够帮助用户创作各种类型的文本。",
            user: "请为我写一首关于春天的短诗。"
        },
        {
            system: "你是一个编程助手，精通多种编程语言。",
            user: "请用Python写一个计算斐波那契数列的函数。"
        }
    ];
    
    const randomExample = examples[Math.floor(Math.random() * examples.length)];
    
    if (confirm('是否要加载一个示例对话？')) {
        document.getElementById('system-input').value = randomExample.system;
        document.getElementById('user-input').value = randomExample.user;
    }
}

// 添加快捷键提示
document.addEventListener('DOMContentLoaded', function() {
    const userInput = document.getElementById('user-input');
    userInput.title = '提示：按 Ctrl+Enter 快速发送消息';
});

// 批量请求功能
let batchResults = [];
let batchTaskId = null;
let batchAbortController = null;
let heartbeatInterval = null;

// 自定义超时设置（毫秒）
const BATCH_REQUEST_TIMEOUT = 30 * 60 * 1000; // 30分钟
const HEARTBEAT_INTERVAL = 30 * 1000; // 30秒心跳

async function startBatchRequest() {
    const batchBtn = document.getElementById('batch-btn');
    const batchBtnText = document.getElementById('batch-btn-text');
    const batchLoadingSpinner = document.getElementById('batch-loading-spinner');
    const batchProgress = document.getElementById('batch-progress');
    const batchResults = document.getElementById('batch-results');
    
    // 获取批量请求参数
    const batchCount = parseInt(document.getElementById('batch-count').value);
    const batchConcurrency = parseInt(document.getElementById('batch-concurrency').value);
    
    // 验证批量请求参数
    if (!batchCount || batchCount < 1) {
        showError('请输入有效的请求次数 (最少1次)');
        return;
    }
    
    if (!batchConcurrency || batchConcurrency < 1) {
        showError('请输入有效的并发数 (最少1个)');
        return;
    }
    
    // 获取基本配置（复用单次请求的验证逻辑）
    const apiKey = document.getElementById('api-key').value.trim();
    const baseUrl = document.getElementById('base-url').value.trim();
    const modelEndpoint = document.getElementById('model-endpoint').value.trim();
    const modelId = document.getElementById('model-id').value.trim();
    const systemContent = document.getElementById('system-input').value.trim();
    const userContent = document.getElementById('user-input').value.trim();
    const logitBiasText = document.getElementById('logit-bias').value.trim();
    
    // 验证基本配置
    if (!apiKey) {
        showError('请输入API密钥');
        return;
    }
    
    if (!baseUrl) {
        showError('请输入模型请求地址');
        return;
    }
    
    try {
        new URL(baseUrl);
    } catch (e) {
        showError('请输入有效的URL地址');
        return;
    }
    
    if (!modelEndpoint) {
        showError('请输入模型端点ID');
        return;
    }
    
    if (!userContent) {
        showError('请输入用户消息');
        return;
    }
    
    // 验证logit_bias格式
    let logitBias = null;
    if (logitBiasText) {
        try {
            logitBias = JSON.parse(logitBiasText);
            if (typeof logitBias !== 'object' || logitBias === null || Array.isArray(logitBias)) {
                showError('logit_bias必须是一个JSON对象');
                return;
            }
        } catch (e) {
            showError('logit_bias格式错误，请输入有效的JSON格式');
            return;
        }
    }
    
    // 禁用批量请求按钮
    batchBtn.disabled = true;
    batchBtnText.style.display = 'none';
    batchLoadingSpinner.style.display = 'inline-block';
    
    // 显示取消按钮
    const cancelBtn = document.getElementById('cancel-batch-btn');
    if (cancelBtn) {
        cancelBtn.style.display = 'inline-block';
    }
    
    // 显示进度区域
    batchProgress.style.display = 'block';
    batchResults.style.display = 'none';
    
    // 重置进度
    updateProgress(0, batchCount, 0, 0);
    
    // 创建AbortController用于超时控制
    batchAbortController = new AbortController();
    
    // 设置自定义超时
    const timeoutId = setTimeout(() => {
        if (batchAbortController) {
            batchAbortController.abort();
            showError(`批量请求超时（${BATCH_REQUEST_TIMEOUT / 60000}分钟），请尝试减少请求数量或增加并发数`);
        }
    }, BATCH_REQUEST_TIMEOUT);
    
    // 显示超时提示
    showBatchStatus(`批量请求已开始，最大等待时间：${BATCH_REQUEST_TIMEOUT / 60000}分钟`);
    
    // 启动心跳机制，定期发送小请求保持连接活跃
    startHeartbeat();
    
    try {
        const requestData = {
            api_key: apiKey,
            base_url: baseUrl,
            model_endpoint: modelEndpoint,
            model_id: modelId,
            system_content: systemContent,
            user_content: userContent,
            batch_count: batchCount,
            batch_concurrency: batchConcurrency
        };
        
        if (logitBias) {
            requestData.logit_bias = logitBias;
        }
        
        showBatchStatus('正在发送批量请求...');
        
        const response = await fetch('/batch_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData),
            signal: batchAbortController.signal
        });
        
        // 清除超时定时器
        clearTimeout(timeoutId);
        
        if (response.ok) {
            showBatchStatus('批量请求完成，正在下载结果文件...');
            
            // 处理Excel文件下载
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `batch_results_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            // 显示完成状态
            updateProgress(batchCount, batchCount, batchCount, 0);
            showBatchComplete(batchCount, batchCount, 0, 0);
            showBatchStatus('批量请求已完成，结果文件已下载');
            
            // 显示结果区域
            batchResults.style.display = 'block';
            document.getElementById('download-btn').style.display = 'none'; // 隐藏下载按钮，因为文件已经下载
        } else {
            const errorData = await response.json();
            showError(errorData.error || '批量请求失败');
        }
        
    } catch (error) {
        // 清除超时定时器
        clearTimeout(timeoutId);
        
        console.error('批量请求错误:', error);
        
        if (error.name === 'AbortError') {
            showError('批量请求已取消或超时');
        } else {
            showError('批量请求失败，请检查网络连接');
        }
    } finally {
        // 停止心跳
        stopHeartbeat();
        
        // 清理AbortController
        batchAbortController = null;
        
        // 隐藏取消按钮
        const cancelBtn = document.getElementById('cancel-batch-btn');
        if (cancelBtn) {
            cancelBtn.style.display = 'none';
        }
        
        // 恢复批量请求按钮状态
        batchBtn.disabled = false;
        batchBtnText.style.display = 'inline';
        batchLoadingSpinner.style.display = 'none';
    }
}

function updateProgress(completed, total, successCount, errorCount) {
    const progressText = document.getElementById('progress-text');
    const successCountEl = document.getElementById('success-count');
    const errorCountEl = document.getElementById('error-count');
    const progressFill = document.getElementById('progress-fill');
    
    progressText.textContent = `${completed}/${total}`;
    successCountEl.textContent = successCount;
    errorCountEl.textContent = errorCount;
    
    const percentage = total > 0 ? (completed / total) * 100 : 0;
    progressFill.style.width = `${percentage}%`;
}

function showBatchComplete(total, success, failed, duration) {
    const totalRequestsEl = document.getElementById('total-requests');
    const finalSuccessCountEl = document.getElementById('final-success-count');
    const finalErrorCountEl = document.getElementById('final-error-count');
    const totalDurationEl = document.getElementById('total-duration');
    
    totalRequestsEl.textContent = total;
    finalSuccessCountEl.textContent = success;
    finalErrorCountEl.textContent = failed;
    totalDurationEl.textContent = duration || '已完成';
}

// 心跳机制函数
function startHeartbeat() {
    // 每30秒发送一个轻量级请求保持连接活跃
    heartbeatInterval = setInterval(async () => {
        try {
            // 发送一个简单的健康检查请求
            await fetch('/health', {
                method: 'GET',
                cache: 'no-cache'
            });
            console.log('心跳检查成功');
        } catch (error) {
            console.warn('心跳检查失败:', error);
        }
    }, HEARTBEAT_INTERVAL);
}

function stopHeartbeat() {
    if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
        heartbeatInterval = null;
    }
}

// 批量请求状态显示函数
function showBatchStatus(message) {
    // 在进度区域显示状态信息
    const statusEl = document.getElementById('batch-status');
    if (statusEl) {
        statusEl.textContent = message;
        statusEl.style.display = 'block';
    } else {
        // 如果没有状态元素，在控制台显示
        console.log('批量请求状态:', message);
    }
}

// 添加取消批量请求的功能
function cancelBatchRequest() {
    if (batchAbortController) {
        batchAbortController.abort();
        showBatchStatus('用户取消了批量请求');
    }
}