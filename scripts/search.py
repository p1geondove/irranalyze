import os
import math
import sqlite3
from typing import Iterable
from pathlib import Path
from mmap import mmap, ACCESS_READ, MADV_SEQUENTIAL
from multiprocessing import Process, Value, Array

from .const import CHUNK_SIZE, FIRST_DIGITS_AMOUNT, PAGE_SIZE, SQLITE_PATH, MAX_PROCESSES
from .identify import identify, get_table_name
from .helper import timer

def search_st(file:Path, pattern:bytes) -> int:
    """ simple single threaded search, semi fast but safe and can search any filesize """
    _,_,_,_,radix = identify(file)
    last_chunk = b""
    chunk_number = -1
    with file.open("rb") as f:
        chunk = f.read(CHUNK_SIZE)
        while chunk:
            position = (last_chunk + chunk).find(pattern)
            if position != -1:
                if chunk_number == -1:
                    return position - radix
                return position + chunk_number * CHUNK_SIZE - radix
            last_chunk = chunk
            chunk_number += 1
            chunk = f.read(CHUNK_SIZE)
    return -1

def multi_search_st(file:Path, patterns:list[bytes]) -> dict[bytes,int]:
    _,_,_,_,radix = identify(file)
    patterns_left = patterns.copy()
    positions = {p:-1 for p in patterns}
    chunk_number = -1
    last_chunk = b""

    with file.open("rb") as f:
        chunk = f.read(CHUNK_SIZE)
        while chunk and patterns_left:
            to_remove = set()
            search_space = last_chunk + chunk

            for pattern in patterns_left:
                pos = search_space.find(pattern)
                if pos != -1:
                    to_remove.add(pattern)
                    if chunk_number == -1:
                        positions[pattern] = pos - radix
                    else:
                        positions[pattern] = pos - radix + chunk_number * CHUNK_SIZE

            for pattern in to_remove:
                patterns_left.remove(pattern)

            chunk_number += 1
            last_chunk = chunk
            chunk = f.read(CHUNK_SIZE)
    return positions

def _serach_mp(file:Path, pattern:bytes, sector:tuple[int,int], position_val):
    """ worker method to search_mp """
    sector_start, sector_end = sector
    sector_size = sector_end - sector_start
    pattern_length = len(pattern)
    chunk_start = 0
    position = -1

    with file.open("r+b") as f:
        with mmap(f.fileno(), length=sector_size, offset=sector_start, access=ACCESS_READ) as mm:
            mm.madvise(MADV_SEQUENTIAL)
            while chunk_start < sector_size:
                chunk_end = chunk_start + CHUNK_SIZE 
                position = mm.find(pattern, chunk_start, chunk_end)

                if position != -1:
                    break

                if position_val.value != -1 and position_val.value < sector_start:
                    return

                chunk_start = chunk_end - pattern_length

    if position == -1:
        return

    position += sector_start
    if position < position_val.value or position_val.value == -1:
        position_val.value = position

def search_mp(file:Path, pattern:bytes, num_workers:int=MAX_PROCESSES) -> int:
    """ multiprocessing approach, fast but expensive and potentially lots of overhead """
    num_workers = max(1,  num_workers or os.cpu_count() or 1)
    _,_,_,_,radix_pos = identify(file)
    num_size = file.stat().st_size - radix_pos
    sector_size = math.ceil(num_size/num_workers) // PAGE_SIZE * PAGE_SIZE
    sectors = []

    for i in range(num_workers):
        start = i*sector_size
        if start >= num_size: break
        end = min(start + sector_size + len(pattern), num_size)
        sectors.append([start,end])
    sectors[-1][1] = num_size

    position = Value("q", -1)
    processes:list[Process] = []

    for sector in sectors:
        p = Process(target=_serach_mp, args=(file, pattern, sector, position))
        processes.append(p)

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    return -1 if position.value==-1 else position.value - radix_pos

def _multi_search_mp(file:Path, patterns:list[bytes], sector:tuple[int,int], found_array):
    _,_,_,_,radix_pos = identify(file)
    sector_start, sector_end = sector # put start end end into seperate variables
    sector_size = sector_end - sector_start # determins sectro size for mmap(length=...)
    pattern_length = max(len(pattern) for pattern in patterns) # overlap chunks by this amount
    chunk_start = 0 # used for checking bounds and mmap.find()
    patterns_left = patterns.copy() # patterns=all patterns, patterns_left=patterns - the ones we found
    order = {p:i for i,p in enumerate(patterns)} # for found_array so we dont have to do patterns.index(pattern)

    with file.open("r+b") as f: # open file
        with mmap(f.fileno(), length=sector_size, offset=sector_start, access=ACCESS_READ) as mm: # make mmap object
            mm.madvise(MADV_SEQUENTIAL) # havent tested, but should make reading faster
            while chunk_start < sector_size and patterns_left: # check we are within sector and have patterns left for searching
                chunk_end = chunk_start + CHUNK_SIZE # determine bounds of chunk
                to_remove = set() # a temporary set of found patterns to be removed

                for pattern in patterns_left: # iterate over all patterns in need of finding
                    position = mm.find(pattern, chunk_start, chunk_end) # try to find pattern

                    if position != -1: # found in chunk
                        abs_pos = position + sector_start - radix_pos
                        idx = order[pattern] # get index of the pattern in found_array
                        with found_array: # lock the found_array
                            pos = found_array[idx] # get stored pos from found_array
                            if pos==-1 or pos > abs_pos: # if pattern is not found or my finding is better/earlier
                                found_array[idx] = abs_pos # store the pos (mm.find() alignes with offset/sector_start)
                                to_remove.add(pattern) # add that pattern to be removed


                # syncronize patterns_left to other processes / found_array
                for pattern in patterns_left: # only bother to check unfound patterns
                    with found_array: # lock the found_array
                        pos = found_array[order[pattern]] # what position in does found_array report for that pattern?
                        if pos!=-1 and pos<sector_start: # if that pattern is found and the position is earlier than what i can do
                            to_remove.add(pattern)

                # actually remove all found patterns from patterns_left
                for pattern in to_remove: # get all found patterns
                    patterns_left.remove(pattern) # remove the pattern

                # determine chunk bounds
                chunk_start = chunk_end - pattern_length

def multi_search_mp(file:Path, patterns:list[bytes], num_workers:int=MAX_PROCESSES) -> dict[bytes,int]:
    """ multiprocessing approach, fast but expensive and potentially lots of overhead """
    num_workers = max(1,  num_workers or os.cpu_count() or 1)
    _,_,_,_,radix_pos = identify(file)
    num_size = file.stat().st_size - radix_pos
    sector_size = math.ceil(num_size/num_workers) // PAGE_SIZE * PAGE_SIZE
    sectors = []

    for i in range(num_workers):
        start = i*sector_size
        if start >= num_size: break
        end = min(start + sector_size + max(len(p) for p in patterns), num_size)
        sectors.append([start,end])
    sectors[-1][1] = num_size

    found_array = Array("q",[-1]*len(patterns))
    processes:list[Process] = []

    for sector in sectors:
        p = Process(target=_multi_search_mp, args=(file, patterns, sector, found_array))
        processes.append(p)

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    return {pattern:pos for pattern,pos in zip(patterns,found_array)}

def search_quick(file:Path, pattern:bytes) -> int:
    """ low latency search, but only first couple digits """
    _,_,_,_,radix_pos = identify(file)
    with file.open("rb") as f:
        f.seek(radix_pos)
        return f.read(FIRST_DIGITS_AMOUNT).find(pattern)

def multi_search_quick(file:Path, patterns:list[bytes]) -> dict[bytes,int]:
    _,_,_,_,radix_pos = identify(file)
    with file.open("rb") as f:
        f.seek(radix_pos)
        chunk = f.read(FIRST_DIGITS_AMOUNT)
    return {p:chunk.find(p) for p in patterns}

def search_db(file:Path, pattern:bytes) -> int:
    """ very quick but limited search, only returns whats stored in the db """
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    table_name = get_table_name(file)
    table_exists = bool(cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name, )).fetchone())
    if not table_exists: return -1
    cursor.execute(f"""SELECT position FROM "{table_name}" WHERE string = ? ORDER BY position ASC LIMIT 1""", (pattern,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return -1

def multi_search_db(file:Path, patterns:list[bytes]|tuple[bytes]) -> dict[bytes,int]:
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    table_name = get_table_name(file)
    table_exists = bool(cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name, )).fetchone())
    if not table_exists: return  {p:-1 for p in patterns}
    query = f"""WITH search_list(pattern) AS (VALUES (?) {', (?)'*(len(patterns)-1)}) SELECT s.pattern, MIN(t.position) FROM search_list s LEFT JOIN "{table_name}" t ON s.pattern = t.string GROUP BY s.pattern"""
    positions = cursor.execute(query,patterns).fetchall()
    return {pat:(pos if pos else -1) for pat,pos in positions}

def _search(file:Path, pattern:bytes, database:bool=True, multithreaded:bool=True):
    """ main search method combines all search methods and potentially fills the database with missing data """
    position = -1

    # 1. check the db if allowed
    if database:
        position = search_db(file, pattern)
        if position != -1:
            return position

    # 2. conventinal search
    # 2.1 always check quicksearch, only takes max 100us
    position = search_quick(file, pattern)
    if position == -1:
        # 2.2 either use multiprocessing on singlethreaded search
        if multithreaded:
            position = search_mp(file, pattern)
        else:
            position = search_st(file, pattern)

    # 3 if something was found thats not already in db and the files constant is known add that to the db
    if database and position != -1:
        name,base,format,_,_ = identify(file)
        # dont try to add anything to db when the constant is unknown
        if name == "unknown":
            return position

        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        table_name = "_".join((name,str(base),format))
        table_exists = bool(cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name, )).fetchone())

        if not table_exists:
            cursor.execute(f"""CREATE TABLE "{table_name}" (string BLOB PRIMARY KEY, position INTEGER)""")

        cursor.execute(f"""INSERT OR IGNORE INTO "{table_name}" (string, position) VALUES (?, ?)""", (pattern, position))
        conn.commit()
        conn.close()

    # return position no matter if found (n>=0) or not (-1)
    return position

def _search_multi(file:Path, patterns:list[bytes]|tuple[bytes], database:bool=True, multithreaded:bool=True):
    positions = {p:-1 for p in patterns}

    # db search
    if database:
        positions = multi_search_db(file,patterns)
        if all(p>-1 for _,p in positions.items()): return positions
        missing_db = {pat for pat,pos in positions.items() if pos==-1}

    # quick search
    patterns_left = [pat for pat,pos in positions.items() if pos==-1]
    if patterns_left:
        found = multi_search_quick(file, patterns_left)
        positions.update({pat:pos for pat,pos in found.items() if pos!=-1})

    # long search
    patterns_left = [pat for pat,pos in positions.items() if pos==-1]
    if patterns_left:
        if multithreaded:
            found = multi_search_mp(file,patterns_left)
            positions.update({pat:pos for pat,pos in found.items() if pos!=-1})
        else:
            found = multi_search_st(file,patterns_left)
            positions.update({pat:pos for pat,pos in found.items() if pos!=-1})

    # add missing to db
    if database:
        name,base,format,_,_ = identify(file)
        if name == "unknown":
            return positions

        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        table_name = "_".join((name,str(base),format))
        table_exists = bool(cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name, )).fetchone())

        if not table_exists:
            cursor.execute(f"""CREATE TABLE "{table_name}" (string BLOB PRIMARY KEY, position INTEGER)""")

        patterns_new = [(pat,pos) for pat,pos in found.items() if pat in missing_db]
        cursor.executemany(f"""INSERT OR IGNORE INTO "{table_name}" VALUES (?, ?)""", patterns_new)
        conn.commit()
        conn.close()

    return positions

def search(file, pattern:bytes|list[bytes]|tuple[bytes], database:bool=True, multithreaded:bool=True):
    if isinstance(pattern,list|tuple):
        return _search_multi(file,pattern,database,multithreaded)
    return _search(file,pattern,database,multithreaded)

