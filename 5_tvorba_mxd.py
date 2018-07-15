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
print "Start 5_tvorba_mxd.py:"

# Merim cas vypoctu
import time
t1 = time.time()

import arcpy, os, csv, config, sys

arcpy.env.workspace = config.workspace
arcpy.env.overwriteOutput = True

def tvorba_mxd(ID, shape, poradi, vhodny_ziv, kraj, okres, obec, X, Y):

    # otevreme vychozi podkladovy mxd dokument
    mxd = arcpy.mapping.MapDocument(r"C:\fenclova\diplomka\vystupy\export_zadani\Zadani_export.mxd")

    # data frame
    df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]

    # zoom na prislusne uzemi
    zoom = arcpy.mapping.ListLayers(mxd)[0]
    df.extent = shape.extent
    df.scale = 25000
    arcpy.RefreshActiveView()
    arcpy.RefreshTOC()

    # změnit napdisy a ZIV
    nadpis = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", "title")[0]
    nadpis.text = "zadání č. {0}".format(poradi)

    elm = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", "vhodny_ziv")[0]
    elm.text = "interval pro hypsometrii: {0} m".format(vhodny_ziv)

    lok = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", "lokace")[0]
    lok.text = "{}, okres {}, {} ({}, {})".format(kraj, okres, obec, X, Y)

    # vybere dane uzemi
    obrys = arcpy.FeatureClassToFeatureClass_conversion(config.ctverce, config.workspace,
                                                        "ctverec{0}.shp".format(poradi), "poradi = {}".format(poradi))
    buffer_obrys = arcpy.Buffer_analysis(obrys, "buffer_obrys.shp", "40 Meters")
    arcpy.FeatureEnvelopeToPolygon_management(buffer_obrys, os.path.join(config.data_pro_mxd, "obrys{}.shp".format(poradi)))

    # pridá obrys do mapy a načte symbologii
    uzemi = arcpy.mapping.Layer(os.path.join(config.data_pro_mxd, "obrys{}.shp".format(poradi)))
    arcpy.ApplySymbologyFromLayer_management(uzemi, "uzemi.lyr")
    arcpy.mapping.AddLayer(df, uzemi, "TOP")

    # nacte řeku
    novarekaLayer = arcpy.mapping.Layer(
        os.path.join(config.vodni_toky, "VodniToky.gdb", "VybranyVodniTok", "v{0}_vodni_tok".format(ID)))

    # pocatecni bod řeky
    pocatek = arcpy.FeatureVerticesToPoints_management(novarekaLayer, os.path.join(config.data_pro_mxd, "pocatek{}.shp".format(poradi)), "START")

    # KRÍŽEK NA VYBRANÉ ŘECE
    vzdalenost = 175
    min_vzdalenost = 75

    while (vzdalenost >= min_vzdalenost):

        # obalka, kde bude bod vybrane řeky
        buffer = arcpy.Buffer_analysis(obrys, "buffer.shp", "{} Meters".format(vzdalenost))
        okoli = arcpy.FeatureEnvelopeToPolygon_management(buffer, "okoli.shp")

        # Vodni toky pro okolí
        dmu25_clip = arcpy.Clip_analysis((config.vstupni_data + "dmu25_reka_potok"), okoli, "vodni_toky_clip.shp", "")

        # prusecik dmú 25 řek a obálky
        inFeatures = ["vodni_toky_clip.shp", "okoli.shp"]
        body_intersect = arcpy.Intersect_analysis(inFeatures, os.path.join(config.data_pro_mxd, "intersect{}.shp".format(poradi)), "", "", "POINT")

        # vymaz pruseciky vzdalenejsi nez 250 m
        inFeatures = body_intersect
        tempLayer = "body.lyr"
        selectFeatures = pocatek
        arcpy.MakeFeatureLayer_management(inFeatures, tempLayer)
        arcpy.SelectLayerByLocation_management(tempLayer, "WITHIN_A_DISTANCE", selectFeatures,
                                               "{} Meters".format(2 * vzdalenost),
                                               "NEW_SELECTION", "INVERT")
        arcpy.DeleteFeatures_management(tempLayer)


        # když existuje právě 1 průsečík dmú 25 s obrysek v okolí 500 m
        if (arcpy.management.GetCount(body_intersect)[0] == "1"):
            print "mam bod"
            nalezen_bod = 1

            krizek = arcpy.mapping.Layer(os.path.join(config.data_pro_mxd, "intersect{}.shp".format(poradi)))
            arcpy.ApplySymbologyFromLayer_management(krizek, "intersect.lyr")
            arcpy.mapping.AddLayer(df, krizek, "TOP")
            break

        # když neexistuje žádný či více než 1 průsečík > křížek v místě bodu
        else:
            vzdalenost = vzdalenost - 5
            print "vz = {}".format(vzdalenost)

            if vzdalenost == min_vzdalenost:
                print "neni bod"
                nalezen_bod = 0

                pocatek = arcpy.mapping.Layer(os.path.join(config.data_pro_mxd, "pocatek{}.shp".format(poradi)))
                arcpy.ApplySymbologyFromLayer_management(pocatek, "pocatek.lyr")
                arcpy.mapping.AddLayer(df, pocatek, "TOP")

    # uloz zmenenou kopii mxd
    mxd.saveACopy(os.path.join(config.dilci_mxd, "zadani{}.mxd".format(poradi)))

    arcpy.mapping.RemoveLayer(df, novarekaLayer)

    arcpy.DeleteFeatures_management("ctverec{0}.shp".format(poradi))
    arcpy.DeleteFeatures_management("buffer_obrys.shp")
    arcpy.DeleteFeatures_management("buffer.shp")
    arcpy.DeleteFeatures_management("okoli.shp")
    arcpy.DeleteFeatures_management("vodni_toky_clip.shp")

    # vysledek: ID, informace zda byl ci nebyl nalezen prusecik DMÚ 25 s okolím
    return [poradi, nalezen_bod]


# tvorba mxd a podkladových dat
ctverce_cursor = arcpy.da.SearchCursor(config.ctverce, ["ID", "SHAPE@", "poradi", "vhodny_ziv", "NAZ_CZNUTS", "NAZ_LAU1", "NAZ_OBEC","X", "Y"])

fieldnames = ["ID", "nalezen_bod"]

# Soubor pro zápis problematických mxd souborů
cislo = 1
while True:
    filename = config.workspace + "5_tvorba_mxd_problem_%s.csv" % cislo
    if not os.path.isfile(filename):
        break
    cislo = cislo +1

with open(filename, "wb") as vysledky_file:
    csv_writer = csv.writer(vysledky_file, delimiter=",")
    csv_writer.writerow(fieldnames)

    for ctverec in ctverce_cursor:
        ID = ctverec[0]
        shape = ctverec[1]
        poradi = ctverec[2]
        vhodny_ziv = ctverec[3]
        kraj = ctverec[4].encode('utf-8').strip()
        okres = ctverec[5].encode('utf-8').strip()
        obec = ctverec[6].encode('utf-8').strip()
        X = int(ctverec[7])
        Y = int(ctverec[8])

        # zmenit cisla, když je poradi menši než 10, př. 002 a menší než 100, př. 089
        if poradi < 10:
            poradi = "00" + str(poradi)
        elif poradi < 100:
            poradi = "0" + str(poradi)
        else:
            poradi = poradi

        print "\n C.: {0}".format(poradi)

        # Volam funkci linarni interpolace
        vysledek = tvorba_mxd(ID, shape, poradi, vhodny_ziv, kraj, okres, obec, X, Y)

        # zapis vysledek do csv souboru
        csv_writer.writerow(vysledek)
        vysledky_file.flush()
vysledky_file.close()

del ctverce_cursor


# Vysledny cas vypoctu
t2 = time.time()
TimeTakenSecs = str(t2 - t1)
print ("cas vypoctu: " + TimeTakenSecs + "sekund")

print "Konec 5_tvorba_mxd.py"

sys.exit(777)
