# searches and converts "y-cruncher" outputs

mostly a wrapper for y-cruncher nums, extensive BigNum class with cool functions like ordering, subscription, iterating and stuff

searching comes in three levels:
1. database (sqlite ~1ms on a 150gb db)
2. quick: BigNum has a @property that saves 1mio digits, put the ol .find on that (~10ms worst case)
3. extensive: chunks the file and searches each chunk, by default multiprocessing + mmap, wowzers (~5s for 100gb, very diskio intensive, fast nvme recommended)

theres a unified search function that houses all other search functions. In there you can enable/disable database interaction as well as multiprocessing

that unified search function also adds stuff to the database if enabled and not found on there

# usage
```
>>> from scripts import *
>>> get_all()
[pi.txt(b10|50M), pi.txt(b10|1G), pi.ycd(b16|415.24M)]
>>> set(_) # nums with different sizes are considered the same
{pi.txt(b10|50M)}

>>> pi = get_one("pi")
>>> pi[:10] # subscriptable
'1415926535'

>>> pi["5926"] # can be used for searching
4
>>> pi[b"123",b"456"] # multi string search is more efficient
{b'123': 1924, b'456': 251}

>>> pi = get_one("pi",16,"ycd") # hex and .ycd files are fine
>>> piy[0] # ints are zero indexed, slices are one indexed
'Ó'

>>> for d in pi: # iterable, wrapper to iter(mmap)
...     print(d)
b'\xd3'
b'\x08'
b'\xa3'
b'\x85'
[...]

>>> pi.to_base(10, digits=10) # base conversion
'3.14159265'

>>> pi.to_base("alnum", digits=10) # predefined special bases
'3.8UYOxDus'

pi.to_base("😀😃😄😁😆😅🤣😂🙂🙃🫠😉😊😇🥰😍🤩😘😗☺️😚😙🥲😋😛😜🤪😝",digits=50) # or custom
'😁.😆😁😄🙂🥲😀😊☺😜😙☺😜😊😉🙃😗😆😂😉🥰😜🫠🥰😘🙃🥲😂🤪😜😀😛😉😊😋😆😆🙂😄😊😛😗️😇🫠☺😗😊️'

>>> txt_to_num("number") # some other functions
'132012010417'
>>> num_to_txt(_.encode()) # those keep the input datatype
b'number'
>>> txt_to_num_all(_) # there are many different representations when you convert like this
<generator object txt_to_num_all at 0x23bc3b3d5c0>
>>> len(list(_))
4096

>>> res = pi[txt_to_num_all("number")] # lets have some fun :)
>>> len(res) = 4096 # this is a dict[bytes,int], returns all patterns, but ones not found are -1
>>> sorted(((pat,pos) for pat,pos in res.items() if pos!=-1), key=lambda x:x[1]) # sort the ones that are found
[(b'919864278217', 901428513)]
```

# installation
 - `git clone https://github.com/p1geondove/irranalyze.git`
 - `cd irranalyze`
 - `uv venv`
 - `uv sync`
 - open setting.json and edit `NUM_DIR` to point to your number directory
 - `uv run build_db.py -i` (run build_db.py -h to get a overview of arguments)
 - `uv run main.py`

 theres a settings.json to set paths of the sqlite file as well as the y-cruncher directory.
 if you run build_db.py with path to db or y-cruncher those paths will be saved into the json as well.
 if you run build_db.py without those it will use the values from setting.json.

# TODO

- add nice tui
  - searching / listing available files
  - querying / inspecting database
  - interactive search

- add more comments, make more readable
- add open ended setting: report not found to db by default
