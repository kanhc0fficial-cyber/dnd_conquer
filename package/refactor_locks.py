import json

locations_file = 'package_drow_minor_city/locations.json'
quests_file = 'package_drow_minor_city/quests.json'

def get_condition_for_npc(npc_id):
    # Bosses / High Level
    if npc_id in ["card_char_xalyth_cult_leader", "card_char_nalfein_baenre", "card_char_mizri_nasadra", "card_char_shadowfire_dragon", "card_char_ilx_oryndoll"]:
        return "pc_level >= 5"
    # Mid-tier
    elif npc_id in ["card_char_talytha_melarn", "card_char_vierna_zauviir", "card_char_veldrin_tax_collector", "card_char_lydia_zhentarim", "card_char_nym_wanderer"]:
        return "pc_level >= 3"
    # Early-tier / accessible
    else:
        return "pc_level >= 1"

# Update locations
with open(locations_file, 'r', encoding='utf-8') as f:
    locations = json.load(f)

for loc_id, loc_data in locations.items():
    if "NPC第一次出场" in loc_data:
        npcs = loc_data.pop("NPC第一次出场")
        loc_data["npc_first_appearances"] = npcs
        for npc in loc_data["npc_first_appearances"]:
            npc["appearance_condition"] = get_condition_for_npc(npc.get("id"))

with open(locations_file, 'w', encoding='utf-8') as f:
    json.dump(locations, f, ensure_ascii=False, indent=2)

# Update quests
with open(quests_file, 'r', encoding='utf-8') as f:
    quests = json.load(f)

for quest_id, quest_data in quests.items():
    # If the user meant quests should also have npc_first_appearances and appearance_condition
    # We will generate it based on involved_npcs, or just add appearance_condition to the quest itself.
    # Since the prompt said "quests和locations中的 NPC第一次出场", let's ensure quests have it if they didn't.
    # Actually, we can just look at involved_npcs and populate npc_first_appearances.
    if "involved_npcs" in quest_data:
        quest_data["npc_first_appearances"] = []
        for npc_id in quest_data["involved_npcs"]:
            quest_data["npc_first_appearances"].append({
                "id": npc_id,
                "appearance_condition": get_condition_for_npc(npc_id)
            })

with open(quests_file, 'w', encoding='utf-8') as f:
    json.dump(quests, f, ensure_ascii=False, indent=2)

print("Successfully refactored locations.json and quests.json with English keys and appearance conditions.")
