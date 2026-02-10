#!/usr/bin/python

import sqlite3
from itertools import chain
from threading import Thread, Lock
from queue import Queue
from time import perf_counter, sleep

from scripts.bignum import BigNum, get_all, get_one
from scripts.const import SQLITE_PATH, FIRST_DIGITS_AMOUNT
from scripts.helper import format_size, format_time

class SharedMem:
    file_queue:Queue[BigNum] = Queue()
    db_lock:Lock = Lock()
    size:int

    files_total:int = 0
    files_done:int = 0
    patterns_total:int = 0
    patterns_done:int = 0
    done:bool = False

def progress(mem:SharedMem):
    time_start = perf_counter()
    patterns_total = FIRST_DIGITS_AMOUNT * mem.size * mem.files_total

    while not mem.done:
        sleep(0.2)
        if mem.patterns_done == 0: continue
        time_elapsed = perf_counter() - time_start
        time_elapsed_f = format_time(time_elapsed)
        speed_pattern = mem.patterns_done / time_elapsed
        speed_pattern_f = format_size(speed_pattern, "/s")
        eta = format_time(patterns_total / speed_pattern - time_elapsed)
        print(" "*100+"\r"+f"elapsed:{time_elapsed_f}\t eta:{eta}\t patterns:{speed_pattern_f}\t files:{mem.files_done}/{mem.files_total}", end="          \r")

def get_patterns(chunk:str|bytes, max_length:int=10, offset:int=0):
    positions = chain.from_iterable((x+offset,)*max_length for x in range(len(chunk)-max_length))
    patterns = []
    for start_idx in range(len(chunk)-max_length):
        for length in range(1,max_length+1):
            part = chunk[start_idx:start_idx+length]
            patterns.append(part)
    return zip(patterns, positions)

def _build(mem:SharedMem):
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    patterns_per_insert = 100000
    size = mem.size

    while not mem.file_queue.empty():
        num = mem.file_queue.get()

        with mem.db_lock:
            string_datatype = "TEXT" if num.format == "txt" else "BLOB"
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {num.table_name} (string {string_datatype} PRIMARY KEY, position INTEGER)")

        for startpos in range(0, FIRST_DIGITS_AMOUNT, patterns_per_insert):
            chunk = num.first_digits[startpos:startpos+patterns_per_insert]
            patterns = get_patterns(chunk, size, startpos+1)
            with mem.db_lock:
                cursor.executemany(f"INSERT OR IGNORE INTO {num.table_name} VALUES (?, ?)", patterns)
                conn.commit()
            mem.patterns_done += size * patterns_per_insert
        mem.files_done += 1

def build(size:int, num_workers:int=6):
    time_start = perf_counter()

    mem = SharedMem()
    mem.size = size

    for num in set(get_all()):
        mem.files_total += 1
        mem.file_queue.put(num)

    prog = Thread(target=progress, args=(mem, ))

    threads = []
    for _ in range(num_workers):
        t = Thread(target=_build, args=(mem,))
        t.start()
        threads.append(t)

    prog.start()

    for t in threads:
        t.join()

    mem.done = True
    prog.join()
    time_total = perf_counter() - time_start

    print(f"whoppa... made a {format_size(SQLITE_PATH.stat().st_size, 'b')} big db in {format_time(time_total)}")

if __name__ == "__main__":
    SQLITE_PATH.unlink(True)
    build(10)
