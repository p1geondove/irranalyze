# tests.py - various unittests

import unittest

from scripts import BigNum, build_db
from scripts.var import Paths, Sizes, Switches
from scripts.search import search_mp, search_quick, search_st, multi_search_mp, multi_search_quick, multi_search_st
from scripts.identify import identify

from pathlib import Path

"""
To run these tests you need to have 4 number files ready, all pi, 2 hex, 2 dec, of which 2 are txt and 2 are ydc, all must be 1b decimal digits exactly
To get those numbers i ran y-cruncher:
open y-crunher -> custom/4 -> decimal digits/3 -> "1b" -> start/0, now you should have the decimal and hexadecimal txt file, now make the ycd file
open y-crunher -> custom/4 -> decimal digits/3 -> "1b" -> digit output/5 -> format/1 -> compressed YCD/2 -> done/0 -> start/0 now you should have both the txt and ycd file both as dex and hex
now also make sure to modify the paths below
"""

IDENTIFY_DB_PATH = Path("identify_only.sqlite").resolve()
BACKUP_DB_PATH = Path("irranalyze.sqlite.bak").resolve()
PATH_PI_DEC_TXT = Path("/home/p1geon/bignum/Pi - Dec - Chudnovsky.txt") # md5: 3901670f41a84174103bd6a8f07651c0 content:"3.141...45519"
PATH_PI_HEX_TXT = Path("/home/p1geon/bignum/Pi - Hex - Chudnovsky.txt") # md5: c4cfd8e5b903aec50818852592ccc330 content:"3.243...dffa2"
PATH_PI_DEC_YCD = Path("/home/p1geon/bignum/Pi - Dec - Chudnovsky - 0.ycd") # md5: e9b8e58f79821c4d77ea17c00cbb6d74 content:"#Comp...��Y�i" (8c d5 59 fc 69)
PATH_PI_HEX_YCD = Path("/home/p1geon/bignum/Pi - Hex - Chudnovsky - 0.ycd") # md5: 282ea2a79aba22eed2f7e4165ab8fff7 content:"#Comp...�D	�F" (ae 44 09 ad 46)

INFO_PI_DEC_TXT = identify(PATH_PI_DEC_TXT)

# these are pattern-position pairs grabbed from angio.net/pi, so pi, base 10 and one indexed, 62 should be enough to cover, feel free to add...
TRUTHS_PI_DEC_TXT = {
    "0":32,
    "1":1,
    "2":6,
    "3":9,
    "4":2,
    "5":4,
    "6":7,
    "7":13,
    "8":11,
    "9":5,
    "333333":710100,
    "3333333":710100, # not sure why but this was a bug in prior version...
    "14159":1,
    "999999":762,
    "12345678":186557266,
    "01234567":112099767,
    "11":94,
    "111":153,
    "1111":12700,
    "11111":32788,
    "111111":255945,
    "1111111":4657555,
    "11111111":159090113,
    '29309616143204':32760, # these lie on potential chunk borders 2**15 - 2**24
    '47272107347413':65528,
    '12267858143917':131064,
    '68747186982843':262136,
    '55176165371188':524280,
    '63742920415458':1048568,
    '66431237915711':2097144,
    '63831112096475':4194296,
    '34042511939864':8388600,
    '27318857182539':16777208
}

TRUTHS_PI_DEC_YCD={}

def reset_db():
    Paths.sqlite_path.unlink()
    IDENTIFY_DB_PATH.copy(Paths.sqlite_path)

class TestSubsript(unittest.TestCase):
    """ SUBSCRIPT """
    def setUp(self) -> None:
        reset_db()

    # --- INT ---
    def test_integer_zero_index(self):
        Switches.one_indexed = False
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(pi[0], b"1")
        self.assertEqual(pi[1], b"4")
        self.assertEqual(pi[40_000_000], b"9")

    def test_integer_one_index(self):
        Switches.one_indexed = True
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(pi[0], b".")
        self.assertEqual(pi[1], b"1")
        self.assertEqual(pi[40_000_000], b"7")

    # --- SLICE ---
    def test_slice_zero_index(self):
        Switches.one_indexed = False
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(pi[:0], b"")
        self.assertEqual(pi[:5], b"14159")
        self.assertEqual(pi[40_000_000:40_000_005], b"91474")
        self.assertEqual(pi[-5:], b"45519")
        self.assertEqual(pi[-5:-1], b"4551")
        self.assertEqual(pi[0:5], pi[:5])
        self.assertEqual(pi[1:5], b"4159")
        self.assertEqual(pi[1:0], b"")
        self.assertEqual(pi[3::-1], b"5141")
        self.assertEqual(pi[3:0:-1], b"514")
        self.assertEqual(pi[5::-2], b'254')

    def test_slice_one_index(self):
        Switches.one_indexed = True
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(pi[:0], b"")
        self.assertEqual(pi[:5], b".1415")
        self.assertEqual(pi[40_000_000:40_000_005], b"79147")
        self.assertEqual(pi[-5:], b"45519")
        self.assertEqual(pi[-5:-1], b"4551")
        self.assertEqual(pi[0:5], pi[:5])
        self.assertEqual(pi[1:5], b"1415")
        self.assertEqual(pi[1:0], b"")
        self.assertEqual(pi[3::-1], b"141.")
        self.assertEqual(pi[3:0:-1], b"141")
        self.assertEqual(pi[5::-2], b'911')


class TestSearch(unittest.TestCase):
    """ SEARCH """
    def setUp(self) -> None:
        reset_db()

    # --- STRING SUBSCRIPT ---
    def test_search_str_zero_index(self):
        Switches.one_indexed = False
        pi = BigNum(PATH_PI_DEC_TXT)
        for pat,pos in TRUTHS_PI_DEC_TXT.items():
            self.assertEqual(pi[pat], pos-1)

    def test_search_str_one_index(self):
        Switches.one_indexed = True
        pi = BigNum(PATH_PI_DEC_TXT)
        for pat,pos in TRUTHS_PI_DEC_TXT.items():
            self.assertEqual(pi[pat], pos)

    # --- BYTES SUBSCRIPT ---
    def test_search_bytes_zero_index(self):
        Switches.one_indexed = False
        pi = BigNum(PATH_PI_DEC_TXT)
        for pat,pos in TRUTHS_PI_DEC_TXT.items():
            self.assertEqual(pi[pat.encode()], pos-1)

    def test_search_bytes_one_index(self):
        Switches.one_indexed = True
        pi = BigNum(PATH_PI_DEC_TXT)
        for pat,pos in TRUTHS_PI_DEC_TXT.items():
            self.assertEqual(pi[pat.encode()], pos)

    # --- QUICK ---
    def test_search_quick_zero_index(self):
        Switches.one_indexed = False
        for pat,pos in TRUTHS_PI_DEC_TXT.items():
            self.assertIn(search_quick(INFO_PI_DEC_TXT,pat.encode()), {pos-1,-1})

    def test_search_quick_one_index(self):
        Switches.one_indexed = True
        for pat,pos in TRUTHS_PI_DEC_TXT.items():
            self.assertIn(search_quick(INFO_PI_DEC_TXT,pat.encode()), {pos,-1})

    # --- SINGLE THREADED ---
    def test_search_st_zero_index(self):
        Switches.one_indexed = False
        for pat,pos in TRUTHS_PI_DEC_TXT.items():
            self.assertEqual(search_st(INFO_PI_DEC_TXT, pat.encode()), pos-1)

    def test_search_st_one_index(self):
        Switches.one_indexed = True
        for pat,pos in TRUTHS_PI_DEC_TXT.items():
            self.assertEqual(search_st(INFO_PI_DEC_TXT, pat.encode()), pos)

    # --- MULTIPROCESSING ---
    def test_search_mp_zero_index(self):
        Switches.one_indexed = False
        for pat,pos in TRUTHS_PI_DEC_TXT.items():
            self.assertEqual(search_mp(INFO_PI_DEC_TXT, pat.encode()), pos-1)

    def test_search_mp_one_index(self):
        Switches.one_indexed = True
        for pat,pos in TRUTHS_PI_DEC_TXT.items():
            self.assertEqual(search_mp(INFO_PI_DEC_TXT, pat.encode()), pos)

    # --- MULTI SEARCH QUICK ---
    def test_search_multi_quick_zero_index(self):
        Switches.one_indexed = False
        patterns = list(map(str.encode, TRUTHS_PI_DEC_TXT.keys()))
        expected = {pat.encode():(pos-1 if pos < Sizes.first_digits_amount else -1) for pat,pos in TRUTHS_PI_DEC_TXT.items()}
        self.assertEqual(multi_search_quick(INFO_PI_DEC_TXT, patterns), expected)
        
    def test_search_multi_quick_one_index(self):
        Switches.one_indexed = True
        patterns = list(map(str.encode, TRUTHS_PI_DEC_TXT.keys()))
        expected = {pat.encode():(pos if pos < Sizes.first_digits_amount else -1) for pat,pos in TRUTHS_PI_DEC_TXT.items()}
        self.assertEqual(multi_search_quick(INFO_PI_DEC_TXT, patterns), expected)

    # --- MULTI SEARCH MULTIPROCESSING ---
    def test_search_multi_mp_zero_index(self):
        Switches.one_indexed = False
        patterns = list(map(str.encode, TRUTHS_PI_DEC_TXT.keys()))
        expected = {pat.encode():pos-1 for pat,pos in TRUTHS_PI_DEC_TXT.items()}
        self.assertEqual(multi_search_mp(INFO_PI_DEC_TXT, patterns), expected)

    def test_search_multi_mp_one_index(self):
        Switches.one_indexed = True
        patterns = list(map(str.encode, TRUTHS_PI_DEC_TXT.keys()))
        expected = {pat.encode():pos for pat,pos in TRUTHS_PI_DEC_TXT.items()}
        self.assertEqual(multi_search_mp(INFO_PI_DEC_TXT, patterns), expected)

    # --- MULTI SEARCH SINGLE THREADED ---
    def test_search_multi_st_zero_index(self):
        Switches.one_indexed = False
        patterns = list(map(str.encode, TRUTHS_PI_DEC_TXT.keys()))
        expected = {pat.encode():pos-1 for pat,pos in TRUTHS_PI_DEC_TXT.items()}
        self.assertEqual(multi_search_st(INFO_PI_DEC_TXT, patterns), expected)

    def test_search_multi_st_one_index(self):
        Switches.one_indexed = True
        patterns = list(map(str.encode, TRUTHS_PI_DEC_TXT.keys()))
        expected = {pat.encode():pos for pat,pos in TRUTHS_PI_DEC_TXT.items()}
        self.assertEqual(multi_search_st(INFO_PI_DEC_TXT, patterns), expected)

class TestAttributes(unittest.TestCase):
    def setUp(self) -> None:
        reset_db()

    def test_first_digits_zero_indexed(self):
        Switches.one_indexed = False
        Sizes.first_digits_amount = 100_000
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(len(pi.first_digits), 100_000)
        self.assertEqual(pi.first_digits[:5], b"14159")
        self.assertEqual(pi.first_digits[-5:], b"24646")

    def test_first_digits_one_indexed(self):
        Switches.one_indexed = True
        Sizes.first_digits_amount = 100_000
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(len(pi.first_digits), 100_000)
        self.assertEqual(pi.first_digits[:5], b".1415")
        self.assertEqual(pi.first_digits[-5:], b"62464")

    def test_iter_zero_index(self):
        Switches.one_indexed = False
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(b"".join([n for n,_ in zip(pi, range(10))]), b"1415926535")

    def test_iter_one_index(self):
        Switches.one_indexed = True
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(b"".join([n for n,_ in zip(pi, range(10))]), b"1415926535")

    def test_to_base(self):
        pi_dec_txt = BigNum(PATH_PI_DEC_TXT)
        pi_hex_txt = BigNum(PATH_PI_HEX_TXT)
        pi_dec_ycd = BigNum(PATH_PI_DEC_YCD)
        pi_hex_ycd = BigNum(PATH_PI_HEX_YCD)

        self.assertEqual(pi_dec_txt.to_base(10,10), "3.14159265")
        self.assertEqual(pi_hex_txt.to_base(10,10), "3.14159265")
        self.assertEqual(pi_dec_ycd.to_base(10,10), "3.14159265")
        self.assertEqual(pi_hex_ycd.to_base(10,10), "3.14159265")

if __name__ == "__main__":
    BACKUP_DB_PATH.unlink(True)
    IDENTIFY_DB_PATH.unlink(True)
    if Paths.sqlite_path.exists():
        Paths.sqlite_path.move(BACKUP_DB_PATH) # backup the current user created database
    build_db.build_identifier() # overwrite with a fresh db
    Paths.sqlite_path.copy(IDENTIFY_DB_PATH) # copy that fresh db to a safe place
    unittest.main() # run tests
    if Paths.sqlite_path.exists():
        BACKUP_DB_PATH.move(Paths.sqlite_path) # overwrite testing db with backup
        BACKUP_DB_PATH.unlink(True) # this also doesnt remove the db
    IDENTIFY_DB_PATH.unlink(True) # remove temp db for testing

