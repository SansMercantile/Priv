# backend/support_ai/indicators/elliott_wave/defines.py

from enum import Enum

# --- Wave Labeling and Interaction Constants ---
# These correspond to keyboard shortcuts in the original MQL application
class EW_KEYS(Enum):
    PREV_LEVEL = 'Q'
    NEXT_LEVEL = 'W'
    DOWN_LEVEL = 'A'
    UP_LEVEL = 'S'
    START_MARKING = 'Z'
    STOP_MARKING = 'X'
    SELECT_GROUP = 0x09  # Tab
    HIDE_PANEL = 0x1B    # Esc
    INCREASE_LEVEL = 'E'
    REDUCE_LEVEL = 'R'
    DELETE_OBJECT = 0x2E # Del
    SELECT = 0x10        # Shift
    START_ANALYSIS_LEFT = '1'
    START_ANALYSIS_RIGHT = '2'
    CONVERT = 'V'
    CLEAR = 'C'

# --- Naming and Identification Constants ---
SEPARATOR = "_"
NAME_LABEL = "$L$"
NAME_WAVE = "$W$"
NAME_AUTO_WAVE = "$A$"

# --- Analysis Type Constants ---
class EW_ANALYSIS_TYPE(Enum):
    COMPLETED_WAVES = 1
    UNBEGUN_WAVES = 2
    UNFINISHED_WAVES = 3
    FULL_ANALYSIS = 4

# --- Trend Direction Constants ---
class EW_TREND(Enum):
    UP = "Up"
    DOWN = "Down"
    UNDEFINED = "Undefined"

# --- Rule Evaluation Constants ---
class EW_RULE_MOD(Enum):
    MIN = "min"
    MAX = "max"
    VALUE = "val"

class EW_RELATION_TYPE(Enum):
    LENGTH = "length"
    TIME = "time"

# --- File and Message Constants ---
NAME_RULES_FILE = "EWM.txt"
MSG_FILE_OPEN_ERROR = "The EWM.txt file open error!"
MSG_ANALYSIS_COMPLETED = "An analysis is complete!"

# --- Wave Labels ---
# Represents the standard labels for different wave degrees
ETALON_LABELS = ["1", "2", "3", "4", "5", "A", "B", "C", "D", "E", "W", "X", "Y", "XX", "Z"]

# --- Data Structure for Wave Level Descriptions ---
# This will be populated by parsing the EWM.txt file
class WaveLevelDescription:
    def __init__(self):
        self.level_name: str = ""
        self.num_level: int = 0
        self.labels: list[str] = []
        self.font: str = ""
        self.font_size: int = 0
        self.color: tuple[int, int, int] = (0, 0, 0)
