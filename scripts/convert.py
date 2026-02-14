from string import ascii_lowercase
from pathlib import Path

import mpmath
import gmpy2

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
    intpart = chunk.split(b"FirstDigits:\t")[1].split(b".")[0]
    base = int(chunk.split(b"Base:\t")[1].split(b"\r\n\r\n")[0])

    if base == 10:
        num = intpart.decode()+"."
        for startpos in range(data_start, data_start + amount_digits, 8):
            bit = chunk[startpos:startpos + 8]
            num += str(int.from_bytes(bit,"little")).rjust(19,"0")
    elif base == 16:
        num = str(int(intpart,16))+"."
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

def base_convert(dec_str:str, base:int|str|list[str]|None = None, digits:int|None = None):
    base_chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"

    if isinstance(base, str): # determine base notation
        if base == "abc":
            base_chars = "abcdefghijklmnopqrstuvwxyz"
        elif base == "ABC":
            base_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        elif base == "alnum":
            base_chars = "01234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        else:
            base_chars = base # custom charset
    elif isinstance(base, int):
        if base == -1 or base is None:
            base = len(base_chars)
        elif not (_base := min(max(2, base), len(base_chars))) == base:
            print(f"warn: clamped base from {base} to {_base}")
            base = _base
        base_chars = base_chars[:base]
    if isinstance(base, list):
        if not all(isinstance(e,str) for e in base):
            ValueError("base must be either int, string or list[str]")
        base_chars = base
    else:
        ValueError("base must be either int, string or list[str]")

    base = len(base_chars)

    radix_pos = dec_str.find(".")
    if radix_pos == -1:
        raise ValueError("input has no decimal point")
    if not (set(dec_str)-set(".")).issubset(set("0123456789")):
        raise ValueError(f"input string must be decimal, {set(dec_str)-set('.')}")

    if digits is None:
        digits = len(dec_str) - radix_pos

    if base == 10:
        return dec_str[:digits] if digits else dec_str

    digits = max(2,int(abs(digits))) # in case digits is negative or float
    input_amt_needed = max(1,int(digits*mpmath.log10(base))) # decimal digits needed to represent number in output base
    if input_amt_needed > (len(dec_str)-radix_pos-1):
        print("WARN: not enough data for accurate base conversion to specified size")
        frac_part = dec_str[radix_pos+1:].ljust(input_amt_needed,"0")
    else:
        frac_part = dec_str[radix_pos+1 : radix_pos+1+input_amt_needed]
    frac_part = gmpy2.mpz(frac_part) #holy fuck my linter is telling me there is no mpz in gmpy2, stfu...
    denominator = gmpy2.mpz("1"+"0"*input_amt_needed)
    mpz_base = gmpy2.mpz(base)
    int_part = "".join(map(
        lambda i: base_chars[i],
        numberToBase(int(dec_str[:radix_pos]), base),
    ))

    result_digits = []
    for _ in range(digits):
        frac_part *= mpz_base
        digit = frac_part // denominator
        frac_part %= denominator
        result_digits.append(base_chars[int(digit)])
        if frac_part == 0:
            break
    return (int_part + "." + "".join(result_digits))[:digits]

def numberToBase(n, b):
    # https://stackoverflow.com/questions/2267362/how-to-convert-an-integer-to-a-string-in-any-base
    if n == 0:
        return [0]
    digits = []
    while n:
        digits.append(int(n % b))
        n //= b
    return digits[::-1]

