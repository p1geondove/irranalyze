import os
import json
from pathlib import Path

SETTINGS_PATH = Path("settings.json")
settings = json.load(SETTINGS_PATH.open())
NUM_DIR = Path(settings["NUM_DIR"])
SQLITE_PATH = Path(settings["SQLITE_PATH"])
NUMS_PER_INSERT = int(settings["NUMS_PER_INSERT"])
CHUNK_SIZE = 8*2**20
FIRST_DIGITS_AMOUNT = 1_000_000
PAGE_SIZE = os.sysconf('SC_PAGE_SIZE')
IDENTIFY_TABLE_NAME = "identify"
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
