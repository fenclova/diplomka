# Nazev:    2_povodi.py
# Autor:    Karolina Fenclova
# Popis:    Skript na kazde uzemi vola funkci "fce_povodi.py", ktera pocita hodnoty kriterii
#           Hodnoty zapisuje do cvs souboru
#
# Vstup:    soubor config = nastaveni workspace + dat ke zpracovani
#
# Vystup:   soubor csv s hodnotou kriterii (vystup fce_povodi.py)

##########################################################################################################
print "Start 2_povodi.py:"

# Merim cas vypoctu
import time
t1 = time.time()

import arcpy, os, csv, config, sys

# import funkce z jineho souboru
import fce_povodi as povodi

arcpy.env.workspace = config.workspace
arcpy.env.overwriteOutput = True
sr = arcpy.SpatialReference(32633)

# Databaze GDB pro ukladani vystupu pro hodnoceni
# if not arcpy.Exists("Outputs.gdb"):
#     outDatabase = str(arcpy.CreateFileGDB_management(out_folder_path= config.workspace, out_name="Outputs", out_version="CURRENT"))
# else:
#     outDatabase = "Outputs.gdb"
#
# if not arcpy.Exists(os.path.join(outDatabase, "VybranyVodniTok")):
#     FCDataset_VybranyVodniTok = str(arcpy.CreateFeatureDataset_management(outDatabase, "VybranyVodniTok", sr))
# else:
#     FCDataset_VybranyVodniTok = os.path.join(outDatabase, "VybranyVodniTok")

# TODO atributy pro zapis do cvs
fieldnames = ["ID", "vrtevnice_pocet"]

# Open csv file for writing the results
cislo = 1
while True:
    filename = config.workspace + "Vrstevnice_vysledky%s.csv" % cislo
    if not os.path.isfile(filename):
        break
    cislo = cislo +1

with open(filename, "wb") as vysledky_file:
    csv_writer = csv.writer(vysledky_file)
    csv_writer.writerow(fieldnames)

    # Vypocet pro vsechna uzemi
    # TODO zmenit na stav povodi - doplnit atribut
    where = "stav_predvyber = 'nevypocteno'"
    ctverce_cursor = arcpy.da.UpdateCursor(config.ctverce, ["Id", "SHAPE@"]) #, "stav_predvyber"], where)

    for ctverec in ctverce_cursor:
        ID = ctverec[0]
        shape = ctverec[1]
        print "\n Pracuji na ctverci: {0}".format(ID)

        # Volam funkci linarni interpolace
        result = povodi.fce_povodi(ID, shape, config.workspace, config.vstupni_data) #FCDataset_VybranyVodniTok)

        print "Vysledek = {0}".format(result)

        # zapis vysledek do csv souboru
        csv_writer.writerow(result)
        vysledky_file.flush()
        print "Zapsano do csv."

        # update stav
        # ctverec[2] = "vypocteno"
        # ctverce_cursor.updateRow(ctverec)

    del ctverce_cursor

vysledky_file.close()

# #########################
# # pokusy na obrazovku:
# ctverce_cursor = arcpy.da.UpdateCursor(config.ctverce, ["Id", "SHAPE@"])
#
# for ctverec in ctverce_cursor:
#     ID = ctverec[0]
#     shape = ctverec[1]
#     print "\n Pracuji na ctverci: {0}".format(ID)
#
#     # Volam funkci linarni interpolace
#     result_povodi = povodi.fce_povodi(ID, shape, config.workspace, config.vstupni_data) #FCDataset_VybranyVodniTok)
#
#     print "Funkce vratila vysledek = {0}".format(result_povodi)
# #######################

# Vysledny cas vypoctu
t2 = time.time()
TimeTakenSecs = str(t2 - t1)
print ("cas vypoctu: " + TimeTakenSecs + "sekund")

print "Konec 2_povodi.py"

sys.exit(777)
