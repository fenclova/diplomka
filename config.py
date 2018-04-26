# ....................................................................................................
# Name:             config.py
# Author:           Karolina Fenclova
# Description:      Configuration file for all other scripts

import os
# path of this file
path = os.path.dirname(os.path.abspath(__file__))

# the area of interest
ctverce = os.path.join(path, r"..\data\vstupni_data.gdb\fishnet")

# Databaze k ukladani vysledku
# databaze = r"C:\fenclova\diplomka\analyza\test.sqlite"

# set the paths
workspace = r"..\mezivysledky\\"
ctverce = os.path.join(path, r"..\data\vstupni_data.gdb\fishnet")
vstupni_data = os.path.join(path, r"..\data\vstupni_data.gdb\\")

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
