import os
from pathlib import Path
import sys
import math
import sqlite3
from mmap import mmap, ACCESS_READ, MADV_SEQUENTIAL
from multiprocessing import Process, Value

from .const import CHUNK_SIZE, FIRST_DIGITS_AMOUNT, PAGE_SIZE, SQLITE_PATH
from .identify import identify, get_table_name
from .helper import timer

def search_st(file:Path|str, pattern:bytes):
    """ simple single threaded search, semi fast but safe and can search any filesize """
    file = Path(file)
    with file.open("rb") as f:
        chunk = f.read(CHUNK_SIZE)
        last_chunk = b""
        chunk_number = 0
        while chunk:
            position = (last_chunk + chunk).find(pattern)
            if position != -1:
                return position + chunk_number * CHUNK_SIZE - 1
            last_chunk = chunk
            chunk_number += 1
    return -1

def _serach_mp(file:Path, pattern:bytes, sector:tuple[int,int], position_val):
    """ worker method to search_mp """
    sector_start, sector_end = sector
    sector_size = sector_end - sector_start
    pattern_length = len(pattern)
    chunk_start = 0
    position = -1

    with file.open("r+b") as f:
        with mmap(f.fileno(), length=sector_size, offset=sector_start, access=ACCESS_READ) as mm:
            #if sys.platform == "linux":
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

def search_mp(file:Path, pattern:bytes, num_workers:int=0):
    """ multiprocessing approach, fast but expensive and potentially lots of overhead """
    num_workers = num_workers or os.cpu_count() or 1
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

def search_quick(file:Path, pattern:bytes):
    """ low latency search, but only first couple digits """
    _,_,_,_,radix_pos = identify(file)
    with file.open("rb") as f:
        f.seek(radix_pos)
        return f.read(FIRST_DIGITS_AMOUNT).find(pattern)

def search_db(file:Path, pattern:bytes):
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

def search(file:Path, pattern:bytes, database=True, multithreaded=True):
    """ main search method combines all search methods and potentially fills the database with missing data """
    position = -1
    in_db = False

    # 1. check the db if allowed
    if database:
        position = search_db(file, pattern)
        if position != -1:
            in_db = True
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
    if database and position != -1 and not in_db:
        name,base,format,_,_ = identify(file)

        # dont try to add anything to db when the constant is unknown
        if name == "unknown":
            return position

        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        table_name = "_".join((name,str(base),format))
        table_exists = bool(cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name, )).fetchone())

        if not table_exists:
            # string_datatype = "TEXT" if file.suffix == ".txt" else "BLOB"
            cursor.execute(f"""CREATE TABLE "{table_name}" (string BLOB PRIMARY KEY, position INTEGER)""")
        cursor.execute(f"""INSERT OR IGNORE INTO "{table_name}" (string, position) VALUES (?, ?)""", (pattern, position))
        conn.commit()
        conn.close()

    # return position no matter if found (n>=0) or not (-1)
    return position
