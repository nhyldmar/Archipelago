from typing import Any, Dict
from .Options import FezOptions, fez_option_groups, fez_option_presets, EnableJetpack
from .Items import FezItem, all_item_data, item_name_groups, filler_items, main_items, knowledge_items, trap_items
from .Locations import FezLocation, all_location_data, location_name_groups
from .Regions import all_region_data, region_name_to_location_name
from .Rules import set_rules, set_knowledge_rules, set_tetromino_rules, HasCubes
from worlds.AutoWorld import WebWorld, World
from BaseClasses import Item, ItemClassification, Region, Tutorial, MultiWorld, Location
import copy
#import logging


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
    item_names = list(item_name_to_id)
    item_name_groups = item_name_groups

    knowledge_names = [knowledge_item.name for knowledge_item in knowledge_items]

    location_name_to_id = {data.name: id for id, data in enumerate(all_location_data, base_id)}
    location_names = list(location_name_to_id)
    location_name_groups = location_name_groups

# start of ordered Main.py calls

    def create_regions(self) -> None:
        # Add all regions
        for data in sorted(all_region_data, key=lambda d: d.name):
            region = Region(data.name, self.player, self.multiworld)
            self.multiworld.regions.append(region)

        # Configure all regions
        for data in sorted(all_region_data, key=lambda d: d.name):
            region = self.multiworld.get_region(data.name, self.player)
            location_names = region_name_to_location_name[data.name]
            locations_in_region = {name: self.location_name_to_id.get(name)
                                   for name in location_names
                                   if (name in location_names and
                                       # If clock anti-cube locations aren't shuffled, remove them
                                       (self.options.shuffle_clock_antis or "Clock Tower" not in name))}
            region.add_locations(locations_in_region, FezLocation)
            region.add_exits(data.exits)

        # Create goal event locations
        self.create_completion_events()

    def create_items(self) -> None:
        main_items_player = copy.deepcopy(main_items)

        # Replace specified number of golden cubes with cube bits
        if self.options.num_cubes_replace_bits > 0:
            bit_idx = [idx for idx, item in enumerate(main_items_player) if "Cube Bit" in item.name][0]
            cube_idx = [idx for idx, item in enumerate(main_items_player) if ("Golden Cube" in item.name and item.classification == ItemClassification.progression)][0]
            main_items_player[bit_idx].count = self.options.num_cubes_replace_bits*8
            main_items_player[cube_idx].count = 32 - self.options.num_cubes_replace_bits

        # If knowledge logic is enabled, maps, sunglasses and skull artifact are all progression
        if self.options.knowledge_logic:
            for idx in range(len(main_items_player)):
                if main_items_player[idx].name in self.knowledge_names:
                    main_items_player[idx].classification = ItemClassification.progression

        # If abilities not randomized, make abilities count zero
        if not self.options.randomize_abilities:
            ability_idx = [idx for idx, item in enumerate(main_items_player)
                           if (item.name == "Carry" or item.name == "Turn Objects")]
            for idx in ability_idx:
                main_items_player[idx].count = 0

        # Add in a jetpack if the option is enabled
        if self.options.enable_jetpack != EnableJetpack.option_disabled:
            jetpack_idx = [idx for idx, item in enumerate(main_items_player) if "Jetpack" in item.name][0]
            main_items_player[jetpack_idx].count = 1
            if self.options.enable_jetpack == EnableJetpack.option_enabled_with_logic:
                main_items_player[jetpack_idx].classification = ItemClassification.progression

        # Account for removed clock anti locations if not shuffling
        clock_tower_filler_cnt = 0
        if not self.options.shuffle_clock_antis:
            clockLocationData = [location for location in all_location_data if "Clock Tower" in location.name]
            clock_tower_filler_cnt = len(clockLocationData)

        spare_cnt = len(self.location_name_to_id) - sum(item.count for item in main_items_player) - clock_tower_filler_cnt
        skippable_cnt = sum(item.count for item in main_items_player if item.classification == ItemClassification.filler)

        if spare_cnt < 0:
            # If there are more items than locations, first add base game filler items to starting inventory
            skippable_cnt = min(skippable_cnt, abs(spare_cnt))

            #logging.info(self.multiworld.player_name[self.player] + " | More items than locations, placing " + str(skippable_cnt) + " filler items in starting inventory")
            skippable_idx = [idx for idx, item in enumerate(main_items_player) if (item.classification == ItemClassification.filler and item.count > 0)]
            for _ in range(skippable_cnt):
                item_idx = self.random.randint(0, len(skippable_idx)-1)
                new_item = self.create_item(main_items_player[skippable_idx[item_idx]].name)
                self.push_precollected(new_item)
                main_items_player[skippable_idx[item_idx]].count -= 1
                spare_cnt += 1
                if main_items_player[skippable_idx[item_idx]].count <= 0:
                    skippable_idx.pop(item_idx)

            # If there are still more items than locations after adding all base game filler items to starting inventory, use progression items to fill the remaining difference
            if spare_cnt < 0:
                #logging.info(self.multiworld.player_name[self.player] + " | Still more items than locations after all base game filler items given, placing " + str(abs(spare_cnt)) + " progression items in starting inventory")
                progression_idx = [idx for idx, item in enumerate(main_items_player) if (item.classification == ItemClassification.progression and item.count > 0)]
                for _ in range(abs(spare_cnt)):
                    item_idx = self.random.randint(0, len(progression_idx)-1)
                    new_item = self.create_item(main_items_player[progression_idx[item_idx]].name)
                    self.push_precollected(new_item)
                    main_items_player[progression_idx[item_idx]].count -= 1
                    if main_items_player[progression_idx[item_idx]].count <= 0:
                        progression_idx.pop(item_idx)

        extra_cube_count = 0

        # Ensure there are enough items moved to the starting inventory such that there are enough filler items (base game or generated) to match excluded locations
        skippable_cnt = sum(item.count for item in main_items_player if item.classification == ItemClassification.filler)
        num_exclude_unaccounted = len(self.options.exclude_locations.value) - skippable_cnt
        if (num_exclude_unaccounted > 0):
            #logging.info(self.multiworld.player_name[self.player] + " | Placing an additional " + str(num_exclude_unaccounted) + " progression items in starting inventory to ensure enough filler items exist for excluded locations")
            progression_idx = [idx for idx, item in enumerate(main_items_player) if (item.classification == ItemClassification.progression and item.count > 0)]
            for _ in range(num_exclude_unaccounted):
                item_idx = self.random.randint(0, len(progression_idx)-1)
                new_item = self.create_item(main_items_player[progression_idx[item_idx]].name)
                self.push_precollected(new_item)
                main_items_player[progression_idx[item_idx]].count -= 1
                if main_items_player[progression_idx[item_idx]].count <= 0:
                    progression_idx.pop(item_idx)

        else:
            # If there are enough filler items to match excluded locations, add up to the location limit for extra golden cubes
            remaining_empty_loc = len(self.location_name_to_id) - sum(item.count for item in main_items_player) - clock_tower_filler_cnt
            if remaining_empty_loc < self.options.extra_cubes:
                #logging.info(self.multiworld.player_name[self.player] + " | Not enough remaining locations to place specified extra Golden Cubes, can only add " + str(remaining_empty_loc) + " extra cubes")
                extra_cube_count = remaining_empty_loc
            elif remaining_empty_loc > 0:
                extra_cube_count = self.options.extra_cubes

        for item in main_items_player:
            # Add count of item to pool
            for _ in range(item.count):
                new_item = self.create_item(item.name)
                self.multiworld.itempool.append(new_item)

            # If abilities not randomized, add abilities to starting inventory
            if not self.options.randomize_abilities and (item.name == "Carry" or item.name == "Turn Objects"):
                ability_item = self.create_item(item.name)
                self.push_precollected(ability_item)

            # Add extra golden cubes
            if "Golden Cube" in item.name and extra_cube_count > 0:
                item_id = self.item_name_to_id[item.name]

                for _ in range(extra_cube_count):
                    new_item = FezItem(item.name, ItemClassification.useful, item_id, self.player)
                    self.multiworld.itempool.append(new_item)

        # Add filler
        fill_size = len(self.location_name_to_id) - sum(item.count for item in main_items_player) - extra_cube_count - clock_tower_filler_cnt
        self.add_filler_items(fill_size)

    def set_rules(self) -> None:
        set_rules(self)  # Common rules
        if self.options.knowledge_logic:
            set_knowledge_rules(self)
        elif self.options.scramble_tetrominos:
            # If knowledge logic is also set, the knowledge logic already covers scramble logic
            set_tetromino_rules(self)

    def fill_slot_data(self) -> Dict[str, Any]:
        return self.options.as_dict(
            "death_link",
            "goal",
            "shuffle_clock_antis",
            "knowledge_logic",
            "scramble_tetrominos",
            "disable_visual_pain",
            "num_cubes_replace_bits",
            "extra_cubes",
            "randomize_abilities"
        )

# end of ordered Main.py calls

    def create_item(self, name: str) -> Item:
        item_id = self.item_name_to_id[name]
        item_data = all_item_data[item_id - self.base_id]
        if self.options.knowledge_logic and name in self.knowledge_names:
            return FezItem(name, ItemClassification.progression, item_id, self.player)
        # Cubes should be deprioritized for minimal accessibility only since they are sorted first for placement under that option
        if self.options.accessibility == "minimal" and (name == "Golden Cube" or name == "Anti-Cube"):
            return FezItem(name, ItemClassification.progression_deprioritized_skip_balancing, item_id, self.player)
        return FezItem(name, item_data.classification, item_id, self.player)

    def get_filler_item_name(self) -> str:
        return self.random.choice(filler_items).name

    def get_trap_item_name(self) -> str:
        if (len(list(self.options.trap_weights.keys())) == 0 or sum(list(self.options.trap_weights.values())) <= 0.0):
            return (self.random.choices(trap_items)[0]).name
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

    def create_completion_events(self) -> None:
        """Set completion condition based on goal option"""
        victory_region = self.multiworld.get_region("Hex Rebuild", self.player)
        victory_loc = FezLocation(self.player, "Hex Rebuild", None, victory_region)
        victory_loc.place_locked_item(FezItem("Victory", ItemClassification.progression, None, self.player))
        self.multiworld.completion_condition[self.player] = lambda state: state.has("Victory", self.player)
        self.set_rule(victory_loc, HasCubes(self.options.goal.value))
        victory_region.locations.append(victory_loc)

    @classmethod
    def stage_fill_hook(cls,
                        multiworld: MultiWorld,
                        progitempool: list[Item],
                        usefulitempool: list[Item],
                        filleritempool: list[Item],
                        fill_locations: list[Location],
                        ) -> None:
        players = multiworld.get_game_players(cls.game)
        minimal_player_ids = {player for player in players
                              if multiworld.worlds[player].options.accessibility == "minimal"}

        def sort_func(item: Item):
            if item.name == "Golden Cube" or item.name == "Anti-Cube":
                if item.player in minimal_player_ids:
                    # Place cubes first for minimal accessibility players
                    # to reduce generation failure
                    return 1
                else:
                    return 0
            else:
                return 0

        progitempool.sort(key=sort_func)
