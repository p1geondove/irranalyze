# search.py - various search methods

import os
import math
import sqlite3
from mmap import mmap, ACCESS_READ, MADV_SEQUENTIAL
from multiprocessing import Process, Value, Array
from threading import Thread
import hyperscan

from .identify import BigNumInfo
from .const import PAGE_SIZE
from .var import Sizes, Paths, Switches
from .helper import timer

def search_quick(file_info:BigNumInfo, pattern:bytes) -> int:
    """ low latency search, but only first couple digits """
    with file_info.path.open("rb") as f:
        f.seek(file_info.radix_pos+1)
        pos = f.read(Sizes.first_digits_amount).find(pattern)
    if pos == -1:
        return -1
    return pos + Switches.one_indexed

def multi_search_quick(file_info:BigNumInfo, patterns:list[bytes]) -> dict[bytes,int]:
    """ low latency search, but only first couple digits """
    with file_info.path.open("rb") as f:
        f.seek(file_info.radix_pos+1)
        chunk = f.read(Sizes.first_digits_amount)
    return {
        pat : (pos + Switches.one_indexed if pos!=-1 else -1) 
        for pat,pos in zip(
            patterns,
            (
                chunk.find(p) 
                for p in patterns
            )
        )
    } # this is technically a oneliner lol

def search_st(file_info:BigNumInfo, pattern:bytes, lower_bound:int|None=None, upper_bound:int|None=None) -> int:
    """ simple single threaded search, semi fast but safe and can search any filesize """
    lower_bound = lower_bound if lower_bound else 0
    upper_bound = upper_bound if upper_bound else file_info.file_size
    with file_info.path.open("r+b") as f:
        with mmap(f.fileno(), length=0, access=ACCESS_READ) as mm:
            mm.madvise(MADV_SEQUENTIAL)
            pos=mm.find(pattern, max(file_info.radix_pos,lower_bound), upper_bound)
    return pos - file_info.radix_pos + Switches.one_indexed - 1

def multi_search_st(file_info:BigNumInfo, patterns:list[bytes]) -> dict[bytes,int]:
    positions = {p:-1 for p in patterns}
    with file_info.path.open("r+b") as f:
        with mmap(f.fileno(), length=0, access=ACCESS_READ) as mm:
            mm.madvise(MADV_SEQUENTIAL)
            for pat in patterns:
                pos = mm.find(pat, file_info.radix_pos)
                if pos != -1:
                    positions[pat] = pos - file_info.radix_pos + Switches.one_indexed - 1
    return positions

def _search_mp(file_info:BigNumInfo, pattern:bytes, sector:tuple[int,int], position_val):
    """ worker method to search_mp """
    sector_start, sector_end = sector # seperate out the sector tuple into 2 variables
    sector_size = sector_end - sector_start
    pattern_length = len(pattern) # used for overlapping chunks, if not we run risk that a pattern is on a chunk border and wont be found
    chunk_start = file_info.radix_pos if sector_start==0 else 0 # if this is the "first" sector make sure to not include the intpart
    position = -1 # we dont really need it for complex reasons, but declaring this can stop breaking stuff

    with file_info.path.open("r+b") as f: # open file
        with mmap(f.fileno(), length=sector_size, offset=sector_start, access=ACCESS_READ) as mm: # mmap magic
            mm.madvise(MADV_SEQUENTIAL) # more mmap magic, basically tell os that we read sequentially
            while chunk_start < sector_size: # technically dont need this either, but we need some sort of loop to loop over chunks
                chunk_end = chunk_start + Sizes.chunk_size # determine chunk end
                position = mm.find(pattern, chunk_start, chunk_end) # vip guest

                if position != -1: # we found something, lets get outta here
                    break

                if position_val.value != -1 and position_val.value < sector_start: # someone else found something and its better than i could ever do
                    return # basically meaning another process of lower sector found something

                chunk_start = chunk_end - pattern_length # determine start of next chunk

    if position == -1: # we mustve looped trough the entire thing not finding anything
        return

    position += sector_start - 1 # dont ask me about this off by one error...

    if position < position_val.value or position_val.value == -1: # we found somehting, so lets check if its better than the rest
        position_val.value = position # we set position if its unset (-1) or the one set is larger (worse) than what we found

def search_mp(file_info:BigNumInfo, pattern:bytes, lower_bound:int|None=None, upper_bound:int|None=None) -> int:
    """ multiprocessing approach, fast but expensive and potentially lots of overhead """
    lower_bound = lower_bound if lower_bound else 0 # if lower_bound is None set it to 0 else use that lower_bound
    upper_bound = upper_bound if upper_bound else file_info.file_size // PAGE_SIZE * PAGE_SIZE + PAGE_SIZE # same as above but make sure to page align it, else mmap screams
    bound_size = upper_bound - lower_bound
    sector_size = math.ceil(bound_size/Sizes.max_processes) // PAGE_SIZE * PAGE_SIZE # sector size is just the search range divided in even chunks, page aligned aswell

    num_workers = Sizes.max_processes
    if sector_size < Sizes.chunk_size: # if we have less sectors than processes
        num_workers = bound_size // Sizes.chunk_size + 1 # then just turn down the amount of processes


    sectors = [] # calculating bounds of sectors
    for i in range(num_workers):
        start = i * sector_size + lower_bound // PAGE_SIZE * PAGE_SIZE # must be page aligned as always
        end = min(upper_bound, start + sector_size + len(pattern))
        sectors.append((start, end))

    position = Value("q", -1) # shared between processes
    processes:list[Process] = []

    for sector in sectors:
        p = Process(target=_search_mp, args=(file_info, pattern, sector, position))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    return -1 if position.value==-1 else position.value - file_info.radix_pos + Switches.one_indexed

def _multi_search_mp(file_info:BigNumInfo, patterns:list[bytes], sector:tuple[int,int], found_array):
    sector_start, sector_end = sector # put start end end into seperate variables
    sector_size = sector_end - sector_start # determins sectro size for mmap(length=...)
    pattern_length = max(len(pattern) for pattern in patterns) # overlap chunks by this amount
    chunk_start = file_info.radix_pos if sector_start==0 else 0 # used for checking bound and mmap.find()
    patterns_left = set(patterns)
    order = {p:i for i,p in enumerate(patterns)} # for found_array so we dont have to do patterns.index(pattern)
    to_remove = set() # a set that contains patterns that in the next loop are being removed from patterns_left

    with file_info.path.open("r+b") as f: # open file
        with mmap(f.fileno(), length=sector_size, offset=sector_start, access=ACCESS_READ) as mm: # make mmap object
            mm.madvise(MADV_SEQUENTIAL) # havent tested, but should make reading faster
            while chunk_start < sector_size and patterns_left: # check we are within sector and have patterns left for searching
                chunk_end = chunk_start + Sizes.chunk_size # determine bounds of chunk
                to_remove.clear()

                for pattern in patterns_left: # iterate over all patterns in need of finding
                    position = mm.find(pattern, chunk_start, chunk_end) # try to find pattern

                    if position != -1: # found in chunk
                        abs_pos = position + sector_start - file_info.radix_pos - 1 # calculate the abs position which really means relative to the radix pos
                        idx = order[pattern] # get index of the pattern in found_array

                        # here i should lock the found_array, however it passes all tests and is never inconsistant...
                        pos = found_array[idx] # get stored pos from found_array
                        if pos==-1 or pos > abs_pos: # if pattern is not found or my finding is better/earlier
                            to_remove.add(pattern) # add that pattern to be removed
                            found_array[idx] = abs_pos # store the pos (mm.find() alignes with offset/sector_start)

                # syncronize patterns_left to other processes / found_array, again somehow without locking the array...
                for pattern in patterns_left: # only bother to check unfound patterns
                    pos = found_array[order[pattern]] # what position in does found_array report for that pattern?
                    if pos!=-1 and pos<sector_start: # if that pattern is found and the position is earlier than what i can do
                        to_remove.add(pattern)

                # actually remove all found patterns from patterns_left
                patterns_left -= to_remove

                # determine chunk bounds
                chunk_start = chunk_end - pattern_length

@timer
def multi_search_mp_old(file_info:BigNumInfo, patterns:list[bytes], num_workers:int=Sizes.max_processes) -> dict[bytes,int]:
    """ multiprocessing approach, fast but expensive and potentially lots of overhead """
    num_workers = max(1,  num_workers or os.cpu_count() or 1)
    sector_size = math.ceil(file_info.file_size/num_workers) // PAGE_SIZE * PAGE_SIZE
    sectors = []

    for i in range(num_workers):
        start = i*sector_size
        if start >= file_info.file_size: break
        end = min(start + sector_size + max(len(p) for p in patterns), file_info.file_size)
        sectors.append([start,end])
    sectors[-1][1] = file_info.file_size

    found_array = Array("q",[-1]*len(patterns))
    processes:list[Process] = []

    for sector in sectors:
        p = Process(target=_multi_search_mp, args=(file_info, patterns, sector, found_array))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    return {pattern:pos+Switches.one_indexed for pattern,pos in zip(patterns,found_array)} # also here pyright thinks that the array is not iterable, but it is... # type:ignore

def _multi_search_hyper(sector_start:int, sector:memoryview, found:dict[int,list], db:hyperscan.Database):
    def match_handler(id:int, from_:int, to:int, flags:int, context=None):
        found[id].append(to + sector_start)
    db.scan(sector, match_handler)
    sector.release()

def multi_search_mp(file_info:BigNumInfo, patterns:list[bytes], num_workers:int=Sizes.max_processes) -> dict[bytes,int]:
    num_workers = max(1,  num_workers or os.cpu_count() or 1)
    sector_size = math.ceil(file_info.file_size/num_workers) // PAGE_SIZE * PAGE_SIZE
    threads:list[Thread] = []
    overlap = max(len(p) for p in patterns)
    found = {n:[-1] for n,pat in enumerate(patterns)}
    id_pattern_map = {n:pat for n,pat in enumerate(patterns)}
    db = hyperscan.Database()
    ids = list(range(len(patterns)))
    flags = [hyperscan.HS_FLAG_SINGLEMATCH] * len(patterns)
    db.compile(patterns, ids, flags=flags)

    with file_info.path.open("r+b") as file:
        with mmap(file.fileno(), length=0, access=ACCESS_READ) as mm:
            mm.madvise(MADV_SEQUENTIAL)
            mv = memoryview(mm)

            for i in range(num_workers):
                start = max(i * sector_size, file_info.radix_pos)
                end = min(start + sector_size + overlap, file_info.file_size)
                sector = mv[start:end]
                t = Thread(target=_multi_search_hyper, args=(start, sector, found, db))
                t.start()
                threads.append(t)

            for t in threads:
                t.join()

            mv.release()

    pairs = {}
    for id, pos in found.items():
        pat = id_pattern_map[id]
        if len(pos) > 1:
            pos.remove(-1)
            pos = min(pos) - len(pat) - file_info.radix_pos + Switches.one_indexed - 1
        else:
            pos = -1
        pairs[pat] = pos
    return pairs

def search_db(file_info:BigNumInfo, pattern:bytes) -> int|None:
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

def multi_search_db(file_info:BigNumInfo, patterns:list[bytes]) -> dict[bytes,int|None]:
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

def _search(file_info:BigNumInfo, pattern:bytes, database:bool=True, multiprocess:bool=True):
    if database: # check if were allowed to use database
        position = search_db(file_info,pattern) # first search database

        if not position is None: # is database returns int (either found or -1)
            return position # return that position

        position = search_quick(file_info,pattern) # db returns None, so normal search

        if position != -1: # if quicksearch found somehting
            _add_to_db(file_info,{pattern:position}) # add that to db
            return position # and return that position

        else: # if quicksearch didnt find anything
            # to make this a bit quicker we can set bounds
            # first lower bound or impossible
            part_found = multi_search_db(file_info, [pattern[:n] for n in range(1,len(pattern))]) # check all patterns smaller than wanted pattern
            part_found = filter(lambda x:x[1], part_found.items()) # filter out all None, we care about found and not presnt only
            part_found = sorted(part_found, key=lambda x:len(x[0])) # exctract the last known position, we sort to get the closest sub pattern to our current pattern
            if part_found:
                canidate = part_found[-1][1]
                if canidate == -1: # if the pattern with the last char missing is not in file, then current pattern cant be in file either
                    _add_to_db(file_info,{pattern:-1})
                    return -1

                lower_bound = canidate # if we do have a aposition from sub pattern, than we can use that as lower bound
            else:
                lower_bound = None

            # upper bound
            if file_info.format == "ycd":
                possible_chars = [bytes((i,)) for i in range(256)]
            else:
                if file_info.base == 10:
                    possible_chars = [b"0",b"1",b"2",b"3",b"4",b"5",b"6",b"7",b"8",b"9"]
                else:
                    possible_chars = [b"0",b"1",b"2",b"3",b"4",b"5",b"6",b"7",b"8",b"9",b"a",b"b",b"c",b"d",b"e",b"f"]

            super_patterns = [pattern+c for c in possible_chars] + [c+pattern for c in possible_chars]
            part_found = multi_search_db(file_info, super_patterns)
            part_found = filter(lambda x:x[1] is not None and x[1] != -1, part_found.items()) # filter out the ones that are not recorded or not present
            part_found = sorted(part_found, key=lambda x:x[1]) # pyright has some issues here again since it thinks that there still None in there which you cant compare against ints, but i just filtered the omg... # type:ignore
            if part_found:
                upper_bound = part_found[0][1]
            else:
                upper_bound = None

            if multiprocess: # check if were allowed to use multiprocessing
                position = search_mp(file_info,pattern,lower_bound,upper_bound) # search mp
            else: # only other option
                position = search_st(file_info,pattern,lower_bound,upper_bound) # search st

        _add_to_db(file_info,{pattern:position}) # doesnt matter if found or not, _add_to_db will decide to add -1 or not

    else: # were not allowed to use db
        position = search_quick(file_info,pattern) # quicksearch first always

        if position != -1: # quicksearch found somehting
            return position # jszt return that

        if multiprocess: # are we allowed to use multiprocessing ?
            position = search_mp(file_info,pattern) # search mp
        else: # only other option
            position = search_st(file_info,pattern) # search st

    return position # return what we found, can only be int (-1 or found doesnt matter)

def _search_multi(file_info:BigNumInfo, patterns:list[bytes], database:bool=True, multiprocess:bool=True) -> dict[bytes,int]:
    if database:
        positions = multi_search_db(file_info, patterns) # first search db, will return {pattern:pos} where pos can be int or None, if pos is None it means its not recorded at all, -1 means reported not in file and anything >-1 is regular position
        missing_db = set(pat for pat,pos in positions.items() if pos is None) # make a set of the patterns that return None / are not recorded
        if not missing_db: # if there arent any missing then we found everything
            return positions # return {pat:pos}, pyright says error here since it thinks we try to return {bytes:int|None} while its only {bytes:int} since we calculated missing_db which hosts all None, but that was empty so there are no None -> all int # type:ignore
        new_positions = multi_search_quick(file_info, list(missing_db)) # some are missing, so we first do a quick search
        still_missing = set(pat for pat,pos in new_positions.items() if pos==-1) # make another set of the ones that return -1, -1 here means not found but maybe in long search we can find it, this can only retun int as pos
        new_found = {pat:new_positions[pat] for pat in new_positions.keys()-still_missing} # a dict containing the valid pat:pos pairs from quicksearch, identical to {pat:pos for pat,pos in new_positions.items() if pos!=-1} but using set math to have smaller loop
        positions.update(new_found) # add valid pairs to positions where positions is our total dict containing everything, ints of -1 and above as well as None still
        if still_missing: # check if that set from earlier has any elements, meaning if theres more to find
            if multiprocess: # switch for multiprocessing or single threaded search
                new_positions = multi_search_mp(file_info, list(still_missing)) # multiprocessing search
            else: # only other option
                new_positions = multi_search_st(file_info, list(still_missing)) # single threaded search
        still_missing = set(pat for pat,pos in new_positions.items() if pos==-1) # make another set of missing patterns
        new_found = {pat:new_positions[pat] for pat in new_positions.keys()-still_missing} # with that missing set we can lower this loop, just like with db -> quick
        positions.update(new_found) # update our total positions dict
        positions = {pat:pos or -1 for pat,pos in positions.items()} # there might still be some that are None:not found at all, these we flip to -1
        _add_to_db(file_info, {pat:pos for pat,pos in positions.items() if pat in missing_db}) # report all positions from missing_db to the db, no matter if found(>-1) or not(-1)
    else: # were not allowed to use database
        positions = multi_search_quick(file_info, patterns) # quicksearch
        still_missing = [pat for pat,pos in positions.items() if pos==-1] # list of patterns that are not found (position = -1)
        if still_missing: # check if there are any missing
            if multiprocess: # mp / st switch
                result = multi_search_mp(file_info,still_missing) # search missing mp
            else: # only other option
                result = multi_search_st(file_info,still_missing) # search missing st
            positions.update({pat:pos for pat,pos in result.items() if pos!=-1}) # insert the additional patterns that have been found
    return positions # return whatever we found

def _add_to_db(file_info:BigNumInfo, patterns:dict[bytes,int]):
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

def search(file_info:BigNumInfo, pattern:bytes|list[bytes], database:bool=True, multithreaded:bool=True):
    if isinstance(pattern,bytes):
        return _search(file_info,pattern,database,multithreaded)
    elif isinstance(pattern,list):
        pattern = list(map(bytes, pattern))
        return _search_multi(file_info,pattern,database,multithreaded)
    print("WARN: Search pattern must either be bytes or list of bytes")

