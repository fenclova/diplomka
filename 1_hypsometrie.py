# Nazev:     1_hypsometrie.py
# Autor:    Karolina Fenclova
# Popis:    Skript na vytvoreni vrstevnic linearni interpolaci pro mapu hypsometrie
#           1. priprava vstupnich dat, 2. vyber vodniho toku, 3. tvorba vrstevnic linearni interpolaci
#
# Vstup:    !!!!! popsat vstupni data
#
# Vystup pro kazde uzemi: vybrany_vodni_tok, ZIV5_hypso, ZIV10_hypso, ZIV20_hypso
#                         zapis vyslednych hodnot do databaze

##########################################################################################################
print "Start 1_hypsometrie.py:"

# Merim cas vypoctu
import time
t1 = time.time()

import arcpy, csv, sqlite3, config

# import funkce z jineho souboru
import fce_linearni_interpolace as hypsometrie

arcpy.env.workspace = config.workspace
arcpy.env.overwriteOutput = True
sr = arcpy.SpatialReference(32633)

# Databaze GDB pro ukladani vystupu pro hodnoceni
if not arcpy.Exists("Outputs.gdb"):
    outDatabase = str(arcpy.CreateFileGDB_management(out_folder_path= config.workspace, out_name="Outputs", out_version="CURRENT"))
else:
    outDatabase = "Outputs.gdb"

if not arcpy.Exists(outDatabase + "VybranyVodniTok"):
    FCDataset_VybranyVodniTok = str(arcpy.CreateFeatureDataset_management(outDatabase, "VybranyVodniTok", sr))
else:
    FCDataset_VybranyVodniTok = "VybranyVodniTok"

if not arcpy.Exists(outDatabase + "HypsoVrstevnice"):
    FCDataset_HypsoVrstevnice = str(arcpy.CreateFeatureDataset_management(outDatabase, "HypsoVrstevnice", sr))
else:
    FCDataset_HypsoVrstevnice = "HypsoVrstevnice"

try:
    # Pripoj k databazi, vytvor cursor
    conn = sqlite3.connect(config.databaze)
    print "Pripojeno k databazi."
    cur = conn.cursor()

    # Vypocet pro vsechna uzemi
    ctverce_cursor = arcpy.da.SearchCursor(config.ctverce, ["Id", "SHAPE@"])

    for ctverec in ctverce_cursor:
        ID = ctverec[0]
        shape = ctverec[1]
        print "\n Pracuji na ctverci: {0}".format(ID)

        # Volam funkci linarni interpolace
        result_linearni_interpolace = hypsometrie.fce_linearni_interpolace(ID, shape, config.workspace, config.vstupni_data, FCDataset_VybranyVodniTok, FCDataset_HypsoVrstevnice)
        print "Funkce linearni interpolace vratila vysledek."

        ZIV5 = result_linearni_interpolace[0]
        ZIV10 = result_linearni_interpolace[1]
        ZIV20 = result_linearni_interpolace[2]

        # Pridani vysledku do databaze, ulozeni
        cur.execute("INSERT INTO hypsometrie_ZIV5 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ZIV5)
        cur.execute("INSERT INTO hypsometrie_ZIV10 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ZIV10)
        cur.execute("INSERT INTO hypsometrie_ZIV20 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ZIV20)
        conn.commit()
        print "Hodnoty pridany do databaze."

    del ctverce_cursor

    # Ukonci pripojeni k databazi
    conn.close()

    # Vysledny cas vypoctu
    t2 = time.time()
    TimeTakenSecs = str(t2 - t1)
    print ("cas vypoctu: " + TimeTakenSecs + "sekund")

    print 'Konec 1_hypsometrie.py'

except ValueError:
    print "Ooups... neco se nepovedlo"
    print arcpy.GetMessages(2)

