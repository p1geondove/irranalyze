# bignum.py - wrapper for number files

from pathlib import Path
from functools import total_ordering
from mmap import mmap, ACCESS_READ, MADV_SEQUENTIAL
from math import log, ceil
from typing import Iterable, Iterator, overload

from .search import search
from .identify import identify, check_valid
from .convert import base_convert, hex_to_dec, ycd_to_str
from .helper import format_size
from .var import Sizes, Paths, Switches

from .helper import timer

@total_ordering
class BigNum:
    """ wrapper for y-cruncher file to get matadata, search and iterate"""
    def __init__(self, path:str|Path) -> None:
        self.path = Path(path)
        if not (self.path.exists() and check_valid(self.path)):
            raise AttributeError("Provided file path is not a number file")
        self.info = identify(self.path)
        self.name = self.info.name
        self.base = self.info.base
        self.format = self.info.format
        self.radix_pos = self.info.radix_pos
        self.intpart = self.info.int_part
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
        """ returns amount of bytes after radix"""
        return self.size

    @overload
    def __getitem__(self, i:int) -> bytes: ...
    @overload
    def __getitem__(self, i:slice) -> bytes: ...
    @overload
    def __getitem__(self, i:str) -> int: ...
    @overload
    def __getitem__(self, i:bytes) -> int: ...
    @overload
    def __getitem__(self, i:Iterable) -> dict[bytes,int]: ...

    def __getitem__(self, i):
        """ just as the search function this is 1-indexed, ergo [0] is always '.', but slices like [:10] dont include the dot. Can also be used as a search proxy if input is str|bytes """
        if isinstance(i, int):
            if i < Sizes.first_digits_amount:
                return bytes((self.first_digits[i],))
            i += self.radix_pos+1-Switches.one_indexed
            return bytes((self.mmap[i],))

        if isinstance(i, slice):
            if i.stop and -1 < i.stop < Sizes.first_digits_amount:
                return self.first_digits[i]
            base = self.radix_pos + 1 - Switches.one_indexed
            virtual_len = len(self.mmap) - base
            start, stop, step = i.indices(virtual_len)
            return self.mmap[base+start:base+stop:step]

        if isinstance(i, str):
            return search(self.info, i.encode())

        if isinstance(i, bytes):
            return search(self.info, i)

        if isinstance(i, Iterable):
            funcs = {
                str:lambda x:x.encode(),
            }
            elements = [funcs.get(type(e),lambda x:x)(e) for e in i]
            if all(isinstance(e, bytes) for e in elements):
                return search(self.info, elements)
            return [self[e] for e in elements]

    def __iter__(self) -> Iterator[bytes]:
        """ yields digits as bytes, radix is never included no matter the state of Switches.one_indexed"""
        i = iter(self.mmap)
        for _ in range(self.radix_pos+1):
            next(i)
        yield from i # no pyright, this is not a Generator[int], mmap always returns single bytes: github.com/python/cpython/issues/70546 # type:ignore

    def __contains__(self, pattern:str|bytes) -> bool:
        """ should technically always return true, but its for the limited file only :P """
        if isinstance(pattern, str):
            pattern = pattern.encode()
        return search(self.info, pattern) != -1

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

    def __buffer__(self, flags):
        return self.mmap.__buffer__(flags)

    @property
    def first_digits(self) -> bytes:
        """ small section of the number, usually 1mio digits after radix """
        if self._first_digits:
            return self._first_digits
        base = self.radix_pos + 1 - Switches.one_indexed
        self._first_digits = self.mmap[base:base+Sizes.first_digits_amount]
        return self._first_digits

    @property
    def mmap(self):
        """ mmap object of the file """
        if self._mmap:
            return self._mmap

        if self._file is None:
            self._file = self.path.open("r+b")

        self._mmap = mmap(self._file.fileno(), length=0, access=ACCESS_READ)
        self._mmap.madvise(MADV_SEQUENTIAL)
        return self._mmap

    def close(self):
        """ closes potentially open file and mmap object """
        if self._mmap:
            self._mmap.close()
            self._mmap = None
        if self._file:
            self._file.close()
            self._file = None

    def to_base(self, base:int|str|list[str], digits:int=-1) -> str:
        """
        convert number to a different base, this includes intpart and radix point
        raw base notation is 0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~
         - if int is provided as base parameter is will use notation[:base]. special case is -1, with that it will use the entire thing
         - if list[str] is provided as base parameter it will treat each element as a digit
         - if str is provided as base parameter there are some special cases:
           - abc -> all lower case letters
           - ABC -> lowercase + uppercase
           - alnum -> lowercase + uppercase + digits
           - anything else will be used directly, like list[str]
        """

        if digits == -1:
            digits = self.size

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
        digits_needed = ceil(digits*log(base_len,self.base))

        if self.format == "ycd":
            frac_part = ycd_to_str(memoryview(self.mmap)[self.radix_pos+1:], self.base, digits_needed)
            num_str = f"{self.intpart}.{frac_part}"
        else:
            _frac = self[:digits_needed]
            if isinstance(_frac,bytes):
                _frac = _frac.decode()
            if not isinstance(_frac, str):
                raise ValueError(f"fracpart is not type str {type(_frac)}")
            num_str = str(self.intpart) + "." + _frac
            if base == self.base:
                return num_str[:digits]

        if self.base == 16:
            num_str = hex_to_dec(num_str)

        return base_convert(num_str, base, digits)

@timer
def get_all(
    name: str | None = None,
    base: int | None = None,
    format: str | None = None,
    size: int | None = None,
    num_dir: str | Path = Paths.num_dir,
    recursive = True
):
    """ gets all BigNum with specified attributes """
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
    num_dir: str | Path = Paths.num_dir,
    recursive = True
):
    """ gets one BigNum with specified attributes """
    files = get_all(name, base, format, size, num_dir, recursive)
    if files: return files[0]
