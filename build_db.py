#!/usr/bin/python

import sqlite3
from itertools import chain
from threading import Thread, Lock
from queue import Queue
from time import perf_counter, sleep

from scripts.bignum import BigNum, get_all
from scripts.const import SQLITE_PATH, FIRST_DIGITS_AMOUNT, IDENTIFY_TABLE_NAME
from scripts.helper import format_size, format_time

def build_identifier():
    from hashlib import md5
    import mpmath
    from mpmath import e, pi, ln, sqrt, inf, root, nsum, fsum, nprod, findroot
    import sympy

    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {IDENTIFY_TABLE_NAME} (hash BLOB PRIMARY KEY, name TEXT)")


    mpmath.mp.dps = 200 # only 100 digits are used but for big expressions evaluation can yield high error so doubling precision should be good enough
    primes = [mpmath.mpf(p) for p in sympy.primerange(1e6)]
    e = mpmath.e
    pi = mpmath.pi
    root2 = sqrt(2)
    root3 = sqrt(3)
    ln2 = ln(2)
    gamma = -mpmath.psi(1/3,1)

    print("evaluating oneliners")
    constants = [
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

    print("calculating hashes and inserting into db")
    for num,name in constants:
        blob = md5(str(num)[:100].encode()).digest()
        cursor.execute(f"INSERT OR IGNORE INTO identify (hash, name) VALUES (?, ?)", (blob, name))

    """ functions """
    print("iterating single argument over functions")

    def check_int(num, tol=mpmath.mpf("1e-50")):
        return num%1<tol or -num%1<tol

    recorded = [c for c,_ in constants]
    def check_recorded(num, tol=mpmath.mpf("1e-50")):
        for c in recorded:
            if mpmath.almosteq(num,c,abs_eps=tol):
                return True
        return False

    inputs = [
        (x,str(x)) for x in range(11)
    ] + [
        (1/mpmath.mpf(x),"1/"+str(x)) for x in range(1,11)
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
            if check_int(num) or check_recorded(num):
                continue
            recorded.append(num)
            blob = md5(str(num)[:100].encode()).digest()
            print(f"{name}:{blob}", end=" "*20+"\r")
            cursor.execute(f"INSERT OR IGNORE INTO identify (hash, name) VALUES (?, ?)", (blob, name))

    # two argument
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
                if check_int(num) or check_recorded(num):
                    continue
                recorded.append(num)
                blob = md5(str(num)[:100].encode()).digest()
                print(f"{name}:{blob}", end=" "*20+"\r")
                cursor.execute(f"INSERT OR IGNORE INTO identify (hash, name) VALUES (?, ?)", (blob, name))

    conn.commit()
    conn.close()
    print("\ndone building identifier table")

class SharedMem:
    file_queue:Queue[BigNum] = Queue()
    db_lock:Lock = Lock()
    amt_digits:int
    substring_len:int

    files_total:int = 0
    files_done:int = 0
    patterns_total:int = 0
    patterns_done:int = 0
    done:bool = False

def progress(mem:SharedMem):
    time_start = perf_counter()
    patterns_total = mem.amt_digits * mem.substring_len * mem.files_total

    while not mem.done:
        sleep(0.2)
        if mem.patterns_done == 0: continue
        time_elapsed = perf_counter() - time_start
        time_elapsed_f = format_time(time_elapsed)
        speed_pattern = mem.patterns_done / time_elapsed
        speed_pattern_f = format_size(speed_pattern, "/s")
        eta = format_time(patterns_total / speed_pattern - time_elapsed)
        print(" "*100+"\r"+f"elapsed:{time_elapsed_f}\t eta:{eta}\t patterns:{speed_pattern_f}\t files:{mem.files_done}/{mem.files_total}", end=" "*10+"\r")

def get_patterns(chunk:str|bytes, max_length:int=10, offset:int=0):
    positions = chain.from_iterable((x+offset,)*max_length for x in range(len(chunk)-max_length))
    patterns = []
    for start_idx in range(len(chunk)-max_length):
        for length in range(1,max_length+1):
            part = chunk[start_idx:start_idx+length]
            patterns.append(part)
    return zip(patterns, positions)

def _build_const(mem:SharedMem):
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    patterns_per_insert = 100000
    substring_len = mem.substring_len
    amt_digits = mem.amt_digits

    while not mem.file_queue.empty():
        num = mem.file_queue.get()

        with mem.db_lock:
            string_datatype = "TEXT" if num.format == "txt" else "BLOB"
            print(f"creating table {num.table_name} of type {string_datatype} | INTEGER")
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS "{num.table_name}" (string {string_datatype} PRIMARY KEY, position INTEGER)""")

        for startpos in range(0, amt_digits, patterns_per_insert):
            chunk = num[startpos:startpos+patterns_per_insert]
            patterns = get_patterns(chunk, substring_len, startpos+1)
            with mem.db_lock:
                cursor.executemany(f"""INSERT OR IGNORE INTO "{num.table_name}" VALUES (?, ?)""", patterns)
                conn.commit()
            mem.patterns_done += substring_len * patterns_per_insert
        mem.files_done += 1

def build_const(amount_digits:int=-1, max_substring_len:int=10, num_workers:int=4):
    time_start = perf_counter()

    if amount_digits==-1:
        amount_digits = FIRST_DIGITS_AMOUNT

    mem = SharedMem()
    mem.amt_digits = amount_digits
    mem.substring_len = max_substring_len

    for num in set(get_all()):
        mem.files_total += 1
        mem.file_queue.put(num)

    prog = Thread(target=progress, args=(mem, ))

    threads = []
    for _ in range(num_workers):
        t = Thread(target=_build_const, args=(mem,))
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
    build_identifier()
    build_const(10**6,6)
