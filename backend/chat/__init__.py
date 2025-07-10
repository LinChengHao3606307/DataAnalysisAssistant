import json
import uuid
from backend.chat.chat_uti import send_whole_chat_content
from backend.file.file_uti import get_file_info
from backend.chat.workflows.main_scripts.simple_workflow import work_on

async def handle_chat_message(websocket, data, user_session):
    """处理所有聊天相关操作"""
    if data["type"] == "chat-user-message":
        if user_session["active"]:
            await websocket.send(json.dumps({
                "type": "system-error",
                "error": "请等待当前请求完成"
            }))
            return
        msg_id = f"user_msg_{uuid.uuid4()}"
        await websocket.send(json.dumps({
            "type": f"chat-user-start",
            "msg_id": msg_id
        }))
        request = ""

        if user_session["current_handling_file_tree"] is not None:
            file_info = get_file_info(user_session)
            request += "可能相关的文件:\n" + file_info + "\n"
            await websocket.send(json.dumps({
                "type": "chat-user-subbox-start",
                "msg_id": msg_id,
                "subbox_name": "可能相关的文件",
                "subbox_color": "#000000",
                "text_color": "#BBBBBB",
                "atb_str": "code"
            }))
            await send_whole_chat_content(
                websocket,
                file_info,
                msg_id=msg_id,
                prefix="user"
            )
            await websocket.send(json.dumps({
                "type": "chat-user-subbox-done",
                "msg_id": msg_id
            }))
        user_prompt = "需求:\n" + data.get("content", "")
        await websocket.send(json.dumps({
            "type": "chat-user-subbox-start",
            "msg_id": msg_id,
            "subbox_name": "需求",
            "subbox_color": "#D8CEBB",
            "text_color": "#000000",
            "atb_str": "raw"
        }))
        await send_whole_chat_content(
            websocket,
            data.get("content", ""),
            msg_id=msg_id,
            prefix="user"
        )
        await websocket.send(json.dumps({
            "type": "chat-user-subbox-done",
            "msg_id": msg_id
        }))
        request += user_prompt
        user_session["history"].add_history(character_id=0, title="request", content=request)
        await websocket.send(json.dumps({
            "type": f"chat-user-done",
            "msg_id": msg_id
        }))
        print("1 "*50)
        await work_on(
            websocket,
            user_session
        )