from dataclasses import dataclass
from typing import Any, Dict

from Options import Choice, DeathLinkMixin, OptionCounter, OptionGroup, PerGameCommonOptions, Range, Toggle
from .Items import trap_items


class Goal(Range):
    """Defines the goal to accomplish in order to complete the randomizer.

    How many cubes are required to beat the randomizer. You must reach the end of the game with at least this many cubes collected.
    """
    display_name = "Goal"
    range_start = 32
    range_end = 64
    default = 32

class NumberCubesReplacedByBits(Range):
    """Replaces a certain number of golden cubes with an equivalent number of bits.

    1 Golden Cube = 8 Cube Bits

    NOTE: Near the upper limit of this option, items (filler, then progression) will be automatically placed in the starting inventory to account for fewer locations than items.
    """
    display_name = "Cube Bits Replacement"
    range_start = 0
    range_end = 16
    default = 0

class NumberExtraGoldenCubes(Range):
    """Adds extra golden cubes to allow for easier goal completion.

    Will only place up to the number of available locations.
    """
    display_name = "Extra Golden Cubes"
    range_start = 0
    range_end = 32
    default = 0

class DisableVisualPain(Toggle):
    """Disables effects that are make eyes not happy like (quantum room and lightning)

    NOTE: For the lightning levels, the invisible triles remain invisible due to a bug that crashes the game if rendering them.
          Hopefully this will be fixed for a future release.
    """
    display_name = "Disable Visual Pain"

class ShuffleClockAntis(Toggle):
    """Whether to add the anti-cubes from the clock tower to the location pool ('true' means you'll likely need to change system time or wait upto a month)."""
    display_name = "Shuffle Clock Antis"

class ScrambleTetrominos(Toggle):
    """Whether to randomly scramble the inputs for the Tetromino codes ('true' means for example that the ▀█▄ tetromino will require you to jump instead of LT)."""
    display_name = "Scramble Tetrominos Inputs"

class KnowledgeLogic(Toggle):
    """Whether to have knowledge sources required for logic (e.g. Counting Cube needed before Bell Tower Anti-Cube)"""
    display_name = "Knowledge Logic"

class TrapPercentage(Range):
    """Replaces filler items with traps, at the specified rate."""
    display_name = "Trap Percentage"
    range_start = 0
    range_end = 100
    default = 50

class TrapWeights(OptionCounter):
    """Specify the weights determining how many of each trap item will be in your itempool.

    If you don't want a specific type of trap, you can set the weight for it to 0.
    """
    display_name = "Trap Weights"
    min = 0
    valid_keys = [trap.name for trap in trap_items]
    default = {
        "Rotation Trap": 1,
        # TODO: Uncomment this once both bugs related to these are fixed
        # "Reload Trap": 1,
        # "Gravity Trap": 1,
    }

class EnableJetpack(Toggle):
    """Puts the Jetpack in the useful item pool."""
    display_name = "Enable Jetpack"


@dataclass
class FezOptions(DeathLinkMixin, PerGameCommonOptions):
    goal: Goal
    num_cubes_replace_bits: NumberCubesReplacedByBits
    extra_cubes: NumberExtraGoldenCubes
    disable_visual_pain: DisableVisualPain
    shuffle_clock_antis: ShuffleClockAntis
    scramble_tetrominos: ScrambleTetrominos
    knowledge_logic: KnowledgeLogic
    trap_percentage: TrapPercentage
    trap_weights: TrapWeights
    enable_jetpack: EnableJetpack


fez_option_groups = [
    OptionGroup("Goal and Logic", [
        Goal,
        NumberCubesReplacedByBits,
        NumberExtraGoldenCubes,
        ShuffleClockAntis,
        KnowledgeLogic,
    ]),
    OptionGroup("Filler Items", [
        TrapPercentage,
        TrapWeights
    ]),
    OptionGroup("Misc", [
        ScrambleTetrominos,
        DisableVisualPain,
        EnableJetpack,
    ]),
]


fez_option_presets: Dict[str, Dict[str, Any]] = {
    "Sync": {
        "goal": 32,
        "shuffle_clock_antis": False,
    },
    "Async": {
        "goal": 64,
        "shuffle_clock_antis": False,
    },
    "Awful": {
        "goal": 64,
        "shuffle_clock_antis": True,
        "scramble_tetrominos": True,
        "trap_percentage": 100,
        "death_link": True,
    },
}
