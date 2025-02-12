from gmpy2 import mpz
import ntimer
import os

@ntimer.timer
def get_int(file_path:str, amt_digits=100) -> mpz:
    first_size = 10
    chunk_size = 4000
    _magic = 10**chunk_size

    with open(file_path, 'rt') as file:
        first_chunk = file.read(first_size)
        decimal_spot = first_chunk.find('.') + 1
        num_size = first_size - decimal_spot # equiv to int(log10(num))

        if not decimal_spot: # invalid file, no decimal found
            return 0, 0
        
        if first_size-decimal_spot > amt_digits: # output digits already in the first chunk
            return mpz(int(first_chunk[decimal_spot : decimal_spot + amt_digits])), num_size
        
        digits_file = os.path.getsize(file_path) - decimal_spot
        num = mpz(int(first_chunk[decimal_spot:])) # start int
        chunk = file.read(chunk_size) # first big chunk, after the small initial
        amt_chunks = int((min((digits_file, amt_digits)) - first_size + decimal_spot) / chunk_size)

        for _ in range(amt_chunks): #safe chunks
            chunk = file.read(chunk_size)
            num = num * _magic + int(chunk)
            num_size += chunk_size

        chunk = file.read(chunk_size) #last chunk with cropping
        rest_amt = amt_digits - num_size

        if rest_amt > 0:
            chunk = chunk[:rest_amt] # crop chunk to fit in desired amt_digits
            num = num * 10**rest_amt + int(chunk)
            num_size += rest_amt

        print(type(num))
        return num, num_size
    
@ntimer.timer
def base_convert(dec_int:int, num_size:int, base:int=2, max_digits:int=100) -> str:
    base_notation = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    
    if isinstance(base,str):
        if base == 'abc':
            base_notation = 'abcdefghijklmnopqrstuvwxyz'
            base = len(base_notation)
    if not isinstance(base, int):
        raise Exception(NotImplementedError, 'base must be of type int')
    
    big_int = 10**num_size+1
    num = []

    for _ in range(max_digits):
        carry, dec_int = divmod(dec_int * base,big_int)
        num.append(base_notation[carry])
    
    return ''.join(num)


file_path = r'\\10.0.0.3\raid\other\bignum\pi\Pi dec 1b.txt'
prec = 100_000
big_int, size = get_int(file_path,prec)
big_str = base_convert(big_int,size,max_digits=prec,base='abc')
print(big_str)