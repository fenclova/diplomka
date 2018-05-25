# Nazev:     1_hypsometrie.py
# Autor:    Karolina Fenclova
# Popis:    Skript na vytvoreni vrstevnic linearni interpolaci pro mapu hypsometrie
#           1. priprava vstupnich dat, 2. tvorba vrstevnic linearni interpolaci
#
# Vstup:    soubor config = nastaveni workspace + dat ke zpracovani

#
# Vystup pro kazde uzemi: vybrany_vodni_tok, ZIV5_hypso, ZIV10_hypso, ZIV20_hypso
#                         zapis vyslednych hodnot do databaze

##########################################################################################################
print "Start 1_hypsometrie.py:"

# Merim cas vypoctu
import time
t1 = time.time()

import arcpy, csv, sqlite3, config, sys, os

# import funkce z jineho souboru
import fce_hypsometrie as hypsometrie

arcpy.env.workspace = config.workspace
arcpy.env.overwriteOutput = True
sr = arcpy.SpatialReference(32633)

# Databaze GDB pro ukladani vystupu pro hodnoceni
outDatabase = "Outputs.gdb"
FCDataset_VybranyVodniTok = os.path.join(outDatabase, "VybranyVodniTok")
FCDataset_HypsoVrstevnice = os.path.join(outDatabase, "HypsoVrstevnice")

# Pripoj k databazi, vytvor cursor
conn = sqlite3.connect(config.databaze)
print "Pripojeno k databazi."
cur = conn.cursor()

# Vypocet pro vsechna uzemi
# TODO dodelat atribut hypso = pocitat (ty ctverce, ktere chci)
where = "stav_hypsometrie= 'nevypocteno'"
ctverce_cursor = arcpy.da.UpdateCursor(config.ctverce, ["Id", "SHAPE@", "stav_hypsometrie"], where)

for ctverec in ctverce_cursor:
    ID = ctverec[0]
    shape = ctverec[1]
    print "\n ID: {0}".format(ID)

    try:
        # Volam funkci linarni interpolace
        result_linearni_interpolace = hypsometrie.linearni_interpolace(ID, shape, config.workspace,
                                                                           config.vstupni_data, FCDataset_VybranyVodniTok,
                                                                           FCDataset_HypsoVrstevnice)
        print "mam vysledek."

        ZIV5 = result_linearni_interpolace[0]
        ZIV10 = result_linearni_interpolace[1]
        ZIV20 = result_linearni_interpolace[2]

        # Pridani vysledku do databaze, ulozeni
        cur.execute("INSERT INTO hypsometrie_ZIV5 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ZIV5)
        cur.execute("INSERT INTO hypsometrie_ZIV10 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    ZIV10)
        cur.execute("INSERT INTO hypsometrie_ZIV20 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    ZIV20)
        conn.commit()
        print "Hodnoty pridany do databaze."

        # update stav
        ctverec[2] = "vypocteno"
        ctverce_cursor.updateRow(ctverec)

    except:
        "Nelze vypocitat."

del ctverce_cursor

# Ukonci pripojeni k databazi
conn.close()

# Vysledny cas vypoctu
t2 = time.time()
TimeTakenSecs = str(t2 - t1)
print ("cas vypoctu: " + TimeTakenSecs + "sekund")

print 'Konec 1_hypsometrie.py'

sys.exit(777)