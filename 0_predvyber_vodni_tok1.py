# -*- coding: utf-8 -*-


# Nazev:    0_predvyber_zaklad.py
# Autor:    Karolina Fenclova
# Popis:    Skript na kazde uzemi vola funkci "fce_predvyber.py", ktera pocita hodnoty kriterii
#           Hodnoty zapisuje do cvs souboru
#
# Vstup:    soubor config = nastaveni workspace + dat ke zpracovani
#
# Vystup:   soubor csv s hodnotou kriterii (vystup fce_predvyber.py)

##########################################################################################################
print "Start 0_predvyber_vodni_tok1.py:"

# Merim cas vypoctu
import time
t1 = time.time()

import arcpy, os, csv, config, sys

# import funkce z jineho souboru
import fce_predvyber as predvyber

arcpy.env.workspace = config.workspace
arcpy.env.overwriteOutput = True
sr = arcpy.SpatialReference(32633)

# Databaze GDB pro ukladani vystupu pro hodnoceni
if not arcpy.Exists("VodniTok_1.gdb"):
    outDatabase = str(arcpy.CreateFileGDB_management(out_folder_path= config.workspace, out_name="VodniTok_1", out_version="CURRENT"))
else:
    outDatabase = "VodniTok_1.gdb"

if not arcpy.Exists(os.path.join(outDatabase, "VybranyVodniTok")):
    FCDataset_VybranyVodniTok = str(arcpy.CreateFeatureDataset_management(outDatabase, "VybranyVodniTok", sr))
else:
    FCDataset_VybranyVodniTok = os.path.join(outDatabase, "VybranyVodniTok")

# outDatabase = "VodniTok_5170.gdb"
# FCDataset_VybranyVodniTok = os.path.join(outDatabase, "VybranyVodniTok")

fieldnames = ["ID",
                "find_path_problem",
                "end_start_kombinace",
                "nejlepsi_podil_ploch",
                "pocet_pruseciku"]

# Open csv file for writing the results
cislo = 1
while True:
    filename = config.workspace + "0_predvyber_vodni_tok1_%s.csv" % cislo
    if not os.path.isfile(filename):
        break
    cislo = cislo +1

with open(filename, "wb") as vysledky_file:
    csv_writer = csv.writer(vysledky_file, delimiter=",")
    csv_writer.writerow(fieldnames)

    # Vypocet pro vsechna uzemi
    where = "stav_vyber_reky = '1'"
    ctverce_cursor = arcpy.da.UpdateCursor(config.ctverce, ["Id", "SHAPE@", "stav_vyber_reky"], where)

    for ctverec in ctverce_cursor:
        ID = ctverec[0]
        shape = ctverec[1]
        print "\n ID: {0}".format(ID)

        # Volam funkci linarni interpolace
        result_predvyber = predvyber.vyber_vodni_tok(ID, shape, config.workspace, config.vstupni_data, FCDataset_VybranyVodniTok)
        print result_predvyber

        # zapis vysledek do csv souboru
        csv_writer.writerow(result_predvyber)
        vysledky_file.flush()

        # update stav
        ctverec[2] = "vypocteno"
        ctverce_cursor.updateRow(ctverec)

    del ctverce_cursor

vysledky_file.close()

# Vysledny cas vypoctu
t2 = time.time()
TimeTakenSecs = str(t2 - t1)
print ("cas vypoctu: " + TimeTakenSecs + "sekund")

print "Konec 0_predvyber_vodni_tok1.py"

sys.exit(777)
