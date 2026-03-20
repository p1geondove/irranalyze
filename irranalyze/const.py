# const.py - various variables that should stay constant

import os
from pathlib import Path

SETTINGS_PATH = Path("settings.json")
PAGE_SIZE = os.sysconf('SC_PAGE_SIZE')
IDENTIFY_TABLE_NAME = "identify"
PAIRS_PER_INSERT = 100000
CONST_TABLE = {
    "1.41421":"sqrt(2)",
    "1.61803":"phi",
    "2.71828":"e",
    "3.14159":"pi",
    "5.24411":"lemniscate",
    "0.69314":"ln(2)",
    "1.20205":"apery's constant",
    "0.91596":"catalan",
    "0.57721":"euler mascheroni",
}
