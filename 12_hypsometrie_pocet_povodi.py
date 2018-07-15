# -*- coding: utf-8 -*-

#  Nazev:     1_hypsometrie.py
# Autor:    Karolina Fenclova
# Popis:    Skript na vytvoreni vrstevnic linearni interpolaci pro mapu hypsometrie
#           1. priprava vstupnich dat, 2. tvorba vrstevnic linearni interpolaci
#
# Vstup:    soubor config = nastaveni workspace + dat ke zpracovani

#
# Vystup pro kazde uzemi: vybrany_vodni_tok, ZIV5_hypso, ZIV10_hypso, ZIV20_hypso
#                         zapis vyslednych hodnot do databaze

##########################################################################################################
print "Start 12_hypsometrie_pocet_povodi.py:"

# Merim cas vypoctu
import time
t1 = time.time()

import arcpy, csv, config, sys, os

# import funkce z jineho souboru
import fce_hypsometrie as hypsometrie
import fce_povodi as povodi
import fce_predvyber as predvyber

arcpy.env.workspace = config.workspace
arcpy.env.overwriteOutput = True
sr = arcpy.SpatialReference(32633)

# Databaze GDB s vodnim tokem
FCDataset_VybranyVodniTok = os.path.join(config.vodni_toky, "VodniToky.gdb", "VybranyVodniTok")

# hlavičky pro zápis do csv souborů
fieldnames5 = ["ID", "ziv5_celkem", "ziv5_1", "ziv5_2", "ziv5_3","ziv5_4","ziv5_5", "ziv5_6", "ziv5_7", "ziv5_8",
               "ziv5_9", "ziv5_10", "ziv5_11", "ziv5_12", "ziv5_13", "ziv5_14", "ziv5_15", "ziv5_16"]

fieldnames10 = ["ID", "ziv10_celkem", "ziv10_1", "ziv10_2", "ziv10_3","ziv10_4","ziv10_5", "ziv10_6", "ziv10_7", "ziv10_8",
               "ziv10_9", "ziv10_10", "ziv10_11", "ziv10_12", "ziv10_13", "ziv10_14", "ziv10_15", "ziv10_16"]

fieldnames20 = ["ID", "ziv20_celkem", "ziv20_1", "ziv20_2", "ziv20_3","ziv20_4","ziv20_5", "ziv20_6", "ziv20_7", "ziv20_8",
               "ziv20_9", "ziv20_10", "ziv20_11", "ziv20_12", "ziv20_13", "ziv20_14", "ziv20_15", "ziv20_16"]

fieldnamesPovodi = ["ID", "pocet_povodi", "pocet_povodi_vse", "rozvodnice_delka", "dibA02_delka"]

fieldnamesKriteria = ["ID", "zeleznice_delka", "silnice_delka", "dalnice_delka", "vrstevnice_delka", "rozvodniceIII_delka", "rozvodniceII_delka", "rozvodniceI_delka",
                "vodni_plohy_rozloha", "vodni_nadrz_rozloha", "dibA02_delka", "relief_rozloha", "zastavba_rozloha"]

#### VODNI TOK ######
# Databaze GDB pro ukladani vystupu pro hodnoceni
if not arcpy.Exists("VodniToky.gdb"):
    outDatabase = str(arcpy.CreateFileGDB_management(out_folder_path= config.workspace, out_name="VodniToky", out_version="CURRENT"))
else:
    outDatabase = "VodniToky.gdb"

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
    filename = config.workspace + "0_predvyber_vodni_tok_%s.csv" % cislo
    if not os.path.isfile(filename):
        break
    cislo = cislo +1


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

cisloPovodi = 1
while True:
    filenamePovodi = config.workspace + "2_pocet_povodi%s.csv" % cisloPovodi
    if not os.path.isfile(filenamePovodi):
        break
    cisloPovodi = cisloPovodi +1

cislo = 1
while True:
    filenameKriteria = config.workspace + "0_predvyber_vice%s.csv" % cislo
    if not os.path.isfile(filenameKriteria):
        break
    cislo = cislo +1

# Vypocet pro vsechna uzemi
where = "Stav = 0"

ctverce_cursor = arcpy.da.UpdateCursor(config.ctverce, ["Id", "SHAPE@", "Stav"], where)

with open(filenameKriteria, "wb") as vysledky_fileKriteria:
    csv_writerKriteria = csv.writer(vysledky_fileKriteria)
    csv_writerKriteria.writerow(fieldnamesKriteria)

    with open(filenamePovodi, "wb") as vysledky_filePovodi:
        csv_writerPovodi = csv.writer(vysledky_filePovodi)
        csv_writerPovodi.writerow(fieldnamesPovodi)

        with open(filename5, "wb") as vysledky_file5:
            csv_writer5 = csv.writer(vysledky_file5)
            csv_writer5.writerow(fieldnames5)

            with open(filename10, "wb") as vysledky_file10:
                csv_writer10 = csv.writer(vysledky_file10)
                csv_writer10.writerow(fieldnames10)

                with open(filename20, "wb") as vysledky_file20:
                    csv_writer20 = csv.writer(vysledky_file20)
                    csv_writer20.writerow(fieldnames20)

                    with open(filename, "wb") as vysledky_file:
                        csv_writer = csv.writer(vysledky_file)
                        csv_writer.writerow(fieldnames)

                        for ctverec in ctverce_cursor:
                            ID = ctverec[0]
                            shape = ctverec[1]
                            print "\n ID: {0}".format(ID)

                            try:
                                # hledam vodni tok
                                result_predvyber = predvyber.vyber_vodni_tok(ID, shape, config.workspace,
                                                                                 config.vstupni_data,
                                                                                 FCDataset_VybranyVodniTok)
                                print result_predvyber

                                # Volam funkci linarni interpolace
                                vysledek_hypso = hypsometrie.linearni_interpolace(ID, shape, config.workspace,
                                                                                  config.vstupni_data,
                                                                                  FCDataset_VybranyVodniTok)
                                print "ok"
                                print vysledek_hypso

                                # Volam funkci na pocet povodi
                                vysledek_povodi = povodi.tvorba_povodi(ID, shape, config.workspace, config.vstupni_data)
                                print "ok"
                                print vysledek_povodi

                                # Volam funkci na vypocet dalsich charakteristik
                                vysledek_kriteria = predvyber.zakladni_kriteria(ID, shape, config.workspace,
                                                                                config.vstupni_data)
                                print "ok"
                                print vysledek_kriteria

                                # Pridani vysledku do CSV souboru, ulozeni
                                csv_writer.writerow(result_predvyber)
                                vysledky_file.flush()

                                csv_writer5.writerow(vysledek_hypso[0])
                                vysledky_file5.flush()

                                csv_writer10.writerow(vysledek_hypso[1])
                                vysledky_file10.flush()

                                csv_writer20.writerow(vysledek_hypso[2])
                                vysledky_file20.flush()

                                csv_writerPovodi.writerow(vysledek_povodi)
                                vysledky_filePovodi.flush()

                                csv_writerKriteria.writerow(vysledek_kriteria)
                                vysledky_fileKriteria.flush()

                                # update stav
                                ctverec[2] = "1"
                                ctverce_cursor.updateRow(ctverec)

                                # Cas vypoctu
                                tp = time.time()
                                TimeTakenSecs = str(tp - t1)
                                print ("Cas:" + TimeTakenSecs + "s")

                            except:
                                "Nelze vypocitat."


                        del ctverce_cursor

                    vysledky_file.close()
                vysledky_file20.close()
            vysledky_file10.close()
        vysledky_file5.close()
    vysledky_filePovodi.close()
vysledky_fileKriteria.close()

# Vysledny cas vypoctu
t2 = time.time()
TimeTakenSecs = str(t2 - t1)
print ("Cas vypoctu: " + TimeTakenSecs + "sekund")

print 'Konec 12_hypsometrie_pocet_povodi.py'

sys.exit(777)