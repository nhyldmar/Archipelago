import functools, dataclasses
from typing import TYPE_CHECKING, Tuple

from typing_extensions import override

from .Items import FezItem
from .Locations import FezLocation
from .Options import KnowledgeLogic, ScrambleTetrominos, EnableJetpack

from BaseClasses import Entrance, ItemClassification, Location, Region, CollectionState
from NetUtils import JSONMessagePart

from rule_builder.rules import CanReachRegion, CanReachEntrance, Has, HasAny, HasAll, Rule, Or, And, Filtered
from rule_builder.field_resolvers import FieldResolver, resolve_field
from rule_builder.options import OptionFilter

if TYPE_CHECKING:
    from . import FezWorld
else:
    FezWorld = object


########################################
# General Rules
########################################

def _get_location(world: FezWorld, name:str) -> Location:
    return world.multiworld.get_location(name, world.player)


def _get_entrance(world: FezWorld, start: str, end: str) -> Entrance:
    return world.multiworld.get_entrance(f"{start} -> {end}", world.player)


def _add_link_door_rule(world: FezWorld, region1: str, region2: str):
    rule = (CanReachRegion(region1) & CanReachRegion(region2))
    world.set_rule(_get_entrance(world, region1, region2), rule)
    world.set_rule(_get_entrance(world, region2, region1), rule)


@dataclasses.dataclass()
class HasCubes(Rule["FezWorld"], game="Fez"):
    count: int | FieldResolver
    """The number of cubes the player is required to have"""

    @override
    def _instantiate(self, world: "FezWorld") -> Rule.Resolved:
        return self.Resolved(
            resolve_field(self.count, world, int),
            player=world.player,
            caching_enabled=getattr(world, "rule_caching_enabled", False),
        )

    @override
    def __str__(self) -> str:
        str_item = "Cubes"
        count = f", count={self.count}" if isinstance(self.count, FieldResolver) or self.count > 1 else ""
        options = f", options={self.options}" if self.options else ""
        return f"{self.__class__.__name__}({str_item}{count}{options})"

    class Resolved(Rule.Resolved):
        count: int

        @override
        def _evaluate(self, state: CollectionState) -> bool:
            return (state.count("Golden Cube", self.player) +
                    state.count("Anti-Cube", self.player) +
                    (state.count("Cube Bit", self.player)//8)
                    >= self.count)

        @override
        def item_dependencies(self) -> [str, list[int]]:
            cube_types = ("Golden Cube", "Anti-Cube", "Cube Bit")
            return {item: {id(self)} for item in cube_types}

        @override
        def explain_json(self, state: CollectionState | None = None) -> list[JSONMessagePart]:
            verb = "Missing " if state and not self(state) else "Has "
            messages: list[JSONMessagePart] = [{"type": "text", "text": verb}]
            if self.count > 1:
                messages.append({"type": "color", "color": "cyan", "text": str(self.count)})
                messages.append({"type": "text", "text": "x "})
            if state:
                color = "green" if self(state) else "salmon"
                messages.append({"type": "color", "color": color, "text": "Cubes"})
            else:
                messages.append({"type": "item_name", "flags": 0b001, "text": "Cubes", "player": self.player})
            return messages

        @override
        def explain_str(self, state: CollectionState | None = None) -> str:
            if state is None:
                return str(self)
            prefix = "Has" if self(state) else "Missing"
            count = f"{self.count}x " if self.count > 1 else ""
            item_name = "Cubes"
            return f"{prefix} {count}{item_name}"

        @override
        def __str__(self) -> str:
            count = f"{self.count}x " if self.count > 1 else ""
            item_name = "Cubes"
            return f"Has {count}{item_name}"


number_rule = CanReachRegion("Oldschool")


alphabet_rule = CanReachRegion("Fox")


tetromino_rule = (CanReachRegion("Code Machine") &
                  CanReachRegion("Nu Zu School", options=[OptionFilter(KnowledgeLogic, True)],
                                 filtered_resolution=True))


scramble_rotate_rule = Filtered(CanReachRegion("Code Machine"),
                                options=[OptionFilter(ScrambleTetrominos, True)],
                                filtered_resolution=True)


first_person_rule = (Has("Sunglasses", options=[OptionFilter(KnowledgeLogic, True)],
                         filtered_resolution=True) &
                     tetromino_rule)


carry_rule = Has("Carry")


pivot_rule = Has("Turn Objects")


water_level_rule = (CanReachRegion("Water Wheel") & pivot_rule)


jetpack_rule = Has("Jetpack", options=[OptionFilter(EnableJetpack, EnableJetpack.option_enabled_with_logic)],
                   filtered_resolution=False)


########################################
# Specific Rules
########################################

def set_rules(world: FezWorld) -> None:
    """Rules that are always present"""
    # Helper functions
    get_entrance = functools.partial(_get_entrance, world)
    get_location = functools.partial(_get_location, world)
    add_link_door_rule = functools.partial(_add_link_door_rule, world)

    # Set ability rules
    set_ability_rules(world)

    # Key doors (requires a specific key to open, unique behaviour to AP)
    world.set_rule(get_entrance("Villageville 3D", "Boileroom"),            Has("Boileroom Door Unlocked"))
    world.set_rule(get_entrance("_LighthouseLower", "Lighthouse House A"),  Has("Lighthouse Door Unlocked"))
    world.set_rule(get_entrance("Tree", "Tree Crumble"),                    Has("Tree Crumble Door Unlocked"))
    world.set_rule(get_entrance("Rails", "Well 2"),                         Has("Well Door Unlocked"))
    world.set_rule(get_entrance("Pivot 1", "Windmill Interior"),            (Has("Windmill Door Unlocked") &
                                                                             Or(pivot_rule, jetpack_rule)))
    world.set_rule(get_entrance("Mausoleum", "Crypt"),                      Has("Mausoleum Door Unlocked"))
    world.set_rule(get_entrance("Sewer Hub", "Sewer QR"),                   (Has("Sewer QR Door Unlocked") &
                                                                             Or(pivot_rule, jetpack_rule)))
    world.set_rule(get_entrance("Sewer Pillars", "Sewer Fork"),             Has("Sewer Fork Door Unlocked"))

    # Custom locked doors to balance sphere sizes
    world.set_rule(get_entrance("Nature Hub", "Arch"),                      Has("Arch Door Unlocked"))
    world.set_rule(get_entrance("Nature Hub", "Bell Tower"),                Has("Bell Tower Door Unlocked"))
    world.set_rule(get_entrance("Tree", "Cabin Interior B"),                Has("Cabin Door Unlocked"))
    world.set_rule(get_entrance("Tree Sky", "Throne"),                      Has("Throne Door Unlocked"))

    # Link doors (requires having been to both ends before being able to use)
    add_link_door_rule("Bell Tower", "Five Towers")
    add_link_door_rule("Industrial Hub", "Well 2")
    add_link_door_rule("Mausoleum", "Tree Roots")
    add_link_door_rule("Memory Core", "Pivot Watertower")
    add_link_door_rule("Nature Hub", "Two Walls")
    add_link_door_rule("Nu Zu Abandoned B", "Sewer to Lava")
    add_link_door_rule("Observatory", "Throne")
    add_link_door_rule("Purple Lodge Ruin", "Visitor")
    add_link_door_rule("Sewer Fork", "Sewer Hub")
    add_link_door_rule("Zu City Ruins", "Zu Library")

    # Cube count doors (requires having a specific number of either golden or anti cubes)
    world.set_rule(get_entrance("Villageville 3D",    "Big Tower"),       HasCubes(1))
    world.set_rule(get_entrance("Big Tower",          "Memory Core"),     HasCubes(2))
    world.set_rule(get_entrance("Memory Core",        "Wall Village"),    HasCubes(4))
    world.set_rule(get_entrance("Memory Core",        "Industrial City"), HasCubes(8))
    world.set_rule(get_entrance("Memory Core",        "Zu City"),         HasCubes(16))
    world.set_rule(get_entrance("Zu City",            "Stargate"),        HasCubes(32))
    world.set_rule(get_entrance("Water Pyramid",      "Temple of Love"),  (water_level_rule &
                                                                           HasCubes(64)))

    # Water level logic (requires lowering the water level)
    world.set_rule(get_entrance("Nature Hub", "Ritual"),              water_level_rule)
    world.set_rule(get_entrance("Waterfall", "Zu Zuish"),             water_level_rule)
    world.set_rule(get_entrance("_LighthouseLower", "Zu Fork"),       water_level_rule)
    world.set_rule(get_entrance("Water Tower", "Watertower Secret"),  water_level_rule)
    world.set_rule(get_entrance("Bell Tower", "Quantum"),             water_level_rule)
    world.set_rule(get_entrance("Water Wheel", "Water Wheel B"),      water_level_rule)

    # Owl logic
    world.set_rule(get_entrance("Owl", "Big Owl"), Has("Owl", count = 4))

    # Watertower secret anti-cube logic for QR Code Map
    world.set_rule(get_entrance("Gomez House", "_WatertowerSecretAntiCube"),
                   (scramble_rotate_rule & Has("QR Code Map")))

    # Exit specific logic
    world.set_rule(get_location("Pivot 3 Cube"), Or(CanReachEntrance("Pivot 3 Cave -> Pivot 3"),
                                                    (CanReachRegion("Pivot 3") & jetpack_rule)))


def set_knowledge_rules(world: FezWorld) -> None:
    """Rules for knowledge logic"""
    # Helper functions
    get_location = functools.partial(_get_location, world)
    get_entrance = functools.partial(_get_entrance, world)

    # Set rules associated with tetromino sequences
    set_tetromino_rules(world)

    # Zu numerals logic
    world.set_rule(get_location("Bell Tower Anti-Cube"), number_rule)

    # Zu alphabet logic
    world.set_rule(get_location("Security Question Heart Cube"), alphabet_rule)

    # Treasure map logic
    world.set_rule(get_location("Arch Chest 2"),           Or(Has("Arch Map"), jetpack_rule))
    world.set_rule(get_location("Tree Sky Chest"),         Or(Has("Tree Sky Map"), jetpack_rule))
    world.set_rule(get_location("Pivot Watertower Chest"), Or(Has("Pivot Map"), jetpack_rule))

    # Crypt map logic
    world.set_rule(get_entrance("Crypt", "Tree of Death"),
                           (HasAll("Crypt Map A", "Crypt Map B",
                                   "Crypt Map C", "Crypt Map D") &
                            number_rule))


def set_tetromino_rules(world: FezWorld):
    """Rules for tetromino codes logic"""
    # Helper functions
    get_location = functools.partial(_get_location, world)
    get_entrance = functools.partial(_get_entrance, world)

    # Tetromino logic
    world.set_rule(get_location("Achievement Anti-Cube"), scramble_rotate_rule)
    world.set_rule(get_location("Parlor Anti-Cube"), scramble_rotate_rule)
    world.set_rule(get_location("Zu Code Loop Anti-Cube"), tetromino_rule)
    world.set_rule(get_location("Code Machine Anti-Cube"), tetromino_rule)
    world.set_rule(get_location("Boileroom Anti-Cube"),
                   (tetromino_rule & Filtered(number_rule,
                                              options=[OptionFilter(KnowledgeLogic, True)],
                                              filtered_resolution=True)))
    world.set_rule(get_location("Nu Zu School Anti-Cube"), tetromino_rule)
    world.set_rule(get_entrance("Waterfall", "CMY"), tetromino_rule)
    world.set_rule(get_entrance("Waterfall", "Water Wheel"), tetromino_rule)

    # Fork tetromino logic
    world.set_rule(get_location("CMY Tune Fork Anti-Cube"), scramble_rotate_rule)
    world.set_rule(get_location("Lava Tune Fork Anti-Cube"), scramble_rotate_rule)
    world.set_rule(get_location("Sewer Tune Fork Anti-Cube"), scramble_rotate_rule)
    world.set_rule(get_location("Zu Tune Fork Anti-Cube"), scramble_rotate_rule)

    # First-person logic
    world.set_rule(get_location("Lighthouse Floor Anti-Cube"), first_person_rule)
    world.set_rule(get_location("Tree Cabin Floor Anti-Cube"), first_person_rule)
    world.set_rule(get_location("Tree Sky Floor Anti-Cube"), first_person_rule)
    world.set_rule(get_location("Zu Bridge Floor Anti-Cube"), first_person_rule)

    # Black monolith logic
    world.set_rule(get_location("Black Monolith Heart Cube"),
                   (tetromino_rule & HasAll("Sunglasses", "Ritual Map", "The Skull Artifact",
                                            options=[OptionFilter(KnowledgeLogic, True)],
                                            filtered_resolution=True)))

    # Throne anti-cube logic
    world.set_rule(get_location("Throne Anti-Cube"),
                   (scramble_rotate_rule &
                    Or(CanReachRegion("Sewer QR"),
                       And(Has("Sunglasses"),
                           CanReachRegion("Code Machine"),
                           CanReachRegion("Zu House Empty"),
                           CanReachRegion("Zu Throne Ruins")),
                       options=[OptionFilter(KnowledgeLogic, True)],
                       filtered_resolution=True)))

    # Watertower Secret Anti-Cube logic for Watertower Secret location
    world.set_rule(get_entrance("Watertower Secret", "_WatertowerSecretAntiCube"),
                   (CanReachRegion("Code Machine") &
                    Has("Sunglasses", options=[OptionFilter(KnowledgeLogic, True)],
                        filtered_resolution=True)))

def set_ability_rules(world: FezWorld):
    """Rules for ability logic"""
    # Helper functions
    get_location = functools.partial(_get_location, world)
    get_entrance = functools.partial(_get_entrance, world)

    # Entrances which require carry
    world.set_rule(get_entrance("Waterfall", "Mine A"), carry_rule)
    world.set_rule(get_entrance("Waterfall", "Zu Code Loop"), carry_rule)
    world.set_rule(get_entrance("Mine A", "Mine Wrap"), carry_rule)
    world.set_rule(get_entrance("Mine Wrap", "Mine Bomb Pillar"), carry_rule)
    world.set_rule(get_entrance("Ancient Walls", "Wall Hole"), Or(carry_rule, jetpack_rule))
    world.set_rule(get_entrance("Zu 4 Side", "Zu Heads"), carry_rule)
    world.set_rule(get_entrance("Arch", "Weightswitch Temple"), carry_rule)
    world.set_rule(get_entrance("Weightswitch Temple", "Zu Switch"), carry_rule)
    world.set_rule(get_entrance("Zu Switch", "Zu Switch B"), carry_rule)
    world.set_rule(get_entrance("Graveyard A", "Graveyard Lesser Gate"), Or(carry_rule, jetpack_rule))

    # Locations which require carry
    world.set_rule(get_location("Mine A Cube Bit"), carry_rule)
    world.set_rule(get_location("Mine Wrap Cube Bit 1"), carry_rule)
    world.set_rule(get_location("Mine Wrap Cube Bit 2"), carry_rule)
    world.set_rule(get_location("Mine Wrap Cube"), Or(carry_rule, jetpack_rule))
    world.set_rule(get_location("Mine Bomb Pillar Cube Bit"), carry_rule)
    world.set_rule(get_location("Mine Bomb Pillar Chest"), Or(carry_rule, jetpack_rule))
    world.set_rule(get_location("Security Question Heart Cube"), carry_rule)
    world.set_rule(get_location("Zu Tetris Anti-Cube"), carry_rule)
    world.set_rule(get_location("Ancient Walls Cube Bit 1"), Or(carry_rule, jetpack_rule))
    world.set_rule(get_location("Ancient Walls Cube Bit 3"), Or(carry_rule, jetpack_rule))
    world.set_rule(get_location("Weightswitch Temple Cube Bit 2"), Or(carry_rule, jetpack_rule))
    world.set_rule(get_location("Graveyard A Cube Bit 3"), Or(carry_rule, jetpack_rule))
    world.set_rule(get_location("Zu Unfold Anti-Cube"), carry_rule)

    # Entrances which require pivot turning
    world.set_rule(get_entrance("Fractal", "Zu 4 Side"), pivot_rule)
    world.set_rule(get_entrance("Water Tower", "Pivot Watertower"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_entrance("Pivot Watertower", "Industrial Hub"),
                   Or(pivot_rule, jetpack_rule, CanReachEntrance("Memory Core -> Pivot Watertower")))
    world.set_rule(get_entrance("Pivot 1", "Pivot 2"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_entrance("Pivot 2", "Pivot 3"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_entrance("Pivot 2", "Extractor A"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_entrance("Pivot 3", "Pivot 3 Cave"), pivot_rule)
    world.set_rule(get_entrance("Industrial Superspin", "Superspin Cave"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_entrance("Triple Pivot Cave", "Spinning Plates"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_entrance("Sewer Start", "Sewer Hub"), pivot_rule)
    world.set_rule(get_entrance("Sewer Hub", "Sewer Treasure 1"), pivot_rule)
    world.set_rule(get_entrance("Sewer Hub", "Sewer to Lava"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_entrance("Sewer to Lava", "Lava"),
                   ((pivot_rule | CanReachEntrance("Nu Zu Abandoned B -> Sewer to Lava")) &
                    Filtered(tetromino_rule,
                             options=[OptionFilter(KnowledgeLogic, True)],
                             filtered_resolution=True) &
                    Filtered(tetromino_rule,
                             options=[OptionFilter(ScrambleTetrominos, True)],
                             filtered_resolution=True)))
    world.set_rule(get_entrance("Lava", "Lava Skull"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_entrance("Sewer Pillars", "Sewer Treasure 2"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_entrance("Sewer Pillars", "Sewer Lesser Gate B"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_entrance("Skull", "Skull B"), pivot_rule)
    world.set_rule(get_entrance("Observatory", "Visitor"),
                   Or(pivot_rule, jetpack_rule, CanReachEntrance("Throne -> Observatory")))
    world.set_rule(get_entrance("Observatory", "Telescope"),
                   Or(pivot_rule, jetpack_rule, CanReachEntrance("Throne -> Observatory")))
    world.set_rule(get_entrance("Visitor", "Orrery"),
                   Or(pivot_rule, jetpack_rule, CanReachEntrance("Purple Lodge Ruin -> Visitor")))
    world.set_rule(get_entrance("Visitor", "Code Machine"),
                   Or(pivot_rule, jetpack_rule, CanReachEntrance("Purple Lodge Ruin -> Visitor")))
    world.set_rule(get_entrance("Library Interior", "Globe"), pivot_rule)
    world.set_rule(get_entrance("Globe", "Globe Interior"), pivot_rule)

    # Locations which require pivot turning
    world.set_rule(get_location("Fractal Cube Bit 1"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_location("Fractal Cube Bit 3"), pivot_rule)
    world.set_rule(get_location("Pivot Watertower Cube Bit"),
                   Or(pivot_rule, jetpack_rule, CanReachEntrance("Memory Core -> Pivot Watertower")))
    world.set_rule(get_location("Pivot Watertower Chest"),
                   Or(pivot_rule, jetpack_rule, CanReachEntrance("Memory Core -> Pivot Watertower")))
    world.set_rule(get_location("Pivot 1 Cube Bit 1"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_location("Pivot 1 Cube Bit 3"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_location("Pivot 1 Owl"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_location("Pivot 2 Cube Bit 1"), pivot_rule)
    world.set_rule(get_location("Pivot 2 Cube Bit 2"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_location("Pivot 2 Cube Bit 3"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_location("Extractor A Cube Bit"), pivot_rule)
    world.set_rule(get_location("Industrial Superspin Cube Bit 3"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_location("Industrial Superspin Chest"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_location("Triple Pivot Cave Cube Bit 1"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_location("Triple Pivot Cave Cube Bit 2"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_location("Spinning Plates Cube Bit"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_location("Spinning Plates Cube"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_location("Sewer Start Cube Bit"), pivot_rule)
    world.set_rule(get_location("Sewer Hub Cube Bit 1"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_location("Sewer Pivot Chest"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_location("Sewer Pillars Cube Bit 1"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_location("Sewer Pillars Cube Bit 2"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_location("Observatory Cube"),
                   Or(pivot_rule, jetpack_rule, CanReachEntrance("Throne -> Observatory")))
    world.set_rule(get_location("Telescope Anti-Cube"),
                   (Filtered(tetromino_rule,
                             options=[OptionFilter(KnowledgeLogic, True)],
                             filtered_resolution=True) &
                    Filtered(tetromino_rule,
                             options=[OptionFilter(ScrambleTetrominos, True)],
                             filtered_resolution=True) &
                    Has("Turn Objects", options=[OptionFilter(KnowledgeLogic, True)],
                        filtered_resolution=True)))
    world.set_rule(get_location("Telescope Heart Cube"),
                   (scramble_rotate_rule & Has("Turn Objects",
                                               options=[OptionFilter(KnowledgeLogic, True)],
                                               filtered_resolution=True)))
    world.set_rule(get_location("Visitor Cube"),
                   Or(pivot_rule, jetpack_rule, CanReachEntrance("Purple Lodge Ruin -> Visitor")))
    world.set_rule(get_location("Visitor Owl"),
                   Or(pivot_rule, jetpack_rule, CanReachEntrance("Purple Lodge Ruin -> Visitor")))
    world.set_rule(get_location("Clock Cube"), Or(pivot_rule, jetpack_rule))
    world.set_rule(get_location("Globe Cube Bit"), pivot_rule)

    # Only set pivot rules for clock tower anti-cubes if they are shuffled
    if world.options.shuffle_clock_antis:
            world.set_rule(get_location("Clock Tower Minute Anti-Cube"), Or(pivot_rule, jetpack_rule))
            world.set_rule(get_location("Clock Tower Hour Anti-Cube"), Or(pivot_rule, jetpack_rule))
            world.set_rule(get_location("Clock Tower Day Anti-Cube"), Or(pivot_rule, jetpack_rule))
            world.set_rule(get_location("Clock Tower Week Anti-Cube"), Or(pivot_rule, jetpack_rule))
