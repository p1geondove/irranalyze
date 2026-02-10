# searches and converts "y-cruncher" outputs

mostly a wrapper for y-cruncher nums, extensive BigNum class with cool functions like ordering, subscription, iterating and stuff

searching comes in three levels:
1. database (sqlite ~1ms on a 150gb db)
2. quick: BigNum has a @property that saves 1mio digits, put the ol .find on that (~10ms worst case)
3. extensive: chunks the file and searches each chunk, by default multiprocessing + mmap, wowzers (~5s for 100gb, very diskio intensive, fast nvme reccomended)

theres a unified search function that houses all other search functions. In there you can enable/disbale database interaction as well as multiprocessing

that unified search function also adds stuff to the database if enabled and not found on there

# expected values:
### pi:
| position    | string    |
|-------------|-----------|
|           1 | 1         |
|         148 | 12        |
|       1_924 | 123       |
|      13_807 | 1234      |
|      49_702 | 12345     |
|   2_458_885 | 123456    |
|   9_470_344 | 1234567   |
| 186_557_266 | 12345678  |
| 523_551_502 | 123456789 |
|          94 | 11        |
|         153 | 111       |
|      12_700 | 1111      |
|      32_788 | 11111     |
|     255_945 | 111111    |
|   4_657_555 | 1111111   |
| 159_090_113 | 11111111  |
| 812_432_526 | 111111111 |
|         762 | 999999    |
|   1_722_776 | 9999999   |

look a christmas tree :)

stuff is one indexed to align with this website: https://www.angio.net/pi/ 

# TODO
- write convert.py
  - convert.base(file:Path,base:int|str) -> str
    - can take either a number or a string, where the string is the custom base notation
    - maybe make it a generator
    - maybe make it fixed length

  - convert.num_to_text(num:str) -> str
    - takes something like '000102' and turn it to 'abc'

  - convert.text_to_num(txt:str) -> str
    - takes something like 'abc' and turns it to '000102'

- clean up build.py
  - argparse
    - files directory, maybe single file aswell
    - max length
    - single/multithreaded switch
  - figure out if multithreaded makes sense
    - fighting for lock
    - increase patterns per puts
    - use better db lol

- add nice tui
  - searching / listing available files
  - querying / inspecting database
  - interactive search

- add more comments, make more readable/digestable
- write more sensible readme, be less autistic

### this is giga stupid what am i doing with my life
#### hey thats highlited as green in my editor, i really like this green
##### omg that purple :3, even cooler lol