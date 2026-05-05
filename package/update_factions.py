import json
import os

factions_file = 'package_drow_minor_city/factions.json'
chars_file = 'package_drow_minor_city/characters.json'

with open(factions_file, 'r', encoding='utf-8') as f:
    factions = json.load(f)

with open(chars_file, 'r', encoding='utf-8') as f:
    characters = json.load(f)

# Step 1: Map existing characters
for fac_id in factions:
    factions[fac_id]['existing_characters'] = []

for char_id, char_data in characters.items():
    fac = char_data.get('faction')
    if fac in factions:
        factions[fac]['existing_characters'].append(char_id)

# Step 2 & 3: Add possible enemies and minor npcs
faction_data = {
    "fac_house_nasadra": {
        "possible_enemies": [
            {"id": "enemy_drow_guard", "name": "纳萨德拉家族卫兵"}, 
            {"id": "enemy_spider_knight", "name": "精锐蜘蛛骑士"}, 
            {"id": "enemy_drow_priestess", "name": "罗丝高阶女祭司"}
        ],
        "possible_minor_npcs": ["仆役", "低阶家族士兵", "信使", "被折磨的奴隶"]
    },
    "fac_deep_blood_resistance": {
        "possible_enemies": [
            {"id": "enemy_goblin_rebel", "name": "武装地精暴徒"}, 
            {"id": "enemy_orc_gladiator", "name": "绝望的兽人角斗士"}, 
            {"id": "enemy_rebel_saboteur", "name": "反抗军破坏者"}
        ],
        "possible_minor_npcs": ["受伤的逃亡奴隶", "传递消息的地精", "暗藏武器的乞丐"]
    },
    "fac_web_smugglers": {
        "possible_enemies": [
            {"id": "enemy_smuggler_thug", "name": "黑市打手"}, 
            {"id": "enemy_drow_rogue", "name": "卓尔游荡者"}, 
            {"id": "enemy_duergar_mercenary", "name": "被雇佣的灰矮人佣兵"}
        ],
        "possible_minor_npcs": ["兜售假情报的线人", "黑市搬运工", "成瘾的买家"]
    },
    "fac_jaezred_chaulssin": {
        "possible_enemies": [
            {"id": "enemy_shadow_assassin", "name": "阴影刺客"}, 
            {"id": "enemy_shadow_demon", "name": "影魔"}, 
            {"id": "enemy_drow_male_infiltrator", "name": "男性卓尔渗透者"}
        ],
        "possible_minor_npcs": ["伪装成平民的密探", "被魅惑的线人"]
    },
    "fac_bregan_daerthe": {
        "possible_enemies": [
            {"id": "enemy_bregan_mercenary", "name": "达耶特精英佣兵"}, 
            {"id": "enemy_drow_gunslinger", "name": "卓尔火枪手"}, 
            {"id": "enemy_illusionist_scout", "name": "幻术师斥候"}
        ],
        "possible_minor_npcs": ["佣兵营地后勤人员", "酒馆情报商"]
    },
    "fac_oryndoll_expedition": {
        "possible_enemies": [
            {"id": "enemy_mind_flayer", "name": "夺心魔调查员"}, 
            {"id": "enemy_intellect_devourer", "name": "噬脑怪"}, 
            {"id": "enemy_thrall_guard", "name": "被心灵控制的卓尔傀儡"}
        ],
        "possible_minor_npcs": ["举止僵硬的平民（被控制）", "无意识的仆役"]
    },
    "fac_deep_dragon_shadowfire": {
        "possible_enemies": [
            {"id": "enemy_dragon_cultist", "name": "盲信的巨龙教徒"}, 
            {"id": "enemy_stone_golem", "name": "活化石雕守卫"}, 
            {"id": "enemy_deep_dragon_wyrmling", "name": "深龙雏龙"}
        ],
        "possible_minor_npcs": ["被迷惑的探险者", "寻找预言的狂热者"]
    },
    "fac_minor_official_veldrin": {
        "possible_enemies": [
            {"id": "enemy_tax_enforcer", "name": "税务执法打手"}, 
            {"id": "enemy_corrupt_guard", "name": "受贿的城市卫兵"}, 
            {"id": "enemy_bounty_hunter", "name": "受雇赏金猎人"}
        ],
        "possible_minor_npcs": ["战战兢兢的记账员", "排队交税的商贩", "被勒索的平民"]
    },
    "fac_clan_iron_hard": {
        "possible_enemies": [
            {"id": "enemy_duergar_warrior", "name": "灰矮人重甲战士"}, 
            {"id": "enemy_duergar_smith_priest", "name": "灰矮人锻造牧师"}, 
            {"id": "enemy_clockwork_hound", "name": "发条机械猎犬"}
        ],
        "possible_minor_npcs": ["挥汗如雨的学徒", "搬运矿石的苦力", "讨价还价的商贩"]
    },
    "fac_slime_cult": {
        "possible_enemies": [
            {"id": "enemy_black_pudding", "name": "黑布丁怪"}, 
            {"id": "enemy_slime_mutant", "name": "粘液变异卓尔"}, 
            {"id": "enemy_gelatinous_cube", "name": "凝胶方块"}
        ],
        "possible_minor_npcs": ["精神错乱的下水道流浪汉", "身上带有奇怪真菌的狂徒"]
    },
    "fac_moon_dancers": {
        "possible_enemies": [
            {"id": "enemy_moon_dancer_blade", "name": "月舞剑客"}, 
            {"id": "enemy_surface_elf_ally", "name": "地表精灵盟友"}, 
            {"id": "enemy_silver_light_cleric", "name": "银光牧师"}
        ],
        "possible_minor_npcs": ["隐藏身份的信徒", "等待护送的难民", "紧张的带路向导"]
    },
    "fac_myconid_glow_cap": {
        "possible_enemies": [
            {"id": "enemy_myconid_sovereign", "name": "蕈人王卫队"}, 
            {"id": "enemy_spore_servant", "name": "孢子仆从"}, 
            {"id": "enemy_hallucinatory_shroom", "name": "致幻毒蘑菇怪"}
        ],
        "possible_minor_npcs": ["散播中立孢子的幼年蕈人", "沉浸在幻觉共鸣中的真菌生物"]
    },
    "fac_zhentarim_spies": {
        "possible_enemies": [
            {"id": "enemy_zhentarim_assassin", "name": "散塔林会毒刃刺客"}, 
            {"id": "enemy_human_mercenary", "name": "人类重装佣兵"}, 
            {"id": "enemy_doppelganger_spy", "name": "变形怪间谍"}
        ],
        "possible_minor_npcs": ["表面热情的香料商人", "负责望风的乞丐", "走私马车夫"]
    },
    "fac_house_baenre_exile": {
        "possible_enemies": [
            {"id": "enemy_shadow_demon", "name": "束缚影魔"}, 
            {"id": "enemy_drow_necromancer", "name": "卓尔死灵法师学徒"}, 
            {"id": "enemy_undead_thrall", "name": "复生的亡灵奴隶"}
        ],
        "possible_minor_npcs": ["被恐惧支配的实验室助手", "运送魔法材料的黑市跑腿"]
    }
}

for fac_id, data in factions.items():
    if fac_id in faction_data:
        data['possible_enemies'] = faction_data[fac_id]['possible_enemies']
        data['possible_minor_npcs'] = faction_data[fac_id]['possible_minor_npcs']
    else:
        # Fallback
        data['possible_enemies'] = [{"id": "enemy_generic_guard", "name": "通用守卫"}]
        data['possible_minor_npcs'] = ["平民"]

with open(factions_file, 'w', encoding='utf-8') as f:
    json.dump(factions, f, ensure_ascii=False, indent=2)

print("factions.json updated successfully.")
