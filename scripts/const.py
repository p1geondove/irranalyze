import os
from pathlib import Path

NUM_DIR = Path("/home/p1geon/bignum/")
CHUNK_SIZE = 8*2**20
FIRST_DIGITS_AMOUNT = 1_000_000
PAGE_SIZE = os.sysconf('SC_PAGE_SIZE')
SQLITE_PATH = Path("irranalyze.sqlite")
IDENTIFY_TABLE_NAME = "identify"
CONST_TABLE = {
    "41421":"sqrt2",
    "73205":"sqrt3",
    "23606":"sqrt5",
    "16227":"sqrt10",
    "61803":"phi",
    "71828":"e",
    "14159":"pi",
    "69314":"ln2",
    "09861":"ln3",
    "38629":"ln4",
    "60943":"ln5",
    "30258":"ln10",
    "24411":"lemniscate",
    "20205":"zeta3",
    "62560":"gamma1/4",
    "91596":"catalan",
    "57721":"gamma",
}

