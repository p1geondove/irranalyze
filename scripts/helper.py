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

    mag = int(abs(log10(time)-3)//3)
    prefix = " mun"[mag]
    return f"{'-' if neg else ''}{time*10**(3*mag):.1f}{prefix}s"

def timer(func):
    def wrapper(*args, **kwargs):
        start = perf_counter()
        res = func(*args, **kwargs)
        print(f"{func.__name__} took {format_time(perf_counter() - start)}")
        return res
    return wrapper

def get_base(file_path:str|Path) -> str:
    """ return int of base of file """
    file_path = Path(file_path)
    chunk = file_path.open("rb").read(1000)
    name = {10:"dec", 16:"hex"}

    if file_path.suffix == ".txt":
        return name[len(set(chunk.split(b".")[1]))]

    elif file_path.suffix == ".ycd":
        return name[int(chunk.split(b"Base:\t")[1].split(b"\r\n\r\n")[0].decode())]

    else:
        raise NotImplementedError(str(file_path)+" of wrong format, either .txt or .ycd")

def get_const_name(file_path:str|Path) -> str:
    """ maps file contents to constant name """
    file_path = Path(file_path)

    if not file_path.is_file():
        raise FileNotFoundError

    if file_path.suffix == ".txt":
        chunk = file_path.open("rb").read(10).split(b".")[1][:5]

    elif file_path.suffix == ".ycd":
        chunk = file_path.open("rb").read(500).split(b"FirstDigits:\t")[1].split(b"\r\n\r\n")[0]
        chunk = chunk.split(b".")[1][:5]

    else:
        raise NotImplementedError(str(file_path)+" of wrong format, either .txt or .ycd")

    if chunk in CONST_TABLE:
        return CONST_TABLE[chunk]

    return "unknown"

def get_table_name(file_path:str|Path) -> str:
    file_path = Path(file_path)
    return "_".join((get_const_name(file_path), get_base(file_path), file_path.suffix[1:]))

def get_radix(file_path:str|Path) -> tuple[int,int]:
    """ returns int part as well as position of the radix point """
    file_path = Path(file_path)
    chunk = file_path.open("rb").read(500)
    base = 10 if get_base(file_path)=="dec" else 16

    if file_path.suffix == ".txt":
        radix_pos = chunk.find(b".")
        intpart = int(chunk[:radix_pos], base)

    elif file_path.suffix == ".ycd":
        radix_pos = chunk.find(b"EndHeader\r\n\r\n") + 13
        intpart = int(chunk.split(b"FirstDigits:\t")[1].split(b"\r\n\r\n")[0].split(b".")[0], base)

    else:
        raise NotImplementedError(str(file_path)+" of wrong format, either .txt or .ycd")

    return intpart, radix_pos

def check_valid(file_path:str|Path) -> bool:
    """ checks wether a given file is valid bignum format """
    file_path = Path(file_path)

    if not file_path.is_file():
        return False

    with file_path.open("rb") as f:
        chunk = f.read(500)

    if file_path.suffix == ".ycd":
        header_end_idx = chunk.find(b"EndHeader")
        if header_end_idx == -1:
            return False

        header = chunk[:header_end_idx+1]
        if not header[:22] == b"#Compressed Digit File":
            return False

        return all(x in header for x in (b"FileVersion", b"Base", b"FirstDigits", b"TotalDigits", b"Blocksize", b"BlockID"))

    elif file_path.suffix == ".txt":
        has_valid_chars = not bool(set(chunk.split(b".")[1]) - set(b"0123456789abcdef"))
        has_radix = chunk.find(b".") != -1
        return has_valid_chars and has_radix

    return False

