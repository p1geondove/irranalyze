# converst.py - housing various conversion methods

import string
from itertools import product
from typing import Generator, overload
from functools import lru_cache

import mpmath
import gmpy2

@overload
def txt_to_num(txt:str) -> str: ...
@overload
def txt_to_num(txt:bytes) -> bytes: ...
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

@overload
def txt_to_num_all(txt:str) -> Generator[str]: ...
@overload
def txt_to_num_all(txt:bytes) -> Generator[bytes]: ...
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

@overload
def num_to_txt(num:int) -> str: ...
@overload
def num_to_txt(num:str) -> str: ...
@overload
def num_to_txt(num:bytes) -> bytes: ...
def num_to_txt(num:int|str|bytes) -> str|bytes:
    """
    converts numeric string to alphabetic string
    pairs up the input string and calls chr(p%26+97) for every pair
    can be treated as the inverse to txt_to_num()
    txt_to_num("132012010417") -> "number"
    """
    is_bytes = False
    if isinstance(num,int):
        num = str(num)
    elif isinstance(num,bytes):
        is_bytes = True
        num = num.decode()
    if not num.isnumeric():
        raise ValueError("input must be numeric")
    if len(num)%2:
        print(f"WARN: input of num_to_txt should have even length")
    pairs = (int(a+b) for a,b in zip(num[::2], num[1::2]))
    if is_bytes:
        return "".join(chr(p%26+97) for p in pairs).encode()
    else:
        return "".join(chr(p%26+97) for p in pairs)

@overload
def alnum_to_num(txt:str) -> str: ...
@overload
def alnum_to_num(txt:bytes) -> bytes: ...
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

def str_to_ycd_gen(mv:memoryview, base:int) -> Generator[bytes]:
    """ a quick generator for str to ycd conversion, needs a memoryview object with int + radix part cut off and the base its stored in """
    if base not in (10,16):
        raise ValueError(f"Base can only be 10 or 16, not {base}")
    chunksize = int(mpmath.log(2**64, base))
    for i in range(0, len(mv) - chunksize + 1, chunksize):
        yield int(mv[i:i+chunksize].tobytes(), base).to_bytes(8, "little")

def str_to_ycd(in_string:str|memoryview, amount_digits:int=-1) -> bytes:
    """ wrapper for str_to_ycd_gen that can also take a string and only returns as many digits as needed """
    chunk = in_string[:300]
    if isinstance(chunk,memoryview):
        try:
            chunk.tobytes().decode()
        except UnicodeDecodeError:
            #print("str_to_ycd was given a memoryview, but that memoryview contained non utf8 bytes. str_to_ycd must always be decodeable")
            raise
    chunk_set = set(chunk)
    base = len(chunk_set)
    if "." in chunk_set:
        #print("str_to_ycd expexts digits after and not including the radix point")
        raise ValueError
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

@overload
def resolve_notation(output_base:int, asbytes=False) -> tuple[str, dict]: ...
@overload
def resolve_notation(output_base:str, asbytes=False) -> tuple[str, dict]: ...
@overload
def resolve_notation(output_base:bytes, asbytes=False) -> tuple[tuple[bytes], dict]: ...
@overload
def resolve_notation(output_base:int, asbytes=True) -> tuple[tuple[bytes], dict]: ...
@overload
def resolve_notation(output_base:str, asbytes=True) -> tuple[tuple[bytes], dict]: ...
@overload
def resolve_notation(output_base:bytes, asbytes=True) -> tuple[tuple[bytes], dict]: ...
def resolve_notation(output_base:int|str|bytes, asbytes=False):
    """ returns a basenotation iterable as well as a translation table for gmpy2 specific base notation """
    trans = {}
    if isinstance(output_base, int):
        base_notation = string.printable[:output_base]

    elif isinstance(output_base, str):
        if output_base == "abc":
            # mpz=dig,lower mine=lower
            base_notation = string.ascii_lowercase
            for a,b in zip(string.digits+string.ascii_lowercase, base_notation):
                trans[a]=b

        elif output_base == "ABC":
            # mpz=dig,upper,lower mine=lower,upper
            base_notation = string.ascii_lowercase + string.ascii_uppercase
            for a,b in zip(string.digits+string.ascii_uppercase+string.ascii_lowercase, base_notation):
                trans[a]=b

        elif output_base == "alnum":
            # mpz=mine
            base_notation = string.digits+string.ascii_lowercase
            # for a,b in zip(string.digits+string.ascii_lowercase, base_notation):
            #     trans[a]=b

        elif output_base == "ALNUM":
            # mpz=dig,upper,lower mine=dig,lower,upper
            base_notation = string.digits+string.ascii_lowercase+string.ascii_uppercase
            for a,b in zip(string.digits+string.ascii_uppercase+string.ascii_lowercase, base_notation):
                trans[a]=b


        else:
            base_notation = output_base
            trans = {}
            for a,b in zip(string.printable ,base_notation):
                trans[a]=b
    
    elif isinstance(output_base, bytes):
        return tuple(bytes((c,)) for c in output_base), {ord(str(i)):c for i,c in zip(string.printable, output_base)}

    else:
        raise ValueError(f"output_base must be either int or str {type(output_base)}")
    
    if asbytes:
        base_notation = tuple(bytes((c,)) for c in base_notation.encode())
        trans = {k:ord(v) for k,v in trans.items()}

    return base_notation, str.maketrans(trans)

def str_to_mpmath(number:str|bytes, base:int|str|bytes, precision_bits:int = 50):
    base_notation,_ = resolve_notation(base, isinstance(number,bytes))
    if isinstance(base_notation, tuple):
        base_notation = b"".join(base_notation)
    notation_table = {char:val for val,char in enumerate(base_notation)}
    number = number.strip()
    if isinstance(number, str):
        negative = number.startswith("-")
        if "." in number:
            int_str, frac_str = number.split(".", 1)
        else:
            int_str, frac_str = number, ""
    else:
        negative = number.startswith(b"-")
        if b"." in number:
            int_str, frac_str = number.split(b".", 1)
        else:
            int_str, frac_str = number, b""
    if negative:
        number = number[1:]
    with mpmath.workprec(precision_bits):
        mpbase = mpmath.mpf(len(base_notation))
        int_val = mpmath.mpf(0)
        for ch in int_str:
            int_val = int_val * mpbase + notation_table[ch]
        frac_val = mpmath.mpf(0)
        for ch in reversed(frac_str):
            frac_val = (frac_val + notation_table[ch]) / mpbase
        result = int_val + frac_val
    return -result if negative else result

def mpmath_to_str(number, base:int|str|bytes, precision_bits:int = 50) -> str|bytes:
    base_notation,_ = resolve_notation(base)
    base = len(base_notation)
    with mpmath.workprec(precision_bits):
        x = mpmath.mpf(number)
        negative = x < 0
        x = mpmath.fabs(x)
        int_part = int(mpmath.floor(x))
        frac_part = x - mpmath.floor(x)
        if int_part == 0:
            int_str = base_notation[0]
        else:
            int_digits = []
            n = int_part
            while n > 0:
                int_digits.append(base_notation[n % base])
                n //= base
            if isinstance(int_digits[0], str):
                int_str = "".join(reversed(int_digits))
            else:
                int_str = b"".join(reversed(int_digits))
        frac_str = "" if isinstance(base_notation, str) else b""
        for _ in range(precision_bits):
            frac_part *= base
            digit = int(mpmath.floor(frac_part))
            frac_str += base_notation[digit]
            frac_part -= mpmath.floor(frac_part)
            if frac_part == 0:
                break
        result = int_str
        if frac_str:
            if isinstance(result, str) and isinstance(frac_str, str):
                result += "." + frac_str
            elif isinstance(result, bytes) and isinstance(frac_str, bytes):
                result += b"." + frac_str
    if isinstance(result, str):
        result = ("-" if negative else "") + result
    else:
        result = (b"-" if negative else b"") + result
    return result

@overload
def base_convert(input_string:str, base_input:int|str|bytes, base_output:int|str|bytes) -> str: ...
@overload
def base_convert(input_string:bytes, base_input:int|str|bytes, base_output:int|str|bytes) -> bytes: ...
def base_convert(input_string:str|bytes, base_input:int|str|bytes, base_output:int|str|bytes):
    """
    convert number to a different base
    raw base notation is 0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
    - if int is provided as base parameter is will use notation[:base]
    - if str is provided as base parameter there are some special cases:
      - "abc" -> all lower case letters
      - "ABC" -> lowercase + uppercase
      - "alnum" -> lowercase + uppercase + digits
      - anything else will be used as the base notation
    """
    base_notation_in, _ = resolve_notation(base_input) # input base as representation iterable and translation table
    base_in = len(base_notation_in) # input base as int
    base_notation_out, trans_table = resolve_notation(base_output, isinstance(input_string, bytes)) # output base as representation iterable and translation table
    base_out = len(base_notation_out) # output base as int
    partial_input = input_string[:50]
    rough_conversion = mpmath_to_str(str_to_mpmath(partial_input, base_input), base_output)
    radix_in = (input_string.find(".") if isinstance(input_string,str) else input_string.find(b".")) + 1
    radix_out = (rough_conversion.find(".") if isinstance(rough_conversion, str) else rough_conversion.find(b".")) + 1
    zero_char = base_notation_out[0]
    input_mp = gmpy2.mpz(input_string[radix_in:], base_in) # type:ignore mpz not a known attribute, no biggie
    n_in = len(input_string) - radix_in
    n_out = int(mpmath.ceil(n_in * mpmath.log(base_in, base_out)))
    pow_out = gmpy2.mpz(base_out) ** n_out # type:ignore mpz not a known attribute, no biggie
    denom = gmpy2.mpz(base_in) ** n_in # type:ignore mpz not a known attribute, no biggie
    res = (input_mp * pow_out) // denom
    if base_out <= 62: digits = res.digits(base_out).translate(trans_table)
    else: digits = make_extractor(base_out, base_notation_out)(res, n_out)

    # bring all variables to the same datatype
    if isinstance(input_string, str):
        if isinstance(digits, bytes):
            digits = digits.decode()
        if isinstance(rough_conversion, bytes):
            rough_conversion = rough_conversion.decode()
        if isinstance(zero_char, bytes):
            zero_char = zero_char.decode()
    elif isinstance(input_string, bytes):
        if isinstance(digits, str):
            digits = digits.encode()
        if isinstance(rough_conversion, str):
            rough_conversion = rough_conversion.encode()
        if isinstance(zero_char, str):
            zero_char = zero_char.encode()

    rough_frac = rough_conversion[radix_out:]
    mp_start = len(rough_frac) - len(rough_frac.lstrip(zero_char))
    return rough_conversion[:radix_out+mp_start] + digits

def make_extractor(base:int, notation:str|tuple[bytes]):
    @lru_cache(maxsize=None)
    def power(k):
        if k == 1: return gmpy2.mpz(base) # type:ignore
        half = power(k // 2)
        p = half * half
        return p * base if k % 2 else p

    def extract(n, num_digits:int):
        if num_digits == 1:
            return notation[n]
        lo = num_digits // 2
        top, bottom = divmod(n, power(lo))
        return extract(top, num_digits - lo) + extract(bottom, lo)

    return extract

