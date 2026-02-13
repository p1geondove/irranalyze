from string import ascii_lowercase
from pathlib import Path
import mpmath

def txt_to_num(txt:str) -> str:
    txt = txt.lower()
    table = {c:f"{p:02d}" for p,c in enumerate(ascii_lowercase)}
    return "".join(table[c] if c.isalpha() else c for c in txt)

def num_to_txt(num:str) -> str:
    if not num.isnumeric():
        raise ValueError("input must be numeric")
    pairs = (int(a+b) for a,b in zip(num[::2], num[1::2]))
    return "".join(chr(p+97) for p in pairs)

def ycd_to_str(file_path:Path, amount_digits:int=1000):
    with file_path.open("rb") as f:
        chunk = f.read(amount_digits + 500) # +500 to account for header (usually ~200bytes)

    if len(chunk) < (amount_digits+500):
        raise OSError("file too small")

    end_header = chunk.find(b"EndHeader")
    if end_header == -1:
        raise OSError("file not ycd format, missing EndHeader")

    data_start = end_header + 14
    intpart = chunk.split(b"FirstDigits:\t")[1].split(b".")[0].decode()
    base = int(chunk.split(b"Base:\t")[1].split(b"\r\n\r\n")[0])
    num = intpart+"."

    if base == 10:
        for startpos in range(data_start, data_start + amount_digits, 8):
            bit = chunk[startpos:startpos + 8]
            num += str(int.from_bytes(bit,"little")).rjust(19,"0")
    elif base == 16:
        for startpos in range(data_start, data_start + amount_digits, 8):
            bit = chunk[startpos:startpos + 8]
            num += format(int.from_bytes(bit, "little"), '016x')
    else:
        raise ValueError(f"unsupported base: {base} {type(base)}")

    return num

def hex_to_dec(in_str:str, amount_digits:int=-1):
    if amount_digits == -1:
        amount_digits = int(19/16*len(in_str))
    mpmath.mp.dps = amount_digits
    radix_pos = in_str.find(".")
    num = mpmath.mpf(in_str[:radix_pos])
    for p,d in enumerate(in_str[radix_pos+1:],1):
        num += int(d,16)*16**(-p)
    return str(num)

