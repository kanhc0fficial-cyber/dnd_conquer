import json
import os

file_path = r'C:\dnd_demo\package_drow_minor_city\locations.json'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for loc in data.values():
    loc['npc_presence'] = {}

mapping = {
    'loc_lift_2': [
        {'id': 'card_char_zzik_zzik', 'name': '吱吱', 'activity': '暗中监视被强酸腐蚀的承重网，准备收买撞破计划的维修工。'}
    ],
    'loc_slaves_pens': [
        {'id': 'card_char_zzik_zzik', 'name': '吱吱', 'activity': '在奴隶中秘密串联，策划破坏升降梯的行动。'}
    ],
    'loc_spider_cavalry_camp_1': [
        {'id': 'card_char_ryltar_captain', 'name': '瑞尔塔队长', 'activity': '愤怒地悬赏寻找破坏升降梯的反抗军线索。'}
    ],
    'loc_gem_appraisal': [
        {'id': 'card_char_shadowfire_dragon', 'name': '盲影', 'activity': '以脆弱盲眼精灵先知的伪装，引诱贪婪的维修工去送致命的伪造预言。'}
    ],
    'loc_melarn_manor': [
        {'id': 'card_char_talytha_melarn', 'name': '塔莉莎·梅拉恩', 'activity': '在庄园中接收密函并部署针对第一家族的伏击；或者因为防守严密而遭到飞贼光顾。'}
    ],
    'loc_tax_office': [
        {'id': 'card_char_veldrin_tax_collector', 'name': '维尔德林', 'activity': '冷酷地处理账务，并试图将装满黑金和勒索信的包裹交给悬在窗外的维修工。'}
    ],
    'loc_flesh_auction': [
        {'id': 'card_char_veldrin_tax_collector', 'name': '维尔德林', 'activity': '严厉查账，寻找机会买下情人的自由契约。'},
        {'id': 'card_char_elara_slave', 'name': '埃拉拉', 'activity': '作为压轴商品被展示在拍卖台上，引发各大家族的竞价。'}
    ],
    'loc_blind_alley_black_market': [
        {'id': 'card_char_kaelen_smuggler', 'name': '凯伦', 'activity': '作为走私老大，在死信箱处等待接收维尔德林的黑账本。'},
        {'id': 'card_char_ilx_oryndoll', 'name': '伊尔克斯', 'activity': '操纵盲女化身在黑市边缘买醉，寻找有感情的猎物体验“约会”。'},
        {'id': 'card_char_nalfein_baenre', 'name': '纳尔芬·班瑞', 'activity': '带着隐形影魔堵住捡到灵魂石的维修工，冷酷地强买强卖。'}
    ],
    'loc_purple_amber_inn': [
        {'id': 'card_char_lydia_zhentarim', 'name': '莉迪亚·暗星', 'activity': '伪装成高阶香料商人，用致幻香气色诱底层工人去安放窃听器。'}
    ],
    'loc_mercenary_camp': [
        {'id': 'card_char_nym_wanderer', 'name': '宁姆·流浪者', 'activity': '在防守严密的帐篷内指挥南门封锁线，随时可能抓包安放窃听器的人。'}
    ],
    'loc_mage_tower_middle': [
        {'id': 'card_char_pharaun_heretic', 'name': '法劳恩', 'activity': '恭维东方武僧，忽悠对方在维护物理蛛网时贴上破坏结界的符文。'}
    ],
    'loc_mage_tower_bottom': [
        {'id': 'card_char_nalfein_baenre', 'name': '纳尔芬·班瑞', 'activity': '进行深渊献祭仪式，召唤影魔去抢劫税务小队的水晶。'}
    ],
    'loc_phantom_dance_scrolls': [
        {'id': 'card_char_lyra_moon_dancer', 'name': '莱拉·星眼', 'activity': '在乐器/卷轴店的伪装下，恳求武僧侠客去刑场上空切断承重网救人。'}
    ],
    'loc_lower_torture_rack': [
        {'id': 'card_char_lyra_moon_dancer', 'name': '莱拉·星眼', 'activity': '绝望地潜伏在刑场边缘，如果没人帮忙切断承重丝，准备亲自上阵。'},
        {'id': 'card_char_elara_slave', 'name': '埃拉拉', 'activity': '即将面临处决的异国公主，等待从高空坠入安全网的救援。'}
    ],
    'loc_duergar_fence': [
        {'id': 'card_char_helga_iron_hard', 'name': '赫尔加·铁石', 'activity': '在隐秘铁砧前开出极高价码，雇佣“死了也没人在乎”的飞贼去偷秘银。'},
        {'id': 'card_char_vorn_one_eye', 'name': '独眼沃恩', 'activity': '在前台两头吃回扣，倒卖一些次品或赃物。'}
    ],
    'loc_broken_web_slum_1': [
        {'id': 'card_char_myconid_princess', 'name': '微光', 'activity': '散发着微光，躲在阴暗角落里用孢子汁液治愈濒死的地精，面临被猎杀的风险。'},
        {'id': 'card_char_kaelen_smuggler', 'name': '凯伦', 'activity': '在无月之夜，指挥三千底层平民和奴隶进行史诗级的大逃亡。'}
    ],
    'loc_waste_dump': [
        {'id': 'card_char_myconid_princess', 'name': '微光', 'activity': '在此播撒净化孢子，试图清理城市的炼金废料。'},
        {'id': 'card_char_yvanna_slime_druid', 'name': '伊万娜·腐缚者', 'activity': '在这里培育强酸软泥怪，与孢子的魔力发生碰撞引发毒雨。'}
    ],
    'loc_bottom_corpse_pit': [
        {'id': 'card_char_yvanna_slime_druid', 'name': '伊万娜·腐缚者', 'activity': '在堆肥深处研究如何将尸体转化为腐烂的原始汤。'}
    ],
    'loc_arena_1': [
        {'id': 'card_char_grom_gladiator', 'name': '格罗姆', 'activity': '在场上连胜，不知道自己的饮水碗即将被维修工高空投毒。'},
        {'id': 'card_char_lydia_zhentarim', 'name': '莉迪亚·暗星', 'activity': '在后台利用美色买通维修工，准备操纵赌局并买下败北的冠军。'}
    ],
    'loc_nightclub_abyss': [
        {'id': 'card_char_vhalin_spymaster', 'name': '瓦林·夜影', 'activity': '带领打手堵住两头通风管，优雅地威胁捡到绝密录音的清洁工。'}
    ],
    'loc_heresy_torture_chamber': [
        {'id': 'card_char_ilx_oryndoll', 'name': '伊尔克斯', 'activity': '违抗主脑命令，将绑架来的幻术师藏在这里欣赏其“充满悲伤情感”的表演。'}
    ],
    'loc_assassin_tools': [
        {'id': 'card_char_syl_shadow_dancer', 'name': '希尔·影舞者', 'activity': '从这里出发，前往外围岗哨执行毫无魔法痕迹的连环暗杀。'}
    ],
    'loc_noble_baths': [
        {'id': 'card_char_yvanna_slime_druid', 'name': '伊万娜·腐缚者', 'activity': '潜行至浴场源头，将神力强酸排入池中溶解洗浴的贵族。'}
    ],
    'loc_matron_council': [
        {'id': 'card_char_mizri_nasadra', 'name': '米兹里主母', 'activity': '在议事大厅表面和气地谈判，背地里她的录音水晶却掉在了夜总会管道里。'}
    ],
    'loc_nasadra_torture_room': [
        {'id': 'card_char_mizri_nasadra', 'name': '米兹里主母', 'activity': '亲自拷打反抗军成员，试图找出破坏升降梯的真凶。'}
    ],
    'loc_broken_tooth_tavern': [
        {'id': 'card_char_ryltar_captain', 'name': '瑞尔塔队长', 'activity': '在酒精中麻痹自己，偶尔因为受贿而对走私视而不见。'}
    ],
    'loc_zauviir_fortress': [
        {'id': 'card_char_vierna_zauviir', 'name': '维尔娜主母', 'activity': '在堡垒内忧心忡忡，处于两大顶级家族夹缝中试图保全自身。'}
    ],
    'loc_hanging_tower_top': [
        {'id': 'card_char_xalyth_cult_leader', 'name': '萨莉丝', 'activity': '在传送门枢纽准备终极仪式，企图将整个城市拉入远域。'}
    ]
}

for loc_id, presences in mapping.items():
    if loc_id in data:
        for p in presences:
            data[loc_id]['npc_presence'][p['id']] = p

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("SUCCESS")
