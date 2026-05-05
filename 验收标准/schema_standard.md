# 人物与地点 JSON 架构 (Schema) 总结标准

本文档基于对 `package_drow_minor_city` 和 `package_baldur's_gate` 两个战役包中现有 `characters.json` 和 `locations.json`（或 `grove_locations.json`）的纯手工汇总与分析。我们将两个包中本质相同但拼写不同的键进行了去重和合并，并保留了完整的嵌套层级。

---

## 1. 角色 (Character) 数据结构

角色 JSON 对象通常包含以下字段（包含嵌套层级）：

1. **`id`** (String): 角色的唯一标识符。
2. **`name`** (String): 角色名称。
3. **`type`** (String): 实体类型（如 "character", "角色", "Player Character" 等）。
4. **`control`** (String): 控制方（如 "player" 表示玩家，"world" 表示世界/NPC）。
5. **`faction`** (String): 角色所属或效忠的阵营 ID。
6. **`location`** (String): 角色当前所在的地点 ID。
7. **`possible_locations`** (Array of Strings): 角色可能会出现的地点 ID 列表。
8. **`image_path`** (String): 角色相关图像的路径。
9. **`summary`** (String): 角色的简短摘要或一句话介绍。
10. **`is_locked`** (Boolean): 角色卡是否处于被锁定状态。
11. **`bound_event_id`** (String / null): 与角色当前绑定的特定剧情事件 ID。

### 1.1 剧情与性格 (Story & Personality)
*(注：合并了 `background`, `_Background`, `_story_info._Background` 以及 `motivation`, `agenda`, `_Goal` 等本质相同的字段。)*

12. **`background`** (String 或 Array of Strings): 角色的背景故事与来历。
13. **`goal`** (Array of Strings): 角色的目标与动机。
14. **`agenda`** (String): 当前的短期行动纲领或意图。
15. **`ghost`** (String): 萦绕在角色心中的过往幽灵或心结。
16. **`wound`** (String): 角色所受的心理创伤。
17. **`lie`** (String): 角色深信不疑的谎言。
18. **`contradictions`** (Array of Strings): 角色性格或行为中表现出的矛盾点。
19. **`trope_references`** (Array of Strings): 角色设定的文学或影视原型标签（如 "TheSociopath"）。

### 1.2 动态机制 (Mechanics & States)
20. **`clock`** (Object): 驱动角色行动的倒计时机制。
    - 20.1 `goal` (String): 倒计时达成的终极目标。
    - 20.2 `current` (Integer): 当前进度。
    - 20.3 `max` (Integer): 最大进度（通常是 6）。
    - 20.4 `next_event` (String): 下一个即将发生的推进事件。
    - 20.5 `pc_entrypoint` (Integer): 玩家最有可能切入干扰的进度节点。
21. **`attitude_value`** (Integer / null): 针对玩家（主角）的好感度数值。
22. **`attitude_desc`** (String): 好感度当前阶段的文字描述。
23. **`attitude_update_rule`** (String): 能够影响好感度增减的互动规则与雷区。
24. **`status` / `condition` / `current_form`** (String): 当前特殊身体状态、局势状态或特殊形态（如德鲁伊的动物变身）。

### 1.3 战斗与角色面板 (Combat & RPG Stats)
25. **`_combat_info`** (Object): D&D 规则战斗数据。
    - 25.1 `_Class` (String): 职业。
    - 25.2 `_Subclass` (String): 子职业。
    - 25.3 `_Level` (Integer): 等级。
    - 25.4 `_Stats` (Object): 属性值 (`STR`, `DEX`, `CON`, `INT`, `WIS`, `CHA`)。
    - 25.5 `_Feats` (Array of Strings): 专长列表。
    - 25.6 `_Equipment` (Object): 穿戴装备 (`MainHand`, `OffHand`, `Armor`)。
    - 25.7 `_Actions` (Array of Objects): 拥有的动作列表，每个动作含 `name`, `type` (Melee/Spell/Ability/Reaction), `effect`。
    - 25.8 `_MaxHP` (Integer): 最大生命值。
    - 25.9 魔法与职业资源: 包含法术位 (`_SpellSlots`)、气点数 (`_ki_points`)、引导神力次数 (`_channel_divinity_uses`) 等。
26. **`_level_info`** (Object): 升级经验信息。
    - 26.1 `_ExpToNextLevel` (Integer): 下一等级所需的经验值。
    - 26.2 `_ExpRules` (String): 经验规则描述。
27. **`current_hp`** (Integer): 当前生命值。
28. **`current_exp`** (Integer): 当前经验值。

### 1.4 外貌特征 (Appearance)
29. **`_appearance`** (Object):
    - 29.1 `_Race` (String): 种族。
    - 29.2 `_Body_and_Face` (Object): 容貌特征，包含 `facial_features` (面部), `eye_color` (瞳色), `hair` (发型与发色), `measurements` (三围), `height` (身高)。
    - 29.3 `_Clothing` (String): 穿着打扮。
    - 29.4 `_Description` (String): 整体外观综合描述。

### 1.5 物品与财富 (Inventory)
30. **`inventory`** (Array of Strings): 持有的物品 ID 或名称列表。
31. **`gold`** (Float / Integer): 拥有的金币数量。

---

## 2. 地点 (Location) 数据结构

地点 JSON 对象通常包含以下字段（包含嵌套层级）：

1. **`id`** (String): 地点的唯一标识符。
2. **`name`** (String): 地点名称。
3. **`coordinates`** (Array of Integers): 在地图上的坐标（如 `[x, y]`）。
4. **`description`** (Array of Strings 或 String): 对地点的综合视觉与氛围描述。*(注：合并了 `_Description` 与 `description`。)*

### 2.1 势力与冲突 (Factions & Tension)
5. **`controlling_faction`** (String): 当前实际控制此地点的阵营 ID。
6. **`contested_by`** (Array of Strings): 正在秘密渗透或试图争夺此地点的阵营 ID 列表。
7. **`core_tension`** (String): 发生在此地的核心冲突、剥削或紧张局势。

### 2.2 探索元素 (Exploration Elements)
8. **`gravity_hooks`** (Array of Strings): “引力钩子”，即吸引玩家注意力或暗示此地有故事的具体感官细节与小事件。
9. **`clues_hidden_here`** (Array of Strings): 隐藏在此处的关键情报或线索。
10. **`clues_pointing_elsewhere`** (Array of Strings): 能够将玩家引导至其他地点的线索。

### 2.3 历史与叙事 (History & Narrative)
11. **`history`** (Array of Strings 或 String): 这里的历史背景，或随着玩家进度而在该地点发生的历史事件流。*(注：合并了 `history_relevant_to_present` 与 `history`。)*
12. **`latest_narrative`** (String): 记录了在此地发生的最新剧情叙事进展。

### 2.4 人物分布 (Entities & Activities)
13. **`card_ids`** (Array of Strings): 当前物理上存在于该地点的角色或物品卡牌 ID 列表。
14. **`character_activities`** (Object): 键值对形式，Key为角色 ID，Value为该角色目前正在该地点执行的具体活动。
15. **`npc_first_appearances`** (Array of Objects): 规范 NPC 首次在此地点登场的设定规则。
    - 15.1 `id` (String): 关联的 NPC ID。
    - 15.2 `name` (String): NPC 名称。
    - 15.3 `activity` (String): NPC 登场时正在做的事情。
    - 15.4 `appearance_condition` (String): 登场的限制条件（例如 `"pc_level >= 3"`）。
