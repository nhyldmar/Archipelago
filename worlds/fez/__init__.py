from typing import Any, Dict
from .Options import FezOptions, fez_option_groups, fez_option_presets
from .Items import FezItem, all_item_data, item_name_groups, filler_items, main_items
from .Locations import FezLocation, all_location_data, location_name_groups
from .Regions import all_region_data, region_name_to_location_name
from .Rules import set_rules, set_knowledge_rules, set_tetromino_rules
from worlds.AutoWorld import WebWorld, World
from BaseClasses import Item, ItemClassification, Region, Tutorial


class FezWeb(WebWorld):
    guide_en = Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up the Fez Archipelago Multiworld",
        "English",
        "setup_en.md",
        "setup/en",
        ["NoliH"]
    )

    tutorials = [guide_en]

    bug_report_page = "https://github.com/nhyldmar/fez-ap/issues"

    options_presets = fez_option_presets
    option_groups = fez_option_groups


class FezWorld(World):
    """
    Gomez is a 2D creature living in a 2D world. Or is he?
    When the existence of a mysterious 3rd dimension is revealed to him,
    Gomez is sent out on a journey that will take him to the very end of time and space.
    Use your ability to navigate 3D structures from 4 distinct classic 2D perspectives.
    """
    game = "Fez"
    web = FezWeb()
    options_dataclass = FezOptions
    options: FezOptions # pyright: ignore[reportIncompatibleVariableOverride]
    topology_present = True  # show path to required location checks in spoiler

    origin_region_name = "Gomez House 2D"

    # First item and location ID
    base_id = 0xFE500

    item_name_to_id = {item.name: id for id, item in enumerate(all_item_data, base_id)}
    item_names = set(item_name_to_id)
    item_name_groups = item_name_groups

    location_name_to_id = {data.name: id for id, data in enumerate(all_location_data, base_id)}
    location_names = set(location_name_to_id)
    location_name_groups = location_name_groups

# start of ordered Main.py calls

    def generate_early(self) -> None:
        # Remove clock antis if not shuffling
        if not self.options.shuffle_clock_antis:
            clockLocationData = [location for location in all_location_data if "Clock Tower" in location.name]
            for location in clockLocationData:
                self.options.exclude_locations.value.add(location.name)
                all_location_data.remove(location)

        # Replace specified number of golden cubes with cube bits
        if self.options.num_cubes_replace_bits > 0:
            bit_idx = [idx for idx, item in enumerate(main_items) if "Cube Bit" in item.name][0]
            cube_idx = [idx for idx, item in enumerate(main_items) if ("Golden Cube" in item.name and item.classification == ItemClassification.progression)][0]
            main_items[bit_idx].count = self.options.num_cubes_replace_bits*8
            main_items[cube_idx].count = 32 - self.options.num_cubes_replace_bits

    def create_regions(self) -> None:
        # Add all regions
        for data in all_region_data:
            region = Region(data.name, self.player, self.multiworld)
            self.multiworld.regions.append(region)

        # Configure all regions
        for data in all_region_data:
            region = self.multiworld.get_region(data.name, self.player)
            location_names = region_name_to_location_name[data.name]
            locations_in_region = {name: self.location_name_to_id.get(name)
                                   for name in location_names
                                   if name in location_names}
            region.add_locations(locations_in_region, FezLocation)
            region.add_exits(data.exits)

    def create_items(self) -> None:
        for item in main_items:
            # If knowledge logic is enabled, maps, sunglasses and skull artifact are all progression
            if self.options.knowledge_logic:
                if item.classification == ItemClassification.deprioritized:
                    item.classification = ItemClassification.progression
            # Add count of item to pool
            for _ in range(item.count):
                new_item = self.create_item(item.name)
                self.multiworld.itempool.append(new_item)
                
            # Add extra golden cubes
            if "Golden Cube" in item.name and self.options.extra_cubes > 0:
                # Only add up to the location limit
                if len(self.location_name_to_id) - sum(item.count for item in main_items) < self.options.extra_cubes:
                    extra_cube_count = len(self.location_name_to_id) - sum(item.count for item in main_items)
                else:
                    extra_cube_count = self.options.extra_cubes

                item_id = self.item_name_to_id[item.name]

                for _ in range(extra_cube_count):
                    new_item = FezItem(item.name, ItemClassification.useful, item_id, self.player)
                    self.multiworld.itempool.append(new_item)
                    

        # Add filler
        fill_size = len(self.location_name_to_id) - sum(item.count for item in main_items)
        self.add_filler_items(fill_size)

    def set_rules(self) -> None:
        set_rules(self)  # Common rules
        if self.options.knowledge_logic:
            set_knowledge_rules(self)
        elif self.options.scramble_tetrominos:
            # If knowledge logic is also set, the knowledge logic already covers scramble logic
            set_tetromino_rules(self, 'scramble')

    def fill_slot_data(self) -> Dict[str, Any]:
        return self.options.as_dict(
            "death_link",
            "goal",
            "scramble_tetrominos",
            "disable_visual_pain"
        )

# end of ordered Main.py calls

    def create_item(self, name: str) -> Item:
        item_id = self.item_name_to_id[name]
        item_data = all_item_data[item_id - self.base_id]
        return FezItem(name, item_data.classification, item_id, self.player)

    def get_filler_item_name(self) -> str:
        return self.random.choice(filler_items).name

    def get_trap_item_name(self) -> str:
        return self.random.choices(list(self.options.trap_weights.keys()), list(self.options.trap_weights.values()))[0]

    def add_filler_items(self, fill_size: int) -> None:
        # Add traps
        trap_count = fill_size * self.options.trap_percentage // 100
        for _ in range(trap_count):
            filler_item = self.create_item(self.get_trap_item_name())
            self.multiworld.itempool.append(filler_item)

        # Add filler
        for _ in range(fill_size - trap_count):
            filler_item = self.create_item(self.get_filler_item_name())
            self.multiworld.itempool.append(filler_item)
