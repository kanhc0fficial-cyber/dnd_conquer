import json
import os

file_path = 'C:\\dnd_demo\\package_drow_minor_city\\quests.json'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

data['quest_05_myconid_healer'] = {
  'name': '黑暗中的微光诊所',
  'type': 'pc_driven',
  'involved_factions': ['fac_myconid_glow_cap', 'fac_house_nasadra'],
  'involved_npcs': ['card_char_myconid_princess'],
  'hook': 'PC在贫民窟清理致命的黑霉菌网时，偶然发现一个极其隐蔽的角落里，浑身散发着微光的美丽孢子公主“微光”正在用自己的汁液治愈几个濒死的地精。',
  'process': '一名暗中跟踪微光的卓尔炼金术士也发现了这里。他许诺给PC一笔足以让PC在高级酒馆挥霍半个月的巨款，要求PC用行会的强效石化网把微光困住，他要活捉这个“极其珍贵的炼金材料”。',
  'task': '做出选择：为了巨款配合炼金术士下网抓捕微光，或者出于朴素的正义感（以及微光那纯洁无瑕的美貌）将炼金术士一脚踹下深渊。',
  'resolution': '如果抓捕微光，PC拿到巨款，但微光会因为惊恐而引爆毒气，毒死周边包括PC在内的所有人（如果PC跑得不够快）。如果救下微光，她会感激地在PC身上留下一个永久的防毒孢子印记。'
}

data['quest_06_alien_romance'] = {
  'name': '致命的盲眼约会',
  'type': 'pc_driven',
  'involved_factions': ['fac_oryndoll_expedition', 'fac_web_smugglers'],
  'involved_npcs': ['card_char_ilx_oryndoll'],
  'hook': 'PC在黑市买醉时，一个戴着眼罩、气质极度清纯美丽的卓尔盲女主动靠近了PC。她羞涩地邀请PC陪她去城市下层“看”一场荧光蘑菇雨。PC的虚荣心和好色心立刻被点燃。',
  'process': '这实际上是夺心魔伊尔克斯操控的化身，它只想体验一把人类的“约会”情绪。但在约会途中，几个同样潜伏在城里的其他夺心魔发现了伊尔克斯的异常，决定杀死这个化身以及“无足轻重”的PC。',
  'task': '在浪漫的荧光蘑菇雨中，突然面临隐形怪物的精神攻击。PC必须一边保护这个看似柔弱的盲女，一边逃离猎杀。',
  'resolution': '如果PC成功带着盲女逃离，伊尔克斯体验到了“心动与吊桥效应”，会暗中在PC的脑海里留下一个精神护盾作为报答。如果PC抛弃盲女逃跑，盲女死亡，伊尔克斯会因为失恋的愤怒而对PC展开持续的精神折磨。'
}

data['quest_07_cursed_soulstone'] = {
  'name': '破烂网里的邪神之石',
  'type': 'pc_driven',
  'involved_factions': ['fac_house_baenre_exile', 'fac_house_nasadra'],
  'involved_npcs': ['card_char_nalfein_baenre'],
  'hook': 'PC在修补法师塔外围的老旧蛛网时，从一具已经风化的白骨怀里摸到了一枚散发着不祥红光的黑宝石（灵魂石）。PC本能地觉得这东西能在黑市卖个好价钱。',
  'process': '当PC带着石头去黑市估价时，一个半边脸布满可怕魔痕但依然难掩高贵气质的女法师（纳尔芬）堵住了PC。她身边跟着一只隐形的影魔。她扔给PC一袋足以买下一栋房子的宝石，冷酷地命令PC把石头交出来。',
  'task': 'PC可以选择见好就收，或者因为贪婪觉得这石头肯定更值钱而试图拒绝或提价。',
  'resolution': '拿钱交货：PC发了一笔横财，但随后几个月城市会因为纳尔芬的召唤仪式而陷入死伤无数的恐怖袭击。试图提价：纳尔芬会直接让影魔斩断PC的一只手臂，强行抢走石头，并留下嘲讽。'
}

data['quest_08_arena_match_fixing'] = {
  'name': '铁笼里的加料水',
  'type': 'pc_driven',
  'involved_factions': ['fac_zhentarim_spies', 'fac_house_nasadra'],
  'involved_npcs': ['card_char_lydia_zhentarim', 'card_char_grom_gladiator'],
  'hook': 'PC接到了去血肉竞技场维护上方铁笼和防死网的肥差。在后台，之前见过面的散塔林艳谍莉迪亚找到了PC。',
  'process': '莉迪亚给了PC一管无色药剂，要求PC在悬空作业时，精确地把药液滴进连胜冠军兽人格罗姆的饮水碗里。她不仅许诺了高昂的报酬，还暗示如果PC愿意，可以成为她在城里的长期“私人伙伴”。',
  'task': '利用高空作业的便利，避开守卫和角斗士的敏锐嗅觉，完成下毒。',
  'resolution': '下毒成功：格罗姆在场上战败被莉迪亚低价买走洗脑，PC拿到钱和女间谍的吻。如果PC因为可怜格罗姆而没下毒：莉迪亚会在下注中损失惨重，随后会派杀手来解决PC这个“废物”。'
}

data['quest_09_doomed_expedition'] = {
  'name': '深渊底部的绝美石雕',
  'type': 'pc_driven',
  'involved_factions': ['fac_deep_dragon_shadowfire', 'fac_house_melarn'],
  'involved_npcs': ['card_char_shadowfire_dragon'],
  'hook': '一个不知天高地厚的梅拉恩次子组织了一支探险队去地渊底部测绘，他急需一个能背着梯子到处搭桥的便宜向导。PC为了每天十个金币的高薪加入了这支“炮灰小队”。',
  'process': '探险队在底部没有发现金银珠宝，反而发现了一个巨大的洞穴，里面摆满了栩栩如生、表情惊恐的卓尔石雕。就在次子兴奋地想要搬走石雕时，黑暗中传来了令人窒息的远古深龙的低语。',
  'task': '深龙的吐息瞬间石化了次子的两个护卫。PC必须在被石化前，利用熟练的攀爬技巧逃离。',
  'resolution': '如果PC在逃跑时顺手把吓瘫的贵族次子一起拉上梯子，会获得梅拉恩家族的重赏。如果PC选择丢下他，自己顺手掰断石雕上的几颗宝石戒指逃跑，次子会被永远石化在那里。'
}

data['quest_10_blackmail_vents'] = {
  'name': '夜总会通风管的秘密',
  'type': 'pc_driven',
  'involved_factions': ['fac_web_smugglers', 'fac_house_nasadra'],
  'involved_npcs': ['card_char_vhalin_spymaster', 'card_char_mizri_nasadra'],
  'hook': '豪华夜总会“深渊之吻”的通风管道被魅魔的体液和香料堵塞，PC被高薪请去清理。在爬行时，PC捡到了一枚掉在缝隙里的录音水晶，里面记录了第一家族主母米兹里极其放荡且涉及谋杀亲夫的音频。',
  'process': 'PC刚倒吸一口凉气，前后通风管就被夜总会老板瓦林的打手堵住了。瓦林在管道外用一种令人毛骨悚然的优雅语气说：“小老鼠，那是我的东西。交出来，你活着拿一笔钱；不交，你死在管子里。”',
  'task': '在狭窄的管道内面临绝境，PC必须决定是乖乖认怂，还是试图用这东西作为要挟。',
  'resolution': '交出水晶：PC拿到一点点“老鼠钱”，瓦林继续他的敲诈大业。如果PC试图带着水晶死里逃生并卖给主母：主母会直接把PC扔进绞肉机灭口。这是个没有好下场的惊悚局。'
}

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print('SUCCESS')
