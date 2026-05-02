"""
demo_advance_day.py
测试"推进一天"的核心循环：
  - 从 package/modes/ 动态加载模式 JSON（narrative / direct_patch / level_up …）
  - 读取 world.json + characters.json + grove_locations.json 作为上下文
  - 根据模式策略（two_round / single_round_tool）调用 LLM
  - 解析返回的自然语言叙事 + JSONPatch 工具调用指令
  - 将 patch 应用到内存中的游戏状态，并打印结果
"""

import json
import os
import sys
import copy
import traceback
from openai import OpenAI

# ── Windows 控制台 UTF-8 修复 ─────────────────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 第一轮配置（叙事生成）
API_KEY  = os.environ.get("OPENAI_API_KEY", "gg-gcli-HByloFRM6KIzamEI2dH81NyjQdum8qc2KQAeZTxBYiY")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://gcli.ggchan.dev/v1")
MODEL    = os.environ.get("OPENAI_MODEL", "gemini-3.1-pro-preview")

# 第二轮配置（工具调用），默认平滑降级回第一轮配置
API_KEY_TOOL  = os.environ.get("OPENAI_API_KEY_TOOL", "sk-9d227aac50594b89875b5ae8266ecc37")
BASE_URL_TOOL = os.environ.get("OPENAI_BASE_URL_TOOL", "https://api.deepseek.com")
MODEL_TOOL    = os.environ.get("OPENAI_MODEL_TOOL", "deepseek-v4-flash")
DATA_DIR  = os.path.dirname(os.path.abspath(__file__))
PKG_DIR   = os.path.join(DATA_DIR, "package")
LOGS_DIR  = os.path.join(DATA_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE  = os.path.join(LOGS_DIR, "run_log.txt")

# ── 文件日志：所有输出和错误同时写入 run_log.txt ─────────────────────────────
import datetime as _dt

def write_log(text: str):
    """追加写入到 run_log.txt，同时打印到控制台。"""
    line = text
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def log_error(label: str, exc: Exception):
    """把异常详情写入日志文件并打印。"""
    msg = f"[ERROR] {label}\n{traceback.format_exc()}"
    write_log(msg)

def load_json(filename: str) -> dict | list:
    path = os.path.join(PKG_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ── 模式加载 ────────────────────────────────────────────────────────────────────
MODES_DIR = os.path.join(PKG_DIR, "modes")

def load_modes() -> dict:
    """从 package/modes/*.json 动态加载所有可用模式。"""
    modes: dict = {}
    if not os.path.isdir(MODES_DIR):
        return modes
    for fname in sorted(os.listdir(MODES_DIR)):
        if fname.endswith(".json"):
            key = fname[:-5]
            with open(os.path.join(MODES_DIR, fname), "r", encoding="utf-8") as f:
                modes[key] = json.load(f)
    return modes

def fill_template(template: str, **kwargs) -> str:
    """将 {key} 占位符替换为对应值，不使用 str.format 避免转义问题。"""
    for key, value in kwargs.items():
        template = template.replace(f"{{{key}}}", str(value))
    return template

# ── 简化版 JSONPatch 执行器 ────────────────────────────────────────────────────
def resolve_path(obj: dict | list, path: str):
    """将 '/dynamic/current_hp' 这样的路径解析为 (parent_obj, key)"""
    parts = [p for p in path.strip("/").split("/") if p]
    cur = obj
    for part in parts[:-1]:
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    last = parts[-1]
    return cur, last

def apply_patch(state: dict, patch: dict, allow_protected: bool = False) -> str:
    """
    支持操作：
      replace  → 直接覆盖
      delta    → 数值增减（LLM 只输出变化量，后端计算）
      add      → 追加到数组（path 以 /- 结尾）或新增字段
      remove   → 删除字段
    """
    op    = patch.get("op")
    path  = patch.get("path", "")
    value = patch.get("value")

    # ── _ 前缀保护：禁止 LLM 修改任何不可变字段 ──────────────────────────────
    if not allow_protected:
        parts = [p for p in path.strip("/").split("/") if p]
        for part in parts:
            if part.startswith("_"):
                return f"[blocked] 路径 {path!r} 包含受保护的字段 '{part}'（_ 前缀），操作已拒绝。"

    # add 到数组末尾的特殊路径 /xxx/yyy/-
    if op == "add" and path.endswith("/-"):
        arr_path = path[:-2]
        try:
            parent, key = resolve_path(state, arr_path)
            target = parent[key] if isinstance(parent, dict) else parent[int(key)]
            if isinstance(target, list):
                target.append(value)
                return f"[add] {path} ← {value!r}"
            else:
                return f"[error] {arr_path} 不是数组，无法 append"
        except (KeyError, IndexError, ValueError) as e:
            return f"[error] 路径 {arr_path!r} 解析失败: {e}"

    try:
        parent, key = resolve_path(state, path)
    except (KeyError, IndexError, ValueError) as e:
        return f"[error] 路径 {path!r} 解析失败: {e}  →  请检查路径是否与注入的 JSON 结构匹配"

    try:
        if op == "replace":
            parent[key] = value
            return f"[replace] {path} = {value!r}"

        elif op == "delta":
            old = parent[key]
            parent[key] = old + value
            return f"[delta] {path}: {old} → {parent[key]} (Δ{value:+})"

        elif op == "add":
            if isinstance(parent, list):
                parent.insert(int(key), value)
            else:
                parent[key] = value
            return f"[add] {path} = {value!r}"

        elif op == "remove":
            if isinstance(parent, list):
                parent.pop(int(key))
            else:
                del parent[key]
            return f"[remove] {path}"

        else:
            return f"[error] 未知操作: {op}"
    except Exception as e:
        return f"[error] 执行 {op} 操作失败: {e}"

# ── 工具定义（传给 API）────────────────────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "reveal_hidden",
            "description": (
                "移除游戏状态中指定对象里所有 [HIDDEN] 标记，揭示被遮蔽的信息。"
                "调用后，目标对象的字符串值中的 [HIDDEN] 前缀将被去除，使后续叙事可以引用该完整信息。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "enum": ["world", "focus_location", "characters_snapshot"],
                        "description": "要揭示隐藏内容的顶层目标对象"
                    },
                    "char_index": {
                        "type": "integer",
                        "description": "当 target=characters_snapshot 时，指定角色索引（从0开始）"
                    },
                    "field_path": {
                        "type": "string",
                        "description": "可选，指定要揭示的字段路径（如 'summary' 或 '_story_info._Background'）。不填则揭示目标对象中全部 [HIDDEN] 内容"
                    }
                },
                "required": ["target"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_json_patch",
            "description": (
                "对游戏状态执行一条 JSONPatch 更新。"
                "路径为相对于当前调用上下文的局部路径。"
                "可在同一次响应中多次调用此工具，每次一条 patch。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "op": {
                        "type": "string",
                        "enum": ["replace", "delta", "add", "remove"],
                        "description": (
                            "replace=直接覆盖; "
                            "delta=数值变化量（后端加减，避免LLM算错）; "
                            "add=追加到数组（path末尾写/-）或新增字段; "
                            "remove=删除字段"
                        )
                    },
                    "path": {
                        "type": "string",
                        "description": "JSONPointer路径，相对于注入给 LLM 的游戏状态 JSON 根节点。可变字段均无_前缀。示例：/characters_snapshot/0/attitude_value、/focus_location/description/-、/world/major_event_history/-"
                    },
                    "value": {
                        "description": "新值（remove 操作时可省略）"
                    }
                },
                "required": ["op", "path"]
            }
        }
    }
]

# ── [HIDDEN] 字段揭示 ────────────────────────────────────────────────────────
def reveal_hidden(obj, field_path: str = None):
    """
    移除字符串中的 [HIDDEN] 标记（及其后紧跟的空格）。
    obj: 字符串、列表或字典
    field_path: 可选，如 'summary' 或 '_story_info._Background'，只处理该字段。
                为 None 时递归处理 obj 中所有字符串值。
    示例：
        reveal_hidden(char)                        # 揭示角色所有隐藏信息
        reveal_hidden(char, 'summary')             # 只揭示 summary 字段
        reveal_hidden(char, '_story_info._Background') # 揭示嵌套字段
    """
    import re
    pattern = re.compile(r'\[HIDDEN\]\s*')

    def _strip(v):
        if isinstance(v, str):
            return pattern.sub('', v)
        if isinstance(v, list):
            return [_strip(i) for i in v]
        if isinstance(v, dict):
            return {k: _strip(val) for k, val in v.items()}
        return v

    if field_path is None:
        if isinstance(obj, dict):
            for k in obj:
                obj[k] = _strip(obj[k])
        elif isinstance(obj, list):
            for i in range(len(obj)):
                obj[i] = _strip(obj[i])
        return obj

    keys = field_path.split('.')
    node = obj
    for k in keys[:-1]:
        node = node[k]
    last = keys[-1]
    if last in node:
        node[last] = _strip(node[last])
    return obj

# ── 构建注入上下文 ────────────────────────────────────────────────────────────
def build_context(world: dict, characters: list, locations: list) -> dict:
    """
    将游戏数据组合为单一字典（game_state）。
    - 扁平结构：所有字段在各实体的根层级，_ 前缀标记不可变字段
    - 此字典同时是 prompt 注入源和 apply_patch 寻址根，两者永远一致
    - 可变字段全部在实体根层级，LLM 写路径时无层级歧义
    """
    focus_location = locations[0] if locations else {}
    char_summaries = []
    for c in characters:
        if c.get("type") == "character":
            # 按照用户要求，将角色的全部字段发给大模型（包含 _ 前缀字段）
            char_summaries.append(copy.deepcopy(c))

    return {
        "world": world,
        "focus_location": focus_location,
        "characters_snapshot": char_summaries
    }

# ── 主流程 ────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  DnD Demo — 动态模式驱动引擎")
    print("=" * 60)

    import argparse
    import datetime
    import time

    # 1. 加载所有可用模式
    AVAILABLE_MODES = load_modes()
    if not AVAILABLE_MODES:
        print("[错误] package/modes/ 目录为空或不存在，无法运行。")
        sys.exit(1)

    # 2. 解析命令行参数
    parser = argparse.ArgumentParser(description="DnD Demo — 动态模式驱动引擎")
    parser.add_argument("player_action", nargs="?",
                        default="我决定前往翠绿林地，与影心一同出发。途中，我对影心说：你的遗物似乎在颤动，有什么异常吗？",
                        help="玩家本回合的行动描述")
    parser.add_argument("--mode", default=None,
                        help="运行模式（package/modes/ 下的 JSON 文件名，不含 .json）。默认: narrative")
    parser.add_argument("--char-ids", nargs="*", default=None,
                        metavar="ID",
                        help="注入的角色 id 列表，空=全部角色")
    parser.add_argument("--location-idx", type=int, default=0,
                        help="焦点地点在 grove_locations.json 中的索引（默认0）")
    parser.add_argument("--location-id", default=None,
                        metavar="LOC_ID",
                        help="按 id 指定焦点地点（优先于 --location-idx）")
    parser.add_argument("--game-state-file", default=None,
                        metavar="PATH",
                        help="直接加载预构建的 game_state JSON，跳过 build_context")
    parser.add_argument("--unlock-protected", action="store_true",
                        help="临时解除 _ 前缀字段的修改保护")
    parser.add_argument("--direct-instruction", default="", type=str,
                        help="直接的状态修改指令（用于 direct_patch 模式）")
    # 向后兼容旧参数
    parser.add_argument("--skip-round-1", action="store_true",
                        help="[已废弃] 等效于 --mode direct_patch")
    args_cli = parser.parse_args()

    # 向后兼容：--skip-round-1 映射到 direct_patch 模式
    mode_key = args_cli.mode
    if mode_key is None:
        mode_key = "direct_patch" if args_cli.skip_round_1 else "narrative"

    mode = AVAILABLE_MODES.get(mode_key)
    if not mode:
        print(f"[错误] 未找到模式 '{mode_key}'")
        print(f"  可用模式: {', '.join(AVAILABLE_MODES.keys())}")
        sys.exit(1)

    strategy   = mode.get("strategy", "two_round")
    advance_day = mode.get("advance_day", True)
    print(f"  模式: {mode.get('name', mode_key)}  策略: {strategy}")

    # 3. 加载数据
    world      = load_json("world.json")
    characters = load_json("characters.json")
    locations  = load_json("grove_locations.json")

    world_state = copy.deepcopy(world)
    char_state  = copy.deepcopy(characters)
    loc_state   = copy.deepcopy(locations)

    # 4. 构建 rule_text
    if args_cli.unlock_protected:
        rule_text = "- 字段可变性规则：🚨【最高权限已开启】本次调用允许且鼓励你修改带有 _ 前缀的固定/规则字段！如果你认为剧情需要彻底改变某项设定、规则、战斗数值或核心描述，请直接对这些 _ 字段发出修改指令。"
    else:
        rule_text = "- 字段可变性规则：带 _ 前缀的字段（如 _combat_info、_world_rules）是固定字段，绝对不可修改。无 _ 前缀的字段是可变字段，可以修改。"

    # 5. 注入的角色 & 地点
    char_filter = args_cli.char_ids
    chars_to_inject = (
        [c for c in char_state if c["id"] in char_filter]
        if char_filter else char_state
    )

    if args_cli.location_id:
        loc_idx = next(
            (i for i, l in enumerate(loc_state) if l.get("id") == args_cli.location_id), 0
        )
    else:
        loc_idx = args_cli.location_idx
    locs_to_inject = loc_state[loc_idx : loc_idx + 1]

    if args_cli.game_state_file:
        with open(args_cli.game_state_file, "r", encoding="utf-8") as _f:
            game_state = json.load(_f)
    else:
        game_state = build_context(world_state, chars_to_inject, locs_to_inject)
    game_context = json.dumps(game_state, ensure_ascii=False, indent=2)

    # 6. 玩家输入 & 玩家角色检测
    player_action = args_cli.player_action
    player_char = next(
        (c for c in chars_to_inject if c.get("control") == "player"), None
    )
    player_name = player_char["name"] if player_char else "玩家"

    # 7. 模板变量
    template_vars = {
        "player_action":     player_action,
        "player_name":       player_name,
        "game_context":      game_context,
        "rule_text":         rule_text,
        "direct_instruction": args_cli.direct_instruction or "",
    }

    # 8. 辅助函数：构建一轮的消息列表
    def build_round_messages(round_cfg: dict) -> list:
        msgs = []
        sys_text = fill_template(round_cfg.get("system_prompt", ""), **template_vars)
        msgs.append({"role": "system", "content": sys_text})

        user_templates = round_cfg.get("user_messages") or []
        if not user_templates and "user_prompt_template" in round_cfg:
            user_templates = [round_cfg["user_prompt_template"]]
        for tmpl in user_templates:
            msgs.append({"role": "user", "content": fill_template(tmpl, **template_vars)})

        prefill = round_cfg.get("assistant_prefill", "")
        if prefill:
            msgs.append({"role": "assistant", "content": prefill})
        return msgs

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    client      = OpenAI(api_key=API_KEY,      base_url=BASE_URL)
    client_tool = OpenAI(api_key=API_KEY_TOOL, base_url=BASE_URL_TOOL)

    fallback_warning = ""
    if API_KEY_TOOL == API_KEY and BASE_URL_TOOL == BASE_URL and MODEL_TOOL == MODEL:
        fallback_warning = "[警告] 第二轮调用配置未设置或相同，已平滑降级使用第一轮的配置进行请求。"

    full_log = {"timestamp": timestamp, "model": MODEL, "mode": mode_key, "steps": []}

    # ══════════════════════════════════════════════════════════════════════
    # 第一轮（仅 two_round 策略执行）
    # ══════════════════════════════════════════════════════════════════════
    narrative_content = ""
    round_1_user_messages: list = []  # 用于在第二轮重新注入上下文
    elapsed1 = 0
    tokens1  = type("Tokens", (), {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})()

    if strategy == "two_round":
        round_1_cfg = mode.get("round_1") or {}
        round_1_messages = build_round_messages(round_1_cfg)
        # 保存 user 消息（含游戏上下文），供第二轮复用
        round_1_user_messages = [m for m in round_1_messages if m["role"] == "user"]

        print("\n" + "─" * 60)
        print("【第一轮】纯文本叙事生成（tool_choice=none）")
        print("─" * 60)

        t0 = time.time()
        response1 = client.chat.completions.create(
            model=MODEL,
            messages=round_1_messages,
            tools=TOOLS,
            tool_choice="none"
        )
        t1 = time.time()
        elapsed1 = t1 - t0
        tokens1  = response1.usage

        narrative_content = response1.choices[0].message.content or ""
        print(f"⏱  耗时: {elapsed1:.2f}s")
        print(f"📊 Token 用量: prompt={tokens1.prompt_tokens}, completion={tokens1.completion_tokens}, total={tokens1.total_tokens}")
        print(f"📄 finish_reason: {response1.choices[0].finish_reason}")
        print("\n" + narrative_content)

        full_log["steps"].append({
            "step": 1,
            "description": "纯文本叙事生成",
            "tool_choice": "none",
            "elapsed_seconds": round(elapsed1, 3),
            "tokens": {
                "prompt": tokens1.prompt_tokens,
                "completion": tokens1.completion_tokens,
                "total": tokens1.total_tokens
            },
            "finish_reason": response1.choices[0].finish_reason,
            "request_messages": round_1_messages,
            "response": json.loads(response1.model_dump_json())
        })
    else:
        print("\n" + "─" * 60)
        print(f"【第一轮】已跳过（策略: {strategy}）")
        print("─" * 60)

    # ══════════════════════════════════════════════════════════════════════
    # 第二轮：工具调用（两种策略均执行）
    # ══════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 60)
    print("【第二轮】状态更新工具调用（tool_choice=auto）")
    if fallback_warning:
        print(fallback_warning)
    print("─" * 60)

    round_2_cfg = mode.get("round_2") or {}
    round_2_system = fill_template(round_2_cfg.get("system_prompt", ""), **template_vars)
    round_2_user_templates = round_2_cfg.get("user_messages") or []
    if not round_2_user_templates and "user_prompt_template" in round_2_cfg:
        round_2_user_templates = [round_2_cfg["user_prompt_template"]]

    if strategy == "two_round":
        # 继承第一轮的 user 消息（游戏上下文），追加叙事和第二轮指令
        messages2 = [{"role": "system", "content": round_2_system}]
        messages2 += round_1_user_messages
        messages2.append({"role": "assistant", "content": narrative_content})
        for tmpl in round_2_user_templates:
            messages2.append({"role": "user", "content": fill_template(tmpl, **template_vars)})
    else:
        # single_round_tool：直接用第二轮配置构建完整消息
        messages2 = [{"role": "system", "content": round_2_system}]
        for tmpl in round_2_user_templates:
            messages2.append({"role": "user", "content": fill_template(tmpl, **template_vars)})

    t2 = time.time()
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response2 = client_tool.chat.completions.create(
                model=MODEL_TOOL,
                messages=messages2,
                tools=TOOLS,
                tool_choice="auto"
            )
            break
        except Exception as e:
            if attempt < max_retries:
                print(f"  [警告] 第二轮调用失败 (尝试 {attempt}/{max_retries}): {e}")
                print("  等待 60 秒后重新发送...")
                write_log(f"[警告] 第二轮调用失败，等待 60 秒后重试: {e}")
                time.sleep(60)
            else:
                write_log(f"[错误] 第二轮调用达到最大重试次数: {e}")
                raise e
    t3 = time.time()
    elapsed2 = t3 - t2

    tokens2 = response2.usage
    patch_message = response2.choices[0].message

    print(f"⏱  耗时: {elapsed2:.2f}s")
    print(f"📊 Token 用量: prompt={tokens2.prompt_tokens}, completion={tokens2.completion_tokens}, total={tokens2.total_tokens}")
    print(f"📄 finish_reason: {response2.choices[0].finish_reason}")

    full_log["steps"].append({
        "step": 2,
        "description": "状态更新工具调用",
        "tool_choice": "auto",
        "elapsed_seconds": round(elapsed2, 3),
        "tokens": {
            "prompt": tokens2.prompt_tokens,
            "completion": tokens2.completion_tokens,
            "total": tokens2.total_tokens
        },
        "finish_reason": response2.choices[0].finish_reason,
        "request_messages": messages2,
        "response": json.loads(response2.model_dump_json())
    })

    # 汇总计时
    total_elapsed = elapsed1 + elapsed2
    total_tokens  = tokens1.total_tokens + tokens2.total_tokens
    full_log["total_elapsed_seconds"] = round(total_elapsed, 3)
    full_log["total_tokens"] = total_tokens

    log_filename = f"log_full_{timestamp}.json"
    with open(os.path.join(LOGS_DIR, log_filename), "w", encoding="utf-8") as f:
        json.dump(full_log, f, ensure_ascii=False, indent=2)
    print(f"\n[系统] 完整请求与返回已记录至 logs/{log_filename}")

    # ══════════════════════════════════════════════════════════════════════
    # 执行 JSONPatch
    # ══════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 60)
    print("【工具调用解析 & 状态更新】")

    patch_log = []
    if patch_message.tool_calls:
        for tc in patch_message.tool_calls:
            fn_name = tc.function.name
            args    = json.loads(tc.function.arguments)

            print(f"\n  调用工具: {fn_name}")
            print(f"  参数    : {json.dumps(args, ensure_ascii=False)}")

            if fn_name == "apply_json_patch":
                result = apply_patch(game_state, args, args_cli.unlock_protected)
                print(f"  执行结果: {result}")
                patch_log.append(result)

            elif fn_name == "reveal_hidden":
                target     = args.get("target")
                char_idx   = args.get("char_index")
                field_path = args.get("field_path")
                if target == "world":
                    obj = game_state["world"]
                    reveal_hidden(obj, field_path)
                    result = f"[reveal_hidden] world{'.' + field_path if field_path else ''} 已揭示"
                elif target == "focus_location":
                    obj = game_state["focus_location"]
                    reveal_hidden(obj, field_path)
                    result = f"[reveal_hidden] focus_location{'.' + field_path if field_path else ''} 已揭示"
                elif target == "characters_snapshot":
                    if char_idx is None:
                        result = "[error] reveal_hidden: characters_snapshot 需要 char_index"
                    else:
                        snap = game_state.get("characters_snapshot", [])
                        if 0 <= char_idx < len(snap):
                            obj = snap[char_idx]
                            reveal_hidden(obj, field_path)
                            result = f"[reveal_hidden] characters_snapshot[{char_idx}]{'.' + field_path if field_path else ''} 已揭示"
                        else:
                            result = f"[error] reveal_hidden: char_index {char_idx} 越界"
                else:
                    result = f"[error] reveal_hidden: 未知 target {target!r}"
                print(f"  执行结果: {result}")
                patch_log.append(result)
    else:
        print("  (第二轮响应未触发任何工具调用)")

    # ══════════════════════════════════════════════════════════════════════
    # 推进天数 & 打印状态
    # ══════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 60)

    if advance_day:
        print(f"[系统] 正常推进流程完毕 → 当前为第 {world_state['day_count']} 天")
    else:
        print("[系统] 此模式不推进天数")

    print("\n【更新后 world.dynamic 状态】")
    print(json.dumps(world_state.get("dynamic", {}), ensure_ascii=False, indent=2))

    print("\n【更新后 影心 dynamic 状态】")
    shadowheart = next((c for c in char_state if c["id"] == "card_char_shadowheart"), None)
    if shadowheart:
        print(json.dumps(shadowheart.get("dynamic", {}), ensure_ascii=False, indent=2))

    print("\n" + "─" * 60)
    print(f"⏱  总耗时: {total_elapsed:.2f}s  |  总 Token: {total_tokens}")
    print("  第一轮（叙事）: {:.2f}s".format(elapsed1))
    print("  第二轮（Patch）: {:.2f}s".format(elapsed2))

    # ── 写回更新后状态到 package/*.json ──────────────────────────────────────
    snap_map = {s.get("id"): s for s in game_state.get("characters_snapshot", []) if s.get("id")}
    for c in char_state:
        if c.get("id") in snap_map:
            snap = snap_map[c["id"]]
            for k, v in snap.items():
                c[k] = v

    fl = game_state.get("focus_location", {})
    if fl.get("id"):
        for loc in loc_state:
            if loc.get("id") == fl["id"]:
                for k, v in fl.items():
                    loc[k] = v
                break

    with open(os.path.join(PKG_DIR, "world.json"), "w", encoding="utf-8") as f:
        json.dump(world_state, f, ensure_ascii=False, indent=2)
    with open(os.path.join(PKG_DIR, "characters.json"), "w", encoding="utf-8") as f:
        json.dump(char_state, f, ensure_ascii=False, indent=2)
    with open(os.path.join(PKG_DIR, "grove_locations.json"), "w", encoding="utf-8") as f:
        json.dump(loc_state, f, ensure_ascii=False, indent=2)
    write_log("[系统] 状态已写回 package/*.json")
    print("=== STATE_UPDATED ===")

    print("\n" + "=" * 60)
    print("  Demo 运行完毕")
    print("=" * 60)


if __name__ == "__main__":
    main()
