import json
import os
import re
import asyncio
import websockets
import argparse
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import threading
from urllib.parse import parse_qs, urlparse

from backend.chat import handle_chat_message
from backend.chat.chat_uti import History
from backend.file import update_display, handle_file_message
from backend.file.file_uti import read_file_tree, create_file_structure
from backend.gpu_monitor import gpu_monitor, start_gpu_monitoring
from others.const import TCP_PORT, WEBSOCKET_PORT, USERS_ZONE_ROOT_PATH, CURRENT_HANDLING_FILE_FOLDER_NAME, \
    USER_ZONE_BASIC_CONFIG

user_sessions = {}

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='DataAnalysisAssistant - 数据分析助手服务器')
    parser.add_argument('--http-port', type=int, default=TCP_PORT,
                       help=f'HTTP服务器端口 (默认: {TCP_PORT})')
    parser.add_argument('--ws-port', type=int, default=WEBSOCKET_PORT,
                       help=f'WebSocket服务器端口 (默认: {WEBSOCKET_PORT})')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='服务器主机地址 (默认: 0.0.0.0)')
    parser.add_argument('--debug', action='store_true',
                       help='启用调试模式')
    
    # Ollama相关配置
    parser.add_argument('--ollama-url', type=str, default=None,
                       help='Ollama API地址 (默认: http://127.0.0.1:11434/api/generate)')
    parser.add_argument('--main-model', type=str, default=None,
                       help='主要模型名称 (默认: deepseek-r1:latest)')
    parser.add_argument('--assistant-model', type=str, default=None,
                       help='助手模型名称 (默认: deepseek-r1:latest)')
    parser.add_argument('--assistant-retry', type=int, default=None,
                       help='助手模型最大重试次数 (默认: 5)')
    
    return parser.parse_args()


def handle_user_work_zone_initiation(client_id):
    all_users_wz = os.listdir(USERS_ZONE_ROOT_PATH)
    if client_id not in all_users_wz:
        new_user_zone_path = os.path.join(USERS_ZONE_ROOT_PATH, client_id)
        os.makedirs(new_user_zone_path, exist_ok=True)
        create_file_structure(base_path=new_user_zone_path, file_tree=USER_ZONE_BASIC_CONFIG)


async def handle_websocket(websocket, path=None):
    """WebSocket连接处理器 - 主路由"""
    print(f"新客户端连接: {websocket.remote_address}")

    try:
        # 1. 等待首条消息（认证消息）
        first_message = await websocket.recv()
        data = json.loads(first_message)

        # 2. 验证消息类型并提取 user_id
        if data.get("type") == "auth":
            user_id = data.get("user_id", "unknown")
            print(f"User connected: {user_id}")
        else:
            await websocket.close(code=1008, reason="Auth required")
            return
    except Exception as e:
        print(f"认证失败: {e}")
        await websocket.close(code=1008, reason="Invalid auth")
        return

    # 3. 初始化用户工作区
    handle_user_work_zone_initiation(user_id)

    # 4. 初始化会话
    current_handling_file_tree = read_file_tree(user_id)
    user_sessions[websocket] = {
        "client_id": user_id,
        "active": False,
        "history": History(),
        "current_uploading_file": None,
        "current_handling_file_tree": current_handling_file_tree,
        "current_viewing_directory": "expl/",
        "current_file_selection": None,
        "gpu_monitoring_task": None
    }
    await update_display(websocket, user_sessions[websocket],["tree/","expl/"])
    
    # 5. 启动GPU监测任务
    if gpu_monitor.initialized:
        user_sessions[websocket]["gpu_monitoring_task"] = asyncio.create_task(
            start_gpu_monitoring(websocket, user_sessions[websocket])
        )
        print(f"为用户 {user_id} 启动GPU监测任务")
    try:
        async for message in websocket:
            try:
                if isinstance(message, str):
                    data = json.loads(message)
                    if data.get("type") == "auth":
                        user_id = data.get("user_id", "unknown")
                        print(f"User connected: {user_id}")
                    # 根据消息类型路由到不同的处理器
                    if data.get("type", "").startswith("file-"):
                        await handle_file_message(
                            websocket,
                            data,
                            user_sessions[websocket]
                        )
                    elif data.get("type", "").startswith("chat-") or data.get("type") == "ping":
                        await handle_chat_message(
                            websocket,
                            data,
                            user_sessions[websocket]
                        )
                    else:
                        await websocket.send(json.dumps({
                            "type": "system-error",
                            "error": "未知的消息类型"
                        }))
                elif isinstance(message, bytes) and user_sessions[websocket]["current_uploading_file"]:
                    user_sessions[websocket]["current_uploading_file"].write(message)

            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "type": "system-error",
                    "error": "无效的JSON格式"
                }))

    except websockets.exceptions.ConnectionClosed:
        print(f"客户端断开: {websocket.remote_address}")
    finally:
        # 清理GPU监测任务
        if websocket in user_sessions:
            gpu_task = user_sessions[websocket].get("gpu_monitoring_task")
            if gpu_task and not gpu_task.done():
                gpu_task.cancel()
                print(f"取消用户 {user_sessions[websocket]['client_id']} 的GPU监测任务")
        
        user_sessions.pop(websocket, None)
        print(f"清理会话: {websocket.remote_address}")


# 与前端交流的配置---------------------------------------------------------------------------------------------------------
class MyHTTPRequestHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        # 修改基础目录为 static 文件夹
        super().__init__(*args, directory="frontend", **kwargs)

    def do_GET(self):
        # 将根路径重定向到 index.html
        if self.path == '/':
            self.path = '/page_layout.html'
        return super().do_GET()


def start_http_server(http_port):
    handler = MyHTTPRequestHandler
    httpd = TCPServer(("", http_port), handler)
    httpd.serve_forever()


async def main():
    args = parse_arguments()
    http_port = args.http_port
    ws_port = args.ws_port
    host = args.host
    debug = args.debug

    # 应用Ollama相关配置
    if args.ollama_url:
        import others.const
        others.const.OLLAMA_API_URL = args.ollama_url
        print(f"✅ 使用自定义Ollama API地址: {args.ollama_url}")
    
    if args.main_model:
        import others.const
        others.const.MAIN_MODEL = args.main_model
        print(f"✅ 使用自定义主模型: {args.main_model}")
    
    if args.assistant_model:
        import others.const
        others.const.ASSISTANT_MODEL = args.assistant_model
        print(f"✅ 使用自定义助手模型: {args.assistant_model}")
    
    if args.assistant_retry:
        import others.const
        others.const.ASSISTANT_MAX_RETRY = args.assistant_retry
        print(f"✅ 设置助手模型最大重试次数: {args.assistant_retry}")

    # 启动HTTP服务器在一个单独的线程中
    http_thread = threading.Thread(target=start_http_server, args=(http_port,))
    http_thread.daemon = True
    http_thread.start()

    # 启动WebSocket服务器
    async with websockets.serve(handle_websocket, host, ws_port):
        print(f"WebSocket服务器运行在 ws://{host}:{ws_port}")
        print("="*20)
        print(f"打开 http://localhost:{http_port} 访问网页")
        print("="*20)
        
        # 显示GPU监测状态
        if gpu_monitor.initialized:
            print("✅ GPU监测功能已启用")
        else:
            print("⚠️ GPU监测功能不可用（需要安装pynvml库）")
            print("   运行: pip install pynvml")
        print("="*20)
        
        await asyncio.Future()  # 永久运行


if __name__ == "__main__":
    asyncio.run(main())
