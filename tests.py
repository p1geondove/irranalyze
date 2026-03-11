# tests.py - various unittests

import unittest
from pathlib import Path

from irranalyze import BigNum, build_db
from irranalyze.var import Paths, Sizes, Switches
from irranalyze.convert import hex_to_dec, ycd_to_str, str_to_ycd

"""
To run these tests you need to have 4 number files ready, all pi, 2 hex, 2 dec, of which 2 are txt and 2 are ydc, all must be 1b decimal digits exactly
To get those numbers i ran y-cruncher:
open y-crunher -> custom/4 -> decimal digits/3 -> "1b" -> start/0, now you should have the decimal and hexadecimal txt file, now make the ycd file
Open y-crunher -> custom/4 -> decimal digits/3 -> "1b" -> digit output/5 -> format/1 -> compressed YCD/2 -> done/0 -> start/0 now you should have both the txt and ycd file both as dex and hex
These files go in your num dir, which is specified in settings.json, or by running setup.py. The filenames are important too, but i took the standard nameing scheme from y-cruncher, however make sure that the files have the right names, seen further down at "if Paths.num_dir.exists():"
If you dont provide files, the tests will still run, but with only the first 1000 digits/bytes and might miss some edge cases
Running the test is done by running "python tests.py" or "uv run tests.py", dont run "python -m unittest"
"""

# for making / swapping a temporary database
IDENTIFY_DB_PATH = Path("test_db.sqlite")
BACKUP_DB_PATH = Path("irranalyze.sqlite.bak")

# these are pattern-position pairs grabbed from angio.net/pi, so pi, base 10 and one indexed, 62 should be enough to cover, feel free to add...
TRUTHS_PI_DEC_TXT_ALL = {
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
TRUTHS_PI_DEC_TXT_SMALL = {pat:pos for pat,pos in TRUTHS_PI_DEC_TXT_ALL.items() if pos < 1000}

# check wether the use provided number files for all tests or just basic testing with limited range
REAL_FILES = False
if Paths.num_dir.exists():
    PATH_PI_DEC_TXT = Paths.num_dir / "Pi - Dec - Chudnovsky.txt" # md5: 3901670f41a84174103bd6a8f07651c0 content:"3.141...45519"
    PATH_PI_HEX_TXT = Paths.num_dir / "Pi - Hex - Chudnovsky.txt" # md5: c4cfd8e5b903aec50818852592ccc330 content:"3.243...dffa2"
    PATH_PI_DEC_YCD = Paths.num_dir / "Pi - Dec - Chudnovsky - 0.ycd" # md5: e9b8e58f79821c4d77ea17c00cbb6d74 content:"#Comp...��Y�i" (8c d5 59 fc 69)
    PATH_PI_HEX_YCD = Paths.num_dir / "Pi - Hex - Chudnovsky - 0.ycd" # md5: 282ea2a79aba22eed2f7e4165ab8fff7 content:"#Comp...�D	�F" (ae 44 09 ad 46)
    REAL_FILES = all(p.exists() for p in (PATH_PI_DEC_TXT, PATH_PI_HEX_TXT, PATH_PI_DEC_YCD, PATH_PI_HEX_YCD))

if not REAL_FILES:
    PI_DEC_TXT = "3.14159265358979323846264338327950288419716939937510582097494459230781640628620899862803482534211706798214808651328230664709384460955058223172535940812848111745028410270193852110555964462294895493038196442881097566593344612847564823378678316527120190914564856692346034861045432664821339360726024914127372458700660631558817488152092096282925409171536436789259036001133053054882046652138414695194151160943305727036575959195309218611738193261179310511854807446237996274956735188575272489122793818301194912983367336244065664308602139494639522473719070217986094370277053921717629317675238467481846766940513200056812714526356082778577134275778960917363717872146844090122495343014654958537105079227968925892354201995611212902196086403441815981362977477130996051870721134999999837297804995105973173281609631859502445945534690830264252230825334468503526193118817101000313783875288658753320838142061717766914730359825349042875546873115956286388235378759375195778185778053217122680661300192787661119590921642019"
    PI_HEX_TXT = "3.243f6a8885a308d313198a2e03707344a4093822299f31d0082efa98ec4e6c89452821e638d01377be5466cf34e90c6cc0ac29b7c97c50dd3f84d5b5b54709179216d5d98979fb1bd1310ba698dfb5ac2ffd72dbd01adfb7b8e1afed6a267e96ba7c9045f12c7f9924a19947b3916cf70801f2e2858efc16636920d871574e69a458fea3f4933d7e0d95748f728eb658718bcd5882154aee7b54a41dc25a59b59c30d5392af26013c5d1b023286085f0ca417918b8db38ef8e79dcb0603a180e6c9e0e8bb01e8a3ed71577c1bd314b2778af2fda55605c60e65525f3aa55ab945748986263e8144055ca396a2aab10b6b4cc5c341141e8cea15486af7c72e993b3ee1411636fbc2a2ba9c55d741831f6ce5c3e169b87931eafd6ba336c24cf5c7a325381289586773b8f48986b4bb9afc4bfe81b6628219361d809ccfb21a991487cac605dec8032ef845d5de98575b1dc262302eb651b8823893e81d396acc50f6d6ff383f442392e0b4482a484200469c8f04a9e1f9b5e21c66842f6e96c9a670c9c61abd388f06a51a0d2d8542f68960fa728ab5133a36eef0b6c137a3be4ba3bf0507efb2a98a1f1651d39af017666ca593e82430e888cee8619456f9fb47d84a5c33b8b5ebee06f75d885c12073401a449f56c16aa64ed3aa62363f77061bfedf72429b023d37d0d724d00a1248db0fea"
    PI_DEC_YCD = b'#Compressed Digit File\r\n\r\nFileVersion:\t1.1.0\r\n\r\nBase:\t10\r\n\r\nFirstDigits:\t3.14159265358979323846264338327950288419716939937510\r\n\r\nTotalDigits:\t0\r\n\r\nBlocksize:\t1000000000\r\nBlockID:\t0\r\n\r\nEndHeader\r\n\r\n\x00`\xe2>\xb8\xaea\xa6\x13#fW\xf6\x84f\xefV.\t\x17\x1e\xbf\xd2~c\x8e"\xa21\xfe\xa8\x16\x83C\xe1)\xbcs\xf4|\x0c\x82\xbe\x7f\xdfP\x84\x16b\x91d#X\x12K\x8e*0\x10\x80k\xda\x93\x1err\xd3\x19\xe6\x1c\xfb\x81\x0f\xf1#\xfd\xa2tcQHI\\\xa1\xe4"1;L\x00\x1e~)sp\xa1NS\xfex\x05h\xc6q \xb2\x0c4?\xe4/\xb1\x0c\x91\x8f\x97\x06\x97z~w\xdd\xec\xce\xba\xca7FT\xd0\x06J\x0f\xbf\xf4\xbex\xcb\xfd\xe1\xb8\x8ee\x1b\x15\xf0\xd6\x18<\x06\xd9Fc\xbcb\xea\x0f\xc0i\xb9\x0f\xb9\xd9i\xbbQz5\x13\x0f\x94\x83\xfb\xedH\x19<m-\x8c\xab2"\xaeI\xde\x1f\xfe\xe3\x9ac\xe2\x18\t[mv\x13\xfd\xba4\xbd\x88<\x1e\xec\xa4+I\x08\x8c7\xbdA\xb3\x0c\x1b\x17\x147\xb1\x13\xa6 [\x02W,0e\x9f&\x84\x18\xc1\x8a{\xab\xb4\x18\r\x18x\xe9\x9e\x07\xbb\xaf(\xec)}A\x8b\x00\xe9]+\xd2\xae\xf1Y\x13)c3Y\x87\xb8\xef3\x91/\xff@\xb4\xa5\xd8{?m\xaa_\x91\xf7\x1cT\x9a/\xdc\x9cY\n\xccm\xf3mvc\xd2.\xd3\xd5\xb1\x1bN\x97\x13\xeb\xf0!\xfd7q\x90a\xa49o\nk\xc3\x86%c\\\x91cE>l\xb6se\xec\xb4\x0e\x9b8\x0c\xd9\xee\x83\x93R\xc4\xd6r\xfd\x00\xd0\xaa\x03\x02\xb1\x84g\x0c\xd8\xe0ESXH*zzo\x00\x06)(\x16\xb2\xfc\x15.\xfc@\x8dz(\xc0\xf1~^\xe8\xce\\\x15\xa4\xd7h\x82\x0e[GY\xf1Ir\xb6\xbe\xb3\x12\x8d)\xc8\x19\xd7|&I\x0e4\x12Uu\x11\xd8\xb5\x88T\xca\x0c\x11\xd94\x11\xe8R\xefc\xff\xe0]\x7fh\xd9\xea\x81\x03\xcc\x98\x93\x93\x80\xb5\x02\xb1\x80;\t*\x07 P\xd3\x16NB\xf6\x9b*d\x9b\x87~F\x8a\xa2\xe2goD\xf7\x87\xf9\x17\x83\x0b\x86J\xe6 \xeaJb{\x1c![\x0f\xae\x14\x1fZ\xf8e\x8f\x81\x18\xd5\xe1jTG\xbd\x15\x1e\xd2\xc8\x01\x07[@\xd4\x8b{iS\xe8\xcc\x81\xee=\x15\x07V\x00I!B\x85\xe9p#\t\xfcr?\xe3\xb2\xf7A\xe4\xb6uoGN\xdd}Yr\xd35\xfc\xbdE\x89W#_\xf7\x18u\xa0[8\xb2\xfc\xed\xad\xe8d\x11h`\x93\xb8O\xd7X"\x1b\xed|\xd0\xe17\xc2d)\x9c\x07\xc6\x9d\xc8[B\x8d6\xd2\xdeuJ\x85\x1e\xaa#\xab5\xe1{&s\xea\xf8\xb2N5\xb3@L\xb1\x8a|\xde\x13%\xad\x80\x8c\xdc\x14\xa7\xe9p_\x1d\t\xb1R\x8f\xe9%H\x03\x9a\xf0,\xd6V\xf9\xd9s\x11\xb8\xd4\xa4\xd8\xcc\xd5$\xf9\xe4\x82\xac\xdc\xa4\x1ei\xac\x987\x9b0\x9c\x08os8(J\x17\x92DDA-\xe2\xbe\xb9\x80\xf6\x01\xe5\x81\xe7\x8c\xfc\xe2\x1e2f\xdd\xb5O\xfb\xea\x13:\xf0\xac\n\xda/F\x9df\xc4\xd5\xe6\x14u\xd4\xb2w\xf1\x88if\xb0\xbf\xb1\x89\x89\xe3\xcf\x95\xc8\x80\x13;G\xdb\x90\x1e\xf8\xcd\xafZ\xccD,*\xdf\xf7`\x7f\x1b;".\x85\xdd\xb2n\xcb\xa8<\xe9.\'!m\x08\xa5\x16\x99\x12\xa8\xfa"\x91:UT\x88VK9\x97\x10\xb7N"\xd0\xf5\x85\x86l'
    PI_HEX_YCD = b'#Compressed Digit File\r\n\r\nFileVersion:\t1.1.0\r\n\r\nBase:\t16\r\n\r\nFirstDigits:\t3.243f6a8885a308d313198a2e03707344a4093822299f31d008\r\n\r\nTotalDigits:\t0\r\n\r\nBlocksize:\t830482024\r\nBlockID:\t0\r\n\r\nEndHeader\r\n\r\n\x00\xd3\x08\xa3\x85\x88j?$Dsp\x03.\x8a\x19\x13\xd01\x9f)"8\t\xa4\x89lN\xec\x98\xfa.\x08w\x13\xd08\xe6!(El\x0c\xe94\xcffT\xbe\xddP|\xc9\xb7)\xac\xc0\x17\tG\xb5\xb5\xd5\x84?\x1b\xfby\x89\xd9\xd5\x16\x92\xac\xb5\xdf\x98\xa6\x0b1\xd1\xb7\xdf\x1a\xd0\xdbr\xfd/\x96~&j\xed\xaf\xe1\xb8\x99\x7f,\xf1E\x90|\xba\xf7l\x91\xb3G\x99\xa1$\x16\xfc\x8e\x85\xe2\xf2\x01\x08iNWq\xd8 ic~=\x93\xf4\xa3\xfeX\xa4X\xb6\x8er\x8ft\x95\r\xeeJ\x15\x82X\xcd\x8bq\xb5YZ\xc2\x1d\xa4T{\x13`\xf2*9\xd50\x9c\xf0\x85`(#\xb0\xd1\xc5\xef8\xdb\xb8\x18yA\xca\x0e\x18:`\xb0\xdcy\x8e>\x8a\x1e\xb0\x8b\x0e\x9el\'K1\xbd\xc1w\x15\xd7`\\`U\xda/\xafx\x94\xabU\xaa\xf3%U\xe6@\x14\xe8cb\x98HW\xb6\x10\xab*j9\xcaU\xce\xe8A\x114\\\xcc\xb4\x93\xe9r|\xaf\x86T\xa1*\xbcoc\x11\x14\xee\xb3\xf61\x18t]\xc5\xa9+\x1e\x93\x87\x9b\x16>\\\xce\\\xcf$l3\xba\xd6\xafw\x86\x95(\x81S2z\xaf\xb9Kk\x98H\x8f;\x93!(f\x1b\xe8\xbf\xc4\x91\xa9!\xfb\xcc\t\xd8a2\x80\xec]`\xac|H\xb1u\x85\xe9]]\x84\xef\x88\x1be\xeb\x02#&\xdc\xc5\xac\x96\xd3\x81>\x89#9B\xf4\x83\xf3om\x0f\x04 \x84\xa4\x82D\x0b.^\x9b\x1f\x9eJ\xf0\xc8i\x9al\xe9\xf6Bh\xc6!\xf0\x88\xd3\xaba\x9c\x0cgh/T\xd8\xd2\xa0Qj\xa33Q\xab(\xa7\x0f\x96\xe4;z\x13l\x0b\xefn\x98*\xfb~P\xf0;\xbav\x01\xaf9\x1de\xf1\xa1\x88\x0eC\x82>Y\xcaf\xb4\x9foE\x19\x86\xee\x8c\xbe^\x8b;\xc3\xa5\x84}s \xc1\x85\xd8uo\xe0\xa6j\xc1V\x9fD\x1a@\x06w?6b\xaa\xd3N=\x02\x9bBr\xdf\xfe\x1bH\x12\n\xd0$\xd7\xd07\x9b\xc0\xf1I\xd3\xea\x0f\xdb{\x1b\x99\x80\xc9rS\x07\xf7\xde\xe8\xf6\xd8y\xd4%;Ly\xb6\x1aP\xfe\xe3\xba\x06\xc0\x04\xbd\xe0l\x97\xc4`\x9f@\xb6O\xa9\xc1c$j\x19\xc2\x9e\\^\xb5Sl>\xafo\xfbho\xecR;\xeb\xb29\x13,\x950\x9b\x1fQ\xfcm\t\xbd^\xafDE\x81\xcc\xfdJ3\xde\x04\xd0\xe3\xbe\xb3K.\x19\x07(\x0ff\x0ft\xc8EW\xa8\xcb\xc0\xdb\xfb\xd3\xb99_\x0b\xd2\n2`\x1a\xbd\xc0yUyr,@\xc6\x00\xa1\xd6\xcc\xa3\x1f\xfb\xfe%\x9fg\xf8"2\xdb\xf8\xe9\xa5\x8e\x15ka\xfd\xdf\x16u<\xabR\x05\xad\xc8\x1eP/`\x87#\xfd\xfa\xb5=2\x82\xdf\x00>H{1S\xa0\x8co\xca\xbbW\\\x9e\xdbi\x17\xdf.V\x87\x1a\xc3\xff~(\xf6\xa8B\xd5sUO\x8c\xc62g\xac\xc8X\xca\xbb\xb0\'[i\xa0\x11\xf0\xb8]\xa3\xff\xe1\xb8\x83!\xfd\x98=\xfa\x10[\xd3\xd1-l\xb5\xfcJeE\xf8\xb6y\xe4S\x9a\x90\x97\xfbK\xbcI\x8e\xd23~\xcb\xa4\xda\xf2\xdd\xe1\xe8\xc6\xe4\xceA\x13\xfbb\x01Lw6\xda\xca \xef\xb4\x1f\xf1+\xfe\x9e~\xd0\x98\x91\x90\xaeM\xda\xdb\x95\xa0\xd5\x93'

    TMP_TESTNUM_DIR = Path("testnums")
    TMP_TESTNUM_DIR.mkdir()

    PATH_PI_DEC_TXT = (TMP_TESTNUM_DIR / "pi_dec_txt")
    PATH_PI_HEX_TXT = (TMP_TESTNUM_DIR / "pi_hex_txt")
    PATH_PI_DEC_YCD = (TMP_TESTNUM_DIR / "pi_dec_ycd")
    PATH_PI_HEX_YCD = (TMP_TESTNUM_DIR / "pi_hex_ycd")
    PATH_PI_DEC_TXT.write_text(PI_DEC_TXT)
    PATH_PI_HEX_TXT.write_text(PI_HEX_TXT)
    PATH_PI_DEC_YCD.write_bytes(PI_DEC_YCD)
    PATH_PI_HEX_YCD.write_bytes(PI_HEX_YCD)

TRUTHS_PI_DEC_TXT = TRUTHS_PI_DEC_TXT_ALL if REAL_FILES else TRUTHS_PI_DEC_TXT_SMALL


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
        self.assertEqual(pi[500], b"9")

    def test_integer_one_index(self):
        Switches.one_indexed = True
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(pi[0], b".")
        self.assertEqual(pi[1], b"1")
        self.assertEqual(pi[500], b"2")

    # --- SLICE ---
    def test_slice_zero_index(self):
        Switches.one_indexed = False
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(pi[:0], b"")
        self.assertEqual(pi[:5], b"14159")
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
        self.assertEqual(pi[0:5], pi[:5])
        self.assertEqual(pi[1:5], b"1415")
        self.assertEqual(pi[1:0], b"")
        self.assertEqual(pi[3::-1], b"141.")
        self.assertEqual(pi[3:0:-1], b"141")
        self.assertEqual(pi[5::-2], b'911')

    # --- IF GIGABYTE FILES PRESENT ---
    # --- INT ---
    @unittest.skipUnless(REAL_FILES, "requires number files")
    def test_integer_zero_index_big(self):
        Switches.one_indexed = False
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(pi[40_000_000], b"9")
        self.assertEqual(pi[-1], b"9")

    @unittest.skipUnless(REAL_FILES, "requires number files")
    def test_integer_one_index_big(self):
        Switches.one_indexed = True
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(pi[40_000_000], b"7")
        self.assertEqual(pi[-1], b"9")

    # --- SLICE ----
    @unittest.skipUnless(REAL_FILES, "requires number files")
    def test_slice_zero_index_big(self):
        Switches.one_indexed = False
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(pi[-5:], b"45519")
        self.assertEqual(pi[-5:-1], b"4551")
        self.assertEqual(pi[40_000_000:40_000_005], b"91474")

    @unittest.skipUnless(REAL_FILES, "requires number files")
    def test_slice_one_index_big(self):
        Switches.one_indexed = True
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(pi[-5:], b"45519")
        self.assertEqual(pi[-5:-1], b"4551")
        self.assertEqual(pi[40_000_000:40_000_005], b"79147")


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
        for pat,pos in pi[TRUTHS_PI_DEC_TXT.keys()].items():
            self.assertEqual(pos, TRUTHS_PI_DEC_TXT[pat.decode()]-1)

    def test_search_str_one_index(self):
        Switches.one_indexed = True
        pi = BigNum(PATH_PI_DEC_TXT)
        for pat,pos in TRUTHS_PI_DEC_TXT.items():
            self.assertEqual(pi[pat], pos)
        for pat,pos in pi[TRUTHS_PI_DEC_TXT.keys()].items():
            self.assertEqual(pos, TRUTHS_PI_DEC_TXT[pat.decode()])

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


class TestAttributes(unittest.TestCase):
    """ ATTRIBUTES """
    def setUp(self) -> None:
        reset_db()

    def test_first_digits_zero_indexed(self):
        Switches.one_indexed = False
        Sizes.first_digits_amount = 500
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(len(pi.first_digits), 500)
        self.assertEqual(pi.first_digits[:5], b"14159")
        self.assertEqual(pi.first_digits[-5:], b'94912')

    def test_first_digits_one_indexed(self):
        Switches.one_indexed = True
        Sizes.first_digits_amount = 500
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(len(pi.first_digits), 500)
        self.assertEqual(pi.first_digits[:5], b".1415")
        self.assertEqual(pi.first_digits[-5:], b'19491')

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
        self.assertEqual(pi_dec_txt.to_base("alnum",500), pi_dec_ycd.to_base("alnum",500))
        self.assertEqual(pi_dec_ycd.to_base("alnum",500), pi_hex_txt.to_base("alnum",500))
        self.assertEqual(pi_hex_txt.to_base("alnum",500), pi_hex_ycd.to_base("alnum",500))

    @unittest.skipUnless(REAL_FILES, "requires number files")
    def test_first_digits_zero_indexed_big(self):
        Switches.one_indexed = False
        Sizes.first_digits_amount = 100_000
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(len(pi.first_digits), 100_000)
        self.assertEqual(pi.first_digits[:5], b"14159")
        self.assertEqual(pi.first_digits[-5:], b"24646")

    @unittest.skipUnless(REAL_FILES, "requires number files")
    def test_first_digits_one_indexed_big(self):
        Switches.one_indexed = True
        Sizes.first_digits_amount = 100_000
        pi = BigNum(PATH_PI_DEC_TXT)
        self.assertEqual(len(pi.first_digits), 100_000)
        self.assertEqual(pi.first_digits[:5], b".1415")
        self.assertEqual(pi.first_digits[-5:], b"62464")


class TestConverters(unittest.TestCase):
    def test_hex_to_dec(self):
        pi_dec_txt = BigNum(PATH_PI_DEC_TXT)
        pi_hex_txt = BigNum(PATH_PI_HEX_TXT)
        dec_str = hex_to_dec(pi_hex_txt.mmap[:500].decode(),500)
        self.assertEqual(len(dec_str), 500)
        self.assertEqual(dec_str, pi_dec_txt.mmap[:500].decode())

    def test_str_to_ycd(self):
        pi_dec_txt = BigNum(PATH_PI_DEC_TXT)
        pi_dec_ycd = BigNum(PATH_PI_DEC_YCD)
        ycd = str_to_ycd(memoryview(pi_dec_txt)[pi_dec_txt.radix_pos+1:], 500)
        self.assertEqual(len(ycd), 500)
        self.assertEqual(ycd, pi_dec_ycd[:500])

    def test_ycd_to_str(self):
        pi_dec_txt = BigNum(PATH_PI_DEC_TXT)
        pi_dec_ycd = BigNum(PATH_PI_DEC_YCD)
        string = ycd_to_str(memoryview(pi_dec_ycd)[pi_dec_ycd.radix_pos+1:], 10, 500)
        self.assertEqual(len(string), 500)
        self.assertEqual(string, pi_dec_txt[:500].decode())


if __name__ == "__main__":
    BACKUP_DB_PATH.unlink(True) # remove old backup
    IDENTIFY_DB_PATH.unlink(True) # remove old identify_only db
    if Paths.sqlite_path.exists():
        Paths.sqlite_path.move(BACKUP_DB_PATH) # backup the current user created database
    build_db.build_identifier() # overwrite with a fresh db
    Paths.sqlite_path.copy(IDENTIFY_DB_PATH) # copy that fresh db to a safe place
    unittest.main(exit=False) # run tests
    if Paths.sqlite_path.exists():
        BACKUP_DB_PATH.move(Paths.sqlite_path) # overwrite testing db with backup
        BACKUP_DB_PATH.unlink(True) # this also doesnt remove the db
    IDENTIFY_DB_PATH.unlink(True) # remove temp db for testing, somehow still there after tests

