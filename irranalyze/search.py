# search.py - various search methods
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .bignum import BigNum

import sqlite3
import hyperscan

from .var import Paths, Switches

def search_file(bignum:BigNum, patterns:list[bytes], lower_bound:int|None = None, upper_bound:int|None = None) -> dict[bytes,int]:
    def match_handler(id:int, start:int, stop:int, flags:int, context=None):
        pat = id_pattern_map[id]
        positions[id_pattern_map[id]] = stop - len(pat) + Switches.one_indexed - 1 + offset_bounds

    # bounds and sizes
    lower_bound = lower_bound if lower_bound is not None else bignum.info.radix_pos
    upper_bound = upper_bound if upper_bound is not None else bignum.info.file_size
    offset_bounds = lower_bound - bignum.info.radix_pos
    bounds_size = upper_bound - lower_bound
    block_size = 2**32-1
    block_mode = bounds_size <= block_size
    print(f"{lower_bound=} {upper_bound=}")

    # hyperscan db setup
    id_pattern_map = {id:pat for id,pat in enumerate(patterns)}
    positions = {p:-1 for p in patterns}
    #scratch = hyperscan.Scratch()
    if block_mode:
        print("scanning using block mode")
        db = hyperscan.Database(mode=hyperscan.HS_MODE_BLOCK)
    else:
        print("scanning using stream mode")
        db = hyperscan.Database(mode=hyperscan.HS_MODE_VECTORED)
    ids = list(range(len(patterns)))
    flags = [hyperscan.HS_FLAG_SINGLEMATCH] * len(patterns)
    db.compile(expressions=patterns, ids=ids, elements=len(patterns), flags=flags)

    mv = memoryview(bignum.mmap)
    print(f"before scanning: {mv.c_contiguous=} {mv.contiguous=}")
    if block_mode:
        print(f"block size for block mode: {len(mv) = }")
        db.scan(mv, match_handler)
    else:
        blocks = [mv[i:i+block_size] for i in range(0,bounds_size,block_size)]
        print(f"blocks size for vector mode: {[len(b) for b in blocks] = }")
        db.scan(blocks, match_handler)
        for b in blocks:
            b.release()
    mv.release()

    return positions

def search_db_single(bignum:BigNum, pattern:bytes) -> int|None:
    """ very quick but limited search, only returns whats stored in the db """
    conn = sqlite3.connect(Paths.sqlite_path)
    cursor = conn.cursor()
    table_exists = bool(cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (bignum.info.table_name, )).fetchone())
    if not table_exists:
        conn.close()
        return None
    cursor.execute(f"""SELECT position FROM "{bignum.info.table_name}" WHERE string = ? ORDER BY position ASC LIMIT 1""", (pattern,))
    result = cursor.fetchone()
    conn.close()
    if isinstance(result,tuple|list):
        result = result[0]
    return result

def search_db_multi(bignum:BigNum, patterns:list[bytes]) -> dict[bytes,int|None]:
    conn = sqlite3.connect(Paths.sqlite_path)
    cursor = conn.cursor()
    table_exists = bool(cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (bignum.info.table_name, )).fetchone())
    if not table_exists:
        conn.close()
        return {p:None for p in patterns}
    query = f"""WITH search_list(pattern) AS (VALUES (?) {', (?)'*(len(patterns)-1)}) SELECT s.pattern, MIN(t.position) FROM search_list s LEFT JOIN "{bignum.info.table_name}" t ON s.pattern = t.string GROUP BY s.pattern"""
    result = cursor.execute(query,patterns).fetchall()
    conn.close()
    return {pat:pos for pat,pos in result}

def search_single(bignum:BigNum, pattern:bytes):
    position = search_db_single(bignum, pattern)

    if position is not None:
        return position

    lower_bound = None
    upper_bound = None

    if len(pattern) > 1:
        part_found = search_db_multi(bignum, [pattern[:n] for n in range(1,len(pattern))]) # check all patterns smaller than wanted pattern
        part_found = filter(lambda x:x[1], part_found.items()) # filter out all None, we care about found and not presnt only
        part_found = sorted(part_found, key=lambda x:len(x[0])) # exctract the last known position, we sort to get the closest sub pattern to our current pattern
        if part_found:
            canidate = part_found[-1][1]
            if canidate == -1: # if the pattern with the last char missing is not in file, then current pattern cant be in file either
                add_to_db(bignum, {pattern:-1})
                return -1

            lower_bound = canidate # if we do have a position from sub pattern, than we can use that as lower bound

        # upper bound
        if bignum.info.format == "ycd":
            possible_chars = [bytes((i,)) for i in range(256)]
        else:
            if bignum.info.base == 10:
                possible_chars = [b"0",b"1",b"2",b"3",b"4",b"5",b"6",b"7",b"8",b"9"]
            else:
                possible_chars = [b"0",b"1",b"2",b"3",b"4",b"5",b"6",b"7",b"8",b"9",b"a",b"b",b"c",b"d",b"e",b"f"]

        super_patterns = [pattern+c for c in possible_chars] + [c+pattern for c in possible_chars]
        part_found = search_db_multi(bignum, super_patterns)
        part_found = filter(lambda x:x[1] is not None and x[1] != -1, part_found.items()) # filter out the ones that are not recorded or not present
        part_found = sorted(part_found, key=lambda x:x[1]) # pyright has some issues here again since it thinks that there still None in there which you cant compare against ints, but i just filtered the omg... # type:ignore
        if part_found:
            upper_bound = part_found[0][1]

    position_dict = search_file(bignum,[pattern], lower_bound, upper_bound)
    add_to_db(bignum, position_dict)
    return position_dict[pattern]

def search_multi(bignum:BigNum, patterns:list[bytes]) -> dict[bytes,int]:
    positions_db = search_db_multi(bignum, patterns) # first search db, will return {pattern:pos} where pos can be int or None, if pos is None it means its not recorded at all, -1 means reported not in file and anything >-1 is regular position
    missing_db = [pat for pat,pos in positions_db.items() if pos is None] # make a set of the patterns that return None / are not recorded
    if not missing_db: # if there arent any missing then we found everything
        return positions_db # return {pat:pos}, pyright says error here since it thinks we try to return {bytes:int|None} while its only {bytes:int} since we calculated missing_db which hosts all None, but that was empty so there are no None -> all int # type:ignore
    positions_db_safe = {pat:pos for pat,pos in positions_db.items() if pos is not None}
    positions_file = search_file(bignum, missing_db) # some are missing, so we first do a quick search
    add_to_db(bignum,positions_file)
    positions_db_safe.update(positions_file)
    return positions_db_safe

def add_to_db(bignum:BigNum, patterns:dict[bytes,int]):
    if bignum.info.name == "unknown": # if the file is unknown
        return # dont do anything

    # with sqlite3.connect(Paths.sqlite_path) as conn: # connection to the db
    conn =sqlite3.connect(Paths.sqlite_path) # connection to the db
    cursor = conn.cursor() # cursor db thingy
    table_exists = bool(cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (bignum.info.table_name, )).fetchone()) # bool wether table exists

    if not table_exists: # is that table doesnt exist
        cursor.execute(f"""CREATE TABLE "{bignum.info.table_name}" (string BLOB PRIMARY KEY, position INTEGER)""") # just make it lol

    patterns = {pat:pos for pat,pos in patterns.items() if not pos is None}
    if Switches.report_not_found: # add -1 to table to signal thats not there?
        patterns_new = [(pat,pos) for pat,pos in patterns.items()] # convert patterns dict to list
    else: # or leave it open, maybe user add bigger number file to find pattern
        patterns_new = [(pat,pos) for pat,pos in patterns.items() if pos != -1] # convert patterns dict to list, but only the ones that are found (!=-1)

    cursor.executemany(f"""INSERT OR IGNORE INTO "{bignum.info.table_name}" VALUES (?, ?)""", patterns_new) # insert all
    conn.commit() # yeah...
    conn.close()

def search(bignum:BigNum, pattern:bytes|list[bytes]):
    if isinstance(pattern,bytes):
        return search_single(bignum, pattern)
    elif isinstance(pattern,list):
        pattern = list(map(bytes, pattern))
        return search_multi(bignum, pattern)
    print("WARN: Search pattern must either be bytes or list of bytes")

