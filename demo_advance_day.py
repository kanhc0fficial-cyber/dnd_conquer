"""
demo_advance_day.py
测试"推进一天"的核心循环：
  - 从 package/modes/ 动态加载模式 JSON（narrative / direct_patch / level_up …）
  - 读取 package/*.json 作为上下文，可按前端固定路径裁剪
  - 根据模式策略（two_round / single_round_tool）调用 LLM
  - 解析返回的自然语言叙事 + JSONPatch 工具调用指令
  - 将 patch 应用到内存中的游戏状态，并打印结果
"""

import json
import os
import sys
import copy
import traceback
import types
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

# 第二轮工具调用失败容忍次数：超过此数后自动切换到第一轮 API 重试
TOOL_ROUND2_FALLBACK_THRESHOLD = 2

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

def list_package_json_files() -> list[str]:
    """列出 package 根目录下的 JSON 数据文件，不包含 modes 子目录。"""
    if not os.path.isdir(PKG_DIR):
        return []
    return sorted(
        fname for fname in os.listdir(PKG_DIR)
        if fname.endswith(".json") and os.path.isfile(os.path.join(PKG_DIR, fname))
    )

def load_package_jsons() -> dict[str, dict | list]:
    """加载 package 根目录下全部 JSON 文件。"""
    return {fname: load_json(fname) for fname in list_package_json_files()}

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

def assistant_message_to_history(message) -> dict:
    """Convert an SDK assistant message into chat history, preserving provider extras."""
    history_msg: dict = {"role": "assistant", "content": message.content}

    extra = getattr(message, "model_extra", None) or {}
    for key in ("reasoning_content",):
        value = getattr(message, key, None)
        if value is None:
            value = extra.get(key)
        if value is not None:
            history_msg[key] = value

    if message.tool_calls:
        history_msg["tool_calls"] = [
            {
                "id": tc.id, "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments}
            }
            for tc in message.tool_calls
        ]
    return history_msg

# ── 简化版 JSONPatch 执行器 ────────────────────────────────────────────────────
def pointer_unescape(part: str) -> str:
    return part.replace("~1", "/").replace("~0", "~")

def pointer_escape(part: object) -> str:
    return str(part).replace("~", "~0").replace("/", "~1")

def parse_pointer(path: str) -> list[str]:
    if path in ("", "/"):
        return []
    return [pointer_unescape(p) for p in path.strip("/").split("/") if p != ""]

def make_pointer(parts: list[object]) -> str:
    return "/" + "/".join(pointer_escape(p) for p in parts)

def resolve_node(obj: dict | list, path: str):
    """解析 JSONPointer 并返回目标节点。"""
    cur = obj
    for part in parse_pointer(path):
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur

def resolve_path(obj: dict | list, path: str):
    """将 '/dynamic/current_hp' 这样的路径解析为 (parent_obj, key)"""
    parts = parse_pointer(path)
    if not parts:
        raise ValueError("不能对文件根路径本身执行该操作")
    cur = obj
    for part in parts[:-1]:
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    last = parts[-1]
    return cur, last

def normalize_selection_paths(raw_pins: list[dict]) -> dict[str, list[str]]:
    """把前端 pins 归一化为 file -> JSONPointer 列表。"""
    selections: dict[str, list[str]] = {}
    for pin in raw_pins or []:
        file_name = os.path.basename(str(pin.get("file", "")))
        if not file_name.endswith(".json"):
            continue
        raw_path = pin.get("path", [])
        if not isinstance(raw_path, list):
            continue
        pointer = make_pointer(raw_path) if raw_path else "/"
        selections.setdefault(file_name, [])
        if pointer not in selections[file_name]:
            selections[file_name].append(pointer)
    return selections

def merge_from_source(dst, source, path_parts: list[str]):
    """从 source 中裁剪 path，同时保留祖先链和对象身份锚点。"""
    if not path_parts:
        return copy.deepcopy(source)

    head = path_parts[0]
    if isinstance(source, list):
        container = dst if isinstance(dst, list) else []
        idx = int(head)
        while len(container) <= idx:
            container.append(None)
        container[idx] = merge_from_source(container[idx], source[idx], path_parts[1:])
        return container

    container = dst if isinstance(dst, dict) else {}
    if isinstance(source, dict):
        for meta_key in ("id", "name", "type"):
            if meta_key in source and meta_key not in container:
                container[meta_key] = copy.deepcopy(source[meta_key])
        container[head] = merge_from_source(container.get(head), source[head], path_parts[1:])
    return container

def build_context(package_state: dict[str, dict | list], selections: dict[str, list[str]]) -> dict:
    """
    构建发送给 LLM 的裁剪上下文。
    原则：
    - 只删除未选字段，不改名、不包裹实体、不重排数组。
    - 每个文件仍位于 package["xxx.json"] 下，文件内路径保持真实 JSONPointer。
    - selections 为空时发送全部 package/*.json。
    """
    selected_files = selections or {fname: ["/"] for fname in package_state}
    context_files: dict[str, dict | list] = {}
    for fname, paths in selected_files.items():
        if fname not in package_state:
            continue
        if "/" in paths:
            context_files[fname] = copy.deepcopy(package_state[fname])
            continue
        pruned = None
        for path in paths:
            pruned = merge_from_source(pruned, package_state[fname], parse_pointer(path))
        context_files[fname] = pruned
    return {"package": context_files}

def is_visible_path(file_name: str, path: str, selections: dict[str, list[str]]) -> bool:
    """判断 path 对应的子树是否完整出现在上下文中。"""
    if not selections:
        return True
    file_paths = selections.get(file_name)
    if not file_paths:
        return False
    target = "/" if path in ("", "/") else path.rstrip("/")
    for selected in file_paths:
        selected = "/" if selected in ("", "/") else selected.rstrip("/")
        if selected == "/" or selected == target or target.startswith(selected + "/"):
            return True
    return False

def apply_patch_to_file(package_state: dict[str, dict | list], patch: dict, selections: dict[str, list[str]], allow_protected: bool = False) -> tuple[str, str | None]:
    """
    支持操作：
      replace  → 直接覆盖
      delta    → 数值增减（LLM 只输出变化量，后端计算）
      add      → 追加到数组（path 以 /- 结尾）或新增字段
      remove   → 删除字段
    """
    file_name = os.path.basename(str(patch.get("file", "")))
    op    = patch.get("op")
    path  = patch.get("path", "")
    value = patch.get("value")
    reason = patch.get("reason", "未提供原因")

    if not file_name or file_name not in package_state:
        return f"[error] 未知或未提供 file: {file_name!r}", None
    state = package_state[file_name]

    # ── _ 前缀保护：禁止 LLM 修改任何不可变字段 ──────────────────────────────
    if not allow_protected:
        parts = parse_pointer(path)
        for part in parts:
            if part.startswith("_"):
                return f"[blocked] {file_name}:{path!r} 包含受保护的字段 '{part}'（_ 前缀），操作已拒绝。", None

    if op == "replace" and isinstance(value, (dict, list)) and not is_visible_path(file_name, path, selections):
        return (
            f"[blocked] {file_name}:{path} 不是完整可见子树，拒绝用裁剪对象整体覆盖。"
            "请改用更具体的叶子字段路径，或固定该完整对象后重试。",
            None
        )

    # add 到数组末尾的特殊路径 /xxx/yyy/-
    if op == "add" and path.endswith("/-"):
        arr_path = path[:-2]
        try:
            parent, key = resolve_path(state, arr_path)
            target = parent[key] if isinstance(parent, dict) else parent[int(key)]
            if isinstance(target, list):
                target.append(value)
                return f"[add] {file_name}:{path} ← {value!r} (原因: {reason})", file_name
            else:
                return f"[error] {file_name}:{arr_path} 不是数组，无法 append", None
        except (KeyError, IndexError, ValueError) as e:
            return f"[error] {file_name}:{arr_path!r} 解析失败: {e}", None

    try:
        parent, key = resolve_path(state, path)
    except (KeyError, IndexError, ValueError) as e:
        return f"[error] {file_name}:{path!r} 解析失败: {e}  →  请检查路径是否与注入的 JSON 结构匹配", None

    try:
        if op == "replace":
            parent[key] = value
            return f"[replace] {file_name}:{path} = {value!r} (原因: {reason})", file_name

        elif op == "delta":
            old = parent[key]
            parent[key] = old + value
            return f"[delta] {file_name}:{path}: {old} → {parent[key]} (Δ{value:+}) (原因: {reason})", file_name

        elif op == "add":
            if isinstance(parent, list):
                parent.insert(int(key), value)
            else:
                parent[key] = value
            return f"[add] {file_name}:{path} = {value!r} (原因: {reason})", file_name

        elif op == "remove":
            if isinstance(parent, list):
                parent.pop(int(key))
            else:
                del parent[key]
            return f"[remove] {file_name}:{path} (原因: {reason})", file_name

        else:
            return f"[error] 未知操作: {op}", None
    except Exception as e:
        return f"[error] 执行 {file_name}:{path} 的 {op} 操作失败: {e}", None

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
                        "description": "要揭示隐藏内容的文件名，如 characters.json、world.json"
                    },
                    "field_path": {
                        "type": "string",
                        "description": "JSONPointer 路径，指定文件内要揭示的对象或字段，如 /card_char_shadowheart/summary。不填或 / 则处理整个文件"
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
                    "reason": {
                        "type": "string",
                        "description": "【必须作为生成的第一个字段】一句话说明进行此修改的原因，以确保在下达修改指令前先进行逻辑思考。"
                    },
                    "file": {
                        "type": "string",
                        "description": "要修改的 package JSON 文件名，如 characters.json、world.json、monster.json"
                    },
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
                        "description": "JSONPointer路径，相对于 file 指定的 JSON 文件根。示例：/card_char_shadowheart/current_hp、/loc_shattered_sanctum/history/-、/major_event_history/-"
                    },
                    "value": {
                        "description": "新值（remove 操作时可省略）"
                    }
                },
                "required": ["reason", "file", "op", "path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_character",
            "description": (
                "原子性地完成一名角色的地点转移：同时更新 characters.json 中该角色的 location 字段，"
                "以及 locations 文件中旧地点的 card_ids（移除）和新地点的 card_ids（添加）与 character_activities（更新在做什么）。"
                "调用前会自动执行一致性校验：若发现该角色同时出现在多个地点，会在返回结果中报告，并以 characters.json 的 location 字段为准。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "【必须作为第一个字段】一句话说明转移原因。"
                    },
                    "character_id": {
                        "type": "string",
                        "description": "要转移的角色 ID，如 card_char_shadowheart"
                    },
                    "from_location_id": {
                        "type": "string",
                        "description": "（可选）转移前的地点 ID，用于额外校验。若提供且与角色当前 location 不符，操作将返回错误。"
                    },
                    "to_location_id": {
                        "type": "string",
                        "description": "转移目标地点 ID，如 loc_the_hollow"
                    },
                    "activity": {
                        "type": "string",
                        "description": "角色抵达新地点后正在做的事，将写入目标地点的 character_activities 字段。例如：'在铁匠铺附近等候，处理装备损耗'"
                    }
                },
                "required": ["reason", "character_id", "to_location_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_event",
            "description": (
                "一次性向世界、角色、地点三个文件同时追加历史记录，避免遗漏并节省 token。"
                "三个目标（world / character / location）均为可选，按需填写。"
                "world 端写入 world.json 的 npc_background_history 数组（后台NPC历史）；"
                "角色端写入 characters.json 指定角色的 history 数组；"
                "地点端写入对应 locations 文件中指定地点的 history 数组。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "【必须作为第一个字段】一句话说明记录此事件的原因。"
                    },
                    "date": {
                        "type": "string",
                        "description": "事件发生的游戏内日期，如'第四天'，将作为前缀附加到所有条目。"
                    },
                    "npc_history_entry": {
                        "type": "string",
                        "description": "要追加到 world.json 的 npc_background_history 的内容（不含日期前缀，由 date 字段自动拼接）。不需要记录则留空或省略。"
                    },
                    "character_id": {
                        "type": "string",
                        "description": "要追加角色历史的角色 ID，如 card_char_halsin。不需要则省略。"
                    },
                    "character_history_entry": {
                        "type": "string",
                        "description": "要追加到该角色 history 数组的内容。character_id 存在时有效。"
                    },
                    "location_id": {
                        "type": "string",
                        "description": "要追加地点历史的地点 ID，如 loc_the_hollow。不需要则省略。"
                    },
                    "location_history_entry": {
                        "type": "string",
                        "description": "要追加到该地点 history 数组的内容。location_id 存在时有效。"
                    }
                },
                "required": ["reason"]
            }
        }
    }
]

# ── 交易专用工具定义 ─────────────────────────────────────────────────────────
TRADE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_item_price",
            "description": (
                "在数据库中按关键词搜索物品的官方参考价格。"
                "调用后服务端会在所有 items_*.json 文件中检索，返回匹配物品的 id、名称与标准市价（cost 字段，如 '15 gp'）。"
                "若未找到，服务端会明确告知，此时请自行根据世界观与物品稀缺度估算合理价格，不要放弃交易。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "搜索关键词，可以是物品名称的一部分（中文或英文均可），例如：'长剑'、'皮甲'、'longbow'"
                    }
                },
                "required": ["keywords"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_trade",
            "description": (
                "原子性地完成一笔或多笔购买/出售交易：自动扣除或增加金币，并从背包移入或移出物品。"
                "此工具同时处理金币与物品栏的所有变动，无需再调用 apply_json_patch 处理金币或物品。"
                "购买时若金币不足、出售时若物品不在背包中，该条交易会返回失败原因，其余条目仍继续执行。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "transactions": {
                        "type": "array",
                        "description": "交易明细列表，每条为一笔独立交易",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["buy", "sell"],
                                    "description": "buy=购买（扣金币、放物品入背包）；sell=出售（移除背包物品、增加金币）"
                                },
                                "character_id": {
                                    "type": "string",
                                    "description": "执行交易的角色 ID，如 card_char_xie_nian"
                                },
                                "item_name": {
                                    "type": "string",
                                    "description": "物品名称。buy 时将以此名称写入背包；sell 时须与背包中的字符串完全一致"
                                },
                                "quantity": {
                                    "type": "integer",
                                    "description": "交易数量，默认 1",
                                    "default": 1
                                },
                                "unit_price": {
                                    "type": "number",
                                    "description": "每件成交价（金币 gp），可含折扣/溢价系数后的最终价格"
                                },
                                "reason": {
                                    "type": "string",
                                    "description": "交易原因描述，用于日志，例如：'玩家在格罗夫市场向商人 Arron 购买皮甲，享受九折优惠'"
                                }
                            },
                            "required": ["type", "character_id", "item_name", "unit_price", "reason"]
                        }
                    }
                },
                "required": ["transactions"]
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

# ── 物品价格搜索 ──────────────────────────────────────────────────────────────
def handle_search_item_price(package_state: dict, args: dict) -> str:
    """在所有 items_*.json 文件中按关键词搜索物品参考价格。"""
    keywords = str(args.get("keywords", "")).strip().lower()
    if not keywords:
        return json.dumps({"found": False, "message": "未提供搜索关键词", "results": []}, ensure_ascii=False)

    results = []
    item_files = sorted(f for f in package_state if f.startswith("items_"))
    for fname in item_files:
        items = package_state.get(fname, {})
        if not isinstance(items, dict):
            continue
        for item_id, item in items.items():
            if not isinstance(item, dict):
                continue
            name = item.get("name", "")
            if keywords in name.lower() or keywords in item_id.lower():
                results.append({
                    "id": item_id,
                    "name": name,
                    "type": item.get("type"),
                    "subtype": item.get("subtype"),
                    "cost": item.get("cost"),
                    "source_file": fname,
                })

    if results:
        return json.dumps({"found": True, "count": len(results), "results": results}, ensure_ascii=False)
    return json.dumps({
        "found": False,
        "message": f"数据库中未找到匹配\"{keywords}\"的物品，请自行根据世界观与物品稀缺度估算价格。",
        "results": [],
    }, ensure_ascii=False)


# ── 原子性交易执行 ────────────────────────────────────────────────────────────
def handle_execute_trade(package_state: dict, args: dict, dirty_files: set) -> str:
    """
    原子性地处理购买/出售交易：直接修改 package_state 中的 gold 与 inventory，
    无需通过 apply_json_patch。
    """
    transactions = args.get("transactions", [])
    if not isinstance(transactions, list) or not transactions:
        return json.dumps({"all_success": False, "message": "未提供有效的交易明细", "results": []}, ensure_ascii=False)

    characters = package_state.get("characters.json", {})
    results = []

    for txn in transactions:
        txn_type   = txn.get("type", "")
        char_id    = str(txn.get("character_id", "")).strip()
        item_name  = str(txn.get("item_name", "")).strip()
        quantity   = max(1, int(txn.get("quantity", 1)))
        unit_price = float(txn.get("unit_price", 0))
        reason     = txn.get("reason", "")
        total_cost = round(unit_price * quantity, 4)

        if not char_id or not item_name:
            results.append({"success": False, "message": "character_id 或 item_name 为空"})
            continue

        char = characters.get(char_id) if isinstance(characters, dict) else None
        if char is None:
            results.append({"success": False, "character_id": char_id,
                            "message": f"未找到角色 {char_id!r}"})
            continue

        # 确保 inventory 和 gold 字段存在（兼容旧角色数据）
        if "inventory" not in char or not isinstance(char["inventory"], list):
            char["inventory"] = []
        if "gold" not in char:
            char["gold"] = 0
        current_gold = float(char["gold"])
        inventory    = char["inventory"]

        if txn_type == "buy":
            if current_gold < total_cost:
                results.append({
                    "success": False, "type": "buy",
                    "character_id": char_id, "item": item_name,
                    "message": f"金币不足：现有 {current_gold:.2f} gp，购买需 {total_cost:.2f} gp",
                })
                continue
            char["gold"] = round(current_gold - total_cost, 4)
            for _ in range(quantity):
                inventory.append(item_name)
            dirty_files.add("characters.json")
            results.append({
                "success": True, "type": "buy",
                "character_id": char_id, "item": item_name,
                "quantity": quantity, "unit_price": unit_price, "total_cost": total_cost,
                "gold_before": current_gold, "gold_after": char["gold"],
                "reason": reason,
            })

        elif txn_type == "sell":
            count_in_bag = inventory.count(item_name)
            if count_in_bag < quantity:
                results.append({
                    "success": False, "type": "sell",
                    "character_id": char_id, "item": item_name,
                    "message": f"背包中 '{item_name}' 仅有 {count_in_bag} 件，需出售 {quantity} 件",
                })
                continue
            for _ in range(quantity):
                inventory.remove(item_name)
            char["gold"] = round(current_gold + total_cost, 4)
            dirty_files.add("characters.json")
            results.append({
                "success": True, "type": "sell",
                "character_id": char_id, "item": item_name,
                "quantity": quantity, "unit_price": unit_price, "total_cost": total_cost,
                "gold_before": current_gold, "gold_after": char["gold"],
                "reason": reason,
            })

        else:
            results.append({"success": False, "message": f"未知交易类型 {txn_type!r}"})

    all_ok = all(r.get("success", False) for r in results)
    return json.dumps({"all_success": all_ok, "results": results}, ensure_ascii=False)


# ── 地点查找辅助 ──────────────────────────────────────────────────────────────
def _find_location_object(package_state: dict, loc_id: str) -> tuple[str | None, dict | None]:
    """
    在所有 package 文件中按 location ID 查找地点对象，返回 (文件名, 地点对象)。
    支持两种结构：
      - dict-of-locations 结构：{loc_id: {id, card_ids, ...}, ...}（grove_locations.json）
      - single-object 结构：{id: loc_id, card_ids: [...], ...}（grove_area.json）
    """
    for fname, fdata in package_state.items():
        if not isinstance(fdata, dict):
            continue
        # Pattern 1: dict keyed by location IDs
        if loc_id in fdata and isinstance(fdata.get(loc_id), dict):
            return fname, fdata[loc_id]
        # Pattern 2: single location object whose id field matches
        if fdata.get("id") == loc_id and "card_ids" in fdata:
            return fname, fdata
    return None, None


# ── 原子性角色地点转移 ────────────────────────────────────────────────────────
def handle_transfer_character(package_state: dict, args: dict, dirty_files: set) -> str:
    """
    一次性完成角色地点转移：
    1. 更新 characters.json 中该角色的 location 字段
    2. 从旧地点的 card_ids 中移除该角色，并清理旧地点的 character_activities
    3. 向新地点的 card_ids 中添加该角色，并写入 character_activities
    4. 执行一致性校验：检测角色是否同时存在于多个地点
    """
    reason    = args.get("reason", "未提供原因")
    char_id   = str(args.get("character_id", "")).strip()
    to_loc_id = str(args.get("to_location_id", "")).strip()
    from_loc_id = str(args.get("from_location_id", "")).strip()
    activity  = str(args.get("activity", "")).strip()

    if not char_id or not to_loc_id:
        return json.dumps({"success": False, "message": "character_id 和 to_location_id 均为必填项"}, ensure_ascii=False)

    # ── 1. 查找角色 ─────────────────────────────────────────────────────────
    characters = package_state.get("characters.json", {})
    char = characters.get(char_id) if isinstance(characters, dict) else None
    if char is None:
        return json.dumps({"success": False, "message": f"未在 characters.json 中找到角色 {char_id!r}"}, ensure_ascii=False)

    current_loc_id = str(char.get("location", "")).strip()

    # 若调用方提供了 from_location_id，做额外校验
    if from_loc_id and from_loc_id != current_loc_id:
        return json.dumps({
            "success": False,
            "message": f"校验失败：角色 {char_id} 的当前位置为 {current_loc_id!r}，与提供的 from_location_id={from_loc_id!r} 不符"
        }, ensure_ascii=False)

    # ── 2. 一致性检查：扫描所有 location 文件，寻找包含该角色的 card_ids ────
    locations_containing_char: list[tuple[str, str]] = []  # [(file, loc_id)]
    for fname, fdata in package_state.items():
        if not isinstance(fdata, dict):
            continue
        # dict-of-locations 结构
        for key, val in fdata.items():
            if isinstance(val, dict) and char_id in val.get("card_ids", []):
                locations_containing_char.append((fname, key))
        # single-object 结构
        if fdata.get("id") and char_id in fdata.get("card_ids", []):
            loc_obj_id = fdata["id"]
            entry = (fname, loc_obj_id)
            if entry not in locations_containing_char:
                locations_containing_char.append(entry)

    consistency_warnings: list[str] = []
    if len(locations_containing_char) > 1:
        consistency_warnings.append(
            f"⚠ 一致性错误：{char_id} 同时出现在以下地点 card_ids 中：{locations_containing_char}"
        )

    # ── 3. 处理旧地点 ────────────────────────────────────────────────────────
    old_fnames_updated: list[str] = []
    if current_loc_id:
        old_fname, old_loc_obj = _find_location_object(package_state, current_loc_id)
        if old_loc_obj is not None:
            card_ids: list = old_loc_obj.get("card_ids", [])
            if char_id in card_ids:
                card_ids.remove(char_id)
                old_loc_obj["card_ids"] = card_ids
            activities: dict = old_loc_obj.get("character_activities")
            if isinstance(activities, dict):
                activities.pop(char_id, None)
            dirty_files.add(old_fname)
            old_fnames_updated.append(old_fname)

    # 也清理一致性检查中发现的其他地点（避免遗留重复）
    for fname, lid in locations_containing_char:
        _, loc_obj = _find_location_object(package_state, lid)
        if loc_obj is None:
            continue
        card_ids = loc_obj.get("card_ids", [])
        if char_id in card_ids:
            card_ids.remove(char_id)
            loc_obj["card_ids"] = card_ids
        activities = loc_obj.get("character_activities")
        if isinstance(activities, dict):
            activities.pop(char_id, None)
        dirty_files.add(fname)

    # ── 4. 处理新地点 ────────────────────────────────────────────────────────
    new_fname, new_loc_obj = _find_location_object(package_state, to_loc_id)
    if new_loc_obj is None:
        return json.dumps({
            "success": False,
            "message": f"未在任何 package 文件中找到目标地点 {to_loc_id!r}",
            "consistency_warnings": consistency_warnings
        }, ensure_ascii=False)

    new_card_ids: list = new_loc_obj.get("card_ids", [])
    if char_id not in new_card_ids:
        new_card_ids.append(char_id)
        new_loc_obj["card_ids"] = new_card_ids

    if activity:
        if not isinstance(new_loc_obj.get("character_activities"), dict):
            new_loc_obj["character_activities"] = {}
        new_loc_obj["character_activities"][char_id] = activity

    dirty_files.add(new_fname)

    # ── 5. 更新角色的 location 字段 ─────────────────────────────────────────
    char["location"] = to_loc_id
    dirty_files.add("characters.json")

    result = {
        "success": True,
        "character_id": char_id,
        "from_location": current_loc_id,
        "to_location": to_loc_id,
        "activity": activity,
        "reason": reason,
    }
    if consistency_warnings:
        result["consistency_warnings"] = consistency_warnings
    return json.dumps(result, ensure_ascii=False)


# ── 批量历史记录写入 ──────────────────────────────────────────────────────────
def handle_record_event(package_state: dict, args: dict, dirty_files: set) -> str:
    """
    一次性向 world.json 的 npc_background_history、指定角色的 history、
    以及指定地点的 history 数组追加历史条目。
    """
    reason          = args.get("reason", "未提供原因")
    date            = str(args.get("date", "")).strip()
    npc_entry       = args.get("npc_history_entry")
    char_id         = str(args.get("character_id", "")).strip()
    char_entry      = args.get("character_history_entry")
    loc_id          = str(args.get("location_id", "")).strip()
    loc_entry       = args.get("location_history_entry")

    def _prefixed(text: str) -> str:
        return f"{date}：{text}" if date else text

    results: list[str] = []

    # ── 写入 world.json npc_background_history ───────────────────────────────
    if npc_entry:
        world = package_state.get("world.json")
        if isinstance(world, dict):
            if not isinstance(world.get("npc_background_history"), list):
                world["npc_background_history"] = []
            world["npc_background_history"].append(_prefixed(npc_entry))
            dirty_files.add("world.json")
            results.append("world.json:npc_background_history ✓")
        else:
            results.append("[error] world.json 不存在或格式错误")

    # ── 写入角色 history ─────────────────────────────────────────────────────
    if char_id and char_entry:
        characters = package_state.get("characters.json", {})
        char = characters.get(char_id) if isinstance(characters, dict) else None
        if char is not None:
            if not isinstance(char.get("history"), list):
                char["history"] = []
            char["history"].append(_prefixed(char_entry))
            dirty_files.add("characters.json")
            results.append(f"characters.json:{char_id}:history ✓")
        else:
            results.append(f"[error] 未在 characters.json 中找到角色 {char_id!r}")

    # ── 写入地点 history ─────────────────────────────────────────────────────
    if loc_id and loc_entry:
        _, loc_obj = _find_location_object(package_state, loc_id)
        if loc_obj is not None:
            if not isinstance(loc_obj.get("history"), list):
                loc_obj["history"] = []
            loc_obj["history"].append(_prefixed(loc_entry))
            # find the filename again to mark dirty
            for fname, fdata in package_state.items():
                if not isinstance(fdata, dict):
                    continue
                if loc_id in fdata and fdata.get(loc_id) is loc_obj:
                    dirty_files.add(fname)
                    break
                if fdata.get("id") == loc_id and fdata is loc_obj:
                    dirty_files.add(fname)
                    break
            results.append(f"{loc_id}:history ✓")
        else:
            results.append(f"[error] 未在任何 package 文件中找到地点 {loc_id!r}")

    if not results:
        results.append("[warning] 所有条目均为空，未写入任何历史记录")

    return json.dumps({"results": results, "reason": reason}, ensure_ascii=False)


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
                        help="运行模式（package/modes/ 下的 JSON 文件名，不含 .json）。默认: narrative（标准叙事模式）")
    parser.add_argument("--game-state-file", default=None,
                        metavar="PATH",
                        help="直接加载预构建的 game_state JSON，跳过 build_context")
    parser.add_argument("--context-selection-file", default=None,
                        metavar="PATH",
                        help="前端固定的上下文路径列表 JSON；为空则注入 package/*.json 全部内容")
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

    # 3. 加载 package 根目录下全部 JSON 数据文件
    package_state = load_package_jsons()
    dirty_files: set[str] = set()

    # 4. 构建 rule_text
    if args_cli.unlock_protected:
        rule_text = "- 字段可变性规则：🚨【最高权限已开启】本次调用允许且鼓励你修改带有 _ 前缀的固定/规则字段！如果你认为剧情需要彻底改变某项设定、规则、战斗数值或核心描述，请直接对这些 _ 字段发出修改指令。"
    else:
        rule_text = "- 字段可变性规则：带 _ 前缀的字段（如 _combat_info、_world_rules）是固定字段，绝对不可修改。无 _ 前缀的字段是可变字段，可以修改。"

    # 5. 构建裁剪上下文
    selections: dict[str, list[str]] = {}
    if args_cli.context_selection_file:
        with open(args_cli.context_selection_file, "r", encoding="utf-8") as _f:
            raw_selection = json.load(_f)
        selections = normalize_selection_paths(raw_selection.get("pins", raw_selection))
    if args_cli.game_state_file:
        with open(args_cli.game_state_file, "r", encoding="utf-8") as _f:
            game_state = json.load(_f)
    else:
        game_state = build_context(package_state, selections)
    game_context = json.dumps(game_state, ensure_ascii=False, indent=2)

    # 6. 玩家输入 & 玩家角色检测
    player_action = args_cli.player_action
    characters_data = package_state.get("characters.json", {})
    if isinstance(characters_data, list):
        all_chars = characters_data
    elif isinstance(characters_data, dict):
        all_chars = list(characters_data.values())
    else:
        all_chars = []
    player_char = next((c for c in all_chars if isinstance(c, dict) and c.get("control") == "player"), None)
    player_name = player_char["name"] if player_char else "玩家"

    # 预生成真实骰子结果，传递给所有模式下的 LLM 避免幻觉
    import random
    dice_pool = {
        "d20": [random.randint(1, 20) for _ in range(30)],
        "d12": [random.randint(1, 12) for _ in range(30)],
        "d10": [random.randint(1, 10) for _ in range(30)],
        "d8":  [random.randint(1, 8) for _ in range(30)],
        "d6":  [random.randint(1, 6) for _ in range(30)],
        "d4":  [random.randint(1, 4) for _ in range(30)],
        "d100": [random.randint(1, 100) for _ in range(30)],
    }
    pre_rolled_dice = "【系统提供的预生成真实骰子结果池（请严格从左到右依次取用相应的骰子结果，不要自己编造）】\n"
    for dtype, rolls in dice_pool.items():
        pre_rolled_dice += f"- {dtype}: {rolls}\n"

    # 7. 模板变量
    template_vars = {
        "player_action":     player_action,
        "player_name":       player_name,
        "game_context":      game_context,
        "rule_text":         rule_text,
        "direct_instruction": args_cli.direct_instruction or "",
        "pre_rolled_dice":   pre_rolled_dice,
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
    tokens1  = types.SimpleNamespace(prompt_tokens=0, completion_tokens=0, total_tokens=0)

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
        # single_round_tool / agentic_tool：直接用第二轮配置构建完整消息
        messages2 = [{"role": "system", "content": round_2_system}]
        for tmpl in round_2_user_templates:
            messages2.append({"role": "user", "content": fill_template(tmpl, **template_vars)})

    # ── 辅助：分发单次工具调用（非 search/execute_trade 的通用工具）─────────────
    def _dispatch_common_tool(fn_name: str, args: dict) -> tuple[str, str | None]:
        """执行 apply_json_patch / reveal_hidden / transfer_character / record_event，返回 (result_str, changed_file_or_None)。"""
        if fn_name == "apply_json_patch":
            result, changed_file = apply_patch_to_file(
                package_state, args, selections, args_cli.unlock_protected)
            return result, changed_file
        elif fn_name == "reveal_hidden":
            target = os.path.basename(str(args.get("target", "")))
            fp     = args.get("field_path") or "/"
            if target not in package_state:
                return f"[error] reveal_hidden: 未知文件 {target!r}", None
            try:
                obj = resolve_node(package_state[target], fp)
                reveal_hidden(obj)
                return f"[reveal_hidden] {target}:{fp} 已揭示", target
            except Exception as exc:
                return f"[error] reveal_hidden: {target}:{fp} 解析失败: {exc}", None
        elif fn_name == "transfer_character":
            result_str = handle_transfer_character(package_state, args, dirty_files)
            result_obj = json.loads(result_str)
            if result_obj.get("success"):
                return f"[transfer_character] {args.get('character_id')} → {args.get('to_location_id')} ✓  {result_str}", None
            else:
                return f"[transfer_character][error] {result_str}", None
        elif fn_name == "record_event":
            result_str = handle_record_event(package_state, args, dirty_files)
            return f"[record_event] {result_str}", None
        else:
            return f"[error] 未知工具: {fn_name}", None

    # ══════════════════════════════════════════════════════════════════════
    # 第二轮执行（agentic_tool：多轮循环；其他：单次调用）
    # ══════════════════════════════════════════════════════════════════════
    elapsed2   = 0.0
    tokens2    = types.SimpleNamespace(prompt_tokens=0, completion_tokens=0, total_tokens=0)
    patch_message = None   # agentic 路径工具调用在循环内处理，无需二次处理
    patch_log: list[str] = []
    max_retries = 3

    if strategy == "agentic_tool":
        # ── 多轮工具调用循环（用于交易模式） ────────────────────────────────
        all_trade_tools = TOOLS + TRADE_TOOLS
        max_iterations  = 10
        last_response   = None

        for iteration in range(1, max_iterations + 1):
            print(f"\n  [交易引擎 迭代 {iteration}/{max_iterations}]")
            t_iter = time.time()
            for attempt in range(1, max_retries + 1):
                try:
                    resp_iter = client_tool.chat.completions.create(
                        model=MODEL_TOOL,
                        messages=messages2,
                        tools=all_trade_tools,
                        tool_choice="auto"
                    )
                    break
                except Exception as e:
                    if attempt < max_retries:
                        print(f"  [警告] 迭代{iteration}调用失败({attempt}/{max_retries}): {e}")
                        write_log(f"[警告] 交易迭代{iteration}失败，等待60秒后重试: {e}")
                        time.sleep(60)
                    else:
                        write_log(f"[错误] 交易迭代{iteration}达到最大重试次数: {e}")
                        raise e
            elapsed2   += time.time() - t_iter
            last_response = resp_iter
            tokens2.prompt_tokens     += resp_iter.usage.prompt_tokens
            tokens2.completion_tokens += resp_iter.usage.completion_tokens
            tokens2.total_tokens      += resp_iter.usage.total_tokens

            msg_iter     = resp_iter.choices[0].message
            finish_reason = resp_iter.choices[0].finish_reason

            if msg_iter.content:
                print(msg_iter.content)

            # 将本轮 assistant 消息写入对话历史；thinking mode 需要回传 reasoning_content。
            messages2.append(assistant_message_to_history(msg_iter))

            if finish_reason != "tool_calls" or not msg_iter.tool_calls:
                # LLM 已完成推理，退出循环
                break

            # 处理本轮所有工具调用，收集结果后注入对话历史
            for tc in msg_iter.tool_calls:
                fn_name  = tc.function.name
                args_tc  = json.loads(tc.function.arguments)
                print(f"\n  调用工具: {fn_name}")
                print(f"  参数    : {json.dumps(args_tc, ensure_ascii=False)}")

                if fn_name == "search_item_price":
                    tool_result = handle_search_item_price(package_state, args_tc)
                    print(f"  搜索结果: {tool_result}")
                    patch_log.append(f"[search_item_price] keywords={args_tc.get('keywords')!r}")
                elif fn_name == "execute_trade":
                    tool_result = handle_execute_trade(package_state, args_tc, dirty_files)
                    print(f"  交易结果: {tool_result}")
                    patch_log.append(f"[execute_trade] {tool_result}")
                else:
                    # apply_json_patch / reveal_hidden 等通用工具
                    tool_result, changed_file = _dispatch_common_tool(fn_name, args_tc)
                    print(f"  执行结果: {tool_result}")
                    patch_log.append(tool_result)
                    if changed_file:
                        dirty_files.add(changed_file)

                messages2.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_result
                })

        print(f"⏱  耗时（全部迭代）: {elapsed2:.2f}s")
        print(f"📊 Token 用量（累计）: prompt={tokens2.prompt_tokens}, "
              f"completion={tokens2.completion_tokens}, total={tokens2.total_tokens}")

        full_log["steps"].append({
            "step": 2,
            "description": "交易多轮工具调用（agentic_tool）",
            "tool_choice": "auto",
            "elapsed_seconds": round(elapsed2, 3),
            "tokens": {
                "prompt": tokens2.prompt_tokens,
                "completion": tokens2.completion_tokens,
                "total": tokens2.total_tokens
            },
            "finish_reason": last_response.choices[0].finish_reason if last_response else "n/a",
            "patch_log": patch_log,
        })

    else:
        # ── 标准单次调用（two_round / single_round_tool） ────────────────────
        # 连续失败 TOOL_ROUND2_FALLBACK_THRESHOLD 次后，自动切换到第一轮的 API（client / MODEL）
        t2 = time.time()
        for attempt in range(1, max_retries + 1):
            use_fallback = attempt > TOOL_ROUND2_FALLBACK_THRESHOLD
            active_client = client if use_fallback else client_tool
            active_model  = MODEL  if use_fallback else MODEL_TOOL
            if use_fallback:
                print(f"  [备用] 第二轮已连续失败 {TOOL_ROUND2_FALLBACK_THRESHOLD} 次，切换至第一轮 API（{BASE_URL}）重试…")
                write_log(f"[备用] 第二轮切换至第一轮 API 重试 (attempt={attempt})")
            try:
                response2 = active_client.chat.completions.create(
                    model=active_model,
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

        tokens2       = response2.usage
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
    # 执行 JSONPatch（仅非 agentic_tool 策略，agentic 在循环内已处理）
    # ══════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 60)
    print("【工具调用解析 & 状态更新】")

    if patch_message is not None and patch_message.tool_calls:
        for tc in patch_message.tool_calls:
            fn_name = tc.function.name
            args    = json.loads(tc.function.arguments)

            print(f"\n  调用工具: {fn_name}")
            print(f"  参数    : {json.dumps(args, ensure_ascii=False)}")

            result, changed_file = _dispatch_common_tool(fn_name, args)
            print(f"  执行结果: {result}")
            patch_log.append(result)
            if changed_file:
                dirty_files.add(changed_file)

    elif not patch_log:
        print("  (第二轮响应未触发任何工具调用)")

    # ══════════════════════════════════════════════════════════════════════
    # 推进天数 & 打印状态
    # ══════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 60)

    world_state = package_state.get("world.json", {})
    if advance_day and isinstance(world_state, dict):
        print(f"[系统] 正常推进流程完毕 → 当前为第 {world_state.get('day_count', '?')} 天")
    else:
        print("[系统] 此模式不推进天数")

    print("\n【更新后 world.dynamic 状态】")
    print(json.dumps(world_state.get("dynamic", {}) if isinstance(world_state, dict) else {}, ensure_ascii=False, indent=2))

    print("\n【更新后 影心 dynamic 状态】")
    characters_state = package_state.get("characters.json", {})
    if isinstance(characters_state, list):
        shadowheart = next((c for c in characters_state if isinstance(c, dict) and c.get("id") == "card_char_shadowheart"), None)
    elif isinstance(characters_state, dict):
        shadowheart = characters_state.get("card_char_shadowheart")
    else:
        shadowheart = None
    if shadowheart:
        print(json.dumps(shadowheart.get("dynamic", {}), ensure_ascii=False, indent=2))

    print("\n" + "─" * 60)
    print(f"⏱  总耗时: {total_elapsed:.2f}s  |  总 Token: {total_tokens}")
    print("  第一轮（叙事）: {:.2f}s".format(elapsed1))
    print("  第二轮（Patch）: {:.2f}s".format(elapsed2))

    # ── 写回更新后状态到 package/*.json ──────────────────────────────────────
    for fname in sorted(dirty_files):
        if fname not in package_state:
            continue
        with open(os.path.join(PKG_DIR, fname), "w", encoding="utf-8") as f:
            json.dump(package_state[fname], f, ensure_ascii=False, indent=2)
    if dirty_files:
        write_log(f"[系统] 状态已写回: {', '.join(sorted(dirty_files))}")
    else:
        write_log("[系统] 无 JSON 文件需要写回")
    print("=== STATE_UPDATED ===")

    print("\n" + "=" * 60)
    print("  Demo 运行完毕")
    print("=" * 60)


if __name__ == "__main__":
    main()
