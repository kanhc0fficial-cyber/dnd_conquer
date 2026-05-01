# DnD Conquer - Interactive Fiction Engine

这是一个基于 D&D (龙与地下城) 规则体系与大语言模型 (LLM) 驱动的互动小说/游戏状态推进引擎。该项目通过模拟“推进一天”的核心循环，处理玩家的输入行动，并利用 LLM 自动生成沉浸式的叙事文本，同时通过工具调用 (Tool Use) 自动以 JSON Patch 的形式对系统背后的角色、地点及世界状态进行动态更新。

## 核心组件

*   **`demo_advance_day.py`**: 游戏推进的主脚本。
    *   读取 `package/` 目录下的世界状态、角色设定和地理位置信息（`world.json`, `characters.json`, `grove_locations.json`）。
    *   结合 `base_prompt.txt` 中定义的小说风格与约束条件，将游戏状态通过上下文注入给大语言模型。
    *   解析大模型的输出：分为叙事文本部分和基于 JSON Patch 的工具调用指令。
    *   将工具调用的结果应用到当前的游戏状态内存中，并写回 JSON 文件实现持久化更新。
*   **`debug_server.py` & `debug.html`**: 调试前端服务器及 Web 界面。
    *   为开发者提供一个可视化的 Web 页面用于测试系统和观察状态变化。
    *   允许直接在前端查看当前各个 JSON 文件的结构与变量。
    *   可以在前端页面直接发起“行动”，观测模型思考的过程与修改游戏数据的 JSONPatch 日志。

## 如何运行与调试

1.  **启动调试服务器**：
    在项目根目录下，运行以下命令启动调试服务器：
    ```bash
    python debug_server.py
    ```
    *(默认端口为 8765)*

2.  **访问调试面板**：
    在浏览器中打开 `http://localhost:8765`。
    
3.  **使用面板进行交互测试**：
    *   在面板中你可以查阅当前的 State JSON（如世界、角色属性）。
    *   在输入框中输入玩家的测试行动。
    *   点击“运行 Demo”，通过控制台实时查看大模型的叙事生成和对 `JSON` 的 Patch 覆盖结果。

## 环境配置

运行前需要确保已设置正确的环境变量以便访问大模型 API：
*   `OPENAI_API_KEY`: 您的模型 API 密钥。
*   `OPENAI_BASE_URL`: API 端点地址。
*   `OPENAI_MODEL`: 模型名称 (例如 `gemini-3.1-pro-preview`)。
