from BaseClasses import Item, ItemClassification
from typing import List

class FezItem(Item):
    game: str = "Fez"


class FezItemData():
    def __init__(self, name: str, count: int, classification: ItemClassification):
        self.name = name
        self.count = count
        self.classification = classification


progression_items: List[FezItemData] = [
    FezItemData("Golden Cube",                  32, ItemClassification.progression),
    FezItemData("Anti-Cube",                    32, ItemClassification.progression),
    FezItemData("Cube Bit",                     0,  ItemClassification.progression),
    FezItemData("Owl",                          4,  ItemClassification.progression),
    FezItemData("Boileroom Door Unlocked",      1,  ItemClassification.progression),
    FezItemData("Lighthouse Door Unlocked",     1,  ItemClassification.progression),
    FezItemData("Tree Crumble Door Unlocked",   1,  ItemClassification.progression),
    FezItemData("Well Door Unlocked",           1,  ItemClassification.progression),
    FezItemData("Windmill Door Unlocked",       1,  ItemClassification.progression),
    FezItemData("Mausoleum Door Unlocked",      1,  ItemClassification.progression),
    FezItemData("Sewer QR Door Unlocked",       1,  ItemClassification.progression),
    FezItemData("Sewer Fork Door Unlocked",     1,  ItemClassification.progression),
    FezItemData("Arch Door Unlocked",           1,  ItemClassification.progression),
    FezItemData("Bell Tower Door Unlocked",     1,  ItemClassification.progression),
    FezItemData("Cabin Door Unlocked",          1,  ItemClassification.progression),
    FezItemData("Throne Door Unlocked",         1,  ItemClassification.progression),
    FezItemData("QR Code Map",                  1,  ItemClassification.progression),
    FezItemData("Carry",                        1,  ItemClassification.progression),
    FezItemData("Turn Objects",                 1,  ItemClassification.progression),
]

knowledge_items: List[FezItemData] = [
    FezItemData("Arch Map",             1,  ItemClassification.filler),
    FezItemData("Crypt Map A",          1,  ItemClassification.filler),
    FezItemData("Crypt Map B",          1,  ItemClassification.filler),
    FezItemData("Crypt Map C",          1,  ItemClassification.filler),
    FezItemData("Crypt Map D",          1,  ItemClassification.filler),
    FezItemData("Pivot Map",            1,  ItemClassification.filler),
    FezItemData("Ritual Map",           1,  ItemClassification.filler),
    FezItemData("Tree Sky Map",         1,  ItemClassification.filler),
    FezItemData("Sunglasses",           1,  ItemClassification.filler),
    FezItemData("The Skull Artifact",   1,  ItemClassification.filler),  # Contains code for black monolith
]

skippable_items: List[FezItemData] = [
    FezItemData("The Writing Cube",     1,  ItemClassification.filler),
    FezItemData("The Counting Cube",    1,  ItemClassification.filler),
    FezItemData("The Tome Artifact",    1,  ItemClassification.filler),
    FezItemData("Heart Cube",           3,  ItemClassification.filler),
    FezItemData("Jetpack",              0,  ItemClassification.useful),
]

trap_items: List[FezItemData] = [
    FezItemData("Rotation Trap",    1,  ItemClassification.trap),
    # TODO: Uncomment this once both bugs related to these are fixed
    # FezItemData("Reload Trap",       1,  ItemClassification.trap),
    # FezItemData("Gravity Trap",     1,  ItemClassification.trap),
]

filler_items: List[FezItemData] = [
    FezItemData("Emotional Support",    1,  ItemClassification.filler),
]

main_items = progression_items + knowledge_items + skippable_items
all_item_data = main_items + trap_items + filler_items

item_name_groups = {
    "Progression":  {item.name for item in progression_items},
    "Knowledge":    {item.name for item in knowledge_items},
    "Skippable":    {item.name for item in skippable_items},
    "Trap":         {item.name for item in trap_items},
    "Filler":       {item.name for item in filler_items},
    "Cubes":        {"Golden Cube", "Anti-Cube"},
    "Doors":        {item.name for item in all_item_data if 'Door Unlocked' in item.name},
    "Maps":         {item.name for item in all_item_data if 'Map' in item.name},
    "Abilities":    {"Carry", "Turn Objects"},
}
