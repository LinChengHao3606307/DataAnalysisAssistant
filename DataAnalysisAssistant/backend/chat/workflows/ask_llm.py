import asyncio

import requests
import aiohttp
import json
from others.const import MODEL_NAMES, OLLAMA_API_URL
from backend.chat.chat_uti import clear_memory

def spilt_signal(signal):
    if len(signal) == 0:
        return []
    re = [""]
    on_s = (signal[0] == "`")
    for i in range(len(signal)):
        if signal[i] == "`":
            if not on_s:
                re.append("")
            on_s = True
        else:
            if on_s:
                re.append("")
            on_s = False
        re[-1] += (signal[i])
    return re

def query_model_ans_only(model_name, prompt) -> str:
    clear_memory(model_name)
    data = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }
    print("query_model_ans_only")
    try:
        response = requests.post(OLLAMA_API_URL, json=data)
        response.raise_for_status()
        res = response.json()["response"]
        print(res)
        return res
    except Exception as e:
        print(f"请求模型出错: {e}")
        return None


async def handle_res(res, is_done, websocket, msg_id, state_dic):
    print(res)
    if not state_dic["is_thinking"]:
        if not "`" in res:
            if state_dic["count_continuous`"] == 3:
                print(" ``` " * 10)
                print(state_dic["split_signal_count"])
                state_dic["split_signal_count"] += 1
                await websocket.send(json.dumps({
                    "type": "chat-chatbot-subbox-done",
                    "msg_id": msg_id
                }))
                if state_dic["split_signal_count"] == 0:
                    await websocket.send(json.dumps({
                        "type": "chat-chatbot-subbox-start",
                        "msg_id": msg_id,
                        "subbox_name": "Decision",
                        "text_color": "#000000",
                        "atb_str": "markdown"
                    }))
                else:
                    await websocket.send(json.dumps({
                        "type": "chat-chatbot-subbox-start",
                        "msg_id": msg_id,
                        "subbox_name": "Python",
                        "subbox_color": "#000000",
                        "text_color": "#BBBBBB",
                        "atb_str": "code"
                    }))
            state_dic["count_continuous`"] = 0
        else:
            state_dic["count_continuous`"] += len(res)
            return
    if res == "<think>":
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        await websocket.send(json.dumps({
            "type": "chat-chatbot-subbox-start",
            "msg_id": msg_id,
            "subbox_name": "Thinking...",
            "subbox_color": "#114466",
            "text_color": "#000000",
            "atb_str": "raw"
        }))
        state_dic["is_thinking"] = True
    elif res == "</think>":
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        await websocket.send(json.dumps({
            "type": "chat-chatbot-subbox-done",
            "msg_id": msg_id
        }))
        await websocket.send(json.dumps({
            "type": "chat-chatbot-subbox-start",
            "msg_id": msg_id,
            "subbox_name": "Decision",
            "text_color": "#000000",
            "atb_str": "markdown"
        }))
        state_dic["is_thinking"] = False
    else:
        await websocket.send(json.dumps({
            "type": "chat-chatbot-chunk",
            "msg_id": msg_id,
            "content": res,
            "done": is_done
        }))

    if not state_dic["is_thinking"] and (not res == "</think>"):
        state_dic["full_response"] += res


async def ask_llm(model_name: str, prompt: str, msg_id: str = None, websocket=None) -> str:
    if websocket is None:
        return query_model_ans_only(model_name, prompt)
    """处理AI聊天流式响应"""
    assert msg_id is not None
    assert model_name in MODEL_NAMES
    clear_memory(model_name)
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": True
            }

            async with session.post(OLLAMA_API_URL, json=payload) as resp:
                state_dic = {
                    "full_response": "",
                    "is_thinking": False,
                    "count_continuous`": 0,
                    "split_signal_count": 0,
                }
                async for line in resp.content:
                    chunk = json.loads(line.decode())
                    res = spilt_signal(chunk["response"])
                    is_done = chunk.get("done", False)
                    print(res)
                    for r in res:
                        await handle_res(r, is_done, websocket, msg_id, state_dic)

            return state_dic["full_response"]
    except Exception as e:
        print(f"AI响应错误: {e}")
        await websocket.send(json.dumps({
            "type": "chat-chatbot-error",
            "msg_id": msg_id,
            "error": str(e)
        }))
        return None