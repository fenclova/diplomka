# -*- coding: utf-8 -*-

#  Nazev:   7_podkaldy_pro_hodnoceni.py
# Autor:    Karolina Fenclova
# Popis:    Skript na vytvoreni vrstevnic linearni interpolaci pro mapu hypsometrie
#           1. priprava vstupnich dat, 2. tvorba vrstevnic linearni interpolaci
#
# Vstup:    soubor config = nastaveni workspace + dat ke zpracovani

#
# Vystup pro kazde uzemi: vybrany_vodni_tok, ZIV5_hypso, ZIV10_hypso, ZIV20_hypso
#                         zapis vyslednych hodnot do databaze

##########################################################################################################
print "Start 7_podklady_pro_hodnoceni.py:"

# Merim cas vypoctu
import time
t1 = time.time()

import arcpy, config, sys, os

# import funkce z jineho souboru
import fce_hypsometrie as hypsometrie
import fce_povodi as povodi

arcpy.env.workspace = config.workspace
arcpy.env.overwriteOutput = True
sr = arcpy.SpatialReference(32633)

# Databaze GDB s vodnim tokem
FCDataset_VybranyVodniTok = os.path.join(config.vysledky, "VybranyVodniTok")

FCDataset_HypsoVrstevnice = os.path.join(config.vysledky, "Hypsometrie")

FCDataset_Povodi = os.path.join(config.vysledky, "Povodi")

print "nacteny databaze pro ulozeni vysledku"


# Vypocet pro vsechna uzemi
where = "poradi = 5"

ctverce_cursor = arcpy.da.SearchCursor(config.ctverce, ["ID", "poradi", "SHAPE@", "vhodny_ziv", "podklady"], where)
print "vytvoren kursor"

for ctverec in ctverce_cursor:
    ID = ctverec[0]
    poradi = ctverec[1]
    shape = ctverec[2]
    vhodny_ziv = ctverec[3]

    print "\n poradi: {0}".format(poradi)

    # Volam funkci linarni interpolace
    # vysledek_hypso = hypsometrie.ulozeni_vrstevnic(ID, poradi, shape, config.workspace,config.vstupni_data, FCDataset_VybranyVodniTok, FCDataset_HypsoVrstevnice, vhodny_ziv)
    # print "ok"

    # Volam funkci na pocet povodi
    vysledek_povodi = povodi.ulozeni_povodi(poradi, shape, config.workspace, config.vstupni_data, FCDataset_Povodi)
    print "ok"

    # update stav
    # ctverec[4] = "povodi"
    # ctverce_cursor.updateRow(ctverec)

    # Cas vypoctu
    tp = time.time()
    TimeTakenSecs = str(tp - t1)
    print ("Cas:" + TimeTakenSecs + "s")

    # except:
    #     "Nelze vypocitat."

del ctverce_cursor


# Vysledny cas vypoctu
t2 = time.time()
TimeTakenSecs = str(t2 - t1)
print ("Cas vypoctu: " + TimeTakenSecs + "sekund")

print 'Konec 7_podklady_pro_hodnoceni.py'

sys.exit(777)