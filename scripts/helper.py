from time import perf_counter
from math import log10
from pathlib import Path

from .const import CONST_TABLE

def format_size(size:int|float, suffix:str="", ndigits:int=2, capitalized:bool=False):
    if size == 0: return "0"+suffix
    prefixes = " kmgtpez"
    index = int(log10(size)/3)
    prefix = prefixes[index].upper() if capitalized else prefixes[index]
    return f"{round(size/10**(index*3), max(0, abs(ndigits))):g}{prefix}{suffix}"

def format_time(time: float):
    if time == 0:
        return "0s"
    if time / 60 / 60 / 24 > 1:
        return f"{int(time/60/60/24)} days"
    elif time / 60 / 60 > 1:
        return f"{int(time/60/60):02d}:{int(time//60)%60:02d} hh:mm"
    elif time / 60 > 1:
        return f"{int(time//60):02d}:{int(time%60):02d} mm:ss"

    neg = False
    if time < 0:
        neg = True
        time = abs(time)

    mag = min(3,int(abs(log10(time)-3)/3))
    return f"{'-' if neg else ''}{time*10**(3*mag):.1f}{' mun'[mag]}s"

def timer(func):
    def wrapper(*args, **kwargs):
        start = perf_counter()
        res = func(*args, **kwargs)
        print(f"{func.__name__} took {format_time(perf_counter() - start)}")
        return res
    return wrapper

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

    else:
        radix_pos = chunk.find(b"EndHeader\r\n\r\n") + 13
        if radix_pos == -1:
            raise ValueError("no EndHeader found")
        else:
            radix_pos += 13
        base = int(chunk.split(b"Base:\t")[1].split(b"\r\n\r\n")[0].decode())
        first_digits = chunk.split(b"FirstDigits:\t")[1].split(b"\r\n\r\n")[0]
        int_part, frac_part = first_digits.split(b".")

    if not base in (10,16):
        raise ValueError("illegal base")

    if base == 16:
        num = 0
        for i,c in enumerate(frac_part[:10],1):
            num += int(chr(c),16)*16**-i
    else:
        num = float(int_part+b"."+frac_part)

    name = CONST_TABLE.get(str(num%1)[2:7], "unknown")

    return name, base, format, int(int_part), radix_pos

def get_table_name(file_path:Path):
    name, base, format, _, _ = identify(file_path)
    return "_".join(map(str, (name,base,format)))

def check_valid(file_path:Path):
    if file_path.suffix not in (".txt", ".ycd"):
        return False
    try:
        identify(file_path)
    except ValueError:
        return False
    else:
        return True
