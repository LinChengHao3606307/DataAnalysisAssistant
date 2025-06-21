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








Here's an optimized version of your resume with both English and Chinese sections, incorporating your internship experience into the Chinese version:

---

**ChengHao Lin**  
Email: - | GitHub: [LinChengHao3606307](https://github.com/LinChengHao3606307)

**Motivated Software Developer** with strong mathematical foundations and passion for AI/Computer Vision. Specializing in Deep Learning/Reinforcement Learning algorithms with hands-on project experience.

### Education
**University of Hong Kong**  
*BSc in Mathematics* | Expected Graduation: 2026.08

### Technical Skills
- **Languages**: Python (PyTorch), C++, Java, JavaScript/HTML
- **AI/ML**: Deep Learning, Reinforcement Learning, Computer Vision (YOLOv5)
- **Development**: Android Studio, Unity, PyGame, SOLIDWORKS
- **Tools**: Git, Pandas, OpenCV, WebSocket

---

### Project Experience

**Automated Game AI System** | Python, PyTorch, YOLOv5  
- Developed vision-based game bot using YOLOv5 for enemy detection (3-month continuous operation)
- Built LSTM/Transformer-based RL agent with custom simulator for behavioral cloning
- Implemented hardware-level input masking for undetectable operation

**2D Game Engine** | Python, PyGame  
- Designed anime-inspired PVP system with destructible terrain physics
- Implemented character class system with 4 unique ability sets
- Optimized collision detection using mask-based spatial partitioning

**Cycling Computer App** | Java, Android Studio  
- Developed real-time cycling metrics app with weather API integration
- Implemented GPS/accelerometer fusion for slope detection
- Designed battery-efficient dark mode UI

**ROBOCON Competition** | SOLIDWORKS, Mechanical Design  
- Co-designed medal-winning robotic shooter system
- Solved propulsion issue by innovating dual-piston mechanism
- Managed 3D printing and aluminum fabrication processes

---

### Professional Experience

**Quantitative Research Intern** | Yu Shun Private Equity Fund (2025.03-2025.06)  
- Developed ML pipeline for alpha factor analysis (IC improvement: +0.019)
- Researched 91 DL/RL papers; implemented formula-generating LSTM agent
- Built local LLM system with file-aware chat interface and MCP workflow
- Technologies: Pandas, PyTorch, WebSocket, Custom RL Environments

---

### Highlights
- Mathematical problem-solving approach to development
- Full-cycle project experience from research to deployment
- Strong collaborative experience (GitHub, ROBOCON)
- Passion for algorithmic optimization

---

## 中文简历优化版

**林承昊**  
邮箱: - | GitHub: [LinChengHao3606307](https://github.com/LinChengHao3606307)

**数学背景的软件开发工程师**，专注深度学习/强化学习算法与计算机视觉应用，具有从研究到部署的全周期项目经验。

### 教育背景
**香港大学**  
*数学理学学士* | 预计毕业: 2026.08

### 技术能力
- **编程语言**: Python (PyTorch), C++, Java, JavaScript/HTML
- **人工智能**: 深度学习, 强化学习, 计算机视觉 (YOLOv5)
- **开发工具**: Android Studio, Unity, PyGame, SOLIDWORKS
- **其他技能**: 量化分析, 3D建模, 硬件交互

---

### 项目经验

**自动化游戏AI系统** | Python, PyTorch, YOLOv5  
- 基于YOLOv5开发视觉识别游戏外挂（稳定运行3个月）
- 构建LSTM/Transformer架构的行为克隆模型
- 设计硬件级输入伪装方案实现完全不可检测

**2D游戏物理引擎** | Python, PyGame  
- 开发《咒术回战》风格的可破坏地形PVP系统
- 实现4种独特角色技能体系
- 优化碰撞检测算法提升性能

**骑行数据应用** | Java, Android Studio  
- 集成天气API的实时骑行数据监测应用
- 开发GPS/加速度计融合坡度检测算法
- 设计省电深色模式界面

**ROBOCON机器人大赛** | SOLIDWORKS, 机械设计  
- 共同设计获奖的气动射击机器人
- 创新双活塞结构解决动力不足问题
- 管理3D打印与铝合金加工流程

---

### 专业经历

**量化研究实习生** | 煜顺私募基金 (2025.03-2025.06)  
- 开发alpha因子分析机器学习管道（IC提升0.019）
- 研究91篇DL/RL论文，实现公式生成LSTM智能体
- 构建具备文件感知能力的本地LLM系统
- 核心技术: Pandas, PyTorch, WebSocket, 自定义RL环境

---

### 优势亮点
- 数学驱动的算法优化能力
- 完整项目周期实施经验
- 出色的团队协作能力(GitHub/ROBOCON)
- 对技术难题的持续钻研精神

---

优化要点：
1. 结构重组 - 按技术相关性重新组织项目
2. 成果量化 - 突出具体技术指标
3. 中英对应 - 保持核心内容一致性
4. 实习整合 - 将量化经历自然融入中文版
5. 重点强化 - 突出AI/数学交叉优势
6. 去除冗余 - 精简技术细节到核心亮点

需要进一步调整可告知具体方向。
