# setup.py - useful dialog setup script

from pathlib import Path
import os

from scripts.var import Paths, Sizes, Switches
from scripts import build_db
from scripts.helper import format_size

def main():
    #  === Setting num_dir ===
    print("\n--- num_dir ---\nThis is the path to all the big number files you have. This doesnt have to be a flat directory, recursive search is enabled by default")
    while True:
        prompt = input(f"path to your numbers [{Paths.num_dir}]: ")
        if prompt == "":
            val = Paths.num_dir
            break
        val = Path(prompt)
        if not val.exists():
            prompt = input(f"{val} does not exist, create it? [y/N]: ").lower()
            if prompt == "y":
                val.mkdir(parents=True)
                break
        else:
            break
    Paths.num_dir = val
    print(f"updated setting 'num_dir' to {val}")

    # === Setting sqlite_path ===
    print("\n--- sqlite_path ---\nThis is the path to the database file that will be created")
    del val
    while True:
        prompt = input(f"path to your sqlite database [{Paths.sqlite_path}]: ")
        if prompt == "":
            val = Paths.sqlite_path
            break
        val = Path(prompt)
        if not val.parent.exists():
            prompt = input(f"{val.parent} does not exist, create it? [y/N]: ").lower()
            if prompt == "y":
                val.parent.mkdir(parents=True)
                break
        else:
            break
    Paths.sqlite_path = val
    print(f"updated setting 'sqlite_path' to {val}")

    # === Setting report_not_found ===
    print("\n--- report_not_found ---\nIf you have fixed number files, reporting -1/not found to db doesnt cause searching the same thing twice uneessecarily. When in future you add bigger number files of the same type you should leave this off")
    del val
    while True:
        prompt = input(f"report -1 to db if search string not found? [{Switches.report_not_found}]: ")
        if prompt == "":
            val = Switches.report_not_found
            break
        try:
            val = bool(prompt)
            break
        except KeyboardInterrupt|EOFError:
            raise
        except:
            print(f"cant convert {prompt} to bool")
            continue
    Switches.report_not_found = val
    print(f"updated setting 'report_not_found' to {val}")

    # === Setting one_indexed ===
    print("\n--- one_indexed ---\nthe first digit after radix point is by default 1 to align with angio.net/pi/piquery, tho for programming the first element is usually 0")
    del val
    while True:
        prompt = input(f"First digits are index 1? [{Switches.one_indexed}]: ")
        if prompt == "":
            val = Switches.one_indexed
            break
        try:
            val = bool(prompt)
            break
        except KeyboardInterrupt|EOFError:
            raise
        except:
            print(f"cant convert {prompt} to bool")
            continue
    Switches.one_indexed = val
    print(f"updated setting 'one_indexed' to {val}")

    # === Setting max_processes ===
    print("\n--- max_processes ---\nThe amount of processes/threads to spawn for search/build_db. More is usually better, usually keep this number to the number of cores you have")
    del val
    while True:
        prompt = input(f"Amount of processes (usually amount of cpu cores) [{os.cpu_count() or 1}]: ")
        if prompt == "":
            val = os.cpu_count() or 1
            break
        try:
            val = int(prompt)
        except KeyboardInterrupt|EOFError:
            raise
        except:
            print(f"cant convert {prompt} to int")
            continue
        if val < 1:
            print("amount of processes has to be more than zero")
        else:
            break
    Sizes.max_processes = val
    print(f"updated setting 'max_processes' to {val}")

    # === Setting pairs_per_insert ===
    print("\n--- pairs_per_insert ---\nThe amount of substring/position pairs to add to database while (optional) precalculating number tables. Changing this can yield minor improvements however default is fine")
    del val
    while True:
        prompt = input(f"Amount of inserts per query for build_db -n [{Sizes.pairs_per_insert}]: ")
        if prompt == "":
            val = Sizes.pairs_per_insert
        else:
            try:
                prompt = eval(prompt)
                val = int(prompt)
            except KeyboardInterrupt|EOFError:
                raise
            except:
                print(f"Cant convert {prompt} to int")
                continue
        if val < 1:
            print("amount of inserts has to be more than zero")
        else:
            break
    Sizes.pairs_per_insert = val
    print(f"updated setting 'pairs_per_insert' to {val}")

    # === Setting chunk_size ===
    print("\n--- chunk_size ---\nThe size of chunks to use for search. Powers of 2 are usually best")
    del val
    while True:
        prompt = input(f"Chunksize for searching [{Sizes.chunk_size}]: ")
        if prompt == "":
            val = Sizes.chunk_size
        else:
            try:
                prompt = eval(prompt)
                val = int(prompt)
            except KeyboardInterrupt|EOFError:
                raise
            except:
                print(f"Cant convert {prompt} to int")
                continue
        if val < 1:
            print("chunksize has to be higher than zero")
        else:
            break
    Sizes.chunk_size = val
    print(f"updated setting 'chunk_size' to {val}")

    # === Setting first_digit_amount ===
    print("\n--- first_digit_amount ---\nThe amount of digits/chars to save in a variable. Used for quicksearch. Low values start multiprocessing search too much, high values will slow down quicksearch, when quicksearch should be low latency")
    del val
    while True:
        prompt = input(f"Amount of digits to cache [{Sizes.first_digit_amount}]: ")
        if prompt == "":
            val = Sizes.first_digit_amount
        else:
            try:
                prompt = eval(prompt)
                val = int(prompt)
            except KeyboardInterrupt|EOFError:
                raise
            except:
                print(f"Cant convert {prompt} to int")
                continue
        if val < 1:
            print("amount of digits has to be more than zero")
        else:
            break
    Sizes.first_digit_amount = val
    print(f"updated setting 'first_digit_amount' to {val}")

    # === Run build_db.py ===
    print("\nFinished setting up Variables!\n")
    build = False
    while True:
        prompt = input(f"Runun build_db to build identifier table and precalculate search strings? (Y/n): ").lower()
        if prompt == "n":
            break
        elif prompt in {"","y"}:
            build = True
            break
        else:
            print(f"{prompt} is not a valid answer")

    if build:
        # always build identifier table
        build_db.build_identifier()

        # Build search tables
        while True:
            from scripts.bignum import get_all
            nums = set(get_all(num_dir=Paths.num_dir))
            if not nums:
                print(f"No number files found, please add number files to {Paths.num_dir}")
                print("Setup Finished!")
                return

            prompt = input(f"Build search table(s)? (This can take some time, further prompts ahead!) (Y/n): ").lower()
            if prompt == "n":
                print("Setup Finished!")
                return

            elif prompt in {"","y"}:
                # check the number files
                while True:
                    prompt = input(f"Found {len(nums)} different number file(s), print overview?: (Y/n): ")
                    if prompt == "n":
                        break
                    elif prompt in {"","y"}:
                        print(nums)
                        break
                    else:
                        print(f"{prompt} is not a valid answer")
                break

        # set parameters (substring length and max position)
        # max digits
        while True:
            prompt = input("Maxium length of string (10**6): ")
            if prompt == "":
                amt_digits = 10**6
                break
            else:
                try:
                    amt_digits = int(prompt)
                    break
                except:
                    try:
                        amt_digits = int(eval(prompt))
                        break
                    except:
                        print(f"{prompt} is not a number")

        # substring length
        while True:
            prompt = input("Maxium length of string (6): ")
            if prompt == "":
                substring_len = 6
                break
            else:
                try:
                    substring_len = int(prompt)
                    break
                except:
                    try:
                        substring_len = int(eval(prompt))
                        break
                    except:
                        print(f"{prompt} is not a number")

        amt_pairs = (amt_digits-(substring_len-1))*substring_len * len(nums)
        amt_bytes_strings = amt_pairs * (substring_len+1)/2
        amt_bytes = amt_pairs * 8 + amt_bytes_strings
        print(f"setting substring length to {substring_len} and amount of digits to {amt_digits} will create {amt_pairs} patterns (up to {format_size(amt_bytes,'b')})")
        prompt = input(f"Go? (Y/n): ").lower()
        if prompt in ("","y"):
            build_db.build_many(amt_digits,substring_len,list(nums))

    print("Finished setup!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt, EOFError:
        print("\nHey please come back :'(\n")
