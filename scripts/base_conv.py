import os
from gmpy2 import mpz
from math import log10

def get_int(file_path:str, amt_digits=100) -> mpz:
    first_size = 10
    chunk_size = 10000
    _magic = 10**chunk_size

    with open(file_path, 'rt') as file:
        first_chunk = file.read(first_size)
        decimal_spot = first_chunk.find('.') + 1
        num_size = first_size - decimal_spot # equiv to int(log10(num))

        if not decimal_spot: # invalid file, no decimal found
            return 0, 0
        
        if first_size-decimal_spot > amt_digits: # output digits already in the first chunk
            return mpz(first_chunk[decimal_spot : decimal_spot + amt_digits]), num_size
        
        digits_file = os.path.getsize(file_path) - decimal_spot
        num = mpz(first_chunk[decimal_spot:]) # start int
        amt_chunks = int((min((digits_file, amt_digits)) - first_size + decimal_spot) / chunk_size)

        for _ in range(amt_chunks): #safe chunks
            chunk = file.read(chunk_size)
            num = num * _magic + mpz(chunk)
            num_size += chunk_size

        chunk = file.read(chunk_size) #last chunk
        rest_amt = amt_digits - num_size

        if rest_amt > 0:
            chunk = chunk[:rest_amt] # crop chunk to fit in desired amt_digits
            # print(chunk)
            num = num * 10**rest_amt + mpz(chunk)
            num_size += rest_amt

        return num

def base_convert(dec_int:int, base:int=2,  max_digits:int=100):
    base_notation = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    
    if isinstance(base,str):
        if base == 'abc': # custom base representing all lowercase
            base_notation = 'abcdefghijklmnopqrstuvwxyz'
            base = len(base_notation)
        elif base == 'ABC':  # custom base representing all lowercase and uppercase
            base_notation = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
            base = len(base_notation)
    if not isinstance(base, int):
        raise Exception(NotImplementedError, 'base must be of type int or special type (abc or ABC)')
    if not (_base := min(max(2,base),len(base_notation))) == base:
        print(f'warn: clamped base from {base} to {_base}')
        base = _base

    chunk_width = 10 ** dec_int.num_digits(10)

    for _ in range(max_digits):
        carry, dec_int = divmod(dec_int * base, chunk_width)
        yield base_notation[carry]

from scripts.ntimer import perf_counter_ns, fmt_ns

def to_base(file_path:str, base:int = 12, amt_digits:int = 1000):
    if base == 'abc':
        read_amount = int(log10(26**amt_digits))
    elif base == 'ABC':
        read_amount = int(log10(52**amt_digits))
    elif isinstance(base, int):
        read_amount = int(log10(base**amt_digits))
    else:
        return
    
    return ''.join(base_convert(get_int(file_path, read_amount), base, amt_digits))
