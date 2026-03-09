# converst.py - housing various conversion methods

import string
from itertools import product
from typing import Generator

import mpmath
import gmpy2

def txt_to_num(txt:str|bytes) -> str|bytes:
    """
    converts alphabetic string to numeric string
    can be treated as the inverse to num_to_txt()
    presevers datatype
    txt_to_num("number") -> "132012010417"
    """
    isbytes = False
    if isinstance(txt,bytes):
        txt = txt.decode()
        isbytes = True
    if not txt.isalpha():
        raise ValueError("input must be alphabetic")
    txt = txt.lower()
    if isbytes:
        return "".join(f"{c-97:02d}" for c in map(ord,txt)).encode()
    else:
        return "".join(f"{c-97:02d}" for c in map(ord,txt))

def txt_to_num_all(txt:str|bytes) -> Generator[str|bytes]:
    """
    converts alphabetic string to numeric string
    this returns all possible conversions
    each character has 3 or 4 representations, "a" can be 00,26,52,75 while w,x,y,z only have 3
    this is also a generator since there are 3**(len(txt)) to 4**(len(txt)) possible representations
    list(txt_to_num("az")) -> ['0025', '0051', '0077', '2625', '2651', '2677', '5225', '5251', '5277', '7825', '7851', '7877']
    """
    isbytes = False
    if isinstance(txt,bytes):
        txt = txt.decode()
        isbytes = True
    table = {c:[f"{(ord(c)-97)+n*26:02d}" for n in range(4) if (ord(c)-97)+n*26<=99] for c in string.ascii_lowercase}
    chars = product(*[table[c] for c in txt.lower()])
    if isbytes:
        for nums in chars:
            yield "".join(nums).encode()
    else:
        for nums in chars:
            yield "".join(nums)

def num_to_txt(num:int|str|bytes, asbytes:bool=False) -> str|bytes:
    """
    converts numeric string to alphabetic string
    pairs up the input string and calls chr(p%26+97) for every pair
    can be treated as the inverse to txt_to_num()
    txt_to_num("132012010417") -> "number"
    """
    if isinstance(num,int):
        num = str(num)
    elif isinstance(num,bytes):
        num = num.decode()
    if not num.isnumeric():
        raise ValueError("input must be numeric")
    if len(num)%2:
        print(f"WARN: input of num_to_txt should have even length")
    pairs = (int(a+b) for a,b in zip(num[::2], num[1::2]))
    if asbytes:
        return "".join(chr(p%26+97) for p in pairs).encode()
    else:
        return "".join(chr(p%26+97) for p in pairs)

def alnum_to_num(txt:str|bytes) -> str|bytes:
    """ similar to txt_to_num but allows for numbers in the input """
    isbytes = False
    if isinstance(txt,bytes):
        txt = txt.decode()
        isbytes = True
    t = {c:f"{i:02d}" for i,c in enumerate(string.ascii_letters)}
    if isbytes:
        return "".join(t[c] if c.isalpha() else str(c) for c in txt).encode()
    else:
        return "".join(t[c] if c.isalpha() else str(c) for c in txt)

def ycd_to_str_gen(mv:memoryview, base:int) -> Generator[str]:
    """ a quick generator for ycd to str conversion, needs a memoryview object with int + radix part cut off and the base its stored in """
    if base == 10:
        for i in range(0, len(mv)-8, 8):
            yield str(int.from_bytes(mv[i:i+8], "little")).rjust(19,"0")
    elif base == 16:
        for i in range(0, len(mv)-8, 8):
            yield format(int.from_bytes(mv[i:i+8], "little"), "016x")
    else:
        raise ValueError(f"Base can only be 10 or 16, not {base}")

def ycd_to_str(in_bytes:bytes|memoryview, base:int, amount_digits:int=-1) -> str:
    """ wrapper for ycd_to_str_gen that can also take bytes and only returns as many digits as needed """
    if base not in (10,16):
        raise ValueError(f"Base can only be 10 or 16, not {base}")
    digits_per_8byte = 19 if base == 10 else 16
    if amount_digits == -1:
        bytes_needed = len(in_bytes)
    else:
        bytes_needed = int(mpmath.ceil(amount_digits / digits_per_8byte)) * 8 + 8
    mv = memoryview(in_bytes)[:bytes_needed]
    out_string = "".join(ycd_to_str_gen(mv,base))
    mv.release()
    if amount_digits>0:
        return out_string[:amount_digits]
    return out_string

def str_to_ycd_gen(mv:memoryview, base:int) -> Generator[bytes, None, None]:
    """ a quick generator for str to ycd conversion, needs a memoryview object with int + radix part cut off and the base its stored in """
    if base not in (10,16):
        raise ValueError(f"Base can only be 10 or 16, not {base}")
    chunksize = int(mpmath.log(2**64, base))
    for i in range(0, len(mv) - chunksize + 1, chunksize):
        yield int(mv[i:i+chunksize].tobytes(), base).to_bytes(8, "little")

def str_to_ycd(in_string:str|memoryview, amount_digits:int=-1):
    """ wrapper for str_to_ycd_gen that can also take bytes and only returns as many digits as needed """
    base = len(set(in_string[:300]))
    if base not in (10,16):
        raise ValueError(f"Base can only be 10 or 16, not {base}")
    digits_per_8byte = 19 if base == 10 else 16
    if amount_digits == -1:
        bytes_needed = len(in_string)
    else:
        bytes_needed = amount_digits // 8 * digits_per_8byte + digits_per_8byte
    if isinstance(in_string, str):
        mv = memoryview(in_string.encode())
    else:
        mv = in_string
    out_bytes = b"".join(str_to_ycd_gen(mv[:bytes_needed], base))
    mv.release()
    if amount_digits>0:
        return out_bytes[:amount_digits]
    return out_bytes

def hex_to_dec(in_str:str, amount_digits:int=-1) -> str:
    """ converts a hexadecimal string to decimal """
    if amount_digits == -1: # if no desired decimal precision
        dec_digits = int(mpmath.log(16,10) * len(in_str)) # this is how many decimal digits we can produce
    else:
        dec_digits = amount_digits # otherwise we use this as working precision
    hex_digits = int(mpmath.ceil(mpmath.log(10,16) * dec_digits)) # this is how many hexadecimal digits we need

    with mpmath.mp.workdps(dec_digits+10): # set working precision + a bit of leeway
        radix_pos = in_str.find(".") # since we work with irrational numbers we need to know where the radix is
        num = mpmath.mpf(0)
        for d in reversed(in_str[radix_pos+1:hex_digits+radix_pos+1]):
            num = (num + mpmath.mpf(int(d, 16))) / mpmath.mpf(16)
        num += mpmath.mpf(int(in_str[:radix_pos], 16))
        num_str = str(num) # convert number to string

    if amount_digits == -1: # if user wants all converted we still clip to the safe part
        return num_str[:dec_digits+radix_pos+1]
    return num_str[:amount_digits] # otherwise clip to wanted precision

def base_convert(dec_str:str, base:int|str|list[str]|None = None, digits:int|None = None) -> str:
    """
    convert number to a different base
    raw base notation is 0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~
    - if int is provided as base parameter is will use notation[:base]. special case is -1, with that it will use the entire thing
    - if list[str] is provided as base parameter it will treat each element as a digit
    - if str is provided as base parameter there are some special cases:
    - abc -> all lower case letters
    - ABC -> lowercase + uppercase
    - alnum -> lowercase + uppercase + digits
    """
    base_chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"

    if isinstance(base, str): # determine base notation
        if base == "abc":
            base_chars = string.ascii_lowercase
        elif base == "ABC":
            base_chars = string.ascii_letters
        elif base == "alnum":
            base_chars = string.digits + string.ascii_letters
        else:
            base_chars = base # custom charset
    elif isinstance(base, int):
        if base == -1:
            base = len(base_chars)
        elif not (_base := min(max(2, base), len(base_chars))) == base:
            print(f"warn: clamped base from {base} to {_base}")
            base = _base
        base_chars = base_chars[:base]
    elif isinstance(base, list):
        if not all(isinstance(e,str) for e in base):
            ValueError("base must be either int, string or list[str]")
        base_chars = base
    elif base is None:
        base = len(base_chars)
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
        print(f"base_convert: {base=} {input_amt_needed=} {len(dec_str)=}")
        frac_part = dec_str[radix_pos+1:].ljust(input_amt_needed,"0")
    else:
        frac_part = dec_str[radix_pos+1 : radix_pos+1+input_amt_needed]
    frac_part = gmpy2.mpz(frac_part) # holy fuck my linter is telling me there is no mpz in gmpy2, stfu...
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
    if n == 0:
        return [0]
    digits = []
    while n:
        digits.append(int(n % b))
        n //= b
    return digits[::-1]
