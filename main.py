from scripts.base_conv import to_base
from scripts.file_finder import one_of_each
from scripts.ntimer import perf_counter_ns, fmt_ns
from claude2 import Solution

amt = 9000
base = 16
_warmup = 1

times_claude = []
times_mainz = []

for x in range(_warmup):
    for file in one_of_each():
        start_ns = perf_counter_ns()
        Solution().base_convert(file.path, base, amt)
        times_claude.append(fmt_ns(perf_counter_ns()-start_ns))
        
        start_ns = perf_counter_ns()
        to_base(file.path, base, amt)
        times_mainz.append(fmt_ns(perf_counter_ns()-start_ns))

print('claude',min(times_claude))
print('mainz',min(times_mainz))

"""
pi to base2

100 = 1.3ms / 8ms
200 = 1.3ms / 8ms
400 = 1.3ms / 8ms
800 = 1.3ms / 1.75ms # next day
1600 = 1.5ms / 2.6ms
3200 = 2.5ms / 4.5ms
6400 = 8.2ms / 7.5ms
12800 = 15.3ms / 22.5ms
25600 = 100ms / 30ms
51200 = 300ms / 100ms
102400 = 1s / 330ms

base conversion only
100    = 30us
1000   = base2:300us base94:1.06ms
10000  = base2:14ms  base94:68ms
100000 = base2:1.02s base94:7.8s

200 = 55us / 75us
400 = 100us / 190us
800 = 220us / 800us
1600 = 600us / 2.3ms
3200 = 1.6ms / 8ms
6400 = 6.6ms / 29ms
12800 = 21ms / 110ms
25600 = 70ms / 450ms
51200 = 270ms / 1.7s
102400 = 1s / 8s
204800 = 4.2s / 65s

base16
...
"""
