import matplotlib.pyplot as plt
import numpy as np
from scripts.base_conv import to_base
from scripts.file_finder import one_of_each
from scripts.ntimer import perf_counter_ns, fmt_ns
from claude2 import Solution

def run_benchmark():
    # Parameter
    base = 16
    amt_values = list(range(1000, 31000, 1000))  # 1000 bis 30000 in 1000er-Schritten
    
    # Ergebnisarrays
    times_claude = []
    times_mainz = []
    
    # Für jeden amt-Wert die Ausführungszeiten messen
    for amt in amt_values:
        print(f"Teste mit amt = {amt}")
        
        # Listen für Zeiten bei aktuellem amt-Wert
        amt_times_claude = []
        amt_times_mainz = []
        
        # Für jede Datei testen
        for file in one_of_each():
            # Claude's Funktion timen
            start_ns = perf_counter_ns()
            Solution().base_convert(file.path, base, amt)
            end_ns = perf_counter_ns()
            amt_times_claude.append(end_ns - start_ns)
            
            # Mainz' Funktion timen
            start_ns = perf_counter_ns()
            to_base(file.path, base, amt)
            end_ns = perf_counter_ns()
            amt_times_mainz.append(end_ns - start_ns)
        
        # Kleinste Zeit für jede Funktion (beste Performance) nehmen
        times_claude.append(min(amt_times_claude))
        times_mainz.append(min(amt_times_mainz))
        
        # Aktuelle beste Zeiten ausgeben
        print(f"  Claude: {fmt_ns(min(amt_times_claude))}")
        print(f"  Mainz: {fmt_ns(min(amt_times_mainz))}")
    
    return amt_values, times_claude, times_mainz

def convert_ns_to_ms(ns_list):
    """Konvertiere Nanosekunden zu Millisekunden für bessere Lesbarkeit im Graphen"""
    return [ns / 1_000_000 for ns in ns_list]

def plot_results(amt_values, times_claude, times_mainz):
    # Konvertiere zu Millisekunden für bessere Lesbarkeit
    times_claude_ms = convert_ns_to_ms(times_claude)
    times_mainz_ms = convert_ns_to_ms(times_mainz)
    
    # Plot erstellen
    plt.figure(figsize=(12, 8))
    
    # Liniengraph
    plt.subplot(2, 1, 1)
    plt.plot(amt_values, times_claude_ms, 'b-o', label='Claude', linewidth=2)
    plt.plot(amt_values, times_mainz_ms, 'r-s', label='Mainz', linewidth=2)
    plt.title('Vergleich der Ausführungszeiten: Solution().base_convert vs to_base', fontsize=14)
    plt.xlabel('Anzahl (amt)', fontsize=12)
    plt.ylabel('Zeit (ms)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=12)
    
    # Verhältnisgraph
    plt.subplot(2, 1, 2)
    ratio = np.array(times_mainz) / np.array(times_claude)
    plt.plot(amt_values, ratio, 'g-^', linewidth=2)
    plt.axhline(y=1.0, color='gray', linestyle='--', alpha=0.7)
    plt.title('Verhältnis: Zeit(Mainz) / Zeit(Claude)', fontsize=14)
    plt.xlabel('Anzahl (amt)', fontsize=12)
    plt.ylabel('Verhältnis', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Für Werte > 1: Mainz ist langsamer, für Werte < 1: Claude ist langsamer
    plt.fill_between(amt_values, ratio, 1, where=(ratio > 1), color='red', alpha=0.3, label='Mainz langsamer')
    plt.fill_between(amt_values, ratio, 1, where=(ratio < 1), color='blue', alpha=0.3, label='Claude langsamer')
    plt.legend(fontsize=12)
    
    plt.tight_layout()
    plt.savefig('performance_vergleich.png', dpi=300)
    plt.show()

def main():
    print("Starte Benchmark...")
    amt_values, times_claude, times_mainz = run_benchmark()
    
    print("\nBenchmark abgeschlossen. Erstelle Graphen...")
    plot_results(amt_values, times_claude, times_mainz)
    
    # Ergebnistabelle ausgeben
    print("\nErgebnisse:")
    print("-" * 50)
    print(f"{'amt':>8} | {'Claude (ms)':>12} | {'Mainz (ms)':>12} | {'Verhältnis':>10}")
    print("-" * 50)
    
    for i, amt in enumerate(amt_values):
        claude_ms = times_claude[i] / 1_000_000
        mainz_ms = times_mainz[i] / 1_000_000
        ratio = mainz_ms / claude_ms if claude_ms > 0 else float('inf')
        
        print(f"{amt:8d} | {claude_ms:12.2f} | {mainz_ms:12.2f} | {ratio:10.2f}")

if __name__ == "__main__":
    main()