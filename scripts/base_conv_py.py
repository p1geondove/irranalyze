import ntimer
from math import log10

def get_pi(file_path:str=None, amt_digits = 100):
    """turns files into integers

    this is used for irrational number analysis.
    it returns a huge int that composes n digits after the decimal point in base 10
    used for base conversion

    Example:
        get_int(20) -> int(14159265358979323846)

    Args:
        file_path (str, optional): path to file. Defaults to cynder raid 1m pi dec
        amt_digits (int, optional): amount of digits to get. Defaults to 100

    Returns:
        int: integer from digits after the decimal point
    """
    if file_path is None:
        file_path = r'\\10.0.0.3\raid\other\bignum\pi\Pi - Dec - Chudnovsky.txt'
    first_size = 100
    chunk_size = 4000
    num = 0

    with open(file_path, 'r') as file:
        first_chunk = file.read(first_size)
        decimal_spot = first_chunk.find('.') + 1
        num_size = first_size-decimal_spot

        if not decimal_spot:
            return 0
        
        if first_size-decimal_spot > amt_digits:
            return int(first_chunk[decimal_spot:decimal_spot+amt_digits])
        
        num += int(first_chunk[decimal_spot:])

        chunk = file.read(chunk_size)
        while chunk and num_size < amt_digits:
            if num_size+chunk_size > amt_digits:
                chunk = chunk[:amt_digits-num_size-chunk_size]
                return num * 10**(len(chunk)) + int(chunk)
            
            num = num * 10**chunk_size + int(chunk)
            num_size += chunk_size
            chunk = file.read(chunk_size)
    
    return num

def base_convert(dec_int:int, base:int=2, max_digits:int=100) -> str:
    base_notation = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    num_size = int(log10(dec_int))+1
    num = []
    times = [[], [], []]
    for _ in range(max_digits):
        t1 = ntimer.perf_counter_ns()
        int2 = dec_int * base #800ns
        t2 = ntimer.perf_counter_ns()
        carry, dec_int = divmod(int2,10**num_size) #3.3us@1000 130us@10000
        t3 = ntimer.perf_counter_ns()
        num.append(base_notation[carry]) #nix
        t4 = ntimer.perf_counter_ns()
        # print('-'*50)
        times[0].append(t2-t1)
        times[1].append(t3-t2)
        times[2].append(t4-t3)
    for i,t in enumerate(times):
        print(f'\n   {['mult','divmod','append'][i]}')
        print(f'min:{ntimer.fmt_ns(min(t))}')
        print(f'max:{ntimer.fmt_ns(max(t))}')
        print(f'avg:{ntimer.fmt_ns(sum(t)/len(t))}')
    return ''.join(num)

@ntimer.timer
def main():
    """
    get_int
        1.2ms 10000
        700us 1000
        600us 100

    base_convert
        1.1s  10000
        2.5ms 1000
        66us  100
    """
    prec = 20000
    pi_int = get_pi(amt_digits=prec)
    base_convert(pi_int, 2, max_digits=prec)

if __name__ == '__main__':
    main()
