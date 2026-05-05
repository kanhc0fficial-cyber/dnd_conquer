import json

monsters_file = 'package_drow_minor_city/monsters.json'

with open(monsters_file, 'r', encoding='utf-8') as f:
    monsters = json.load(f)

new_monsters = {
  "monster_drow_priestess": {
    "id": "monster_drow_priestess",
    "name": "罗丝高阶女祭司",
    "type": "类人生物 (卓尔精灵)",
    "description": "罗丝的狂热信徒，掌握着致命的蜘蛛神术与强大的暗影魔法，地位崇高。",
    "challenge_rating": 8,
    "stats": {
      "AC": 16,
      "HP": 71,
      "speed": "30尺",
      "abilities": { "STR": 10, "DEX": 14, "CON": 12, "INT": 13, "WIS": 17, "CHA": 18 }
    },
    "traits": [
      {"name": "精类血统", "effect": "对魅惑的豁免具有优势，并且魔法无法使其陷入睡眠。"},
      {"name": "日照敏感", "effect": "在阳光照射下，攻击检定和察觉检定具有劣势。"}
    ],
    "actions": [
      {"name": "连击", "effect": "进行两次灾祸鞭攻击。"},
      {"name": "灾祸鞭", "effect": "近战武器攻击: +5命中, 伤害: 5(1d6+2)穿刺伤害，外加17(5d6)毒素伤害。"},
      {"name": "召唤恶魔 (1/日)", "effect": "尝试召唤一只妖蛛(Yochlol)，成功率50%。"}
    ]
  },
  "monster_drow_mage": {
    "id": "monster_drow_mage",
    "name": "卓尔法师",
    "type": "类人生物 (卓尔精灵)",
    "description": "研习奥术的卓尔男性，通常在家族中担任顾问或召唤师，擅长破坏与控制法术。",
    "challenge_rating": 7,
    "stats": {
      "AC": 12,
      "HP": 45,
      "speed": "30尺",
      "abilities": { "STR": 9, "DEX": 14, "CON": 10, "INT": 17, "WIS": 13, "CHA": 12 }
    },
    "traits": [
      {"name": "精类血统", "effect": "对魅惑豁免优势，魔法免疫睡眠。"}
    ],
    "actions": [
      {"name": "毒涂法杖", "effect": "近战武器攻击: +2命中, 伤害: 2(1d6-1)钝击伤害外加毒素。"},
      {"name": "施法", "effect": "可施放火球术, 闪电束, 臭云术，或死云术。豁免DC 14。"}
    ]
  },
  "monster_drider": {
    "id": "monster_drider",
    "name": "蛛化精灵 (Drider)",
    "type": "怪兽",
    "description": "被罗丝诅咒的卓尔精灵，下半身变异为巨大的蜘蛛，充满了无尽的痛苦和狂怒。",
    "challenge_rating": 6,
    "stats": {
      "AC": 19,
      "HP": 123,
      "speed": "30尺, 攀爬30尺",
      "abilities": { "STR": 16, "DEX": 16, "CON": 18, "INT": 13, "WIS": 14, "CHA": 12 }
    },
    "traits": [
      {"name": "蛛行", "effect": "可以在困难表面上攀爬，包括倒吊在天花板上，无需进行属性检定。"}
    ],
    "actions": [
      {"name": "连击", "effect": "进行三次长剑攻击，或者三次长弓攻击。它也可以将其中一次攻击替换为撕咬。"},
      {"name": "长剑", "effect": "近战武器攻击: +6命中, 伤害: 7(1d8+3)挥砍伤害。"},
      {"name": "撕咬", "effect": "近战武器攻击: +6命中, 伤害: 2(1d4)穿刺伤害，外加9(2d8)毒素伤害。"}
    ]
  },
  "monster_phase_spider": {
    "id": "monster_phase_spider",
    "name": "相位蜘蛛",
    "type": "怪兽",
    "description": "拥有在物质界和以太位面之间穿梭能力的恐怖伏击捕食者。",
    "challenge_rating": 3,
    "stats": {
      "AC": 13,
      "HP": 32,
      "speed": "30尺, 攀爬30尺",
      "abilities": { "STR": 15, "DEX": 15, "CON": 12, "INT": 6, "WIS": 10, "CHA": 6 }
    },
    "traits": [
      {"name": "以太步", "effect": "相位蜘蛛可以在它的移动和动作结束后，以一个附赠动作从物质界进入以太位面，或反之。"}
    ],
    "actions": [
      {"name": "毒牙啃咬", "effect": "近战武器攻击: +4命中, 伤害: 7(1d10+2)穿刺伤害。目标需进行DC 11体质豁免，失败受18(4d8)毒素伤害，成功减半。如果毒素伤害使目标HP降至0，目标稳定在0HP但陷入中毒和麻痹状态。"}
    ]
  },
  "monster_hook_horror": {
    "id": "monster_hook_horror",
    "name": "钩怪",
    "type": "怪兽",
    "description": "长着甲虫般坚硬外壳、头部像秃鹫且前肢为两只锋利骨钩的地底生物，经常在洞穴中通过敲击墙壁交流。",
    "challenge_rating": 3,
    "stats": {
      "AC": 15,
      "HP": 75,
      "speed": "30尺, 攀爬30尺",
      "abilities": { "STR": 18, "DEX": 10, "CON": 15, "INT": 6, "WIS": 12, "CHA": 7 }
    },
    "traits": [
      {"name": "回声定位", "effect": "拥有60尺盲视。"}
    ],
    "actions": [
      {"name": "连击", "effect": "进行两次骨钩攻击。"},
      {"name": "骨钩", "effect": "近战武器攻击: +6命中, 伤害: 11(2d6+4)穿刺伤害。"}
    ]
  },
  "monster_umber_hulk": {
    "id": "monster_umber_hulk",
    "name": "土巨怪",
    "type": "怪兽",
    "description": "庞大的虫形巨兽，通过挖掘坚硬的岩石在幽暗地域中开辟通道，其复眼能使直视者陷入迷惘。",
    "challenge_rating": 5,
    "stats": {
      "AC": 18,
      "HP": 93,
      "speed": "30尺, 掘地20尺",
      "abilities": { "STR": 20, "DEX": 8, "CON": 16, "INT": 9, "WIS": 10, "CHA": 10 }
    },
    "traits": [
      {"name": "迷乱凝视", "effect": "任何在它30尺内直视它复眼的生物，必须进行DC 15魅力豁免，失败则无法执行动作，且随机移动。"}
    ],
    "actions": [
      {"name": "连击", "effect": "进行三次攻击：两次爪击，一次啃咬。"},
      {"name": "爪击", "effect": "近战武器攻击: +8命中, 伤害: 9(1d8+5)挥砍伤害。"}
    ]
  },
  "monster_mind_flayer": {
    "id": "monster_mind_flayer",
    "name": "夺心魔",
    "type": "异怪",
    "description": "来自未知远域的残酷心灵暴君，通过奴役其他生物并吸食他们的大脑为生。",
    "challenge_rating": 7,
    "stats": {
      "AC": 15,
      "HP": 71,
      "speed": "30尺",
      "abilities": { "STR": 11, "DEX": 12, "CON": 12, "INT": 19, "WIS": 17, "CHA": 17 }
    },
    "traits": [
      {"name": "魔法抗性", "effect": "对法术和其他魔法效果的豁免具有优势。"},
      {"name": "心灵感应", "effect": "120尺内可以与任何懂语言的生物交流。"}
    ],
    "actions": [
      {"name": "触须", "effect": "近战武器攻击: +7命中, 伤害: 15(2d10+4)心灵伤害。若目标是中型或更小生物将被擒抱(逃脱DC 15)。"},
      {"name": "榨取大脑", "effect": "近战武器攻击: +7命中, 对一个被它擒抱且处于失能状态的类人生物。造成 55(10d10)穿刺伤害，若这使得目标HP降至0，则夺心魔吸食其大脑，立刻杀死目标。"},
      {"name": "心灵震爆 (充能 5-6)", "effect": "60尺锥形范围。范围内的生物必须进行DC 15智力豁免，失败受22(4d8+4)心灵伤害并震慑1分钟。"}
    ]
  },
  "monster_intellect_devourer": {
    "id": "monster_intellect_devourer",
    "name": "噬脑怪",
    "type": "异怪",
    "description": "像是一颗长着四条兽腿的类人生物大脑。它是夺心魔创造的可怕仆从，能够吞噬并取代宿主的大脑。",
    "challenge_rating": 2,
    "stats": {
      "AC": 12,
      "HP": 21,
      "speed": "40尺",
      "abilities": { "STR": 6, "DEX": 14, "CON": 13, "INT": 12, "WIS": 11, "CHA": 10 }
    },
    "traits": [
      {"name": "侦测心智", "effect": "可以感知300尺范围内有智力的生物的心智存在。"}
    ],
    "actions": [
      {"name": "爪击", "effect": "近战武器攻击: +4命中, 伤害: 7(2d4+2)挥砍伤害。"},
      {"name": "吞噬心智", "effect": "对10尺内一个有智力的生物使用，目标需进行DC 12智力豁免，失败受到2d10心灵伤害。同时噬脑怪掷3d6，若结果大于等于目标当前智力值，目标智力降至0被震慑。"},
      {"name": "躯体窃贼", "effect": "与一个5尺内被震慑且智力为0的类人生物进行智力对抗。若噬脑怪获胜，它将在魔法作用下吞噬目标大脑并钻入其头颅，完全控制宿主躯体。"}
    ]
  },
  "monster_gelatinous_cube": {
    "id": "monster_gelatinous_cube",
    "name": "凝胶方块",
    "type": "泥怪",
    "description": "完美的方形透明软泥怪，在地下通道中缓慢滑行，将路过的一切有机物悄无声息地包裹并消化。",
    "challenge_rating": 2,
    "stats": {
      "AC": 6,
      "HP": 84,
      "speed": "15尺",
      "abilities": { "STR": 14, "DEX": 3, "CON": 20, "INT": 1, "WIS": 6, "CHA": 1 }
    },
    "traits": [
      {"name": "透明", "effect": "即便凝胶方块处于视线内，若它未曾移动过，察觉其存在需通过DC 15的察觉检定。"}
    ],
    "actions": [
      {"name": "伪足", "effect": "近战武器攻击: +4命中, 伤害: 10(3d6)强酸伤害。"},
      {"name": "吞没", "effect": "移动进入生物空间，目标需通过DC 12敏捷豁免。失败则被吞没并受到10(3d6)强酸伤害，且被束缚。"}
    ]
  },
  "monster_black_pudding": {
    "id": "monster_black_pudding",
    "name": "黑布丁怪",
    "type": "泥怪",
    "description": "一种盲目且充满饥饿的黑色粘液，能够溶蚀金属和血肉。武器的劈砍不仅无法杀死它，反而会使其分裂。",
    "challenge_rating": 4,
    "stats": {
      "AC": 7,
      "HP": 85,
      "speed": "20尺, 攀爬20尺",
      "abilities": { "STR": 16, "DEX": 5, "CON": 16, "INT": 1, "WIS": 6, "CHA": 1 }
    },
    "traits": [
      {"name": "腐蚀形态", "effect": "在近战攻击黑布丁怪时，若使用的是非魔法金属武器，武器攻击后将受到永久性的腐蚀（伤害骰-1）。"},
      {"name": "分裂", "effect": "受到挥砍或闪电伤害时，若生命值高于10且体型为中型或以上，它分裂为两只新的布丁怪。"}
    ],
    "actions": [
      {"name": "伪足", "effect": "近战武器攻击: +5命中, 伤害: 6(1d6+3)钝击伤害外加18(4d8)强酸伤害。目标装备的非魔法金属护甲受到永久性削弱（AC-1）。"}
    ]
  },
  "monster_roper": {
    "id": "monster_roper",
    "name": "树绳妖 (Roper)",
    "type": "怪兽",
    "description": "外观伪装成钟乳石的可怕伏击者。它伸出粘稠而强韧的触须将猎物拉向自己那满是利齿的巨口。",
    "challenge_rating": 5,
    "stats": {
      "AC": 20,
      "HP": 93,
      "speed": "10尺, 攀爬10尺",
      "abilities": { "STR": 18, "DEX": 8, "CON": 17, "INT": 7, "WIS": 16, "CHA": 6 }
    },
    "traits": [
      {"name": "假外观", "effect": "闭上嘴巴时与普通的钟乳石或石笋一模一样。"}
    ],
    "actions": [
      {"name": "连击", "effect": "进行四次触须攻击，可以用一次咬击替换一次或全部未命中的触须攻击。"},
      {"name": "触须", "effect": "近战武器攻击: +7命中, 射程50尺。目标被擒抱，束缚状态。"},
      {"name": "咬击", "effect": "近战武器攻击: +7命中, 伤害: 22(4d8+4)穿刺伤害。"}
    ]
  },
  "monster_shadow_demon": {
    "id": "monster_shadow_demon",
    "name": "影魔",
    "type": "邪魔 (恶魔)",
    "description": "由纯粹的暗影与恶毒构成的恶魔，能在黑暗中无声穿梭并汲取鲜血。",
    "challenge_rating": 4,
    "stats": {
      "AC": 13,
      "HP": 71,
      "speed": "30尺, 飞行30尺",
      "abilities": { "STR": 1, "DEX": 17, "CON": 12, "INT": 14, "WIS": 13, "CHA": 14 }
    },
    "traits": [
      {"name": "非实体移动", "effect": "可以穿过其他生物或物体，若在物体中结束回合，受到1d10力场伤害。"},
      {"name": "暗影匿踪", "effect": "在微光或黑暗环境中，可以在附赠动作中隐匿。"}
    ],
    "actions": [
      {"name": "爪击", "effect": "近战武器攻击: +5命中, 伤害: 10(2d6+3)心灵伤害，在光照充足时伤害减半；若它隐匿且目标未发现它，则伤害增加至17(4d6+3)。"}
    ]
  },
  "monster_duergar_warlord": {
    "id": "monster_duergar_warlord",
    "name": "灰矮人督军",
    "type": "类人生物 (矮人)",
    "description": "全副武装、经历过无数次地底血战的灰矮人军事领袖，能在战场上轻易粉碎敌人的阵型。",
    "challenge_rating": 6,
    "stats": {
      "AC": 20,
      "HP": 75,
      "speed": "25尺",
      "abilities": { "STR": 18, "DEX": 11, "CON": 16, "INT": 12, "WIS": 12, "CHA": 14 }
    },
    "traits": [
      {"name": "灰矮人恢复力", "effect": "对毒素、魅惑和麻痹有优势。"},
      {"name": "日照敏感", "effect": "在阳光照射下，攻击检定和察觉检定具有劣势。"}
    ],
    "actions": [
      {"name": "连击", "effect": "进行三次战锤攻击。"},
      {"name": "战锤", "effect": "近战武器攻击: +7命中, 伤害: 9(1d8+4)钝击伤害。若目标为中型以下，会被击退10尺。"},
      {"name": "变巨术 (充能后可用)", "effect": "体积变为大型。近战攻击伤害骰加倍。"}
    ]
  },
  "monster_gloom_stalker": {
    "id": "monster_gloom_stalker",
    "name": "暗影刺客 (Gloom Stalker Assassin)",
    "type": "类人生物 (卓尔或其他)",
    "description": "杰兹雷·乔森或其他秘密结社的高级刺客，专精于在绝对黑暗中一击毙命。",
    "challenge_rating": 8,
    "stats": {
      "AC": 16,
      "HP": 78,
      "speed": "30尺, 攀爬30尺",
      "abilities": { "STR": 11, "DEX": 18, "CON": 14, "INT": 13, "WIS": 11, "CHA": 10 }
    },
    "traits": [
      {"name": "暗视免疫", "effect": "敌人的黑暗视觉无法在黑暗中看到他，对他们而言刺客视为隐形。"},
      {"name": "偷袭", "effect": "每回合一次，对一名对它处于优势或目标5尺内有刺客盟友的生物，造成额外4d6伤害。"}
    ],
    "actions": [
      {"name": "连击", "effect": "进行两次毒刺短剑攻击。"},
      {"name": "毒刺短剑", "effect": "近战武器攻击: +7命中, 伤害: 7(1d6+4)穿刺伤害，附带14(4d6)毒素伤害。"}
    ]
  },
  "monster_otyugh": {
    "id": "monster_otyugh",
    "name": "奥体格 (Otyugh)",
    "type": "异怪",
    "description": "生存在垃圾坑和下水道中的腐食异怪，拥有三条粗壮的触手和一张散发着恶臭的恐怖巨口。",
    "challenge_rating": 5,
    "stats": {
      "AC": 14,
      "HP": 114,
      "speed": "30尺",
      "abilities": { "STR": 16, "DEX": 11, "CON": 19, "INT": 6, "WIS": 13, "CHA": 6 }
    },
    "traits": [
      {"name": "有限心灵感应", "effect": "可以用简单的概念和情绪与120尺内的懂语言生物进行交流。"}
    ],
    "actions": [
      {"name": "连击", "effect": "进行一次撕咬和两次触手攻击。"},
      {"name": "触手", "effect": "近战武器攻击: +6命中, 伤害: 7(1d8+3)钝击伤害外带4(1d8)穿刺伤害。若击中，目标被擒抱。"},
      {"name": "生疫撕咬", "effect": "近战武器攻击: +6命中, 伤害: 12(2d8+3)穿刺伤害。目标需通过DC 15体质豁免否则感染恐怖疾病。"}
    ]
  },
  "monster_cloaker": {
    "id": "monster_cloaker",
    "name": "蛰伏伪怪 (Cloaker)",
    "type": "异怪",
    "description": "外观看似一件黑色或深灰色皮质披风，实际上是一种邪恶且致命的地底捕食者。",
    "challenge_rating": 8,
    "stats": {
      "AC": 14,
      "HP": 78,
      "speed": "10尺, 飞行40尺",
      "abilities": { "STR": 17, "DEX": 15, "CON": 12, "INT": 13, "WIS": 12, "CHA": 14 }
    },
    "traits": [
      {"name": "假外观", "effect": "当其处于静止时，与一件普通的暗色披风无异。"}
    ],
    "actions": [
      {"name": "连击", "effect": "进行一次咬击和一次尾击。"},
      {"name": "咬击", "effect": "近战武器攻击: +6命中, 伤害: 10(2d6+3)穿刺伤害。若目标体型大或以下，伪怪吸附于目标身上，目标视为被擒抱及目盲。"},
      {"name": "恐惧哀嚎", "effect": "发出让人心神俱裂的呻吟。30尺内的生物需进行DC 13感知豁免，失败则恐慌，直到此状态结束前它们必须用尽移动力逃离该声音。"}
    ]
  }
}

monsters.update(new_monsters)

with open(monsters_file, 'w', encoding='utf-8') as f:
    json.dump(monsters, f, ensure_ascii=False, indent=2)

print(f"Added {len(new_monsters)} new monsters to {monsters_file}.")
