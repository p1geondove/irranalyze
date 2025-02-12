import threading
import queue
import ntimer
import os
from math import log, log10
from time import sleep
import gmpy2

class SharedData:
    size = 0
    writing_speed = 0
    generate_speed = 0
    running = True
    q:queue.Queue = None
    sample = 'a'

@ntimer.timer
def get_int(file_path:str, amt_digits=100) -> int:
    first_size = 100
    chunk_size = 4000

    with open(file_path, 'r') as file:
        first_chunk = file.read(first_size)
        decimal_spot = first_chunk.find('.') + 1
        num_size = first_size - decimal_spot # equiv to int(log10(num))

        if not decimal_spot: # invalid file, no decimal found
            return 0
        
        if first_size-decimal_spot > amt_digits: # output digits already in the first chunk
            return int(first_chunk[decimal_spot : decimal_spot + amt_digits])
        
        num = int(first_chunk[decimal_spot:]) # start int
        chunk = file.read(chunk_size) # first big chunk, after the small initial

        while chunk and num_size < amt_digits:
            if num_size+chunk_size > amt_digits:
                chunk = chunk[:amt_digits - num_size - chunk_size] # crop chunk to fit in desired amt_digits
                return num * 10**(len(chunk)) + int(chunk) # return final int
            
            num = num * 10**chunk_size + int(chunk) # bitshift in base 10 and add chunk
            num_size += chunk_size 
            chunk = file.read(chunk_size)
    
    return num

def generator_thread(dec_int, digits_amt_out, batch_size:int, shared_data:SharedData):
    base_notation = 'abcdefghijklmnopqrstuvwxyz'
    base = len(base_notation)
    big_int = 10**(int(log10(dec_int))+1)
    time_tmp = ntimer.perf_counter_ns()

    for _ in range(digits_amt_out//batch_size):
        batch = ''

        for _ in range(batch_size):
            carry, dec_int = divmod(dec_int * base,big_int)
            batch = batch + base_notation[carry]

        shared_data.q.put(batch)
        now = ntimer.perf_counter_ns()
        shared_data.generate_speed = batch_size/((now-time_tmp)/1e9)
        time_tmp = now
        shared_data.size += len(batch)

    if batch:
        shared_data.q.put(''.join(batch))
    shared_data.running = False
    shared_data.q.put(None)

def writer_thread(out_file, shared_data:SharedData):
    time_tmp = ntimer.perf_counter_ns()
    with open(out_file, 'w') as file:
        while True:
            batch = shared_data.q.get()
            if batch is None:
                break
            file.write(batch)
            now = ntimer.perf_counter_ns()
            shared_data.writing_speed = len(batch)/((now-time_tmp)/1e9)
            shared_data.sample = batch
            time_tmp = now
            shared_data.size -= len(batch)
        time_tmp = ntimer.perf_counter_ns()

def parent_thread(shared_data:SharedData):
    while shared_data.running:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"""
backlog_size: {shared_data.size}
write: \t{shared_data.writing_speed:.0f}/s
gen: \t{shared_data.generate_speed:.0f}/s
sample: \t{shared_data.sample}
""")
        sleep(1)
    
def write_base(in_file:str, out_base:int, in_base:int=10, out_file:str=None, batch_size:int=1000):
    if out_file is None:
        out_file = f'0x{out_base}_{in_file}'

    digits_amt_in = os.path.getsize(in_file)
    int_in,num_size = get_int(in_file, digits_amt_in)
    # digits_amt_out = int(log(int_in, out_base)) + 1
    digits_amt_out = num_size

    # q = queue.Queue(maxsize=1000)
    shared_data = SharedData()
    shared_data.q = queue.Queue(maxsize=1000)

    gen_thread = threading.Thread(target=generator_thread, args=(int_in, digits_amt_out, batch_size, shared_data))
    write_thread = threading.Thread(target=writer_thread, args=(out_file, shared_data))
    print_thread = threading.Thread(target=parent_thread, args=(shared_data,))

    gen_thread.start()
    write_thread.start()
    print_thread.start()

    gen_thread.join()
    write_thread.join()
    print_thread.join()

@ntimer.timer
def main():
    file_path = r'\\10.0.0.3\raid\other\bignum\pi\Pi - Dec - Chudnovsky.txt'
    write_base(file_path, 2, out_file='bin.txt')

if __name__ == '__main__':
    main()
