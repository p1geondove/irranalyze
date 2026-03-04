# searches and converts "y-cruncher" outputs

mostly a wrapper for y-cruncher nums, extensive BigNum class with useful functions like ordering, subscription, iterating

searching comes in three levels:
1. database (sqlite ~1ms on a 150gb db)
2. quick: BigNum has a @property that saves 100k digits, put the ol .find on that (~200us worst case)
3. extensive: chunks the file and searches each chunk, by default multiprocessing + mmap, wowzers (~10s for 100gb, very diskio intensive, fast nvme recommended)

theres a unified search function that houses all other search functions. In there you can enable/disable database interaction as well as multiprocessing

that unified search function also adds stuff to the database if enabled and not found on there

# installation
 - install astral/uv
 - make sure you have cpython 3.14, pypy3 not reccomended sadly
 - `git clone https://github.com/p1geondove/irranalyze.git`
 - `cd irranalyze`
 - `uv venv`
 - `uv sync`
 - `uv run setup.py`

# examples
```
>>> from scripts import *
>>> get_all()
[pi.txt(b10|50M), pi.txt(b10|1G), pi.ycd(b16|415.24M)]
>>> set(_) # nums with different sizes are considered the same
{pi.txt(b10|50M), pi.ydc(b16|415.25M)}
>>> pi = get_one("pi")
>>> pi[:10] # subscriptable
'1415926535'
>>> pi["15926",slice(None,-13,-2)] # searching and slicing
[2, b'954521']
>>> pi[b"123","456"] # multi string search is more efficient
{b'123': 1924, b'456': 251}

>>> Switches.one_indexed = False # if you search for 1 it will return 0 now instead of 1
>>> pi["1"] # however this has already been saved in the db
1
>>> Paths.sqlite_path.unlink() # so before toggleing indexing mode reset the db
>>> pi["1"] # caching always comes at an expense...
0

>>> pi = get_one("pi",16,"ycd") # hex and .ycd files are fine
>>> pi[0]
b'\x00'
>>> for d in pi: # iterable, wrapper to iter(mmap), yields individual bytes
...     print(d)
b'\x00'
b'\xd3'
b'\x08'
b'\xa3'
b'\x85'
[...]

>>> pi.to_base(10, digits=10) # base conversion
'3.14159265'
>>> pi.to_base("alnum", digits=10) # predefined special bases
'3.8UYOxDus'
>>>pi.to_base("😀😃😄😁😆😅😂🙃😉😊😇😍😘😗😚😙😋😛😜😝",digits=20) # or custom
'😁.😄😋😘😚😋😊😋😍😛😝😊😗😄😃😛😜😛😍'

>>> pi.intpart # saves the int part as int
3
>>> pi.size # filesize - position of radix
415244091
>>> pi.first_digits # caches some digits
b'\x00\xd3\x08\xa3\x85\x88j?$D...
>>> pi.mmap # can also be accessed
<mmap.mmap closed=False, access=ACCESS_READ, length=415244288, pos=0, offset=0>

>>> txt_to_num("number") # some other functions
'132012010417'
>>> num_to_txt(_.encode()) # those keep the input datatype
b'number'
>>> txt_to_num_all(_) # there are many different representations when you convert like this
<generator object txt_to_num_all at 0x23bc3b3d5c0>
>>> len(list(_))
4096

>>> res = pi[txt_to_num_all("number")] # takes 1:30 min:sec
>>> res = pi[txt_to_num_all("number")] # takes 6.13 ms since its now in the database
>>> sorted(((pat,pos) for pat,pos in res.items() if pos!=-1), key=lambda x:x[1]) # sort the ones that are found
[(b'919864278217', 901428513)]
```

# todo
 - implement aho-corasick algorithm for multi_search
 - add functionality:
   - find streak
   - find street
