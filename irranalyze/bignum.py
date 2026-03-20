# bignum.py - wrapper for number files

from pathlib import Path
from functools import total_ordering
from mmap import mmap, ACCESS_READ, MADV_SEQUENTIAL
from math import log, ceil
from typing import Iterable, Iterator, overload

from .search import search
from .identify import identify, check_valid
from .convert import base_convert, resolve_notation, ycd_to_str
from .helper import format_size
from .var import Sizes, Paths, Switches

@total_ordering
class BigNum:
    """ wrapper for y-cruncher file to get matadata, search and iterate"""
    def __init__(self, path:str|Path) -> None:
        self.path = Path(path)
        if not (self.path.exists() and check_valid(self.path)):
            raise AttributeError("Provided file path is not a number file")
        self.info = identify(self.path)
        self._first_digits = None # lazy loaded because it can be big
        self._key = (self.info.name, self.info.base, self.info.format) # static key
        self._hash = hash(self._key) # also static hash
        self._file = None
        self._mmap = None

    def __repr__(self) -> str:
        """ eg pi.txt(dec|50M) """
        return f"{self.info.name}.{self.info.format}(b{self.info.base}|{format_size(self.info.file_size,capitalized=True)})"

    def __len__(self) -> int:
        """ returns amount of bytes after radix"""
        return self.info.file_size

    @overload
    def __getitem__(self, i:int) -> bytes: ...
    @overload
    def __getitem__(self, i:slice) -> bytes: ...
    @overload
    def __getitem__(self, i:str) -> int: ...
    @overload
    def __getitem__(self, i:bytes) -> int: ...
    @overload
    def __getitem__(self, i:Iterable[int]) -> list[bytes]: ...
    @overload
    def __getitem__(self, i:Iterable[slice]) -> list[bytes]: ...
    @overload
    def __getitem__(self, i:Iterable[str|bytes]) -> dict[bytes,int]: ...

    def __getitem__(self, i):
        """ just as the search function this is 1-indexed, ergo [0] is always '.', but slices like [:10] dont include the dot. Can also be used as a search proxy if input is str|bytes """
        if isinstance(i, int):
            if -1 < i < Sizes.first_digits_amount:
                return bytes((self.first_digits[i],))
            if i > -1:
                i += self.info.radix_pos+1-Switches.one_indexed
            return bytes((self.mmap[i],))

        if isinstance(i, slice):
            if i.stop and -1 < i.stop < Sizes.first_digits_amount:
                return self.first_digits[i]
            base = self.info.radix_pos + 1 - Switches.one_indexed
            virtual_len = len(self.mmap) - base
            start, stop, step = i.indices(virtual_len)
            return self.mmap[base+start:base+stop:step]

        if isinstance(i, str):
            return search(self, i.encode())

        if isinstance(i, bytes):
            return search(self, i)

        if isinstance(i, Iterable):
            funcs = {
                str:lambda x:x.encode(),
            }
            elements = [funcs.get(type(e),lambda x:x)(e) for e in i]
            if all(isinstance(e, bytes) for e in elements):
                return search(self, elements)
            return [self[e] for e in elements]

    def __iter__(self) -> Iterator[bytes]:
        """ yields digits as bytes, radix is never included no matter the state of Switches.one_indexed"""
        i = iter(self.mmap)
        for _ in range(self.info.radix_pos+1):
            next(i)
        yield from i # no pyright, this is not a Generator[int], mmap always returns single bytes: github.com/python/cpython/issues/70546 # type:ignore

    def __contains__(self, pattern:str|bytes) -> bool:
        """ should technically always return true, but its for the limited file only :P """
        if isinstance(pattern, str):
            pattern = pattern.encode()
        return search(self, pattern) != -1

    def __hash__(self) -> int:
        return self._hash

    def __lt__(self, other: object, /) -> bool:
        if not isinstance(other, BigNum):
            return NotImplemented

        if self.info.name != other.info.name:
            return self.info.name < other.info.name

        if self.info.format != other.info.format:
            return self.info.format < other.info.format

        if self.info.base != other.info.base:
            return self.info.base < other.info.base

        return self.info.file_size < other.info.file_size

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

    def __exit__(self):
        self.close()

    def __buffer__(self, flags):
        return self.mmap.__buffer__(flags)

    @property
    def first_digits(self) -> bytes:
        """ small section of the number, usually 1mio digits after radix """
        if self._first_digits:
            return self._first_digits
        base = self.info.radix_pos + 1 - Switches.one_indexed
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

    def to_base(self, base:int|str, digits:int=-1) -> str:
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
            digits = self.info.file_size

        base_notation, _ = resolve_notation(base)
        digits_needed = ceil(digits*log(len(base_notation),self.info.base))

        if self.info.format == "ycd":
            frac_part = ycd_to_str(memoryview(self)[self.info.radix_pos+1:], self.info.base, digits_needed)
        else:
            frac_part = self[:digits_needed].decode()

        num_str = f"{self.info.int_part}.{frac_part}"

        if base == self.info.base:
            return num_str[:digits]

        return base_convert(num_str,self.info.base,base)[:digits]

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
    if name:   files = filter(lambda file: file.info.name == name, files)
    if base:   files = filter(lambda file: file.info.base == base, files)
    if format: files = filter(lambda file: file.info.format == format, files)
    if size:   files = filter(lambda file: file.info.file_size == size, files)
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
