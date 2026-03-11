# __init__.py - init file to scripts module

def sanity():
    from .var import Paths
    from pathlib import Path
    if Paths.num_dir == Path("/path/to/numbers/"):
        print(f"WARN: NUM_DIR ({Paths.num_dir}) is not set up properly, run setup.py")

sanity()

from .bignum import BigNum, get_all, get_one
from .convert import num_to_txt, txt_to_num, txt_to_num_all, alnum_to_num, base_convert
from .var import Sizes, Switches, Paths
