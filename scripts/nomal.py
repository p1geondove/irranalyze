from multiprocessing import cpu_count, Pool
from gmpy2 import mpz
import os
from collections import Counter
from math import log10

def get_int(file_path:str, amt_digits=-1) -> mpz:
    # reads a file and returns the digits after decimal point as a big mpz int
    first_size = 10
    chunk_size = 4000
    _magic = 10**chunk_size

    with open(file_path, 'rt') as file:
        first_chunk = file.read(first_size)
        decimal_spot = first_chunk.find('.') + 1
        if amt_digits == -1:
            amt_digits = os.path.getsize(file_path) - decimal_spot 
        num_size = first_size - decimal_spot # equiv to int(log10(num))

        if not decimal_spot: # invalid file, no decimal found
            return 0
        
        if first_size-decimal_spot > amt_digits: # output digits already in the first chunk
            return mpz(int(first_chunk[decimal_spot : decimal_spot + amt_digits]))
        
        num = mpz(int(first_chunk[decimal_spot:])) # start int
        digits_file = os.path.getsize(file_path) - decimal_spot
        amt_chunks = int((min((digits_file, amt_digits)) - first_size + decimal_spot) / chunk_size)

        for _ in range(amt_chunks): #safe chunks
            chunk = file.read(chunk_size)
            num = num * _magic + int(chunk)
            num_size += chunk_size

        chunk = file.read(chunk_size) #last chunk with cropping
        rest_amt = amt_digits - num_size

        if rest_amt > 0 and chunk:
            chunk = chunk[:rest_amt] # crop chunk to fit in desired amt_digits
            num = num * 10**rest_amt + int(chunk)
            num_size += rest_amt

        return num

def digit_generator(big_int:mpz, base=2, max_digits=None):
    # converts a gmpy2.mpz int to str using base conversion and yields a character
    notation = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    if isinstance(base, str):
        if base == 'abc':
            base_notation = 'abcdefghijklmnopqrstuvwxyz'
            base = len(base_notation)
    if not isinstance(base, int):
        raise Exception(NotImplementedError, 'base must be of type int')
    if max_digits is None:
        digits_amt_out = float('inf')
    else:
        digits_amt_out = max_digits

    num_size = big_int.num_digits(10)
    chunk_width = 10**num_size
    if digits_amt_out == float('inf'):
        while True:
            carry, big_int = divmod(big_int * base, chunk_width)
            yield notation[carry]
    else:
        digits_amt_out = int(max(1, min(num_size/log10(base), digits_amt_out)))
        for _ in range(digits_amt_out):
            carry, big_int = divmod(big_int * base, chunk_width)
            yield notation[carry]

def check_normal(args):
    big_int, base, prec = args
    count = Counter(digit_generator(big_int, base, prec))
    print(base, max(abs(amt-prec//base) for amt in count.values())/(prec//base))

def main():
    file_path = r'\\10.0.0.3\raid\other\bignum\pi\Pi - Dec - Chudnovsky.txt'
    big_int = get_int(file_path)
    prec = 10000
    num_cores = cpu_count()
    work_items = [(big_int, base, prec) for base in range(2, 80)]
    
    with Pool(num_cores) as pool:
        pool.map(check_normal, work_items)

if __name__ == '__main__':
    main()