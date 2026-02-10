import os
from pathlib import Path

NUM_DIR = Path("/home/p1geon/bignum/")
CHUNK_SIZE = 8*2**20 # 8mib
FIRST_DIGITS_AMOUNT = 10_000_000
PAGE_SIZE = os.sysconf('SC_PAGE_SIZE')
SQLITE_PATH = Path("irranalyze.sqlite")
CONST_TABLE = {
    b"41421":"sqrt2",
    b"73205":"sqrt3",
    b"23606":"sqrt5",
    b"16227":"sqrt10",
    b"61803":"phi",
    b"71828":"e",
    b"14159":"pi",
    b"69314":"ln2",
    b"09861":"ln3",
    b"38629":"ln4",
    b"60943":"ln5",
    b"30258":"ln10",
    b"24411":"lemniscate",
    b"20205":"zeta3",
    b"62560":"gamma1/4",
    b"91596":"catalan",
    b"57721":"gamma",

    b"6a09e":"sqrt2",
    b"bb67a":"sqrt3",
    b"3c6ef":"sqrt5",
    b"298b0":"sqrt10",
    b"9e377":"phi",
    b"b7e15":"e",
    b"243f6":"pi",
    b"b1721":"ln2",
    b"193ea":"ln3",
    b"62e42":"ln4",
    b"9c041":"ln5",
    b"4d763":"ln10",
    b"3e7e5":"lemniscate",
    b"33ba0":"zeta3",
    b"a027f":"gamma1/4",
    b"ea7cb":"catalan",
    b"93c46":"gamma",
}

CONST_TABLE_2 = {
    "catalan"   :(b"91596",b"ea7cb"),
    "e"         :(b"71828",b"b7e15"),
    "gamma"     :(b"57721",b"93c46"),
    "gamma1/4"  :(b"62560",b"a027f"),
    "lemniscate":(b"24411",b"3e7e5"),
    "ln2"       :(b"69314",b"b1721"),
    "ln3"       :(b"09861",b"193ea"),
    "ln4"       :(b"38629",b"62e42"),
    "ln5"       :(b"60943",b"9c041"),
    "ln10"      :(b"30258",b"4d763"),
    "phi"       :(b"61803",b"9e377"),
    "pi"        :(b"14159",b"243f6"),
    "sqrt2"     :(b"41421",b"6a09e"),
    "sqrt3"     :(b"73205",b"bb67a"),
    "sqrt5"     :(b"23606",b"3c6ef"),
    "sqrt10"    :(b"16227",b"298b0"),
    "zeta3"     :(b"20205",b"33ba0"),
}
