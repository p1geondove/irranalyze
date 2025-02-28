import os
import itertools

def read_pi_digits(file_path, num_digits=1000):
    """Liest die ersten num_digits Ziffern von Pi aus einer Datei ein, ohne sie vollständig zu laden."""
    with open(file_path, "r") as f:
        # Überspringe die "3."
        first_line = f.readline().strip()
        assert first_line.startswith("3."), "Datei sollte mit '3.' beginnen"
        
        # Lazy lesen der nächsten num_digits Zeichen (ohne '3.')
        return ''.join(itertools.islice((char for char in f.read() if char.isdigit()), num_digits))

def base_convert(number_str, base):
    """Konvertiert eine Dezimalbruch-Zahl (als String) in eine andere Basis."""
    if base < 2 or base > 36:
        raise ValueError("Basis muss zwischen 2 und 36 sein")
    
    decimal_value = sum(int(digit) * (10 ** -i) for i, digit in enumerate(number_str, 1))
    
    result = "0."
    while decimal_value > 0 and len(result) < 1002:  # 1000 Ziffern + "0."
        decimal_value *= base
        digit = int(decimal_value)
        decimal_value -= digit
        result += "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[digit]
    
    return result

def main():
    file_path = r"\\10.0.0.3\raid\other\bignum\pi\Pi dec 1b.txt"
    target_base = 16  # Beispiel: Hexadezimal
    
    pi_digits = read_pi_digits(file_path)
    converted_pi = base_convert(pi_digits, target_base)
    print(f"Pi in Basis {target_base}: {converted_pi}")

if __name__ == "__main__":
    main()