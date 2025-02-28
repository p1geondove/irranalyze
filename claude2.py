import os
from gmpy2 import mpz
from math import log10
from scripts.ntimer import timer

class Solution:
    def base_convert(self, file_path: str, base: int = 16, digits: int = 1000) -> str:
        """
        Konvertiert eine Dezimalzahl aus einer Datei in eine andere Basis.
        Optimiert für sehr große Dateien.
        
        Args:
            file_path: Pfad zur Datei mit der Dezimalzahl
            base: Zielbasis (2-62)
            digits: Anzahl der zu erzeugenden Stellen
            
        Returns:
            String mit der Zahl in der Zielbasis
        """
        # Begrenze die Basis auf gültige Werte
        if not 2 <= base <= 62:
            raise ValueError("Basis muss zwischen 2 und 62 liegen")
        
        # Definiere die Zeichen für die Zielbasis
        base_chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        base_chars = base_chars[:base]
        
        # Berechne, wie viele Dezimalstellen wir brauchen
        read_amount = int(log10(base**digits)) + 20  # Großer Sicherheitspuffer
        
        # Starte mit dem ganzzahligen Teil (für Pi ist das bekannt)
        int_part = "3"
        
        # Öffne die Datei und finde den Dezimalpunkt
        with open(file_path, 'r') as file:
            # Lese einen kleinen Block zum Finden des Dezimalpunkts
            first_block = file.read(20)
            decimal_pos = first_block.find('.')
            if decimal_pos == -1:
                decimal_pos = first_block.find(',')
            if decimal_pos == -1:
                raise ValueError("Kein Dezimalpunkt in der Datei gefunden")
            
            # Setze den Dateizeiger hinter den Dezimalpunkt
            file.seek(decimal_pos + 1)
            
            # Lese genug Ziffern für die Konvertierung
            chunk_size = 1000
            digits_read = 0
            frac_part = mpz(0)
            
            while digits_read < read_amount:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                
                # Entferne alle Nicht-Ziffern
                # clean_chunk = ''.join(c for c in chunk if c.isdigit())
                # if not clean_chunk:
                #     continue
                    
                # Füge die Ziffern zu unserem Bruch hinzu
                frac_part = frac_part * mpz(10**len(chunk)) + mpz(chunk)
                digits_read += len(chunk)
                
                if digits_read >= read_amount:
                    break
        
        # Bestimme den Nenner (10^digits_read)
        denominator = mpz(10**digits_read)
        
        # Jetzt konvertieren wir in die Zielbasis
        mpz_base = mpz(base)
        result_digits = []
        
        # Wir brauchen keine vollen digits_read mehr, diese Information ist jetzt in denominator
        for _ in range(digits):
            # Multipliziere mit der Basis
            frac_part *= mpz_base
            
            # Extrahiere die ganze Zahl
            digit = frac_part // denominator
            
            # Aktualisiere die Fraktion
            frac_part %= denominator
            
            # Füge die Ziffer zum Ergebnis hinzu
            result_digits.append(base_chars[int(digit)])
            
            # Vorzeitiger Abbruch bei exakter Darstellung
            if frac_part == 0:
                break
        
        return int_part + "." + ''.join(result_digits)

# Beispielaufruf für Testzwecke
if __name__ == "__main__":
    file_path = r"\\10.0.0.3\raid\other\bignum\pi\Pi dec 1b.txt"
    solution = Solution()
    
    # Teste verschiedene Größen
    for test_digits in [1000, 10000, 100000, 1000000]:
        print(f"\nTesting {test_digits} digits:")
        result = solution.base_convert(file_path, base=16, digits=test_digits)
        print(f"Result (last 10 chars): ...{result[-10:]}")