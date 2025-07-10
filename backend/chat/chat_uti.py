
import asyncio
import uuid
import requests
import json
from others.const import OLLAMA_API_URL, POSSIBLE_CODE_TYPES
from typing import List

def tab_front(content:str, num_tab:int) -> str:
    result = ""
    for line in content.splitlines():
        result += "\t"*num_tab + line + "\n"
    return result

class History:
    def __init__(self):
        self.history = []

    def add_history(self, character_id: int, title: str, content: str):
        self.history.append((character_id, title, content))

    def get_characterized_history(self, c_map: List[List])->str:
        """
        :param c_map: character_id 和 character_config 的对应关系，
        格式为[
                ...,
                [角色名，1类历史记录，2类历史记录，...],
                ...
            ]
        如：
            [
                ['user','file_referred','request'], #character_id=0代表用户
                [], #屏蔽character_id=1的记录
                ['chat_bot', 'aim', 'plan', 'code', 'execution_result'] #character_id=2代表LLM
            ]
        :return: characterized_history，指定视野下的历史记录
        """
        characterized_history = "History:\n"
        prev_character = ""
        for character_id, title, content in self.history:
            if len(c_map[character_id]) != 0:
                if title in c_map[character_id][1:]:
                    if prev_character != c_map[character_id][0]:
                        characterized_history += "\t" + c_map[character_id][0] + ":\n"
                        prev_character = c_map[character_id][0]
                    characterized_history += "\t\t" + title + "\n"
                    characterized_history += tab_front(content, num_tab=3)

        return characterized_history

    def __iter__(self):
        return iter(self.history)


def clear_memory(model_name):
    """清除Ollama模型的对话上下文记忆"""
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": model_name,
                "prompt": "/clear/buy",  # 使用clear指令清除记忆
                "stream": False
            }
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"清除记忆失败: {e}")
        return False

async def send_whole_chat_content(websocket, message: str, msg_id: str = None, prefix: str = "user",
                                  chunk_size: int = 20, delay: float = 0.05):
    is_new = False
    """分段发送完整消息内容"""
    if msg_id is None:
        msg_id = f"{prefix}_msg_{uuid.uuid4()}"
        is_new = True

    if is_new:
        # 发送开始标记
        await websocket.send(json.dumps({
            "type": f"chat-{prefix}-start",
            "msg_id": msg_id
        }))

    # 分段发送内容
    length = len(message)
    for i in range(0, length, chunk_size):
        await asyncio.sleep(delay)
        chunk = message[i:i + chunk_size]
        await websocket.send(json.dumps({
            "type": f"chat-{prefix}-chunk",
            "msg_id": msg_id,
            "content": chunk
        }))
    if is_new:
        # 发送结束标记
        await websocket.send(json.dumps({
            "type": f"chat-{prefix}-done",
            "msg_id": msg_id,
            "final_text": message
        }))
    return msg_id

def generate_variations(words):
    variations = []
    for word in words:
        w = word.lower()
        variations.append(w.upper())
        variations.append(w.capitalize())
        variations.append(w)
    return variations

def extract_code_blocks(response: str, possible_code_types:list[str]=None) -> List[str]:
    """
    更健壮的代码块提取函数，能够处理各种格式的代码块标记
    返回所有找到的代码块列表
    """
    code_blocks = []
    lines = response.split('\n')
    in_code_block = False
    current_code = []
    if possible_code_types is None:
        possible_code_types = generate_variations(POSSIBLE_CODE_TYPES)
        possible_code_types.append("")
    code_block_markers = ['```'+t for t in possible_code_types]  # 支持多种代码块标记

    for line in lines:
        # 检查是否是代码块开始标记
        if any(line.startswith(marker) for marker in code_block_markers) and not in_code_block:
            in_code_block = True
            # 移除标记行中的语言标识（如"python"）
            line = line.split('```')[-1].strip()
            if line and line not in possible_code_types:
                current_code.append(line)
            continue

        # 检查是否是代码块结束标记
        if line.strip() == '```' and in_code_block:
            if current_code:  # 确保不是空代码块
                code_blocks.append('\n'.join(current_code))
            current_code = []
            in_code_block = False
            continue

        # 如果是代码块内容
        if in_code_block:
            current_code.append(line)

    # 处理最后未闭合的代码块（如果有）
    if in_code_block and current_code:
        code_blocks.append('\n'.join(current_code))

    return code_blocks