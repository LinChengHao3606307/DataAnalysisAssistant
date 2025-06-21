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
