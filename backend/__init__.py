
import json
import os

from backend.chat import handle_chat_message
from backend.chat.chat_uti import History

import re
import asyncio
import websockets
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import threading

from backend.file import update_display, handle_file_message
from backend.file.file_uti import read_file_tree, create_file_structure
from others.const import TCP_PORT, WEBSOCKET_PORT, USERS_ZONE_ROOT_PATH, CURRENT_HANDLING_FILE_FOLDER_NAME, \
    USER_ZONE_BASIC_CONFIG
from urllib.parse import parse_qs, urlparse


user_sessions = {}

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
        "current_viewing_directory": "",
        "current_file_selection": None
    }
    await update_display(websocket, user_sessions[websocket],["tree/","expl/"])
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
        #pynvml.nvmlShutdown()
        user_sessions.pop(websocket, None)
        print(f"清理会话: {websocket.remote_address}")


# 与前端交流的配置---------------------------------------------------------------------------------------------------------
# ... (保留原有的HTTP服务器和main函数代码)
class MyHTTPRequestHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        # 修改基础目录为 static 文件夹
        super().__init__(*args, directory="frontend", **kwargs)

    def do_GET(self):
        # 将根路径重定向到 index.html
        if self.path == '/':
            self.path = '/page_layout.html'
        return super().do_GET()


def start_http_server():
    handler = MyHTTPRequestHandler
    httpd = TCPServer(("", TCP_PORT), handler)
    httpd.serve_forever()


async def main():
    # 启动HTTP服务器在一个单独的线程中
    http_thread = threading.Thread(target=start_http_server)
    http_thread.daemon = True
    http_thread.start()

    # 启动WebSocket服务器
    async with websockets.serve(handle_websocket, "0.0.0.0", WEBSOCKET_PORT):
        print(f"WebSocket服务器运行在 ws://localhost:{WEBSOCKET_PORT}")
        await asyncio.Future()  # 永久运行


if __name__ == "__main__":
    asyncio.run(main())