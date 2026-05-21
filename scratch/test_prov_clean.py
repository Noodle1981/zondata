import re

BLACKLIST_PROVINCIAS = ["santa fe", "mendoza", "buenos aires", "córdoba", "cordoba", "san luis", "chile", "nacional", "rosario", "neuquén", "misionero", "corrientes"]

text = "Secciones San Luis"

cleaned = text
for prov in BLACKLIST_PROVINCIAS:
    cleaned = re.sub(re.escape(prov), "", cleaned, flags=re.IGNORECASE)

print("Original:", text)
print("Cleaned:", cleaned)
