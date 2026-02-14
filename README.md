# searches and converts "y-cruncher" outputs

mostly a wrapper for y-cruncher nums, extensive BigNum class with cool functions like ordering, subscription, iterating and stuff

searching comes in three levels:
1. database (sqlite ~1ms on a 150gb db)
2. quick: BigNum has a @property that saves 1mio digits, put the ol .find on that (~10ms worst case)
3. extensive: chunks the file and searches each chunk, by default multiprocessing + mmap, wowzers (~5s for 100gb, very diskio intensive, fast nvme reccomended)

theres a unified search function that houses all other search functions. In there you can enable/disbale database interaction as well as multiprocessing

that unified search function also adds stuff to the database if enabled and not found on there

# usage
```
>>> from scripts import *
>>> get_all()
[pi.txt(b10|50M), pi.txt(b10|1G)]
>>> set(_) # nums with different sizes are considered the same
{pi.txt(b10|50M)}

>>> pi = get_one("pi")
>>> pi[:10] # subscriptable
'1415926535'

>>> pi["5926"] # can be used for searching
4

>>> pi = get_one("pi",16,"ycd") # hex and .ycd files are fine
>>> pi[:10]
b'\xd3\x08\xa3\x85\x88j?$Ds'

>>> for d in pi: # iterable
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
```

# installation
 - `git clone https://github.com/p1geondove/irranalyze.git`
 - `cd irranalyze`
 - `uv venv`
 - `uv sync`
 - `uv run build_db.py -i` (run build_db.py -h to get a overview of arguments)
 - `uv run main.py`

 theres a settings.json to set paths of the sqlite file as well as the y-cruncher directory.
 if you run build_db.py with path to db or y-cruncher those paths will be saved into the json aswell.
 if you run build_db.py without those it will use the values from setting.json.

# TODO

- add nice tui
  - searching / listing available files
  - querying / inspecting database
  - interactive search

- add more comments, make more readable/digestable