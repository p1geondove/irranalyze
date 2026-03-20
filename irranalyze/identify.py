# identify.py - used for identifying number files

import sqlite3
from pathlib import Path
from hashlib import md5
from dataclasses import dataclass
from math import log

from .const import CONST_TABLE, IDENTIFY_TABLE_NAME
from .var import Paths
from .convert import hex_to_dec, ycd_to_str_gen

@dataclass
class BigNumInfo:
    path:Path # the path to the file
    name:str # the name of the constant, like "pi", "e" etc
    base:int # base of the constant, should either be 10 or 16 since y-crucnher does only that
    format:str # format of the file, can only be "txt" or "ycd"
    int_part:int # the integer part saved as int
    radix_pos:int # position of the radix pos inside the file
    file_size:int # actual filesize
    decimal_digits:int # the amount of decimal digits in the file, no matter if file is dec or hex
    table_name:str # the table name for the constant

def identify(file_path:Path) -> BigNumInfo:
    """
    unified identify method for number files, raises ValueError if illegal file

    :param file_path: path to file
    :type file_path: Path
    :rtype: tuple[str, int, str, int, int]
    :return:
    1. name      (pi,e...)
    2. base      (10,16)
    3. format    (txt,ycd)
    4. int_part  (3,0...)
    5. radix_pos (1,196...)
    """
    file_size = file_path.stat().st_size

    with file_path.open("rb") as f:
        chunk = f.read(500)

    format = "ycd" if b"#Compressed Digit File" in chunk else "txt"

    if format == "txt":
        radix_pos = chunk.find(b".")
        if radix_pos == -1:
            raise ValueError("no radix point found")
        frac_part = chunk[radix_pos+1:]
        base = len(set(frac_part)) # base is determinde by the ammount of different chars after radix, so only estimate, but worst case is 16 different chars in ~500 chars
        int_part = int(chunk[:radix_pos],base)
        num = chunk.decode()
        decimal_digits = file_size - radix_pos
    else:
        radix_pos = chunk.find(b"EndHeader\r\n\r\n")
        if radix_pos == -1:
            raise ValueError("no EndHeader found")
        else:
            radix_pos += 13 # 13 = EndHeader\r\n\r\n
        base = int(chunk.split(b"Base:\t")[1].split(b"\r\n\r\n")[0].decode())
        first_digits = chunk.split(b"FirstDigits:\t")[1].split(b"\r\n\r\n")[0]
        int_part = int(first_digits.split(b".")[0],base)
        frac_part = "".join(ycd_to_str_gen(memoryview(chunk)[radix_pos+1:], base))
        num = f"{int_part}.{frac_part}"
        decimal_digits = int(chunk.split(b"Blocksize:\t")[1].split(b"\r\n")[0])

    # y-cruncher only outputs hex and dec
    if base!=10 and base!=16:
        raise ValueError("illegal base")

    if base == 16:
        decimal_digits = int(log(16,10) * decimal_digits)
        num = hex_to_dec(num)

    # check if db exists
    if Paths.sqlite_path.exists():
        conn = sqlite3.connect(Paths.sqlite_path)
        cursor = conn.cursor()
        table_exists = bool(cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (IDENTIFY_TABLE_NAME, )).fetchone())
        # check if identify table exists 
        if table_exists:
            blob = md5(num[:100].encode()).digest()
            cursor.execute(f"SELECT name FROM {IDENTIFY_TABLE_NAME} WHERE hash = ?", (blob,))
            name = cursor.fetchone()
            if name:
                name = str(name[0])
            else:
                name = "unknown"
        else:
            print("WARN: identify table not created yet, using fallback")
            name = CONST_TABLE.get(num[:7],"unknown")
        conn.close()
    else:
        print("WARN: identify table not created yet, using fallback")
        name = CONST_TABLE.get(num[:7],"unknown")

    table_name = "_".join(map(str,(name,base,format)))

    return BigNumInfo(file_path,name,base,format,int(int_part),radix_pos,file_size,decimal_digits,table_name)

def get_table_name(file_path:Path) -> str|None:
    """ helper function that calls identify and returns the table name if constant name is known """
    info = identify(file_path)
    if info.name == "unknown":
        return
    return "_".join(map(str, (info.name,info.base,info.format)))

def check_valid(file_path:Path) -> bool:
    """ check wether a given file is a usable number file """
    if file_path.suffix not in (".txt", ".ycd"):
        return False
    with file_path.open("rb") as f:
        chunk = f.read(500)

    if file_path.suffix == ".ycd":
        header = all(p in chunk for p in (b"#Compressed Digit File", b"Base", b"FirstDigits", b"EndHeader"))
        if not header: return False
        start_data = chunk.find(b"EndHeader")+14
        if len(chunk)<start_data: return False

    if file_path.suffix == ".txt":
        if chunk.count(b".") != 1: return False
        digits = set(chunk)-set(b".")
        if len(digits) not in (10,16): return False

    return True
