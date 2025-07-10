import time
import os
WEBSOCKET_PORT = 8108
TCP_PORT = 8102
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAMES = ["deepseek-r1:latest"]
MAIN_MODEL = "deepseek-r1:latest"
ASSISTANT_MODEL = "deepseek-r1:latest"
ASSISTANT_MAX_RETRY = 5
OTHERS_ROOT_PATH = os.path.dirname(__file__)
UPLOADED_FILES_ROOT_PATH = os.path.join(OTHERS_ROOT_PATH, "uploaded_files")
USERS_ZONE_ROOT_PATH = os.path.join(OTHERS_ROOT_PATH, "users")

CURRENT_HANDLING_FILE_FOLDER_NAME = "current_handling_files"
USER_ZONE_BASIC_CONFIG = {
    "current_handling_files": {},
    "state.txt": {},
    "history": {}
}

POSSIBLE_CODE_TYPES = ["python", "json"]


if __name__ == "__main__":
    import aiohttp
    import asyncio
    import json
    import time
    from collections import defaultdict

    # 全局接收池和统计工具
    response_queue = asyncio.Queue()
    timing_data = []
    start_time = time.perf_counter()


    def avg(data):
        return sum(data) / len(data) if data else 0


    async def query_ollama(prompt, delay):
        """发送请求到Ollama，支持延迟启动"""
        await asyncio.sleep(delay)  # ✅ 使用异步睡眠，不阻塞事件循环
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    "http://127.0.0.1:11434/api/generate",
                    json={"model": "deepseek-r1:32b", "prompt": prompt, "stream": True}
            ) as resp:
                async for line in resp.content:
                    if line:
                        chunk = json.loads(line.decode())
                        if "response" in chunk:
                            await response_queue.put(chunk["response"])


    async def result_consumer():
        """实时从队列消费数据并打印"""
        while True:
            start_t = time.perf_counter()
            response = await response_queue.get()
            interval = (time.perf_counter() - start_t) * 1000  # 毫秒
            print(f"响应间隔: {interval:.1f}ms | 内容: {response} ")
            timing_data.append(interval)
            response_queue.task_done()


    async def test(prompt_confs):
        consumer_task = asyncio.create_task(result_consumer())
        await asyncio.gather(*[query_ollama(*p) for p in prompt_confs])
        await response_queue.join()
        consumer_task.cancel()
        print("\n" * 5)
        print(f"平均间隔: {avg(timing_data[1:]):.1f}ms\n")
        timing_data.clear()


    async def main():
        print("=== 测试1: 单请求（无延迟）===")
        prompts = [("list 3 linux command", 0)]
        await test(prompts)

        print("=== 测试2: 双请求（第二个延迟5秒）===")
        prompts = [
            ("what are the most famous colleges in USA", 0),  # 立即开始
            ("如何在电脑里创建Linux虚拟机", 5)  # 5秒后开始
        ]
        await test(prompts)

        print("=== 测试3: 3请求 ===")
        prompts = [
            ("what are the most famous colleges in USA", 0),  # 立即开始
            ("如何在电脑里创建Linux虚拟机", 5),  # 5秒后开始
            ("讲讲谷歌的历史", 2)
        ]
        await test(prompts)



    asyncio.run(main())
