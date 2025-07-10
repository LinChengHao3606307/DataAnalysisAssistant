# DataAnalysisAssistant - 数据分析助手

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 现代浏览器（支持 WebSocket）
- Conda 环境管理器

### 启动步骤
1. **克隆项目**
   ```bash
   git clone https://github.com/LinChengHao3606307/DataAnalysisAssistant.git
   ```

2. **进入项目目录**
   ```bash
   cd DataAnalysisAssistant
   ```

3. **创建并激活 Conda 环境**
   ```bash
   conda env create -f environment.yml
   conda activate dda
   ```

4. **启动服务器**
   ```bash
   # 使用默认配置启动
   python main.py
   
   # 或使用自定义端口启动
   python main.py --http-port 8080 --ws-port 8088
   
   # 查看所有可用选项
   python main.py --help
   ```

5. **访问应用**
   - 打开浏览器访问 `http://localhost:8102` (或自定义端口)
   - WebSocket 服务器运行在 `ws://localhost:8108` (或自定义端口)

### 功能特性
- ✅ 文件拖拽上传
- ✅ 文件树和浏览器双视图
- ✅ 实时 AI 对话
- ✅ 文件操作（移动、删除、重命名）
- ✅ GPU 使用率监控（显存、温度、风扇、功率）
- ✅ 波浪动画效果（根据GPU使用率动态调整）
- ✅ 代码执行和结果显示
- ✅ 多用户支持
- ✅ 流式响应和子框系统

## ⚙️ 配置选项

### 命令行参数
启动服务器时可以使用以下命令行参数：

```bash
python main.py [选项]

选项:
  --http-port INT     HTTP服务器端口 (默认: 8102)
  --ws-port INT      WebSocket服务器端口 (默认: 8108)
  --host STR         服务器主机地址 (默认: 0.0.0.0)
  --debug            启用调试模式
  --ollama-url STR   Ollama API地址 (默认: http://127.0.0.1:11434/api/generate)
  --main-model STR   主要模型名称 (默认: deepseek-r1:latest)
  --assistant-model STR 助手模型名称 (默认: deepseek-r1:latest)
  --assistant-retry INT 助手模型最大重试次数 (默认: 5)
  -h, --help         显示帮助信息
```

**使用示例：**
```bash
# 使用自定义端口
python main.py --http-port 8080 --ws-port 8088

# 指定主机地址
python main.py --host 127.0.0.1 --http-port 9000

# 启用调试模式
python main.py --debug

# 使用自定义Ollama配置
python main.py --ollama-url http://192.168.1.100:11434/api/generate --main-model llama2:7b

# 使用不同的助手模型
python main.py --assistant-model codellama:7b --assistant-retry 3

# 完整配置示例
python main.py --http-port 8080 --ws-port 8088 --ollama-url http://localhost:11434/api/generate --main-model deepseek-coder:6.7b --assistant-model llama2:7b --assistant-retry 5
```

### 配置文件修改
可以通过修改 `others/const.py` 文件来更改默认配置：

```python
# 服务器端口配置
WEBSOCKET_PORT = 8108  # WebSocket服务器端口
TCP_PORT = 8102        # HTTP服务器端口

# Ollama API配置
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAMES = ["deepseek-r1:latest"]
MAIN_MODEL = "deepseek-r1:latest"
ASSISTANT_MODEL = "deepseek-r1:latest"

# 路径配置
OTHERS_ROOT_PATH = os.path.dirname(__file__)
UPLOADED_FILES_ROOT_PATH = os.path.join(OTHERS_ROOT_PATH, "uploaded_files")
USERS_ZONE_ROOT_PATH = os.path.join(OTHERS_ROOT_PATH, "users")
```

**主要配置项说明：**
- `WEBSOCKET_PORT`: WebSocket服务器端口
- `TCP_PORT`: HTTP服务器端口
- `OLLAMA_API_URL`: Ollama API地址
- `MODEL_NAMES`: 可用的模型列表
- `MAIN_MODEL`: 主要使用的模型
- `ASSISTANT_MODEL`: 助手模型
- `UPLOADED_FILES_ROOT_PATH`: 上传文件存储路径
- `USERS_ZONE_ROOT_PATH`: 用户工作区路径

---

## 项目概述
这是一个基于 WebSocket 的实时数据分析助手系统，提供文件管理、AI 驱动的数据分析功能和 GPU 监控。系统采用双面板设计，左侧为文件管理区域，右侧为 AI 对话区域，支持实时波浪动画效果和 GPU 使用率可视化。

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
- **子框系统**: 支持结构化信息展示（代码、原始文本、Markdown、思考过程）
- **上下文管理**: 自动包含相关文件信息到对话上下文
- **代码执行**: 支持 Python 代码的实时执行和结果显示
- **工作流系统**: 基于对话历史的多轮交互分析流程

#### **3. 实时监控**
- **GPU 监控**: 实时显示 GPU 使用率、显存使用率
- **波浪动画**: 根据 GPU 使用率动态调整波浪动画速度和高度
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

## 📁 项目结构

### 后端 `backend/`

#### `chat/` - 聊天功能模块
- **`workflows/`** - 响应前端主要任务的主体与配件
  - **`action_executors/`** - (参数化)回答 → 硬件执行 → (optional)结果
    - 模型能调用的各种程序，如: `script_executor.py` (Python代码执行器)
  - **`ask_llm.py`** - 完整场景问题 → 主力/助理LLM → 原始回答
    - 仅调用LLM回答问题，也是直接调用LLM的唯一函数，会与前端交互
    - 只固定支持 though，response，code 等常见块
  - **`hints/`** - 需求 → 长文本提示词
    - 存储不同任务侧重可能需要的提示，就是一个词典，包含:
      - `__init__.py`: Hint类，负责加载需要的json文件
      - 各种具体的 `hint.json` (如 `plot_graph_h1.json`)
  - **`conversation_handlers/`** - 格式化回答的组件
    - 历史(截至到问题提出) → 视角变换 & 响应模式定义 → 完整场景问题
    - 原始回答 → 助理LLM → JSON回答 → (参数化)回答
    - 包含:
      - `__init__.py`: 通用的Prompt类，负责:
        - **格式化提问**: runtime_input:history → init_para:character_map + history → mh(经过选择性屏蔽与角色带入的历史) → mh + init_para:task_description → mh + init_para:answer_format_dict → full_prompt
        - **解析回答**: runtime_input:latest_response → init_para:answer_format_dict → ask_llm → JSON_ans → JSON_ans + init_para:answer_format_dict → parameterized_response
      - 各种具体的 `prompt.json` (如 `da_conductor_p1.json`, `da_supervisor_p1.json`)
  - **`main_scripts/`** - 主要工作流脚本
    - 历史(截至到问题提出) → 分段行动 & 前端响应 → 历史(截止到回答完成)
    - 包括`simple_workflow.py`在内的，调用以上组件完成工作的程序，也可互相调用

  - **`chat_assist.py`** - 杂务 → 分类处理 → 回应
  - 响应前端杂事（如：清空历史，打断，新对话，管理历史...）
  - 当前为空文件，预留扩展接口
- **`chat_uti.py`** - 工具包
- **`__init__.py`** - 处理全部发生在 chat_zone 的前端事件
  - 前端事件 → 主要任务 & 杂物
  - 主要任务 + 用户历史 → 历史(截至到问题提出) → main_workflow.py → 历史(截止到回答完成)
  - 杂务 → chat_uti.py → 回应

#### `file/` - 文件管理模块
- **`file_uti.py`** - 文件请求处理工具
- **`__init__.py`** - 处理全部发生在 file_zone 的前端事件

#### `gpu_monitor.py` - GPU监控模块
- **GPU信息获取**: 使用pynvml库获取GPU显存、温度、风扇、功率信息
- **实时监控**: 异步监控GPU状态并推送到前端
- **多GPU支持**: 支持监控多个GPU设备

#### `__init__.py` - 主入口
- 处理全部前端事件

### 前端 `frontend/`

#### `app/` - 应用逻辑
- **`app_left.js`** - file_zone的全部前端逻辑
- **`app_right.js`** - chat_zone的全部前端逻辑
- **`wave_controller.js`** - 波浪动画控制器，根据GPU使用率动态调整动画

#### `styles/` - 样式文件
- **`style_left.css`** - file_zone的样式
- **`style_right.css`** - chat_zone的样式
- **`wave_animation.css`** - 波浪动画样式

#### `assets/` - 静态资源
- **波浪图片**: 多种颜色的波浪动画素材

#### `page_layout.html` - 整体页面

### 其他 `others/`

#### `uploaded_files/` - 用户上传文件存储
- 存储用户上传的文件

#### `users/` - 用户工作区
- 每个用户的独立工作目录和会话数据

#### `history/` - 历史记录
- 系统历史数据存储

#### `const.py` - 项目配置
- 项目默认值和配置常量
