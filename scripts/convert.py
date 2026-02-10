from string import ascii_lowercase

def txt_to_num(txt:str) -> str:
    txt = txt.lower()
    table = {c:f"{p:02d}" for p,c in enumerate(ascii_lowercase)}
    return "".join(table[c] if c.isalpha() else c for c in txt)

def num_to_txt(num:str) -> str:
    if not num.isnumeric():
        raise ValueError("input must be numeric")
    pairs = (int(a+b) for a,b in zip(num[::2], num[1::2]))
    return "".join(chr(p+97) for p in pairs)

