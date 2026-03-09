# build_db.py - used to init the db with identifier table and precalculate some pattern:pos pairs

import sqlite3
from pathlib import Path
from fractions import Fraction
from typing import Any

from itertools import chain
from threading import Thread
from queue import Queue
from time import perf_counter, sleep

from .bignum import BigNum
from .helper import format_size, format_time
from .var import Sizes, Paths
from .const import IDENTIFY_TABLE_NAME

def build_identifier(verbose:bool=False):
    from hashlib import md5
    import mpmath
    from mpmath import e, pi, ln, sqrt, inf, root, nsum, fsum, nprod, findroot
    import sympy

    # a useful function to check if a number is interesting at all
    tol_int = mpmath.mpf("1e-90") # used for checking if int
    tol_rat = 10**90 # used for checking if rational
    def is_valid(num): # returns False if a number is +/-infinity, integer or rational
        return -mpmath.inf<num<mpmath.inf and num%1>tol_int and -num%1>tol_int and Fraction(str(num)).denominator > tol_rat

    if verbose:
        print("setting up identifier generation")

    # only 100 digits are used but for big expressions evaluation can yield high error so increasing precision
    # if you wanna add constants maybe put this to 200 and look at the md5 hash of the generated db, then lower it until it changes, thats how i did it
    # 120 for now is the limit, altho funnily enough all my files still get identified with 105
    mpmath.mp.dps = 120
    primes = [mpmath.mpf(p) for p in sympy.primerange(1e5)]
    e = mpmath.e
    pi = mpmath.pi
    root2 = sqrt(2)
    root3 = sqrt(3)
    ln2 = ln(2)
    gamma = -mpmath.psi(1/3,1)

    if verbose:
        print("evaluating oneliners")
    constants:list[tuple[Any,str]] = [
        (pi, "pi"),
        (pi*2, "tau"),
        (e, "e"),
        (+mpmath.phi, "phi"),
        (root2+1, "silver ratio"),
        (+mpmath.catalan, "catalan's constant"),
        (+mpmath.apery, "apery's constant"),
        (+mpmath.mertens, "mertens constant"),
        (+mpmath.twinprime, "twin prime constant"),
        (+mpmath.khinchin, "khinchin's constant"),
        (findroot(lambda x:x**2+1-x**3,1), "supergolden ratio"),
        (sqrt(2+root2), "connective constant"),
        (mpmath.elliprf(0,1,2)*4, "lemniscate"),
        (gamma, "euler mascheroni"),
        (nprod(lambda x:mpmath.cos(pi/x), [3,inf]), "kepler-bouwkamp constant"),
        (root((45-sqrt(1929))/18,3) + root((45+sqrt(1929))/18,3), "wallis's constant"),
        (nsum(lambda x:1/(2**x-1), [1,inf]), "erdos-borwein constant"),
        (mpmath.lambertw(1), "omega constant"),
        (findroot(lambda x:(x*mpmath.exp(sqrt(1+x**2)))/(1+sqrt(1+x**2))-1,1.2), "laplace limit"),
        (1/mpmath.agm(1,root2), "gauss's constant"),
        (2/root3, "second hermite constant"),
        (nsum(lambda x:1/(10**mpmath.factorial(x)), [1,inf]), "liouville's constant"),
        (mpmath.besseli(1,2)/mpmath.besseli(0,2), "first continued fraction constant"),
        (e**(pi*sqrt(163)), "ramanujan's constant"),
        (+mpmath.glaisher, "glaisher-kinkelin constant"),
        (findroot(lambda x:x-mpmath.cos(x),0.75), "dottie number"),
        (+mpmath.mertens, "meissel-mertens constant"),
        (ln(1+root2)+root2, "universal parabolic constant"),
        (e**pi, "gelfond's constant"),
        (2**root2, "gelfond-schneider constant"),
        (pi**2/8, "second favard constant"),
        (pi*(3-sqrt(5)), "golden angle"),
        (pi*ln((4*pi**3*e**(2*-mpmath.diff(mpmath.gamma,1)))/mpmath.gamma(1/4)**4), "sierpinski's constant"),
        (pi**2/12, "first nielsen-ramanujan constant"),
        ((9-mpmath.polygamma(1,2/3)+mpmath.polygamma(1,4/3))/(4*root3), "gieseking constant"),
        (findroot(lambda x:x**3-x**2-x-1,1.8), "tribonacci constant"),
        (findroot(lambda x:x**3-x-1,1.3), "plastic ratio"),
        (1/4*(2-nprod(lambda x:1-1/(2**2**x),[0,inf])), "prouhet-thue-morse constant"),
        ("0."+"".join(str(x) for x in range(120)), "champernowne constant"),
        (findroot(lambda x:x**10+x**9-x**7-x**6-x**5-x**4-x**3+x+1, 1.2), "salem constant"),
        (pi**2/(12*ln2), "first levy's constant"),
        (e**(pi**2 / (12*ln2)), "second levy's constant"),
        ("0."+"".join(str(int(p)) for p in primes[:50]), "copeland-erdos constant"),
        (-e*(gamma+nsum(lambda x:(-1)**x/(x*mpmath.fac(x)),[1,inf])), "gompertz constant"),
        (pi/ln2, "van der pauw constant"),
        (mpmath.atan(root2), "magic angle rad"),
        (mpmath.atan(root2)*180/pi, "magic angle deg"),
        (6*ln2*(48*ln(mpmath.glaisher)-4*ln(pi)-ln2-2)/pi**2-1/2, "porter's constant"),
        (sum(1/2**p for p in primes), "prime constant"),
        ((6*ln2*ln(10))/pi**2, "lochs constant"),
        (findroot(lambda x:4*x**8-28*x**6-7*x**4+16*x**2+16, 1), "devicci's tesseract constant"),
        (8/(root3*3), "lieb's sqiare ice constant"),
        (1 + nsum(lambda x:1-1/mpmath.zeta(x),[2,inf]), "niven's constant"),
        (nsum(lambda x:8**2**x/(2**2**(x+2)-1),[0,inf]), "regular paperfolding sequence"),
        (nsum(lambda x:1/mpmath.fib(x),[1,inf]), "reciprocal fibonacci constant"),
        (1-(1+ln(ln2))/ln2, "erdos-tenebaum-ford constant"),
        (nsum(lambda x:(-1)**x*(x**(1/x)-1),[1,inf]), "mbr constant"),
        (mpmath.gamma(1/4)**2/(4*pi**(3/2)), "logarithmic capacity of the unit disk")
    ]

    """ constants i couldnt find a nice oneliner for """
    if verbose:
        print("evaluating more complex constants")

    # cahen's constant
    s = [mpmath.mpf(2)]
    for _ in range(15):
        s.append(s[-1] * (s[-1] - 1) + 1)
    num = fsum((-1)**k / (s[k] - 1) for k in range(len(s)))
    name = "cahen's constant"
    constants.append((num,name))

    # conway's constant
    coeffs = [1,0,-1,-2,-1,2,2,1,-1,-1,-1,-1,-1,2,5,3,-2,-10,-3,-2,6,6,1,9,-3,-7,-8,-8,10,6,8,-5,-12,7,-7,7,1,-3,10,1,-6,-2,-10,-3,2,9,-3,14,-8,0,-7,9,3,-4,-10,-7,12,7,2,-12,-4,-2,5,0,1,-7,7,-4,12,-6,3,-6]
    num = [s for s in mpmath.polyroots(coeffs) if isinstance(s,mpmath.mpf) and 1.3<s<1.305][0]
    name = "conway's constant"
    constants.append((num,name))

    if verbose:
        print("calculating hashes and inserting into db")

    hash_name_pairs:list[tuple[bytes,str]] = []
    hash_set:set[bytes] = set()

    for num,name in constants:
        num_hash = md5(str(num)[:100].encode()).digest()
        if num_hash in hash_set:
            continue
        hash_set.add(num_hash)
        hash_name_pairs.append((
            num_hash,
            name
        ))

    """ functions """
    if verbose:
        print("iterating single argument over functions")
    # inputs to functions 0->10 & 1/2->1/10 & some special ones
    inputs = [
        (x,str(x)) for x in range(11)
    ] + [
        (1/mpmath.mpf(x),"1/"+str(x)) for x in range(2,11)
    ] + [
        (root2,"root2"),
        (root3,"root3"),
        (mpmath.sin(1), "sin1"),
        (mpmath.cos(1), "cos1"),
        (mpmath.tan(1), "tan1"),
        (pi, "pi"),
        (pi*2, "tau"),
        (e, "e"),
        (ln2, "ln2")
    ]

    # single argument
    functions = [
        (mpmath.sqrt, "sqrt"),
        (mpmath.cbrt, "cbrt"),
        (mpmath.sin, "sin"),
        (mpmath.cos, "cos"),
        (mpmath.tan, "tan"),
        (ln, "ln"),
        (mpmath.lambertw, "W"),
        (mpmath.zeta, "zeta"),
        (mpmath.gamma, "gamma")
    ]

    for fval,fname in functions:
        for ival,iname in inputs:
            name = f"{fname}({iname})"
            try:
                num = fval(ival)
            except:
                continue
            if not is_valid(num):
                continue
            blob = md5(str(num)[:100].encode()).digest()
            if blob in hash_set:
                continue
            hash_set.add(blob)
            hash_name_pairs.append((blob,name))
            if verbose:
                print(f"{name}:{blob}", end=" "*20+"\r")

    # two argument
    if verbose:
        print(f"\niterating multi argument fucntions")
    functions = [
        (root, "root"),
        (mpmath.beta, "beta"),
        (mpmath.agm, "agm")
    ]

    for fval,fname in functions:
        for i1val,i1name in inputs:
            for i2val,i2name in inputs:
                name = f"{fname}({i1name},{i2name})"
                try:
                    num = fval(i1val,i2val)
                except:
                    continue
                if not is_valid(num):
                    continue
                blob = md5(str(num)[:100].encode()).digest()
                if blob in hash_set:
                    continue
                hash_set.add(blob)
                hash_name_pairs.append((blob,name))
                if verbose:
                    print(f"{name}:{blob}", end=" "*20+"\r")

    mpmath.mp.dps = 20
    # put all aggregated hash and name pairs into the database
    conn = sqlite3.connect(Paths.sqlite_path)
    cursor = conn.cursor()
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {IDENTIFY_TABLE_NAME} (hash BLOB PRIMARY KEY, name TEXT)")
    cursor.executemany(f"""INSERT OR IGNORE INTO {IDENTIFY_TABLE_NAME} VALUES (?, ?)""", hash_name_pairs)
    conn.commit()
    conn.close()

    if verbose:
        print("\ndone building identifier table")

def get_patterns(chunk:str|bytes, max_length:int=10, offset:int=0):
    positions = chain.from_iterable((x+offset,)*max_length for x in range(len(chunk)-max_length))
    patterns = []
    for start_idx in range(len(chunk)-max_length):
        for length in range(1,max_length+1):
            part = chunk[start_idx:start_idx+length]
            patterns.append(part)
    return zip(patterns, positions)

def build_one(amount_digits:int, max_substring_len:int, num:BigNum):
    time_start = perf_counter()
    patterns_done = 0
    patterns_total = amount_digits * max_substring_len

    conn = sqlite3.connect(Paths.sqlite_path)
    cursor = conn.cursor()

    print(f"creating table {num.table_name}"+" "*50)
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS "{num.table_name}" (string BLOB PRIMARY KEY, position INTEGER)""")

    for startpos in range(0, amount_digits, Sizes.pairs_per_insert):
        chunk = num[startpos : startpos + Sizes.pairs_per_insert]
        patterns = get_patterns(chunk, max_substring_len, startpos+1)
        cursor.executemany(f"""INSERT OR IGNORE INTO "{num.table_name}" VALUES (?, ?)""", patterns)
        conn.commit()
        patterns_done += Sizes.pairs_per_insert * max_substring_len

        # progress printing
        time_elapsed = perf_counter() - time_start
        time_elapsed_f = format_time(time_elapsed)
        speed_pattern = patterns_done / time_elapsed
        speed_pattern_f = format_size(speed_pattern, "/s")
        eta = format_time(patterns_total / speed_pattern - time_elapsed)
        print(" "*120+"\r"+f"elapsed:{time_elapsed_f}\t eta:{eta}\t patterns:{speed_pattern_f}", end="\r")

    conn.close()
    total_time = perf_counter()-time_start
    print(f"done building search string table {num.table_name} in {format_time(total_time)}")

class SharedMem:
    nums_queue:Queue[BigNum] = Queue()
    amount_digits:int
    max_substring_len:int
    files_total:int
    files_done:int = 0
    patterns_total:int
    patterns_done:int = 0
    time_start:float
    finished:bool = False
    tmp_tables:Queue[Path] = Queue()
    tmp_tables_dir:Path

def progress_mt(mem:SharedMem):
    while not mem.finished:
        sleep(0.3)
        try:
            time_elapsed = perf_counter() - mem.time_start
            time_elapsed_f = format_time(time_elapsed)
            speed_pattern = mem.patterns_done / time_elapsed
            speed_pattern_f = format_size(speed_pattern, "/s")
            eta = format_time(mem.patterns_total / speed_pattern - time_elapsed)
            print(" "*120+"\r"+f"elapsed:{time_elapsed_f}\t eta:{eta}\t patterns:{speed_pattern_f}", end="\r")
        except:
            ...

def build_mt(mem:SharedMem):
    while not mem.nums_queue.empty():
        num = mem.nums_queue.get()
        db_path = mem.tmp_tables_dir/Path(num.table_name)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"""CREATE TABLE IF NOT EXISTS "{num.table_name}" (string BLOB PRIMARY KEY, position INTEGER)""")

        for startpos in range(0, mem.amount_digits, Sizes.pairs_per_insert):
            chunk = num[startpos : startpos + Sizes.pairs_per_insert]
            patterns = get_patterns(chunk, mem.max_substring_len, startpos+1)
            cursor.executemany(f"""INSERT OR IGNORE INTO "{num.table_name}" VALUES (?, ?)""", patterns)
            conn.commit()
            mem.patterns_done += Sizes.pairs_per_insert * mem.max_substring_len

        conn.close()
        mem.files_done += 1
        mem.tmp_tables.put(db_path)

def build_many(amount_digits:int, max_substring_len:int, nums:list[BigNum]):
    mem = SharedMem()
    mem.amount_digits = amount_digits
    mem.max_substring_len = max_substring_len
    mem.time_start = perf_counter()
    mem.files_total = len(nums)
    mem.patterns_total = amount_digits * max_substring_len * len(nums)
    mem.tmp_tables_dir = Path("tmp_part_tables")
    mem.tmp_tables_dir.mkdir()

    for n in nums:
        mem.nums_queue.put(n)

    progress_thread = Thread(target=progress_mt, args=(mem,))
    progress_thread.start()

    threads = []
    amt_processes = min(Sizes.max_processes, len(nums))
    for id in range(amt_processes):
        t = Thread(target=build_mt, args=(mem,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    mem.finished = True
    progress_thread.join()

    print("\nDone creating tables, now merging them")
    conn = sqlite3.connect(Paths.sqlite_path)
    cursor = conn.cursor()
    while not mem.tmp_tables.empty():
        tmp_db_path = mem.tmp_tables.get()
        cursor.execute(f"""ATTACH DATABASE "{str(tmp_db_path)}" AS tmp_db""")
        cursor.execute("SELECT name FROM tmp_db.sqlite_master WHERE type='table'")
        table_name = cursor.fetchone()[0]
        cursor.execute(f"""
CREATE TABLE IF NOT EXISTS "{table_name}" AS SELECT * FROM tmp_db."{table_name}"
""")
        cursor.execute(f"DETACH DATABASE tmp_db")
        tmp_db_path.unlink()
    conn.commit()
    conn.close()

    for file in mem.tmp_tables_dir.iterdir():
        file.unlink()
    mem.tmp_tables_dir.rmdir()

    print("Done!")

