
from backend.chat.workflows.action_executors.script_executor import execute_script
from backend.chat.workflows.ask_llm import ask_llm
from backend.chat.chat_uti import send_whole_chat_content, History

import uuid
import json

from backend.chat.workflows.conversation_handlers import ConvHandler


async def work_on(websocket, history: History):
    """处理用户消息的完整流程"""

    msg_id = f"msg_{uuid.uuid4()}"
    conv_handler = ConvHandler("da_conductor_p1")

    # 发送聊天开始标记
    await websocket.send(json.dumps({
        "type": "chat-chatbot-start",
        "msg_id": msg_id
    }))

    while True:

        # 获取AI响应
        full_prompt = await conv_handler.get_prompt(history)
        print(full_prompt)
        response = await ask_llm("deepseek-r1:32b", full_prompt, msg_id, websocket)
        print("main llm end" + " =" * 20)

        if not response:
            break

        # 解析响应
        parsed = await conv_handler.parse_response(response)

        if parsed["is_end"]:
            history.add_history(character_id=1, title="final_result", content=parsed["final_result"])
            # 发送聊天结束标记
            await websocket.send(json.dumps({
                "type": "chat-chatbot-done",
                "msg_id": msg_id
            }))
            print("=======================================")
            return
        else:
            # 执行代码并返回结果
            history.add_history(character_id=1, title="plan", content=parsed["plan"])

            if len(parsed["code"]) > 0:
                history.add_history(character_id=1, title="code", content=parsed["code"])
                code_result = execute_script(parsed["code"])
                history.add_history(character_id=1, title="execution_result", content=code_result)

                await websocket.send(json.dumps({
                    "type": "chat-chatbot-subbox-start",
                    "msg_id": msg_id,
                    "subbox_name": "Code Result",
                    "subbox_color": "#666666",
                    "atb_str": "raw"
                }))
                # 发送代码执行结果
                await send_whole_chat_content(
                    websocket,
                    code_result,
                    msg_id=msg_id,
                    prefix="chatbot"
                )
                await websocket.send(json.dumps({
                    "type": "chat-chatbot-subbox-done",
                    "msg_id": msg_id
                }))