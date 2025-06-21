import copy
import json
import os

from backend.chat.chat_uti import History, tab_front, extract_code_blocks
from backend.chat.workflows.ask_llm import ask_llm
from others.const import ASSISTANT_MODEL, ASSISTANT_MAX_RETRY

prompt_of_assistant_head = """
你是一名格式转换助手兼JSON语法爱好者，请从以下回答中提取信息，填写目标JSON框架里所有的_TODO_:
注意:原回答中没有答的就填""，不可原创

原回答：

"""

prompt_of_assistant_tail = """

请注意，你的回答必须是包在```里的JSON格式的回答，参考以下格式示范:
```
{
    "q1": {
        "question": "老板最初想要什么",
        "answer_format": "str",
        "answer": "老板想要data.csv中return列的可视化"
    },
    "q2": {
        "question": "我上一步做了什么",
        "answer_format": "str",
        "answer": "我上一步用代码打印了表头，可见，data.csv里有一个名为future_5d_return的列，而没有其他与return相关的列，所以老板应该是在查询这一列"
    },
    "q3": {
        "question": "我是否已经完成了任务，知道了足够信息，这一步可以向老板汇报成果了",
        "answer_format": "bool",
        "answer": false
    },
    "q4": {
        "question": "我的具体成果",
        "answer_format": "str",
        "answer": ""
    },
    "q5": {
        "question": "我这一步要做什么",
        "answer_format": "str",
        "answer": "弄清楚列名后，我这一步计划访问这一列的数据并将其可视化"
    },
    "q6": {
        "question": "这一步需要执行的代码",
        "answer_format": "str",
        "answer": "import pandas as pd\\nimport matplotlib.pyplot as plt\\n\\n# 加载CSV文件中的数据\\ndata = pd.read_csv('data.csv')\\n\\n# 绘制 'future_5d_return' 列\\nplt.figure(figsize=(10, 6))\\nplt.plot(data['future_5d_return'], label='Future 5D Return')\\nplt.xlabel('Index')\\nplt.ylabel('Future 5D Return')\\nplt.title('Future 5D Return Over Time')\\nplt.legend()\\nplt.grid(True)\\nplt.show()"
    }
}
```
作为格式转换助手，你的结果将经过json.loads解析，所以格式务必准确
需要提醒你的是:
    用来包裹JSON的```请单占一行
    "answer_format": "str"的问题对应的答案里不能出现 " , 如 
        原答案是
            ```print("hi")```
        那么"answer"应该为
            "print('hi')"
        而非
            "print("hi")"
"""

# First create a mapping from your string type names to Python types
type_mapping = {
    "str": str,
    "bool": bool,
    "int": int,
    "float": float,
    # Add any other types you need
}


# 获取脚本的绝对路径
script_path = os.path.abspath(__file__)
print(f"脚本的绝对路径是: {script_path}")

# 获取脚本所在的目录
script_dir = os.path.dirname(script_path)
print(f"脚本所在的目录是: {script_dir}")


class ConvHandler:
    def __init__(self, name:str, assistant_name:str=ASSISTANT_MODEL):
        with open(os.path.join(script_dir, name + ".json"), encoding='utf-8') as f:
            self.json_config = json.load(f)
        self.assistant = assistant_name

    async def get_prompt(self, history:History):
        characterized_history = history.get_characterized_history(self.json_config['characters_map'])
        characterized_history += "Task:\n"
        characterized_history += tab_front(self.json_config['task_description'], num_tab=1)
        characterized_history += "\n\t回答以下问题中满足前置条件的(无条件则必答)，并空出无需回答的:\n"
        num_q = len(self.json_config['questions'])
        for i in range(num_q):
            question = self.json_config['questions'][f"q{i+1}"]
            characterized_history += f"\tq{i+1}. " + question["question"] + ": _ ("
            characterized_history += " 前置条件: " + question['prerequisite'] + " ;"
            characterized_history += " 期望回答: " + question['expected_answer'] + " )\n"
        if "remarks" in self.json_config:
            characterized_history += "Remarks:\n" + tab_front(self.json_config['remarks'], num_tab=1)
        if "examples" in self.json_config:
            characterized_history += "Examples:\n" + tab_front(self.json_config['examples'], num_tab=1)
        characterized_history += "\n\t注意按照{question}:{ans}回答就行，不要重复(前置条件:...,期望回答:...)"
        return characterized_history

    async def parse_response(self, response:str):

        # prompt形成
        prompt_of_assistant = prompt_of_assistant_head

        prompt_of_assistant += response
        prompt_of_assistant += "\n目标JSON框架:\n"
        all_q = copy.deepcopy(self.json_config['questions'])
        l = len(all_q)
        for i in range(l):
            all_q[f"q{i + 1}"]["answer"] = "_TODO_"
            all_q[f"q{i + 1}"].pop("record_type")
            all_q[f"q{i + 1}"].pop("prerequisite")
            all_q[f"q{i + 1}"].pop("expected_answer")
        prompt_of_assistant += json.dumps(all_q, indent=4) + "\n"

        prompt_of_assistant += prompt_of_assistant_tail

        # 取得带json的回答
        for i in range(ASSISTANT_MAX_RETRY):
            print("assistant's prompt" + " =" * 20)
            print(prompt_of_assistant)
            try:
                parsed_response = await ask_llm(model_name=self.assistant,prompt=prompt_of_assistant)
                parsed_response = json.loads(extract_code_blocks(parsed_response)[0])
                full_result = {}
                l = len(parsed_response)
                done = True
                for i in range(l):
                    rct = self.json_config['questions'][f"q{i + 1}"]["record_type"]
                    expected_dtype = self.json_config['questions'][f"q{i + 1}"]["answer_format"]
                    ans = parsed_response[f"q{i + 1}"]["answer"]

                    # Get the actual Python type from your mapping
                    expected_type = type_mapping.get(expected_dtype.lower())

                    if expected_type is None:
                        raise ValueError(f"Unknown expected data type: {expected_dtype}")

                    if not isinstance(ans, expected_type):
                        print("数据类型错误：")
                        ori = json.dumps(parsed_response[f"q{i + 1}"], indent=4)
                        print(ori)
                        # Handle type mismatch
                        prompt_of_assistant += f"小心不要把 q{i + 1} 的答案写成 \n{ori}"
                        done = False
                    full_result[rct] = ans

            except Exception as e:
                print("助手解析错误：")
                print(e)
                prompt_of_assistant += "\n小心不要造成json.loads时的:" + str(e)
                done = False
            if done:
                return full_result
        return None


