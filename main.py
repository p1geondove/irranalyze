from scripts import bignum
from scripts.search import search
from string import ascii_lowercase

def txt_to_num(txt:str):
    txt = txt.lower()
    table = {c:f"{p:02d}" for p,c in enumerate(ascii_lowercase)}
    return "".join(table[c] if c.isalpha() else c for c in txt)

def main():
    #file = bignum.get_one("pi", 10, "txt")
    file = bignum.BigNum("/home/p1geon/documents/bignum/Pi - Dec - Chudnovsky 100b.txt")
    if file is None:
        return

    while True:
        try:
            pattern = txt_to_num(input("pattern: ")).encode()
            pos = search(file, pattern)
            print(pos)
        except KeyboardInterrupt:
            return
        except EOFError:
            return

if __name__ == "__main__":
    main()
