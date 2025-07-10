# DataAnalysisAssistant - 数据分析助手

## 项目概述
这是一个基于 WebSocket 的实时数据分析助手系统，提供文件管理和 AI 驱动的数据分析功能。

## 前后端交互设计原则

### 🏗️ 架构设计

#### **1. 双服务器架构**
- **HTTP 服务器** (端口 8102): 提供静态文件服务
- **WebSocket 服务器** (端口 8108): 处理实时双向通信

#### **2. 消息路由机制**
```javascript
// 前端统一消息路由
if (msg.type.startsWith('file-') || msg.type === 'gpu-usage') {
    // 文件操作消息 → 左侧面板处理
    window.dispatchEvent(new CustomEvent('left-panel-event', { detail: msg }));
} else {
    // 聊天消息 → 右侧面板处理
    window.dispatchEvent(new CustomEvent('chat-event', { detail: msg }));
}
```

#### **3. 后端消息分发**
```python
# 根据消息类型前缀路由到不同处理器
if data.get("type", "").startswith("file-"):
    await handle_file_message(websocket, data, user_session)
elif data.get("type", "").startswith("chat-") or data.get("type") == "ping":
    await handle_chat_message(websocket, data, user_session)
```

### 📡 通信协议

#### **1. 认证机制**
```javascript
// 前端连接时发送认证消息
ws.send(JSON.stringify({
    type: "auth",
    user_id: getOrCreateUserId()
}));
```

#### **2. 消息格式规范**
- **请求消息**: `{ type: "操作类型", ...其他参数 }`
- **响应消息**: `{ type: "响应类型", ...响应数据 }`
- **流式消息**: 支持分块传输，用于大文件和大文本

#### **3. 错误处理**
```python
# 统一错误响应格式
await websocket.send(json.dumps({
    "type": "system-error",
    "error": "错误描述"
}))
```

### 🔄 状态管理

#### **1. 会话状态**
```python
user_sessions[websocket] = {
    "client_id": user_id,
    "active": False,                    # 是否正在处理请求
    "history": History(),               # 对话历史
    "current_uploading_file": None,     # 当前上传文件
    "current_handling_file_tree": None, # 当前文件树
    "current_viewing_directory": None,  # 当前浏览目录
    "current_file_selection": None      # 当前选中文件
}
```

#### **2. 状态同步**
- 文件操作后自动更新相关视图
- 支持增量更新和全量更新
- 状态变更通过 WebSocket 实时推送到前端

### 🎯 功能模块设计

#### **1. 文件管理模块**
- **操作类型**: `file-upload-start`, `file-move`, `file-delete`, `file-rename` 等
- **视图更新**: 操作完成后自动更新文件树和浏览器视图
- **拖拽支持**: 支持文件在树形结构和浏览器之间拖拽

#### **2. 聊天模块**
- **流式响应**: 支持实时流式文本输出
- **子框系统**: 支持结构化信息展示（代码、原始文本、Markdown）
- **上下文管理**: 自动包含相关文件信息到对话上下文

#### **3. 实时监控**
- **GPU 监控**: 实时显示 GPU 使用率
- **内存监控**: 监控 JavaScript 内存使用情况

### 🔧 技术实现细节

#### **1. 事件委托**
```javascript
// 使用事件委托避免重复绑定
function setupEventDelegation() {
    if (window._eventDelegationSetup) {
        return; // 防止重复设置
    }
    // 设置事件监听器
    window._eventDelegationSetup = true;
}
```

#### **2. 文件传输**
- **分块上传**: 大文件分块传输，支持进度显示
- **二进制传输**: 支持二进制文件传输
- **断点续传**: 支持上传中断后恢复

#### **3. 用户隔离**
- **用户工作区**: 每个用户有独立的工作目录
- **会话隔离**: WebSocket 连接与用户会话绑定
- **数据持久化**: 用户数据持久化存储

### 🚀 扩展性设计

#### **1. 模块化架构**
- 前端按功能模块分离（左侧文件管理，右侧聊天）
- 后端按业务逻辑分离（文件处理、聊天处理）
- 支持插件式扩展

#### **2. 消息类型扩展**
- 通过消息类型前缀实现功能扩展
- 支持自定义消息处理器
- 向后兼容的消息格式

#### **3. 多用户支持**
- 基于用户 ID 的会话管理
- 支持多用户并发访问
- 用户数据隔离

---

# 项目结构
***
## 后端 `backend`
- <h3>`chat`</h3>
  - `workflows`
    - *响应 <u>前端主要任务</u> 的主体与配件*
    <br> </br>
    - `action_executors`
      - <u>(参数化)回答 -> 硬件执行 -> (optional)结果</u>
      - *模型能调用的各种程序，如:* `code_executor.py`
    <br> </br>
    - `ask_llm.py`
      - <u>完整场景问题 -> 主力/助理LLM -> 原始回答</u>
      - *仅调用LLM回答问题，也是直接调用LLM的唯一函数，会与前端交互*
      - *只固定支持 though，response，code 等常见块*
    <br> </br>
    - `hints`
      - <u>需求 -> 长文本提示词</u>
        - *存储不同任务侧重可能需要的提示，就是一个词典，包含*
          - `__init__.py`:*Hint类，负责加载需要的json文件*
          - *各种具体的`hint.json`*
    <br> </br>
    - `conversation_handlers`
      - <u>历史(截至到问题提出) -> 视角变换 & 响应模式定义 -> 完整场景问题</u>
      - <u>原始回答 -> 助理LLM -> JSON回答 -> (参数化)回答</u>
      - *格式化回答的组件，包含：*
        - `__init__.py`:*通用的Prompt类，负责：*
          - *格式化提问*
            - *runtime_input:history ->*
            - *init_para:character_map + history -> mh(经过选择性屏蔽与角色带入的历史)*
            - *mh + init_para:task_description -> mh*
            - *mh + init_para:answer_format_dict -> full_prompt*
            - *-> full_prompt*
          - *解析回答*
            - *runtime_input:latest_response ->*
            - *init_para:answer_format_dict -> ask_llm -> JSON_ans*
            - *JSON_ans + init_para:answer_format_dict -> parameterized_response*
            - *parameterized_response ->*
        - *各种具体的`prompt.json`*
    <br> </br>
    - `main_scripts`
      - <u>历史(截至到问题提出) -> 分段行动 & 前端响应 -> 历史(截止到回答完成)</u>
      - *包括main_workflow在内的，调用以上组件完成工作的程序，也可互相调用*
    <br> </br>
  - `chat_assist.py`
    - <u>杂务 -> 分类处理 -> 回应</u>
    - *响应前端杂事（如：清空历史，打断，新对话，管理历史...）*
    <br> </br>
  - `chat_uti.py`
    - *工具包*
    <br> </br>
  - `__init__.py`
    - <u>前端事件 -> 主要任务 & 杂物</u>
      - <u>主要任务 + 用户历史 -> 历史(截至到问题提出) -> main_workflow.py -> 历史(截止到回答完成)</u>
      - <u>杂务 -> chat_uti.py -> 回应</u>
    - *处理全部发生在 chat_zone 的前端事件*
    <br> </br>
- <h3>`file`</h3>
  - `uti.py`
    - *文件请求处理工具*
  <br> </br>
  - `__init__.py`
    - *处理全部发生在 file_zone 的前端事件*
  <br> </br>
- <h3>`__init__.py`</h3>
  - *处理全部前端事件*
***
## 前端 `frontend`
- <h3>`app`</h3>
  - `app_left.js`
    - *file_zone的全部前端逻辑*
    <br> </br>
  - `app_right.js`
    - *chat_zone的全部前端逻辑*
    <br> </br>
- <h3>`styles`</h3>
  - `style_left.css`
    - *file_zone的样式*
    <br> </br>
  - `style_right.css`
    - *chat_zone的样式*
    <br> </br>
- <h3>`page_layout.html`</h3>
  - *整体页面*
  <br> </br>
***
## 其他 `others`
- <h3>`uploaded_files`</h3>
  - *描用户上传的文件*
- <h3>`const.py`</h3>
  - *项目默认值*

---

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 现代浏览器（支持 WebSocket）

### 启动步骤
1. **安装依赖**
   ```bash
   pip install websockets
   ```

2. **启动服务器**
   ```bash
   python main.py
   ```

3. **访问应用**
   - 打开浏览器访问 `http://localhost:8102`
   - WebSocket 服务器运行在 `ws://localhost:8108`

### 功能特性
- ✅ 文件拖拽上传
- ✅ 文件树和浏览器双视图
- ✅ 实时 AI 对话
- ✅ 文件操作（移动、删除、重命名）
- ✅ GPU 使用率监控
- ✅ 多用户支持

## 🔧 开发指南

### 添加新的消息类型
1. **前端**: 在相应的事件处理器中添加新消息类型
2. **后端**: 在消息路由中添加新的处理器
3. **测试**: 确保前后端消息格式一致

### 扩展文件操作
1. **后端**: 在 `backend/file/__init__.py` 中添加新的处理逻辑
2. **前端**: 在 `frontend/app/app_left.js` 中添加相应的 UI 交互
3. **更新**: 确保操作后调用 `update_display` 更新视图

### 自定义聊天功能
1. **后端**: 在 `backend/chat/workflows/` 中添加新的工作流
2. **前端**: 在 `frontend/app/app_right.js` 中添加新的消息类型处理
3. **集成**: 确保与现有的流式响应系统兼容

## 📝 注意事项

### 性能优化
- 大文件传输使用分块上传
- 使用事件委托避免重复绑定
- 及时清理无用的 WebSocket 连接

### 安全考虑
- 用户数据隔离
- 文件路径验证
- 输入参数检查

### 错误处理
- 统一的错误响应格式
- 前端友好的错误提示
- 连接断开自动重连
