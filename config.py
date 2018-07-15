# -*- coding: utf-8 -*-
# ....................................................................................................
# Name:             config.py
# Author:           Karolina Fenclova
# Description:      Configuration file for all other scripts

import os
# path of this file
path_config = os.path.dirname(os.path.abspath(__file__))

# set the paths
workspace = os.path.join(os.path.dirname(path_config), r'mezivysledky\\')
# stavajici mapy - od Lysaka 253 ctvercu
ctverce = os.path.join(r'C:\fenclova\diplomka\vystupy\kartografie_250zadani.gdb\zadani250nej_lokace')
ctverce = r'C:\fenclova\diplomka\analyza\vysledky\vysledek_SHP\250nej.shp'
#ctverce = os.path.join(os.path.dirname(path_config), r'data\vstupni_data.gdb\fishnet_big_1991') # fishnet_big_4472, fishnet = 875 ctvercu (prvni selekce) # fishnet_3ctverce # fishnet_big = 34 tisic
vstupni_data = os.path.join(os.path.dirname(path_config), r'data\vstupni_data.gdb\\')
#vodni_toky = os.path.join(os.path.dirname(path_config), r'vysledky\\')
#vodni_toky = os.path.join(os.path.dirname(path_config), r'mezivysledky\\')
vysledky = os.path.join(r"C:\fenclova\diplomka\vystupy\kartografie_250zadani.gdb\\")

# --------------------- fce_linearni_interpolace.py -----------------------------------

# Rozliseni rastru pro tvorbu DMT
dmt_resolution = 5

# Uzemi okolo ctverce (orez dat, tvorba dmt)
buffer_ctverec_vzdalenost = "500 Meters"

# Vzdalenost od centroidu, kdy ma prioritu prusecik s rekou
centroid_tolerance = "125 Meters"   # 125 m ve skutecnosti = 0,5 cm v mape

# --------------------- fce_predvyber.py -----------------------------------
# Zona pro vyber dat DIBAVOD vodni toky
buffer_vodni_toky = "200 meters"
buffer_vodni_plochy = "100 meters"

# Jak daleko od hranic uzemi muze byt pocatecni/koncovy bod linie vodniho toku pri vyberu vhodneho vodniho toku
tolerance_start = "0.01 meters"
tolerance_end = "0.01 meters"

# Tolerance pro rozdeleni uzemi rekou na 2 casti
tolerance_FeatureToPolygon = "0.5 meters"

# --------------------- fce_povodi.py -----------------------------------
# Obalova zona okolo uzemi, ze ktere vybiram vodni toky pro analyzu povodi
buffer_povodi = "1000 meters"

# ----------------- tvroba a export jednotlivych zadani ------------------
data_pro_mxd = r"C:\fenclova\diplomka\vystupy\export_zadani\data_pro_mxd\\"
dilci_mxd = r"C:\fenclova\diplomka\vystupy\export_zadani\dilci_mxd\\"
pdf_zadani = r"C:\fenclova\diplomka\vystupy\export_zadani\pdf_zadani\\"