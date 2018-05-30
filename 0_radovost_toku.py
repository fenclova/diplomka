# Nazev:    2_radovost_toku.py
# Autor:    Karolina Fenclova
# Popis:    Skript pocita delku vodnich toku podle absolutni radovosti
#           Na kazde uzemi vola funkci "fce_povodi.py", ktera pocita hodnoty kriterii
#           Hodnoty zapisuje do cvs souboru
#
# Vstup:    soubor config = nastaveni workspace + dat ke zpracovani
#
# Vystup:   soubor csv s hodnotou kriterii (vystup fce_povodi.py)

##########################################################################################################
print "Start 0_radovost_toku.py"

# Merim cas vypoctu
import time
t1 = time.time()

import arcpy, os, csv, config, sys

# import funkce z jineho souboru
import fce_povodi as povodi

arcpy.env.workspace = config.workspace
arcpy.env.overwriteOutput = True
sr = arcpy.SpatialReference(32633)


# atributy pro zapis vysledku do csv souboru
fieldnames = ["ID", "celkova_delka", "r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10"]

# Open csv file for writing the results
cislo = 1
while True:
    filename = config.workspace + "0_radovost_toku%s.csv" % cislo
    if not os.path.isfile(filename):
        break
    cislo = cislo +1

with open(filename, "wb") as vysledky_file:
    csv_writer = csv.writer(vysledky_file)
    csv_writer.writerow(fieldnames)

    # Vypocet pro vsechna uzemi
    where = "stav_radovost = 'nevypocteno'"
    ctverce_cursor = arcpy.da.UpdateCursor(config.ctverce, ["Id", "SHAPE@", "stav_radovost"], where)

    for ctverec in ctverce_cursor:
        ID = ctverec[0]
        shape = ctverec[1]
        print "\n ID: {0}".format(ID)

        # Volam funkci linarni interpolace
        result = povodi.radovost_vodnich_toku(ID, shape, config.workspace, config.vstupni_data) #FCDataset_VybranyVodniTok)

        # print "Vysledek = {0}".format(result)
        print '.'

        # zapis vysledek do csv souboru
        csv_writer.writerow(result)
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

print "Konec 2_povodi.py"

sys.exit(777)
