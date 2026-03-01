# search.py - various search methods

import os
import math
import sqlite3
from typing import Iterable
from pathlib import Path
from mmap import mmap, ACCESS_READ, MADV_SEQUENTIAL
from multiprocessing import Process, Value, Array

from .identify import identify, get_table_name
from .const import PAGE_SIZE
from .var import Sizes, Paths, Switches
from .helper import timer


def search_st(file:Path, pattern:bytes) -> int:
    """ simple single threaded search, semi fast but safe and can search any filesize """
    _,_,_,_,radix = identify(file)
    last_chunk = b""
    chunk_number = -1
    with file.open("rb") as f:
        chunk = f.read(Sizes.chunk_size)
        while chunk:
            position = (last_chunk + chunk).find(pattern)
            if position != -1:
                if chunk_number == -1:
                    return position - radix + Switches.one_indexed - 1
                return position + chunk_number * Sizes.chunk_size - radix + Switches.one_indexed
            last_chunk = chunk
            chunk_number += 1
            chunk = f.read(Sizes.chunk_size)
    return -1


def multi_search_st(file:Path, patterns:Iterable[bytes]) -> dict[bytes,int]:
    _,_,_,_,radix = identify(file)
    patterns = list(patterns)
    patterns_left = patterns.copy()
    positions = {p:-1 for p in patterns}
    chunk_number = -1
    last_chunk = b""

    with file.open("rb") as f:
        chunk = f.read(Sizes.chunk_size)
        while chunk and patterns_left:
            to_remove = set()
            search_space = last_chunk + chunk

            for pattern in patterns_left:
                pos = search_space.find(pattern)
                if pos != -1:
                    to_remove.add(pattern)
                    if chunk_number == -1:
                        positions[pattern] = pos - radix + Switches.one_indexed - 1
                    else:
                        positions[pattern] = pos - radix + chunk_number * Sizes.chunk_size + Switches.one_indexed

            for pattern in to_remove:
                patterns_left.remove(pattern)

            chunk_number += 1
            last_chunk = chunk
            chunk = f.read(Sizes.chunk_size)
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
                chunk_end = chunk_start + Sizes.chunk_size 
                position = mm.find(pattern, chunk_start, chunk_end)

                if position != -1:
                    break

                if position_val.value != -1 and position_val.value < sector_start:
                    return

                chunk_start = chunk_end - pattern_length

    if position == -1:
        return

    #position += sector_start - Switches.one_indexed + (not sector_start==0)
    position += sector_start - (sector_start==0)
    if position < position_val.value or position_val.value == -1:
        position_val.value = position


def search_mp(file:Path, pattern:bytes, num_workers:int=Sizes.max_processes) -> int:
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

    return -1 if position.value==-1 else position.value - radix_pos + Switches.one_indexed


def _multi_search_mp(file:Path, patterns:list[bytes], sector:tuple[int,int], found_array):
    _,_,_,_,radix_pos = identify(file)
    sector_start, sector_end = sector # put start end end into seperate variables
    sector_size = sector_end - sector_start # determins sectro size for mmap(length=...)
    pattern_length = max(len(pattern) for pattern in patterns) # overlap chunks by this amount
    chunk_start = 0 # used for checking bounds and mmap.find()
    patterns_left = set(patterns)
    order = {p:i for i,p in enumerate(patterns)} # for found_array so we dont have to do patterns.index(pattern)
    to_remove = set() # a set that contains patterns that in the next loop are being removed from patterns_left
    with file.open("r+b") as f: # open file
        with mmap(f.fileno(), length=sector_size, offset=sector_start, access=ACCESS_READ) as mm: # make mmap object
            mm.madvise(MADV_SEQUENTIAL) # havent tested, but should make reading faster
            while chunk_start < sector_size and patterns_left: # check we are within sector and have patterns left for searching
                chunk_end = chunk_start + Sizes.chunk_size # determine bounds of chunk
                to_remove.clear()

                for pattern in patterns_left: # iterate over all patterns in need of finding
                    position = mm.find(pattern, chunk_start, chunk_end) # try to find pattern

                    if position != -1: # found in chunk
                        abs_pos = position + sector_start - radix_pos - (sector_start==0) # calculate the abs position which really means relative to the radix pos
                        idx = order[pattern] # get index of the pattern in found_array

                        #with found_array: # lock the found_array because we might write to it
                        pos = found_array[idx] # get stored pos from found_array
                        if pos==-1 or pos > abs_pos: # if pattern is not found or my finding is better/earlier
                            to_remove.add(pattern) # add that pattern to be removed
                            with found_array: # lock the found_array because we write to it
                                found_array[idx] = abs_pos # store the pos (mm.find() alignes with offset/sector_start)


                # syncronize patterns_left to other processes / found_array
                for pattern in patterns_left: # only bother to check unfound patterns
                    #with found_array: # lock the found_array
                    pos = found_array[order[pattern]] # what position in does found_array report for that pattern?
                    if pos!=-1 and pos<sector_start: # if that pattern is found and the position is earlier than what i can do
                        to_remove.add(pattern)

                # actually remove all found patterns from patterns_left
                patterns_left -= to_remove
                #for pattern in to_remove: # get all found patterns
                #    patterns_left.remove(pattern) # remove the pattern

                # determine chunk bounds
                chunk_start = chunk_end - pattern_length

def multi_search_mp(file:Path, patterns:Iterable[bytes], num_workers:int=Sizes.max_processes) -> dict[bytes,int]:
    """ multiprocessing approach, fast but expensive and potentially lots of overhead """
    patterns = list(patterns)
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

    return {pattern:pos+Switches.one_indexed for pattern,pos in zip(patterns,found_array)}


def search_quick(file:Path, pattern:bytes) -> int:
    """ low latency search, but only first couple digits """
    _,_,_,_,radix_pos = identify(file)
    with file.open("rb") as f:
        f.seek(radix_pos+1)
        pos = f.read(Sizes.first_digits_amount).find(pattern)
    if pos == -1:
        return -1
    return pos + Switches.one_indexed
    return pos + 1 - Switches.one_indexed


def multi_search_quick(file:Path, patterns:Iterable[bytes]) -> dict[bytes,int]:
    _,_,_,_,radix_pos = identify(file)
    with file.open("rb") as f:
        f.seek(radix_pos)
        chunk = f.read(Sizes.first_digits_amount)
    return {pat:(pos+Switches.one_indexed-radix_pos if pos!=-1 else -1) for pat,pos in zip(patterns,(chunk.find(p) for p in patterns))}


def search_db(file:Path, pattern:bytes) -> int|None:
    """ very quick but limited search, only returns whats stored in the db """
    conn = sqlite3.connect(Paths.sqlite_path)
    cursor = conn.cursor()
    table_name = get_table_name(file)
    table_exists = bool(cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name, )).fetchone())
    if not table_exists:
        conn.close()
        return None
    cursor.execute(f"""SELECT position FROM "{table_name}" WHERE string = ? ORDER BY position ASC LIMIT 1""", (pattern,))
    result = cursor.fetchone()
    conn.close()
    if isinstance(result,Iterable):
        result = list(result)[0]
    return result


def multi_search_db(file:Path, patterns:Iterable[bytes]) -> dict[bytes,int|None]:
    patterns = list(patterns)
    # with sqlite3.connect(Paths.sqlite_path) as conn:
    conn = sqlite3.connect(Paths.sqlite_path)
    cursor = conn.cursor()
    table_name = get_table_name(file)
    table_exists = bool(cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name, )).fetchone())
    if not table_exists:
        conn.close()
        return {p:None for p in patterns}
    query = f"""WITH search_list(pattern) AS (VALUES (?) {', (?)'*(len(patterns)-1)}) SELECT s.pattern, MIN(t.position) FROM search_list s LEFT JOIN "{table_name}" t ON s.pattern = t.string GROUP BY s.pattern"""
    result = cursor.execute(query,patterns).fetchall()
    conn.close()
    return {pat:pos for pat,pos in result}


def _search(file:Path, pattern:bytes, database:bool=True, multiprocess:bool=True):
    if database: # check if were allowed to use database
        position = search_db(file,pattern) # first search database
        if not position is None: # is database returns int (either found or -1)
            return position # return that position
        position = search_quick(file,pattern) # db returns None, so normal search
        if position != -1: # if quicksearch found somehting
            _add_to_db(file,{pattern:position}) # add that to db
            return position # and return that position
        else: # if quicksearch didnt find anything
            if multiprocess: # check if were allowed to use multiprocessing
                position = search_mp(file,pattern) # search mp
            else: # only other option
                position = search_st(file,pattern) # search st
        _add_to_db(file,{pattern:position}) # doesnt matter if found or not, _add_to_db will decide to add -1 or not
    else: # were not allowed to use db
        position = search_quick(file,pattern) # quicksearch first always
        if position != -1: # quicksearch found somehting
            return position # jszt return that
        if multiprocess: # are we allowed to use multiprocessing ?
            position = search_mp(file,pattern) # search mp
        else: # only other option
            position = search_st(file,pattern) # search st
    return position # return what we found, can only be int (-1 or found doesnt matter)


def _search_multi(file:Path, patterns:Iterable[bytes], database:bool=True, multiprocess:bool=True) -> dict[bytes,int]:
    if database:
        positions = multi_search_db(file, patterns) # first search db, will return {pattern:pos} where pos can be int or None, if pos is None it means its not recorded at all, -1 means reported not in file and anything >-1 is regular position
        missing_db = set(pat for pat,pos in positions.items() if pos is None) # make a set of the patterns that return None / are not recorded
        if not missing_db: # if there arent any missing then we found everything
            return positions # return {pat:pos}, pyright says error here since it thinks we try to return {bytes:int|None} while its only {bytes:int} since we calculated missing_db which hosts all None, but that was empty so there are no None -> all int
        new_positions = multi_search_quick(file, missing_db) # some are missing, so we first do a quick search
        still_missing = set(pat for pat,pos in new_positions.items() if pos==-1) # make another set of the ones that return -1, -1 here means not found but maybe in long search we can find it, this can only retun int as pos
        new_found = {pat:new_positions[pat] for pat in new_positions.keys()-still_missing} # a dict containing the valid pat:pos pairs from quicksearch, identical to {pat:pos for pat,pos in new_positions.items() if pos!=-1} but using set math to have smaller loop
        positions.update(new_found) # add valid pairs to positions where positions is our total dict containing everything, ints of -1 and above as well as None still
        if still_missing: # check if that set from earlier has any elements, meaning if theres more to find
            if multiprocess: # switch for multiprocessing or single threaded search
                new_positions = multi_search_mp(file, still_missing) # multiprocessing search
            else: # only other option
                new_positions = multi_search_st(file, still_missing) # single threaded search
        still_missing = set(pat for pat,pos in new_positions.items() if pos==-1) # make another set of missing patterns
        new_found = {pat:new_positions[pat] for pat in new_positions.keys()-still_missing} # with that missing set we can lower this loop, just like with db -> quick
        positions.update(new_found) # update our total positions dict
        positions = {pat:pos or -1 for pat,pos in positions.items()} # there might still be some that are None:not found at all, these we flip to -1
        _add_to_db(file, {pat:pos for pat,pos in positions.items() if pat in missing_db}) # report all positions from missing_db to the db, no matter if found(>-1) or not(-1)
    else: # were not allowed to use database
        positions = multi_search_quick(file, patterns) # quicksearch
        still_missing = [pat for pat,pos in positions.items() if pos==-1] # list of patterns that are not found (position = -1)
        if still_missing: # check if there are any missing
            if multiprocess: # mp / st switch
                result = multi_search_mp(file,still_missing) # search missing mp
            else: # only other option
                result = multi_search_st(file,still_missing) # search missing st
            positions.update({pat:pos for pat,pos in result.items() if pos!=-1}) # insert the additional patterns that have been found
    return positions # return whatever we found


def _add_to_db(file:Path, patterns:dict[bytes,int]):
    name,base,format,_,_ = identify(file) # identify the file, later used for table_name
    if name == "unknown": # if the file is unknown
        return # dont do anything

    # with sqlite3.connect(Paths.sqlite_path) as conn: # connection to the db
    conn =sqlite3.connect(Paths.sqlite_path) # connection to the db
    cursor = conn.cursor() # cursor db thingy
    table_name = "_".join((name,str(base),format)) # create table name
    table_exists = bool(cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name, )).fetchone()) # bool wether table exists

    if not table_exists: # is that table doesnt exist
        cursor.execute(f"""CREATE TABLE "{table_name}" (string BLOB PRIMARY KEY, position INTEGER)""") # just make it lol

    patterns = {pat:pos for pat,pos in patterns.items() if not pos is None}
    if Switches.report_not_found: # add -1 to table to signal thats not there?
        patterns_new = [(pat,pos) for pat,pos in patterns.items()] # convert patterns dict to list
    else: # or leave it open, maybe user add bigger number file to find pattern
        patterns_new = [(pat,pos) for pat,pos in patterns.items() if pos != -1] # convert patterns dict to list, but only the ones that are found (!=-1)

    cursor.executemany(f"""INSERT OR IGNORE INTO "{table_name}" VALUES (?, ?)""", patterns_new) # insert all
    conn.commit() # yeah...
    conn.close()


def search(file, pattern:bytes|Iterable[bytes], database:bool=True, multithreaded:bool=True):
    if isinstance(pattern,bytes):
        return _search(file,pattern,database,multithreaded)
    return _search_multi(file,pattern,database,multithreaded)

