from scripts.bignum import get_all, check_valid, get_one
from scripts.search import search_mp, test, search_quick, search
from build_db import generate_patterns_bytes
from scripts.helper import timer
from array import array
from itertools import chain

@timer
def get_patterns(chunk:str|bytes, max_length:int=10, offset:int=0):
    positions = chain.from_iterable((x+offset,)*max_length for x in range(len(chunk)-max_length))
    patterns = []
    for start_idx in range(len(chunk)-max_length):
        for length in range(1,max_length+1):
            part = chunk[start_idx:start_idx+length]
            patterns.append(part)
    print(len(patterns), len(list(positions)))
    # return zip(patterns, positions)


if __name__ == "__main__":
    file = get_one("pi",10)
    if file is None: exit(1)
    chunk = file.first_digits
    # for _ in range(10):
    patterns = get_patterns(chunk, 10)
    # print(*patterns, sep="\n")

"""

      100:50us  2_000_000/s
    1_000:600us 1_666_666/s
   10_000:8ms   1_250_000/s
  100_000:140ms   714_285/s
1_000_000:6s      166_666/s


"""