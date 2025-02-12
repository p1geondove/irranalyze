from time import *

def fmt_ns(time_ns:int) -> str:
    scales = {
        'ns' : 1e0,
        'us' : 1e3,
        'ms' : 1e6,
        's' : 1e9,
    }

    for name, size in scales.items():
        if time_ns < size*1e3:
            return f'{time_ns/size:.2f}{name}'
    
    time_s = time_ns // 10**9
    if time_s/60/60/24 > 1:
        return f'{int(time_s/60/60/24)} days'
    elif time_s/60/60 > 1:
        return f'{int(time_s/60/60):2d}:{int(time_s//60)%60:2d} hh:mm'
    elif time_s/60 > 1:
        return f'{time_s//60:2d}:{time_s%60:2d} mm:ss'
        
def timer(func):
    def wrapper(*args, **kwargs):
        start_ns = perf_counter_ns()
        res = func(*args, **kwargs)
        time_ns = perf_counter_ns() - start_ns
        print(f'{func.__name__} took {fmt_ns(time_ns)}')
        return res
    return wrapper

def time_func(func, *args, **kwargs):
    start_ns = perf_counter_ns()
    res = func(*args, **kwargs)
    time_ns = perf_counter_ns() - start_ns
    print(f'{func.__name__} took {fmt_ns(time_ns)}')
    return res

def x_per_sec(old_ns:int, amt:int|float, new_ns:int = None) -> str:
    new_ns:int = perf_counter_ns() if new_ns is None else new_ns
    amt_s:float = amt / ((new_ns-old_ns) / 1e9)
    scales = {
        '' : 1e0,
        'k' : 1e3,
        'm' : 1e6,
        'g' : 1e9,
    }
    for name, size in scales.items():
        if amt_s < size*1e3:
            return f'{amt_s/size:.1f}{name} terms / s'

def speedtest(func):
    times = []
    start_wall = perf_counter_ns()

    def wrapper(*args, **kwargs):
        while perf_counter_ns() - start_wall < 3e9:
            start_ns = perf_counter_ns()
            func(*args, **kwargs)
            time_ns = perf_counter_ns() - start_ns
            times.append(time_ns)

        print(f'{len(times)}x{func.__name__} in ~3s | min:{fmt_ns(min(times))} | max:{fmt_ns(max(times))} | avg:{fmt_ns(sum(times)/len(times))}')
        # print(f'first: {fmt_ns(times[0])}')
    return wrapper