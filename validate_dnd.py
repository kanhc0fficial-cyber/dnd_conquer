import os
import json
import glob

def find_files():
    package_dirs = []
    # 查找所有带有 'package' 的文件夹
    for root, dirs, files in os.walk('.'):
        for d in dirs:
            if 'package' in d.lower():
                package_dirs.append(os.path.join(root, d))
    
    char_files = []
    loc_files = []
    for d in package_dirs:
        for f in os.listdir(d):
            if f.endswith('.json'):
                fname = f.lower()
                # 模糊匹配 characters 和 locations
                if 'char' in fname:
                    char_files.append(os.path.join(d, f))
                if 'loc' in fname:
                    loc_files.append(os.path.join(d, f))
                    
    return char_files, loc_files

def extract_char_ids_from_loc(loc_data):
    found = set()
    def walk(node):
        if isinstance(node, dict):
            if "id" in node and isinstance(node["id"], str):
                val = node["id"]
                # 识别常见的角色ID前缀
                if val.startswith(("card_char_", "char_", "npc_")):
                    found.add(val)
            for k, v in node.items():
                walk(v)
        elif isinstance(node, list):
            for item in node:
                if isinstance(item, str):
                    if item.startswith(("card_char_", "char_", "npc_")):
                        found.add(item)
                else:
                    walk(item)
    walk(loc_data)
    return found

def main():
    char_files, loc_files = find_files()
    
    print(f"找到的角色文件: {char_files}")
    print(f"找到的地点文件: {loc_files}")
    print("-" * 50)
    
    # 提前读取所有地点数据，并收集合法的 location ID
    valid_loc_ids = set()
    loc_data_cache = {}
    for lf in loc_files:
        try:
            with open(lf, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    loc_data_cache[lf] = data
                    for loc_id in data.keys():
                        valid_loc_ids.add(loc_id)
        except Exception as e:
            print(f"读取 {lf} 时出错: {e}")
            
    missing_loc_chars = []
    invalid_loc_chars = []
    
    # 1. 校验 characters.json 中是否所有人物都安排了 location，以及 location 是否有效
    for cf in char_files:
        try:
            with open(cf, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for char_id, char_info in data.items():
                        if isinstance(char_info, dict):
                            loc = char_info.get("location")
                            if not loc:
                                missing_loc_chars.append((cf, char_id, char_info.get("name", "Unknown")))
                            elif loc not in valid_loc_ids:
                                invalid_loc_chars.append((cf, char_id, char_info.get("name", "Unknown"), loc))
        except Exception as e:
            print(f"读取 {cf} 时出错: {e}")
            
    print("【1. 角色 Location 字段校验结果】")
    if not missing_loc_chars and not invalid_loc_chars:
        print("✅ 所有角色都安排了 location，且 location 均存在有效。")
    
    if missing_loc_chars:
        print(f"❌ 发现 {len(missing_loc_chars)} 个角色未安排 location:")
        for cf, cid, name in missing_loc_chars:
            print(f"  - 文件: {cf} | 角色ID: {cid} | 姓名: {name}")
            
    if invalid_loc_chars:
        print(f"❌ 发现 {len(invalid_loc_chars)} 个角色指向了不存在的 location:")
        for cf, cid, name, loc in invalid_loc_chars:
            print(f"  - 文件: {cf} | 角色ID: {cid} | 姓名: {name} | 无效的Location: {loc}")
            
    print("-" * 50)
    
    # 2. 校验 locations.json 中是否存在人物同时存在在多个地方的情况
    char_to_locs = {}
    
    for lf, data in loc_data_cache.items():
        for loc_id, loc_info in data.items():
            chars_in_loc = extract_char_ids_from_loc(loc_info)
            for cid in chars_in_loc:
                if cid not in char_to_locs:
                    char_to_locs[cid] = []
                char_to_locs[cid].append((lf, loc_id, loc_info.get("name", "Unknown")))

    print("【2. 地点中人物多重存在校验结果】")
    multiple_loc_chars = {cid: locs for cid, locs in char_to_locs.items() if len(locs) > 1}
    
    if not multiple_loc_chars:
        print("✅ 没有发现人物同时存在于多个地点的情况。")
    else:
        print(f"❌ 发现 {len(multiple_loc_chars)} 个人物同时存在于多个地点:")
        for cid, locs in multiple_loc_chars.items():
            print(f"  - 角色ID: {cid}")
            for lf, lid, lname in locs:
                print(f"      存在于 -> 文件: {lf} | 地点ID: {lid} | 地点名称: {lname}")

if __name__ == '__main__':
    main()
