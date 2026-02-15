import sqlite3
from pathlib import Path
from hashlib import md5

from .const import CONST_TABLE, SQLITE_PATH, IDENTIFY_TABLE_NAME
from .convert import ycd_to_str, hex_to_dec

def identify(file_path:Path) -> tuple[str,int,str,int,int]:
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
    with file_path.open("rb") as f:
        chunk = f.read(1000)

    format = "ycd" if b"#Compressed Digit File" in chunk else "txt"

    if format == "txt":
        radix_pos = chunk.find(b".")
        if radix_pos == -1:
            raise ValueError("no radix point found")
        int_part = chunk[:radix_pos]
        frac_part = chunk[radix_pos+1:]
        base = len(set(frac_part))
        num = chunk.decode()
    else:
        radix_pos = chunk.find(b"EndHeader\r\n\r\n")
        if radix_pos == -1:
            raise ValueError("no EndHeader found")
        else:
            radix_pos += 13 # 13 = EndHeader\r\n\r\n
        base = int(chunk.split(b"Base:\t")[1].split(b"\r\n\r\n")[0].decode())
        num = ycd_to_str(file_path,200)
        first_digits = chunk.split(b"FirstDigits:\t")[1].split(b"\r\n\r\n")[0]
        int_part, _ = first_digits.split(b".")

    # y-cruncher only outputs hex and dec
    if not base in (10,16):
        raise ValueError("illegal base")

    # always convert to decimal, since identify table only hosts hashes to decimal expansion
    if base == 16:
        num = hex_to_dec(num)

    # check if db exists
    if SQLITE_PATH.exists():
        conn = sqlite3.connect(SQLITE_PATH)
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

    return name, base, format, int(int_part), radix_pos

def get_table_name(file_path:Path) -> str|None:
    """ helper function that calls identify and returns the table name if constant name is known """
    name, base, format, _, _ = identify(file_path)
    if name == "unknown":
        return
    return "_".join(map(str, (name,base,format)))

def check_valid(file_path:Path) -> bool:
    """ check wether a given file is a usable number file """
    if file_path.suffix not in (".txt", ".ycd"):
        return False
    with file_path.open("rb") as f:
        chunk = f.read(1000)

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
