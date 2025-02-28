from scripts.ntimer import timer
from decimal import Decimal, getcontext
import os

class Solution:
    @timer
    def base_convert(self, file_path: str, base: int = 16, digits: int = 1000) -> str:
        """
        Liest eine Dezimalzahl aus einer Datei und konvertiert sie in eine andere Basis.
        
        Args:
            file_path: Pfad zur Datei, die die Dezimalzahl enthält
            base: Zielbasis (2-62)
            digits: Anzahl der Stellen, die zurückgegeben werden sollen
            
        Returns:
            Die konvertierte Zahl als String
        """
        if not 2 <= base <= 62:
            raise ValueError("Basis muss zwischen 2 und 62 liegen")
            
        # Bestimme die Zeichen für die Basis
        chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        base_chars = chars[:base]
        
        # Überprüfe, ob die Datei existiert
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Die Datei '{file_path}' wurde nicht gefunden")
        
        # Optimiere die Präzision basierend auf der Basis und der gewünschten Stellenzahl
        # Für höhere Basen brauchen wir weniger Dezimalstellen
        log_factor = 1
        if base >= 8:
            log_factor = 1.2
        if base >= 16:
            log_factor = 1.5
        if base >= 32:
            log_factor = 2
            
        precision = int(digits * log_factor) + 10  # Ein kleiner Puffer für Sicherheit
        getcontext().prec = precision
        
        # Lese die Datei effizient ein
        with open(file_path, 'r') as file:
            # Überprüfe, ob es einen Dezimalpunkt gibt
            first_chunk = file.read(100)
            file.seek(0)
            
            # Finde den Dezimalpunkt
            decimal_pos = -1
            if '.' in first_chunk:
                decimal_pos = first_chunk.find('.')
            elif ',' in first_chunk:
                decimal_pos = first_chunk.find(',')
            
            # Lese die Zahl ein
            if decimal_pos >= 0:
                # Lese den ganzzahligen Teil
                integer_part = file.read(decimal_pos)
                # Überspringe den Dezimalpunkt
                file.read(1)
                
                # Berechne, wie viele Dezimalstellen wir effektiv benötigen
                decimal_digits_needed = precision
                
                # Lese die Dezimalstellen in Blöcken
                fractional_part = ""
                remaining = decimal_digits_needed
                
                # Optimierte Blockgröße für effizientes Lesen
                block_size = min(100000, remaining)
                
                while remaining > 0:
                    chunk = file.read(block_size)
                    if not chunk:
                        break
                    # Entferne Nicht-Ziffern effizient
                    clean_chunk = ''.join(filter(str.isdigit, chunk))
                    fractional_part += clean_chunk
                    remaining -= len(clean_chunk)
                    if remaining <= 0:
                        break
                
                # Bereinige den ganzzahligen Teil
                integer_part = ''.join(filter(str.isdigit, integer_part))
                
                # Erstelle die Dezimalzahl
                if integer_part:
                    decimal_value = Decimal(integer_part)
                else:
                    decimal_value = Decimal('0')
                
                # Füge den Bruchteil hinzu
                if fractional_part:
                    fractional_value = Decimal('0.' + fractional_part)
                    decimal_value += fractional_value
            else:
                # Wenn kein Dezimalpunkt gefunden wurde
                integer_str = file.read().strip()
                integer_part = ''.join(filter(str.isdigit, integer_str))
                decimal_value = Decimal(integer_part)
        
        # Konvertiere in die Zielbasis - optimiert für Geschwindigkeit
        # Berechne den ganzzahligen Teil
        integer_result = ""
        int_part = int(decimal_value)
        
        if int_part == 0:
            integer_result = "0"
        else:
            # Optimierte Schleife für den ganzzahligen Teil
            digits_list = []
            while int_part > 0:
                int_part, remainder = divmod(int_part, base)
                digits_list.append(base_chars[remainder])
            integer_result = ''.join(reversed(digits_list))
        
        # Berechne den Bruchteil
        fractional_result = ""
        frac_part = decimal_value - int(decimal_value)
        
        # Optimierte Schleife für den Bruchteil
        if frac_part > 0:
            # Vorallokierter Buffer für bessere Performance
            frac_digits = []
            for _ in range(digits):
                frac_part *= base
                digit = int(frac_part)
                frac_digits.append(base_chars[digit])
                frac_part -= digit
                
                if frac_part == 0:
                    break
                    
            fractional_result = ''.join(frac_digits)
        
        # Kombiniere die Ergebnisse
        if fractional_result:
            result = integer_result + "." + fractional_result
        else:
            result = integer_result
            
        return result

# Beispielaufruf (für Testzwecke)
if __name__ == "__main__":
    file_path = r"\\10.0.0.3\raid\other\bignum\pi\Pi dec 1b.txt"
    solution = Solution()
    
    # Teste verschiedene Größen
    for test_digits in [1000, 10000, 100000]:
        print(f"\nTesting {test_digits} digits:")
        result = solution.base_convert(file_path, base=16, digits=test_digits)
        print(f"Result (last 10 chars): ...{result[-10:]}")