# converst.py - housing various conversion methods

import string
from itertools import product
from typing import Generator, overload

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

def resolve_notation(output_base:int|str):
    """ returns a basenotation string as well as a translation table for gmpy2 specific base notation """
    trans = {}
    base_chars = string.digits + string.ascii_lowercase + string.ascii_uppercase

    if isinstance(output_base, int):
        if 1 < output_base < 63:
            base_notation = base_chars[:output_base]
        else:
            raise ValueError(f"output_base be between 2 and 62 (both included) not {output_base}")

    elif isinstance(output_base, str):
        if output_base == "abc":
            # map 0-9-a-z -> a-z
            base_notation = string.ascii_lowercase
            for a,b in zip(string.digits+string.ascii_lowercase, base_notation):
                trans[a]=b

        elif output_base == "ABC":
            # map 0-9-A-Z-a-z -> a-z-A-Z
            base_notation = string.ascii_lowercase + string.ascii_uppercase
            for a,b in zip(string.digits+string.ascii_uppercase+string.ascii_lowercase, base_notation):
                trans[a]=b

        elif output_base == "alnum":
            # map 0-9-A-Z-a-z -> a-z-A-Z
            base_notation = base_chars
            for a,b in zip(string.digits+string.ascii_uppercase+string.ascii_lowercase, base_notation):
                trans[a]=b

        else:
            if 2 < len(output_base) < 63:
                base_notation = output_base
                trans = {}
                for a,b in zip(string.digits+string.ascii_uppercase+string.ascii_lowercase, base_notation):
                    trans[a]=b
            else:
                raise ValueError(f"output_base must have a length of 2-62 not {len(output_base)}")
    else:
        raise ValueError(f"output_base must be either int or str {type(output_base)}")

    return base_notation, str.maketrans(trans)

def str_to_mpmath(number:str, base:int|str, precision_bits:int = 50):
    base_notation,_ = resolve_notation(base)
    if not 1 < len(base_notation) < 63:
        raise ValueError("Base must be between 2 and 36")
    number = number.strip().lower()
    negative = number.startswith("-")
    if negative:
        number = number[1:]
    if "." in number:
        int_str, frac_str = number.split(".", 1)
    else:
        int_str, frac_str = number, ""
    with mpmath.workprec(precision_bits):
        mpbase = mpmath.mpf(len(base_notation))
        int_val = mpmath.mpf(0)
        for ch in int_str:
            int_val = int_val * mpbase + base_notation.index(ch)
        frac_val = mpmath.mpf(0)
        for ch in reversed(frac_str):
            frac_val = (frac_val + base_notation.index(ch)) / mpbase
        result = int_val + frac_val
    return -result if negative else result

def mpmath_to_str(number, base:int|str, precision_bits:int = 50) -> str:
    base_notation,_ = resolve_notation(base)
    if not 1 < len(base_notation) < 63:
        raise ValueError("Base must be between 2 and 36")
    base = len(base_notation)
    with mpmath.workprec(precision_bits):
        x = mpmath.mpf(number)
        negative = x < 0
        x = mpmath.fabs(x)
        int_part = int(mpmath.floor(x))
        frac_part = x - mpmath.floor(x)
        if int_part == 0:
            int_str = "0"
        else:
            int_digits = []
            n = int_part
            while n > 0:
                int_digits.append(base_notation[n % base])
                n //= base
            int_str = "".join(reversed(int_digits))
        frac_str = ""
        for _ in range(precision_bits):
            frac_part *= base
            digit = int(mpmath.floor(frac_part))
            frac_str += base_notation[digit]
            frac_part -= mpmath.floor(frac_part)
            if frac_part == 0:
                break
        result = int_str
        if frac_str:
            result += "." + frac_str
    return ("-" if negative else "") + result

def base_convert(input_string:str|bytes, base_input:int|str, base_output:int|str):
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
    base_notation_out, trans_table = resolve_notation(base_output)
    base_output = len(base_notation_out)

    if isinstance(input_string, str):
        rough_conversion = mpmath_to_str(str_to_mpmath(input_string[:50],base_input),base_output)
        radix_pos_in = input_string.find(".")
    else:
        rough_conversion = mpmath_to_str(str_to_mpmath(input_string[:50].decode(),base_input),base_output)
        radix_pos_in = input_string.find(b".")

    radix_pos_out = rough_conversion.find(".")
    input_mp = gmpy2.mpz(input_string[radix_pos_in+1:], base_input) # type:ignore
    n_in = len(input_string) - radix_pos_in - 1
    n_out = int(mpmath.ceil(n_in * mpmath.log(base_input, base_output)))
    pow_out = gmpy2.mpz(base_output) ** n_out # type:ignore
    denom = gmpy2.mpz(base_input) ** n_in # type:ignore
    res = (input_mp * pow_out) // denom
    digits = res.digits(base_output).translate(trans_table)
    rough_frac = rough_conversion.split(".")[1]
    mp_start = len(rough_frac) - len(rough_frac.lstrip(base_notation_out[0]))
    output = rough_conversion[:radix_pos_out+mp_start+1] + digits
    if isinstance(input_string, bytes):
        output = output.encode()
    return output

