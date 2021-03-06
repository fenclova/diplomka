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

# Databaze GDB s vodnim tokem
FCDataset_VybranyVodniTok = os.path.join(config.vodni_toky, "VodniToky.gdb", "VybranyVodniTok")
FCDataset_VybranyVodniTok = os.path.join(config.vodni_toky, "VodniToky.gdb", "VybranyVodniTok")

# Feature Class pro ukladani vysledku hypsometrie - dodelat gdb
FCDataset_HypsoVrstevnice = os.path.join("Stavajici_mapy.gdb", "Vrstevnice")

fieldnames5 = ["ID", "ziv5_celkem", "ziv5_1", "ziv5_2", "ziv5_3","ziv5_4","ziv5_5", "ziv5_6", "ziv5_7", "ziv5_8",
               "ziv5_9", "ziv5_10", "ziv5_11", "ziv5_12", "ziv5_13", "ziv5_14", "ziv5_15", "ziv5_16"]

fieldnames10 = ["ID", "ziv10_celkem", "ziv10_1", "ziv10_2", "ziv10_3","ziv10_4","ziv10_5", "ziv10_6", "ziv10_7", "ziv10_8",
               "ziv10_9", "ziv10_10", "ziv10_11", "ziv10_12", "ziv10_13", "ziv10_14", "ziv10_15", "ziv10_16"]

fieldnames20 = ["ID", "ziv20_celkem", "ziv20_1", "ziv20_2", "ziv20_3","ziv20_4","ziv20_5", "ziv20_6", "ziv20_7", "ziv20_8",
               "ziv20_9", "ziv20_10", "ziv20_11", "ziv20_12", "ziv20_13", "ziv20_14", "ziv20_15", "ziv20_16"]

# Open csv file for writing the results
cislo5 = 1
while True:
    filename5 = config.workspace + "1_hypsometrieZIV5_%s.csv" % cislo5
    if not os.path.isfile(filename5):
        break
    cislo5 = cislo5 +1

cislo10 = 1
while True:
    filename10 = config.workspace + "1_hypsometrieZIV10_%s.csv" % cislo10
    if not os.path.isfile(filename10):
        break
    cislo10 = cislo10 +1

cislo20 = 1
while True:
    filename20 = config.workspace + "1_hypsometrieZIV20_%s.csv" % cislo20
    if not os.path.isfile(filename20):
        break
    cislo20 = cislo20 +1

# Vypocet pro vsechna uzemi
where = "HypsoPovodi = 1"
#ctverce_cursor = arcpy.da.UpdateCursor(config.ctverce, ["Id", "SHAPE@", "stav_hypsometrie"], where)
ctverce_cursor = arcpy.da.UpdateCursor(config.ctverce, ["Id", "SHAPE@"], where)

with open(filename5, "wb") as vysledky_file5:
    csv_writer5 = csv.writer(vysledky_file5, delimiter=",")
    csv_writer5.writerow(fieldnames5)

    with open(filename10, "wb") as vysledky_file10:
        csv_writer10 = csv.writer(vysledky_file10, delimiter=",")
        csv_writer10.writerow(fieldnames10)

        with open(filename20, "wb") as vysledky_file20:
            csv_writer20 = csv.writer(vysledky_file20, delimiter=",")
            csv_writer20.writerow(fieldnames20)

            for ctverec in ctverce_cursor:
                ID = ctverec[0]
                shape = ctverec[1]
                print "\n ID: {0}".format(ID)

                try:
                    # Volam funkci linarni interpolace
                    result_linearni_interpolace = hypsometrie.linearni_interpolace(ID, shape, config.workspace,
                                                                                       config.vstupni_data, FCDataset_VybranyVodniTok, FCDataset_HypsoVrstevnice)

                    # Pridani vysledku do CSV souboru, ulozeni
                    csv_writer5.writerow(result_linearni_interpolace[0])
                    vysledky_file5.flush()

                    csv_writer10.writerow(result_linearni_interpolace[1])
                    vysledky_file10.flush()

                    csv_writer20.writerow(result_linearni_interpolace[2])
                    vysledky_file20.flush()

                    # update stav
                    #ctverec[2] = "vypocteno"
                    #ctverce_cursor.updateRow(ctverec)

                except:
                    "Nelze vypocitat."

            del ctverce_cursor

        vysledky_file20.close()
    vysledky_file10.close()
vysledky_file5.close()

# Vysledny cas vypoctu
t2 = time.time()
TimeTakenSecs = str(t2 - t1)
print ("cas vypoctu: " + TimeTakenSecs + "sekund")

print 'Konec 1_hypsometrie.py'

sys.exit(777)