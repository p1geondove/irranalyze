from gmpy2 import mpz
import os
import threading
import queue
from ntimer import sleep, perf_counter_ns, fmt_ns
# from math import log
import curses

class SharedData:
    big_int:mpz
    in_file:str = ''
    out_file:str = ''
    start_ns = perf_counter_ns()
    amt_written = 0
    writing_ns = 0
    generate_ns = 0
    running = True
    q:queue.Queue = None
    sample = ''
    base = 2

def get_int(file_path:str, amt_digits=-1) -> mpz:
    # reads a file and returns the digits after decimal point as a big mpz int
    first_size = 10
    chunk_size = 4000
    _magic = 10**chunk_size

    with open(file_path, 'rt') as file:
        first_chunk = file.read(first_size)
        decimal_spot = first_chunk.find('.') + 1
        if amt_digits == -1:
            amt_digits = os.path.getsize(file_path) - decimal_spot 
        num_size = first_size - decimal_spot # equiv to int(log10(num))

        if not decimal_spot: # invalid file, no decimal found
            return 0
        
        if first_size-decimal_spot > amt_digits: # output digits already in the first chunk
            return mpz(int(first_chunk[decimal_spot : decimal_spot + amt_digits]))
        
        num = mpz(int(first_chunk[decimal_spot:])) # start int
        digits_file = os.path.getsize(file_path) - decimal_spot
        amt_chunks = int((min((digits_file, amt_digits)) - first_size + decimal_spot) / chunk_size)

        for _ in range(amt_chunks): #safe chunks
            chunk = file.read(chunk_size)
            num = num * _magic + int(chunk)
            num_size += chunk_size

        chunk = file.read(chunk_size) #last chunk with cropping
        rest_amt = amt_digits - num_size

        if rest_amt > 0 and chunk:
            chunk = chunk[:rest_amt] # crop chunk to fit in desired amt_digits
            num = num * 10**rest_amt + int(chunk)
            num_size += rest_amt

        return num

def thread_generator(shared_data:SharedData, batch_size=100):
    # converts a gmpy2.mpz int to str using base conversion and puts batches in a queue
    # input int must be digits after decimal point in base 10
    def process(amt):
        if amt<1: return
        nonlocal shared_data, chunk_width
        t1 = perf_counter_ns()
        batch = []
        
        for _ in range(amt):
            carry, shared_data.big_int = divmod(shared_data.big_int * shared_data.base, chunk_width)
            batch.append(base_notation[carry])

        batch = ''.join(batch)
        shared_data.q.put(batch)
        t2 = perf_counter_ns()
        shared_data.generate_ns = t2 - t1

    base_notation = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    if isinstance(shared_data.base,str):
        if shared_data.base == 'abc':
            base_notation = 'abcdefghijklmnopqrstuvwxyz'
            shared_data.base = len(base_notation)
        elif shared_data.base == 'ABC':
            base_notation = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
            shared_data.base = len(base_notation)
    if not isinstance(shared_data.base, int):
        raise Exception(NotImplementedError, 'base must be of type int')
    
    print(base_notation)
    digits_amt_out = shared_data.big_int.num_digits(shared_data.base)
    num_size = shared_data.big_int.num_digits(10)
    # digits_amt_out = int(num_size/log(shared_data.base))
    amt_batches, amt_rest = divmod(digits_amt_out, batch_size)
    chunk_width = 10**num_size

    for _ in range(amt_batches):
        process(batch_size)
    
    process(amt_rest)
    shared_data.q.put(None)
    shared_data.running = False

def thread_writer(shared_data:SharedData):
    # reads batches from the queue and writes it to a file
    with open(shared_data.out_file, 'w') as file:
        batch = shared_data.q.get()
        while batch:
            t1 = perf_counter_ns()
            file.write(batch)
            shared_data.sample = batch[:10]
            shared_data.amt_written += len(batch)
            t2 = perf_counter_ns()
            shared_data.writing_ns = t2 - t1
            batch = shared_data.q.get()

def curses_interface(shared_data:SharedData):
    # prints contents of shared data / debug infos
    while shared_data.running:
        # os.system('cls' if os.name == 'nt' else 'clear')
        print(f"""
write:      {fmt_ns(shared_data.writing_ns)}
gen:        {fmt_ns(shared_data.generate_ns)}
chars/s:    {shared_data.amt_written * 10**9 / (perf_counter_ns()-shared_data.start_ns):.0f}
total:      {shared_data.amt_written}
sample:     {shared_data.sample}
runtime:    {fmt_ns(perf_counter_ns() - shared_data.start_ns)}    
""")
        sleep(1)

# def curses_interface(stdscr, shared_data:SharedData):# Initialisierung von Curses
def thread_print(stdscr, shared_data:SharedData):# Initialisierung von Curses
    curses.curs_set(0)  # Verstecke den Cursor
    stdscr.nodelay(True)  # Lässt getch() nicht blockieren
    while shared_data['running']:
        stdscr.clear()

        # Berechne Werte für die Ausgabe, hier wird angenommen, dass 'start_ns' bereits initialisiert wurde.
        chars_per_second = (shared_data['amt_written'] * 1_000_000_000) / (perf_counter_ns() - shared_data['start_ns'])

        # Formatiere und drucke den Status
        stdscr.addstr(0, 0, f"Write:      {fmt_ns(shared_data['writing_ns'])}")
        stdscr.addstr(1, 0, f"Generate:   {fmt_ns(shared_data['generate_ns'])}")
        stdscr.addstr(2, 0, f"Chars/s:    {chars_per_second:.0f}")
        stdscr.addstr(3, 0, f"Total:      {shared_data['amt_written']}")
        stdscr.addstr(4, 0, f"Sample:     {shared_data['sample']}")
        stdscr.addstr(5, 0, f"Runtime:    {fmt_ns(perf_counter_ns() - shared_data['start_ns'])}")

        # Aktualisiere das Fenster
        stdscr.refresh()

        # Pausiere kurz, um das Terminal nicht zu überlasten
        sleep(.3)

def write_txt(in_file:str, out_file:str, base=2):
    # main function for file base conversion
    shared_data = SharedData()
    shared_data.q = queue.Queue()
    shared_data.big_int = get_int(in_file)
    shared_data.in_file = in_file
    shared_data.out_file = out_file
    shared_data.base = base

    gen_thread   = threading.Thread(target=thread_generator, args=(shared_data,))
    write_thread = threading.Thread(target=thread_writer,    args=(shared_data,))
    print_thread = threading.Thread(target=thread_print,     args=(shared_data,))

    gen_thread.start()
    write_thread.start()
    print_thread.start()
    
    gen_thread.join()
    write_thread.join()
    print_thread.join()


def main():
    file_path = r'\\10.0.0.3\raid\other\bignum\pi\Pi - Dec - Chudnovsky.txt'
    write_txt(file_path,'ABC.txt','ABC')

if __name__ == '__main__':
    main()
