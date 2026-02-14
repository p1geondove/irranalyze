import sys
from pathlib import Path
from functools import total_ordering
from mmap import mmap, ACCESS_READ, MADV_SEQUENTIAL
from math import log

from .search import search
from .identify import identify, check_valid
from .convert import base_convert, hex_to_dec, ycd_to_str
from .helper import format_size
from .const import NUM_DIR, FIRST_DIGITS_AMOUNT

@total_ordering
class BigNum:
    """ wrapper for y-cruncher file to get matadata, search and iterate"""
    def __init__(self, path:str|Path) -> None:
        self.path = Path(path)
        self.name, self.base, self.format, self.intpart, self.radix_pos = identify(self.path) # sweep it under the rug lol
        self.size = self.path.stat().st_size - self.radix_pos - 1 # file_size - radix_pos (- off by one error)
        self._first_digits = None # lazy loaded because it can be big
        self._key = (self.name, str(self.base), self.format) # static key
        self.table_name = "_".join(self._key) # used for sqlite
        self._hash = hash(self._key) # also static hash
        self._file = None
        self._mmap = None

    def __repr__(self) -> str:
        """ eg pi.txt(dec|50M) """
        return f"{self.name}.{self.format}(b{self.base}|{format_size(self.size,capitalized=True)})"

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, i) -> str|bytes|int|None:
        """ just as the search function this is 1-indexed, ergo [0] is always '.', but slices like [:10] dont include the dot. Can also be used as a search proxy if input is str|bytes """
        if isinstance(i, int): # key == int
            if i < FIRST_DIGITS_AMOUNT:
                return self.first_digits[i]
            return self.mmap[i]

        if isinstance(i, slice): # key == slice
            if i.stop and i.stop < FIRST_DIGITS_AMOUNT:
                return self.first_digits[i]

            return self.mmap[i]

        if isinstance(i, str): # key == str
            return search(self.path, i.encode())

        if isinstance(i, bytes): # key == bytes
            return search(self.path, i)

    def __iter__(self):
        """ yields digits after radix point """
        i = iter(self.mmap)
        for _ in range(self.radix_pos+1):
            next(i)
        yield from i

    def __contains__(self, pattern:str|bytes) -> bool:
        """ should technically always return true, but its for the limited file only :P """
        if isinstance(pattern, str):
            pattern = pattern.encode()
        return search(self.path, pattern) >= 0

    def __hash__(self) -> int:
        return self._hash

    def __lt__(self, other: object, /) -> bool:
        if not isinstance(other, BigNum):
            return NotImplemented

        if self.name != other.name:
            return self.name < other.name

        if self.format != other.format:
            return self.format < other.format

        if self.base != other.base:
            return self.base < other.base

        return self.size < other.size

    def __eq__(self, other: object, /) -> bool:
        if not isinstance(other, BigNum):
            return NotImplemented
        return self._key == other._key

    def __del__(self):
        try:
            self.close()
        except Exception as e:
            print(f"CRITICAL: Exception when closing {self}: {e}")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @property
    def first_digits(self) -> str|bytes:
        """ small section of the number, usually 1mio digits after radix """
        if self._first_digits:
            return self._first_digits
        digits = self.path.open("rb").read(FIRST_DIGITS_AMOUNT)[self.radix_pos+1:]
        self._first_digits = digits.decode() if self.format == "txt" else digits
        return self._first_digits

    @property
    def mmap(self):
        if self._mmap:
            return self._mmap

        if self._file is None:
            self._file = self.path.open("r+b")

        self._mmap = mmap(self._file.fileno(), length=0, access=ACCESS_READ)

        if sys.platform == "linux":
            self._mmap.madvise(MADV_SEQUENTIAL)

        return self._mmap

    def close(self):
        if self._mmap:
            self._mmap.close()
            self._mmap = None
        if self._file:
            self._file.close()
            self._file = None

    def to_base(self, base:int|str|list[str], amount_digits:int=-1):
        if amount_digits == -1:
            amount_digits = self.size

        # determine size of base notation
        if isinstance(base,int):
            base_len = base
        elif isinstance(base,list):
            base_len = len(base)
        elif isinstance(base, str):
            if base == "abc":
                base_len = 26
            elif base == "ABC":
                base_len = 52
            elif base == "alnum":
                base_len = 62
            else:
                base_len = len(base)

        # how many digits are needed for given base size (ignore ycd compression)
        digits_needed = int(amount_digits*log(base_len)/log(self.base)+1)

        if self.format == "ycd":
            num_str = ycd_to_str(self.path, digits_needed)
        else:
            _frac = self[:digits_needed]
            if isinstance(_frac,bytes):
                _frac = _frac.decode()
            if not isinstance(_frac, str):
                raise ValueError(f"fracpart is not type str {type(_frac)}")
            num_str = str(self.intpart) + "." + _frac
            if base == self.base:
                return num_str[:amount_digits]

        if self.base == 16:
            num_str = hex_to_dec(num_str)

        return base_convert(num_str, base, amount_digits)


def get_all(
    name: str | None = None,
    base: int | None = None,
    format: str | None = None,
    size: int | None = None,
    num_dir: str | Path = NUM_DIR,
    recursive = False
):
    """ gets all BigNum with specified attributes
    name (str): constant name like "pi", "e", "catalan" ...
    base (str): base of the number, either "dec" or "hex"
    format (str): either txt or ycd
    size (int): amount of digits after radix point
    num_dir (str|Path): path to the files
    recursive: scan all subdirectories
    """
    num_dir = Path(num_dir)
    if recursive:
        files = [BigNum(p) for p in num_dir.rglob("*") if p.is_file and check_valid(p)]
    else:
        files = [BigNum(p) for p in num_dir.iterdir() if p.is_file and check_valid(p)]
    if name:   files = filter(lambda file: file.name == name, files)
    if base:   files = filter(lambda file: file.base == base, files)
    if format: files = filter(lambda file: file.format == format, files)
    if size:   files = filter(lambda file: file.size == size, files)
    return list(files)

def get_one(
    name: str | None = None,
    base: int | None = None,
    format: str | None = None,
    size: int | None = None,
    num_dir: str | Path = NUM_DIR,
):
    """ gets one BigNum with specified attributes
    name (str): constant name like "pi", "e", "catalan" ...
    base (int): base of the number, either "dec" or "hex"
    format (str): either
    size (int): amount of digits after radix point
    """
    files = get_all(name, base, format, size, num_dir)
    if files: return files[0]

