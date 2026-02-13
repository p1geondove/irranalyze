from time import perf_counter
from math import log10

def format_size(size:int|float, suffix:str="", ndigits:int=2, capitalized:bool=False):
    if size == 0: return "0"+suffix
    prefixes = " kmgtpez"
    index = int(log10(size)/3)
    prefix = prefixes[index].upper() if capitalized else prefixes[index]
    return f"{round(size/10**(index*3), max(0, abs(ndigits))):g}{prefix}{suffix}"

def format_time(time: float):
    if time == 0:
        return "0s"
    if time / 60 / 60 / 24 > 1:
        return f"{int(time/60/60/24)} days"
    elif time / 60 / 60 > 1:
        return f"{int(time/60/60):02d}:{int(time//60)%60:02d} hh:mm"
    elif time / 60 > 1:
        return f"{int(time//60):02d}:{int(time%60):02d} mm:ss"

    neg = False
    if time < 0:
        neg = True
        time = abs(time)

    mag = min(3,int(abs(log10(time)-3)/3))
    return f"{'-' if neg else ''}{time*10**(3*mag):.1f}{' mun'[mag]}s"

def timer(func):
    def wrapper(*args, **kwargs):
        start = perf_counter()
        res = func(*args, **kwargs)
        print(f"{func.__name__} took {format_time(perf_counter() - start)}")
        return res
    return wrapper

