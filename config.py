# Nazev:    config.py
# Autor:    Karolina Fenclova
# Popis:    Konfiguracni soubor pro skripty: fce_linearni_interpolace.py
import os

cesta = os.path.dirname(os.path.abspath(__file__))
ctverce = os.path.join(cesta, r"../te")

# Databaze k ukladani vysledku
databaze = r"C:\fenclova\diplomka\analyza\test.sqlite"

# Uzemi, pro ktere pocitam
ctverce = r"C:\fenclova\diplomka\analyza\data\vstupni_data.gdb\fishnet"

# Pracovni prostredi, zdroje dat
workspace = r"C:\fenclova\diplomka\analyza\mezivysledky\\"
vstupni_data = r"C:\fenclova\diplomka\analyza\data\vstupni_data.gdb\\"

# --------------------- fce_linearni_interpolace.py -----------------------------------

# Rozliseni rastru pro tvorbu DMT
dmt_resolution = 5

# Uzemi okolo ctverce (orez dat, tvorba dmt)
buffer_ctverec_vzdalenost = "500 meters"

# Vzdalenost od centroidu, kdy ma prioritu prusecik s rekou
centroid_tolerance = "125 Meters"   # 125 m ve skutecnosti = 0,5 cm v mape

# --------------------- fce_predvyber.py -----------------------------------
# Zona pro vyber dat DIBAVOD vodni toky
buffer_vodni_toky = "150 meters"
buffer_vodni_plochy = "100 meters"

# Jak daleko od hranic uzemi muze byt pocatecni/koncovy bod linie vodniho toku pri vyberu vhodneho vodniho toku
tolerance_start = "0.01 meters"
tolerance_end = "0.01 meters"

# Tolerance pro rozdeleni uzemi rekou na 2 casti
tolerance_FeatureToPolygon = "0.5 meters"
