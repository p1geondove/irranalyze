import sqlite3
from pathlib import Path
from hashlib import md5

from .const import SQLITE_PATH, IDENTIFY_TABLE_NAME
from .convert import ycd_to_str, hex_to_dec

def identify(file_path:Path) -> tuple[str,int,str,int,int]:
    """ 
    unified identify method for number files, raises ValueError if illegal file
    returns:
        name      :str (pi,e...)
        base      :int (10,16)
        format    :str (txt,ycd)
        int_part  :int (3,0...)
        radix_pos :int (1,196...)
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
        radix_pos = chunk.find(b"EndHeader\r\n\r\n") + 13
        if radix_pos == -1:
            raise ValueError("no EndHeader found")
        else:
            radix_pos += 13
        base = int(chunk.split(b"Base:\t")[1].split(b"\r\n\r\n")[0].decode())
        num = ycd_to_str(file_path,200)
        first_digits = chunk.split(b"FirstDigits:\t")[1].split(b"\r\n\r\n")[0]
        int_part, _ = first_digits.split(b".")

    if not base in (10,16):
        raise ValueError("illegal base")

    if base == 16:
        num = hex_to_dec(num)

    blob = md5(num[:100].encode()).digest()
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    table_exists = bool(cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (IDENTIFY_TABLE_NAME, )).fetchone())

    if not table_exists:
        raise OSError("identify table missing")

    cursor.execute(f"SELECT name FROM {IDENTIFY_TABLE_NAME} WHERE hash = ?", (blob,))
    if name:=cursor.fetchone():
        name = name[0]
    else:
        name = "unknown"
    #print(f"inside identify: {file_path=} {name=}")

    return name, base, format, int(int_part), radix_pos

def get_table_name(file_path:Path):
    name, base, format, _, _ = identify(file_path)
    return "_".join(map(str, (name,base,format)))

def check_valid(file_path:Path):
    if file_path.suffix not in (".txt", ".ycd"):
        return False

    chunk = file_path.open("rb").read(1000)

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

