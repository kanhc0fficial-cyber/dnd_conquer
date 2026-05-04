import json

loc_path = r'C:\dnd_demo\package_drow_minor_city\locations.json'
with open(loc_path, 'r', encoding='utf-8') as f:
    locs = json.load(f)

# 移除之前可能错误的分配
for loc in locs.values():
    if 'NPC第一次出场' in loc:
        del loc['NPC第一次出场']

# 人工校对的最合理“初次相遇”地点
explicit_first_appearances = {
    'card_char_zzik_zzik': 'loc_lift_2', # Hook 01: PC去修二号升降梯时初次撞破他
    'card_char_ryltar_captain': 'loc_spider_cavalry_camp_1', # 队长大本营
    'card_char_shadowfire_dragon': 'loc_gem_appraisal', # Hook 02: 盲眼先知在鉴定所屋顶诱惑PC
    'card_char_talytha_melarn': 'loc_flesh_auction', # 塔莉莎经营的血肉拍卖台
    'card_char_veldrin_tax_collector': 'loc_tax_office', # Hook 03: 税务局窗户外的初次接触
    'card_char_elara_slave': 'loc_flesh_auction', # 被拍卖的公主初登场
    'card_char_kaelen_smuggler': 'loc_blind_alley_black_market', # 走私黑市老大大本营
    'card_char_ilx_oryndoll': 'loc_blind_alley_black_market', # Hook 06: 盲女在黑市买醉邀约
    'card_char_nalfein_baenre': 'loc_mage_tower_bottom', # 她的主要藏身与施法地
    'card_char_lydia_zhentarim': 'loc_purple_amber_inn', # Hook 04: 高级客栈的温柔陷阱
    'card_char_nym_wanderer': 'loc_mercenary_camp', # 佣兵大本营
    'card_char_pharaun_heretic': 'loc_mage_tower_middle', # Hook 05: 法师塔主层的忽悠
    'card_char_lyra_moon_dancer': 'loc_phantom_dance_scrolls', # 月舞者的乐器/卷轴店大本营
    'card_char_helga_iron_hard': 'loc_duergar_fence', # Hook 03: 去灰矮人店铺买东西时被雇佣
    'card_char_vorn_one_eye': 'loc_duergar_fence', # 销账铺前台
    'card_char_myconid_princess': 'loc_broken_web_slum_1', # Hook 05: 贫民窟阴暗角落发现她在救人
    'card_char_yvanna_slime_druid': 'loc_bottom_corpse_pit', # 粘液德鲁伊的堆肥坑老巢
    'card_char_grom_gladiator': 'loc_arena_1', # 竞技场
    'card_char_vhalin_spymaster': 'loc_nightclub_abyss', # Hook 10: 在夜总会管道外威胁PC
    'card_char_syl_shadow_dancer': 'loc_assassin_tools', # 刺客店
    'card_char_mizri_nasadra': 'loc_matron_council', # 主母大本营
    'card_char_vierna_zauviir': 'loc_zauviir_fortress', # 佐维尔堡垒
    'card_char_xalyth_cult_leader': 'loc_hanging_tower_top' # 邪教塔顶
}

# 对应的活动描述 (复用之前的描述)
activities = {
    'card_char_zzik_zzik': {'name': '吱吱', 'activity': '暗中监视被强酸腐蚀的承重网，准备收买撞破计划的维修工。'},
    'card_char_ryltar_captain': {'name': '瑞尔塔队长', 'activity': '愤怒地悬赏寻找破坏升降梯的反抗军线索。'},
    'card_char_shadowfire_dragon': {'name': '盲影', 'activity': '以脆弱盲眼精灵先知的伪装，引诱贪婪的维修工去送致命的伪造预言。'},
    'card_char_talytha_melarn': {'name': '塔莉莎·梅拉恩', 'activity': '作为拍卖行的实际控制者，在幕后审视所有高价值的交易。'},
    'card_char_veldrin_tax_collector': {'name': '维尔德林', 'activity': '冷酷地处理账务，并试图将装满黑金和勒索信的包裹交给悬在窗外的维修工。'},
    'card_char_elara_slave': {'name': '埃拉拉', 'activity': '作为压轴商品被展示在拍卖台上，引发各大家族的竞价。'},
    'card_char_kaelen_smuggler': {'name': '凯伦', 'activity': '在黑市指挥走私网络。'},
    'card_char_ilx_oryndoll': {'name': '伊尔克斯', 'activity': '操纵盲女化身在黑市边缘买醉，寻找有感情的猎物体验“约会”。'},
    'card_char_nalfein_baenre': {'name': '纳尔芬·班瑞', 'activity': '在底层准备深渊献祭仪式，并偶尔前往黑市强行收购邪恶灵魂石。'},
    'card_char_lydia_zhentarim': {'name': '莉迪亚·暗星', 'activity': '伪装成高阶香料商人，在高级客栈用致幻香气色诱底层工人去安放窃听器。'},
    'card_char_nym_wanderer': {'name': '宁姆·流浪者', 'activity': '在防守严密的帐篷内指挥佣兵团的日常运作。'},
    'card_char_pharaun_heretic': {'name': '法劳恩', 'activity': '恭维东方武僧，忽悠对方在维护物理蛛网时贴上破坏结界的符文。'},
    'card_char_lyra_moon_dancer': {'name': '莱拉·星眼', 'activity': '在卷轴店的伪装下，寻找身手敏捷的人去刑场上空切断承重网救人。'},
    'card_char_helga_iron_hard': {'name': '赫尔加·铁石', 'activity': '在隐秘铁砧前开出极高价码，雇佣“死了也没人在乎”的飞贼去偷秘银。'},
    'card_char_vorn_one_eye': {'name': '独眼沃恩', 'activity': '在前台两头吃回扣，倒卖一些次品或赃物。'},
    'card_char_myconid_princess': {'name': '微光', 'activity': '散发着微光，躲在阴暗角落里用孢子汁液治愈濒死的地精，面临被猎杀的风险。'},
    'card_char_yvanna_slime_druid': {'name': '伊万娜·腐缚者', 'activity': '在堆肥深处研究如何将尸体转化为腐烂的原始汤。'},
    'card_char_grom_gladiator': {'name': '格罗姆', 'activity': '在场上连胜，不知道自己的饮水碗即将被维修工高空投毒。'},
    'card_char_vhalin_spymaster': {'name': '瓦林·夜影', 'activity': '带领打手堵住两头通风管，优雅地威胁捡到绝密录音的清洁工。'},
    'card_char_syl_shadow_dancer': {'name': '希尔·影舞者', 'activity': '在刺客工具店伪装成冷酷的男性战士，准备下一次暗杀。'},
    'card_char_mizri_nasadra': {'name': '米兹里主母', 'activity': '在议事大厅表面和气地谈判，背地里密谋清洗。'},
    'card_char_vierna_zauviir': {'name': '维尔娜主母', 'activity': '在堡垒内忧心忡忡，处于两大顶级家族夹缝中试图保全自身。'},
    'card_char_xalyth_cult_leader': {'name': '萨莉丝', 'activity': '在传送门枢纽准备终极仪式，企图将整个城市拉入远域。'}
}

for npc_id, loc_id in explicit_first_appearances.items():
    if loc_id in locs:
        if 'NPC第一次出场' not in locs[loc_id]:
            locs[loc_id]['NPC第一次出场'] = []
        locs[loc_id]['NPC第一次出场'].append({
            'id': npc_id,
            'name': activities[npc_id]['name'],
            'activity': activities[npc_id]['activity']
        })

with open(loc_path, 'w', encoding='utf-8') as f:
    json.dump(locs, f, ensure_ascii=False, indent=2)

print("CORRECTED_LOCATIONS")
for loc_id, loc_data in locs.items():
    if 'NPC第一次出场' in loc_data:
        print(f"- {loc_id}: {[n['name'] for n in loc_data['NPC第一次出场']]}")
