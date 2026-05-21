import re

pattern = r"(?:[Cc]alle[s]?|[Aa]v\.?|[Aa]venida|[Rr]uta)?\s*([A-ZÁÉÍÓÚ][a-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-zñáéíóú]+)*)\s*(?:y|e|esquina|intersección\s+con|a\s+la\s+altura\s+de|frente\s+al)\s*(?:[Cc]alle[s]?|[Aa]v\.?|[Aa]venida|[Rr]uta)?\s*([A-ZÁÉÍÓÚ][a-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-zñáéíóú]+)*)"

text_clean = "Secciones San Juan Política Economía Cuyo Minero Suplemento Verd & Revista, Dominguito, San Martín"

match = re.search(pattern, text_clean)
if match:
    print("Match found!")
    print("Full match:", match.group(0))
    print("Group 1:", match.group(1))
    print("Group 2:", match.group(2))
else:
    print("No match found")
