# search.py - various search methods

import sqlite3
from mmap import mmap, ACCESS_READ, MADV_SEQUENTIAL
import hyperscan

from .identify import BigNumInfo
from .var import Paths, Switches

def search_file(file_info:BigNumInfo, patterns:list[bytes], lower_bound:int|None = None, upper_bound:int|None = None) -> dict[bytes,int]:
    def match_handler(id:int, from_:int, to:int, flags:int, context=None):
        pat = id_pattern_map[id]
        positions[id_pattern_map[id]] = to - len(pat) + Switches.one_indexed - 1 + offset_bounds + offset_chunk

    # bounds and sizes
    lower_bound = lower_bound if lower_bound is not None else file_info.radix_pos
    upper_bound = upper_bound if upper_bound is not None else file_info.file_size
    offset_bounds = lower_bound - file_info.radix_pos
    bounds_size = upper_bound - lower_bound
    chunk_size = 2**30
    block_mode = bounds_size < 2**32

    # hyperscan db setup
    id_pattern_map = {id:pat for id,pat in enumerate(patterns)}
    positions = {p:-1 for p in patterns}
    scratch_space = hyperscan.Scratch()
    db = hyperscan.Database(scratch_space, hyperscan.HS_MODE_BLOCK) # id like to use vector mode for big files
    ids = list(range(len(patterns)))
    flags = [hyperscan.HS_FLAG_SINGLEMATCH] * len(patterns)
    db.compile(patterns, ids, flags=flags) 

    with file_info.path.open("r+b") as f:
        with mmap(f.fileno(), length=file_info.file_size, access=ACCESS_READ) as mm:
            mm.madvise(MADV_SEQUENTIAL)
            mv = memoryview(mm)[lower_bound:upper_bound]

            if block_mode:
                offset_chunk = 0
                db.scan(mv, match_handler)
            else:
                # since python-hyperscan doesnt allow for blocks bigger than 4gib and vector / stream mode is bugged i have to fix their issue in python by chunking and runnign each chunk in block mode
                # funnily enough underlying hyperscan also doesnt allow for blocks bigger than 4gib, unsigned long long are used in vector and streaming mode, but the length of blocks cant be bigger than 4gib, even tho they could i think, maybe fseek ftell legacy issue...
                for offset_chunk in range(0, bounds_size, chunk_size):
                    chunk = mv[offset_chunk : offset_chunk + chunk_size]
                    db.scan(chunk, match_handler)
                    chunk.release()
            mv.release()

    return positions

def search_db_single(file_info:BigNumInfo, pattern:bytes) -> int|None:
    """ very quick but limited search, only returns whats stored in the db """
    conn = sqlite3.connect(Paths.sqlite_path)
    cursor = conn.cursor()
    table_exists = bool(cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (file_info.table_name, )).fetchone())
    if not table_exists:
        conn.close()
        return None
    cursor.execute(f"""SELECT position FROM "{file_info.table_name}" WHERE string = ? ORDER BY position ASC LIMIT 1""", (pattern,))
    result = cursor.fetchone()
    conn.close()
    if isinstance(result,tuple|list):
        result = result[0]
    return result

def search_db_multi(file_info:BigNumInfo, patterns:list[bytes]) -> dict[bytes,int|None]:
    conn = sqlite3.connect(Paths.sqlite_path)
    cursor = conn.cursor()
    table_exists = bool(cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (file_info.table_name, )).fetchone())
    if not table_exists:
        conn.close()
        return {p:None for p in patterns}
    query = f"""WITH search_list(pattern) AS (VALUES (?) {', (?)'*(len(patterns)-1)}) SELECT s.pattern, MIN(t.position) FROM search_list s LEFT JOIN "{file_info.table_name}" t ON s.pattern = t.string GROUP BY s.pattern"""
    result = cursor.execute(query,patterns).fetchall()
    conn.close()
    return {pat:pos for pat,pos in result}

def search_single(file_info:BigNumInfo, pattern:bytes):
    position = search_db_single(file_info, pattern)

    if position is not None:
        return position

    lower_bound = None
    upper_bound = None

    if len(pattern) > 1:
        part_found = search_db_multi(file_info, [pattern[:n] for n in range(1,len(pattern))]) # check all patterns smaller than wanted pattern
        part_found = filter(lambda x:x[1], part_found.items()) # filter out all None, we care about found and not presnt only
        part_found = sorted(part_found, key=lambda x:len(x[0])) # exctract the last known position, we sort to get the closest sub pattern to our current pattern
        if part_found:
            canidate = part_found[-1][1]
            if canidate == -1: # if the pattern with the last char missing is not in file, then current pattern cant be in file either
                add_to_db(file_info,{pattern:-1})
                return -1

            lower_bound = canidate # if we do have a position from sub pattern, than we can use that as lower bound

        # upper bound
        if file_info.format == "ycd":
            possible_chars = [bytes((i,)) for i in range(256)]
        else:
            if file_info.base == 10:
                possible_chars = [b"0",b"1",b"2",b"3",b"4",b"5",b"6",b"7",b"8",b"9"]
            else:
                possible_chars = [b"0",b"1",b"2",b"3",b"4",b"5",b"6",b"7",b"8",b"9",b"a",b"b",b"c",b"d",b"e",b"f"]

        super_patterns = [pattern+c for c in possible_chars] + [c+pattern for c in possible_chars]
        part_found = search_db_multi(file_info, super_patterns)
        part_found = filter(lambda x:x[1] is not None and x[1] != -1, part_found.items()) # filter out the ones that are not recorded or not present
        part_found = sorted(part_found, key=lambda x:x[1]) # pyright has some issues here again since it thinks that there still None in there which you cant compare against ints, but i just filtered the omg... # type:ignore
        if part_found:
            upper_bound = part_found[0][1]

    position_dict = search_file(file_info,[pattern], lower_bound, upper_bound)
    add_to_db(file_info, position_dict)
    return position_dict[pattern]

def search_multi(file_info:BigNumInfo, patterns:list[bytes]) -> dict[bytes,int]:
    positions_db = search_db_multi(file_info, patterns) # first search db, will return {pattern:pos} where pos can be int or None, if pos is None it means its not recorded at all, -1 means reported not in file and anything >-1 is regular position
    missing_db = [pat for pat,pos in positions_db.items() if pos is None] # make a set of the patterns that return None / are not recorded
    if not missing_db: # if there arent any missing then we found everything
        return positions_db # return {pat:pos}, pyright says error here since it thinks we try to return {bytes:int|None} while its only {bytes:int} since we calculated missing_db which hosts all None, but that was empty so there are no None -> all int # type:ignore
    positions_db_safe = {pat:pos for pat,pos in positions_db.items() if pos is not None}
    positions_file = search_file(file_info, missing_db) # some are missing, so we first do a quick search
    add_to_db(file_info,positions_file)
    positions_db_safe.update(positions_file)
    return positions_db_safe

def add_to_db(file_info:BigNumInfo, patterns:dict[bytes,int]):
    if file_info.name == "unknown": # if the file is unknown
        return # dont do anything

    # with sqlite3.connect(Paths.sqlite_path) as conn: # connection to the db
    conn =sqlite3.connect(Paths.sqlite_path) # connection to the db
    cursor = conn.cursor() # cursor db thingy
    table_exists = bool(cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (file_info.table_name, )).fetchone()) # bool wether table exists

    if not table_exists: # is that table doesnt exist
        cursor.execute(f"""CREATE TABLE "{file_info.table_name}" (string BLOB PRIMARY KEY, position INTEGER)""") # just make it lol

    patterns = {pat:pos for pat,pos in patterns.items() if not pos is None}
    if Switches.report_not_found: # add -1 to table to signal thats not there?
        patterns_new = [(pat,pos) for pat,pos in patterns.items()] # convert patterns dict to list
    else: # or leave it open, maybe user add bigger number file to find pattern
        patterns_new = [(pat,pos) for pat,pos in patterns.items() if pos != -1] # convert patterns dict to list, but only the ones that are found (!=-1)

    cursor.executemany(f"""INSERT OR IGNORE INTO "{file_info.table_name}" VALUES (?, ?)""", patterns_new) # insert all
    conn.commit() # yeah...
    conn.close()

def search(file_info:BigNumInfo, pattern:bytes|list[bytes]):
    if isinstance(pattern,bytes):
        return search_single(file_info, pattern)
    elif isinstance(pattern,list):
        pattern = list(map(bytes, pattern))
        return search_multi(file_info, pattern)
    print("WARN: Search pattern must either be bytes or list of bytes")

