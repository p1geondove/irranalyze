import ntimer
import os
from math import log, log10


@ntimer.timer
def get_int(file_path:str, amt_digits=100) -> int:
    first_size = 100
    chunk_size = 4000

    with open(file_path, 'r') as file:
        first_chunk = file.read(first_size)
        decimal_spot = first_chunk.find('.') + 1
        num_size = first_size - decimal_spot # equiv to int(log10(num))

        if not decimal_spot: # invalid file, no decimal found
            return 0
        
        if first_size-decimal_spot > amt_digits: # output digits already in the first chunk
            return int(first_chunk[decimal_spot : decimal_spot + amt_digits])
        
        num = int(first_chunk[decimal_spot:]) # start int
        chunk = file.read(chunk_size) # first big chunk, after the small initial

        while chunk and num_size < amt_digits:
            if num_size+chunk_size > amt_digits:
                chunk = chunk[:amt_digits - num_size - chunk_size] # crop chunk to fit in desired amt_digits
                return num * 10**(len(chunk)) + int(chunk) # return final int
            
            num = num * 10**chunk_size + int(chunk) # bitshift in base 10 and add chunk
            num_size += chunk_size 
            chunk = file.read(chunk_size)
    
    return num

@ntimer.timer
def base_convert(dec_int:int, base:int=2, max_digits:int=100) -> str:
    base_notation = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    
    if isinstance(base,str):
        if base == 'abc':
            base_notation = 'abcdefghijklmnopqrstuvwxyz'
            base = len(base_notation)
    if not isinstance(base, int):
        raise Exception(NotImplementedError, 'base must be of type int')
    
    big_int = 10**(int(log10(dec_int))+1)
    num = []

    for _ in range(max_digits):
        carry, dec_int = divmod(dec_int * base,big_int)
        num.append(base_notation[carry])

    return ''.join(num)

def txt_gen(dec_int:int, max_digits:int=100):
    base_notation = 'abcdefghijklmnopqrstuvwxyz'
    base = len(base_notation)
    big_int = 10**(int(log10(dec_int))+1)

    for _ in range(max_digits):
        carry, dec_int = divmod(dec_int * base,big_int)
        yield base_notation[carry]

def write_base(in_file:str, out_base:int, in_base:int=10, out_file:str=None):
    if out_file is None:
        out_file = f'0x{out_base}_{in_file}'

    digits_amt_in = os.path.getsize(in_file)
    int_in = get_int(in_file, digits_amt_in)
    digits_amt_out = int(log(int_in, out_base))+1

    with open(out_file, 'w') as file:
        for char in txt_gen(int_in, digits_amt_out):
            file.write(char)

@ntimer.timer
def main():
    file_path = r'\\10.0.0.3\raid\other\bignum\pi\Pi - Dec - Chudnovsky.txt'
    # prec = 100000
    
    write_base(file_path, 2, out_file='bin.txt')
    
    # pi_int = get_int(file_path, prec)
    # long_str = base_convert(pi_int, 'abc', prec)
    # print(long_str.find('max'))
    # base_print(pi_int, prec)

if __name__ == '__main__':
    main()
