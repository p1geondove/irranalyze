# tests.py - various unittests

import unittest

from scripts import BigNum, get_one, const, build_db
from scripts.var import Paths, Sizes, Switches
from scripts.search import search, search_db, search_mp, search_quick, search_st, multi_search_db, multi_search_mp, multi_search_quick, multi_search_st

from pathlib import Path

PI_PATH_DEC_TXT = Path("/home/p1geon/bignum/Pi - Dec - Chudnovsky.txt")
PI_PATH_HEX_TXT = Path("/home/p1geon/bignum/Pi - Hex - Chudnovsky.txt")
PI_PATH_DEC_YCD = Path("/home/p1geon/bignum/Pi - Dec - Chudnovsky - 0.ycd")
PI_PATH_HEX_YCD = Path("/home/p1geon/bignum/Pi - Hex - Chudnovsky - 0.ycd")

class TestSubsript(unittest.TestCase):
    """ SUBSCRIPT """
    def setUp(self) -> None:
        Path("./identify_only.sqlite").copy("irranalyze.sqlite")

    # --- INT ---
    def test_integer_zero_index(self):
        Switches.one_indexed = False
        pi = BigNum(PI_PATH_DEC_TXT)
        self.assertEqual(pi[0], b"1")
        self.assertEqual(pi[1], b"4")
        self.assertEqual(pi[40_000_000], b"9")

    def test_integer_one_index(self):
        Switches.one_indexed = True
        pi = BigNum(PI_PATH_DEC_TXT)
        self.assertEqual(pi[0], b".")
        self.assertEqual(pi[1], b"1")
        self.assertEqual(pi[40_000_000], b"7")

    # --- SLICE ---
    def test_slice_zero_index(self):
        Switches.one_indexed = False
        pi = BigNum(PI_PATH_DEC_TXT)
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
        pi = BigNum(PI_PATH_DEC_TXT)
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
        Path("./identify_only.sqlite").copy("irranalyze.sqlite")

    # --- STRING SUBSCRIPT ---
    def test_search_str_zero_index(self):
        Switches.one_indexed = False
        pi = BigNum(PI_PATH_DEC_TXT)
        self.assertEqual(pi["1"], 0)
        self.assertEqual(pi["14159"], 0)
        self.assertEqual(pi["12345678"], 186557266)

    def test_search_str_one_index(self):
        Switches.one_indexed = True
        pi = BigNum(PI_PATH_DEC_TXT)
        self.assertEqual(pi["1"], 1)
        self.assertEqual(pi["14159"], 1)
        self.assertEqual(pi["12345678"], 186557267)

    # --- BYTES SUBSCRIPT ---
    def test_search_bytes_zero_index(self):
        Switches.one_indexed = False
        pi = BigNum(PI_PATH_DEC_TXT)
        self.assertEqual(pi[b"1"], 0)
        self.assertEqual(pi[b"14159"], 0)
        self.assertEqual(pi[b"12345678"], 186557266)

    def test_search_bytes_one_index(self):
        Switches.one_indexed = True
        pi = BigNum(PI_PATH_DEC_TXT)
        self.assertEqual(pi[b"1"], 1)
        self.assertEqual(pi[b"14159"], 1)
        self.assertEqual(pi[b"12345678"], 186557267)

    # --- QUICK ---
    def test_search_quick_zero_index(self):
        Switches.one_indexed = False
        self.assertEqual(search_quick(PI_PATH_DEC_TXT,b"1"), 0)
        self.assertEqual(search_quick(PI_PATH_DEC_TXT,b"14159"), 0)
        self.assertEqual(search_quick(PI_PATH_DEC_TXT,b"999999"), 761)
        self.assertEqual(search_quick(PI_PATH_DEC_TXT,b"12345678"), -1)

    def test_search_quick_one_index(self):
        Switches.one_indexed = True
        self.assertEqual(search_quick(PI_PATH_DEC_TXT,b"1"), 1)
        self.assertEqual(search_quick(PI_PATH_DEC_TXT,b"14159"), 1)
        self.assertEqual(search_quick(PI_PATH_DEC_TXT,b"999999"), 762)
        self.assertEqual(search_quick(PI_PATH_DEC_TXT,b"12345678"), -1)

    # --- SINGLE THREADED ---
    def test_search_st_zero_index(self):
        Switches.one_indexed = False
        self.assertEqual(search_st(PI_PATH_DEC_TXT,b"1"), 0)
        self.assertEqual(search_st(PI_PATH_DEC_TXT,b"14159"), 0)
        self.assertEqual(search_st(PI_PATH_DEC_TXT,b"999999"), 761)
        self.assertEqual(search_st(PI_PATH_DEC_TXT,b"12345678"), 186557266)

    def test_search_st_one_index(self):
        Switches.one_indexed = True
        self.assertEqual(search_st(PI_PATH_DEC_TXT,b"1"), 1)
        self.assertEqual(search_st(PI_PATH_DEC_TXT,b"14159"), 1)
        self.assertEqual(search_st(PI_PATH_DEC_TXT,b"999999"), 762)
        self.assertEqual(search_st(PI_PATH_DEC_TXT,b"12345678"), 186557267)

    # --- MULTIPROCESSING ---
    def test_search_mp_zero_index(self):
        Switches.one_indexed = False
        self.assertEqual(search_mp(PI_PATH_DEC_TXT, b"1"), 0)
        self.assertEqual(search_mp(PI_PATH_DEC_TXT, b"14159"), 0)
        self.assertEqual(search_mp(PI_PATH_DEC_TXT, b"999999"), 761)
        self.assertEqual(search_mp(PI_PATH_DEC_TXT, b"12345678"), 186557266)

    def test_search_mp_one_index(self):
        Switches.one_indexed = True
        self.assertEqual(search_mp(PI_PATH_DEC_TXT, b"1"), 1)
        self.assertEqual(search_mp(PI_PATH_DEC_TXT, b"14159"), 1)
        self.assertEqual(search_mp(PI_PATH_DEC_TXT, b"999999"), 762)
        self.assertEqual(search_mp(PI_PATH_DEC_TXT, b"12345678"), 186557267)

    # --- MULTI SEARCH QUICK ---
    def test_search_multi_quick_zero_index(self):
        Switches.one_indexed = False
        self.assertEqual(multi_search_quick(PI_PATH_DEC_TXT, [b"1",b"14159",b"999999",b"12345678"]), {b"1":0, b"14159":0,b"999999":761,b"12345678":-1})

    def test_search_multi_quick_one_index(self):
        Switches.one_indexed = True
        self.assertEqual(multi_search_quick(PI_PATH_DEC_TXT, [b"1",b"14159",b"999999",b"12345678"]), {b"1":1, b"14159":1,b"999999":762,b"12345678":-1})

    # --- MULTI SEARCH MULTIPROCESSING ---
    def test_search_multi_mp_zero_index(self):
        Switches.one_indexed = False
        self.assertEqual(multi_search_mp(PI_PATH_DEC_TXT, [b"1",b"14159",b"999999",b"12345678"]), {b"1":0, b"14159":0,b"999999":761,b"12345678":186557266})

    def test_search_multi_mp_one_index(self):
        Switches.one_indexed = True
        self.assertEqual(multi_search_mp(PI_PATH_DEC_TXT, [b"1",b"14159",b"999999",b"12345678"]), {b"1":1, b"14159":1,b"999999":762,b"12345678":186557267})

    # --- MULTI SEARCH SINGLE THREADED ---
    def test_search_multi_st_zero_index(self):
        Switches.one_indexed = False
        self.assertEqual(multi_search_st(PI_PATH_DEC_TXT, [b"1",b"14159",b"999999",b"12345678"]), {b"1":0, b"14159":0,b"999999":761,b"12345678":186557266})

    def test_search_multi_st_one_index(self):
        Switches.one_indexed = True
        self.assertEqual(multi_search_st(PI_PATH_DEC_TXT, [b"1",b"14159",b"999999",b"12345678"]), {b"1":1, b"14159":1,b"999999":762,b"12345678":186557267})

class TestAttributes(unittest.TestCase):
    def setUp(self) -> None:
        Path("./identify_only.sqlite").copy("irranalyze.sqlite")

    def test_first_digits_zero_indexed(self):
        Switches.one_indexed = False
        Sizes.first_digits_amount = 100_000
        pi = BigNum(PI_PATH_DEC_TXT)
        self.assertEqual(len(pi.first_digits), 100_000)
        self.assertEqual(pi.first_digits[:5], b"14159")
        self.assertEqual(pi.first_digits[-5:], b"24646")

    def test_first_digits_one_indexed(self):
        Switches.one_indexed = True
        Sizes.first_digits_amount = 100_000
        pi = BigNum(PI_PATH_DEC_TXT)
        self.assertEqual(len(pi.first_digits), 100_000)
        self.assertEqual(pi.first_digits[:5], b".1415")
        self.assertEqual(pi.first_digits[-5:], b"62464")

    def test_iter_zero_index(self):
        Switches.one_indexed = False
        pi = BigNum(PI_PATH_DEC_TXT)
        self.assertEqual(b"".join([n for n,_ in zip(pi, range(10))]), b"1415926535")

    def test_iter_one_index(self):
        Switches.one_indexed = True
        pi = BigNum(PI_PATH_DEC_TXT)
        self.assertEqual(b"".join([n for n,_ in zip(pi, range(10))]), b"1415926535")

    def test_to_base(self):
        pi_dec_txt = BigNum(PI_PATH_DEC_TXT)
        pi_hex_txt = BigNum(PI_PATH_HEX_TXT)
        pi_dec_ycd = BigNum(PI_PATH_DEC_YCD)
        pi_hex_ycd = BigNum(PI_PATH_HEX_YCD)

        self.assertEqual(pi_dec_txt.to_base(10,10), "3.14159265")
        self.assertEqual(pi_hex_txt.to_base(10,10), "3.14159265")
        self.assertEqual(pi_dec_ycd.to_base(10,10), "3.14159265")
        self.assertEqual(pi_hex_ycd.to_base(10,10), "3.14159265")

if __name__ == "__main__":
    unittest.main()
