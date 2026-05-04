import json

loc_path = r'C:\dnd_demo\package_drow_minor_city\locations.json'
char_path = r'C:\dnd_demo\package_drow_minor_city\characters.json'

with open(loc_path, 'r', encoding='utf-8') as f:
    locs = json.load(f)
with open(char_path, 'r', encoding='utf-8') as f:
    chars = json.load(f)

npc_possible_locations = {}
npc_first_location = {}
npc_activities = {}

# Pass 1: gather data from the existing npc_presence
for loc_id, loc_data in locs.items():
    presence = loc_data.get('npc_presence', {})
    for npc_id, npc_data in presence.items():
        if npc_id not in npc_possible_locations:
            npc_possible_locations[npc_id] = []
        loc_name = loc_data.get('name', loc_id)
        if loc_name not in npc_possible_locations[npc_id]:
            npc_possible_locations[npc_id].append(loc_name)
        
        # Determine first location (just picking the first one encountered in the JSON keys, which is deterministic)
        if npc_id not in npc_first_location:
            npc_first_location[npc_id] = loc_id
            npc_activities[npc_id] = npc_data

# Pass 2: modify locations.json
for loc_id, loc_data in locs.items():
    if 'npc_presence' in loc_data:
        del loc_data['npc_presence']
    
    first_appearances = []
    for npc_id, first_loc_id in npc_first_location.items():
        if first_loc_id == loc_id:
            first_appearances.append(npc_activities[npc_id])
    
    # Add the Chinese key requested by user
    if first_appearances:
        loc_data['NPC第一次出场'] = first_appearances

# Pass 3: modify characters.json
missing_chars = []
for char_id, char_data in chars.items():
    if char_id in npc_possible_locations:
        char_data['possible_locations'] = npc_possible_locations[char_id]
    else:
        char_data['possible_locations'] = []
        missing_chars.append(char_data.get('name', char_id))

with open(loc_path, 'w', encoding='utf-8') as f:
    json.dump(locs, f, ensure_ascii=False, indent=2)

with open(char_path, 'w', encoding='utf-8') as f:
    json.dump(chars, f, ensure_ascii=False, indent=2)

print("MISSING_CHARS:", json.dumps(missing_chars, ensure_ascii=False))
