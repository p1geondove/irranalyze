from scripts import *

def main():
    #file = get_one("pi", 10, "txt")
    file = BigNum("/home/p1geon/documents/bignum/e - Dec - exp(1) 100b.txt")
    if file is None:
        print("no viable file found")
        return
    print("searching " + str(file))

    while True:
        try:
            pattern = input("pattern: ")
            if not pattern.isnumeric():
                pattern = txt_to_num(pattern)
            pos = file[pattern]
            print(pos)
        except KeyboardInterrupt:
            print()
            return
        except EOFError:
            print()
            return

if __name__ == "__main__":
    main()
