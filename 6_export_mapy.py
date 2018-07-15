# -*- coding: utf-8 -*-

# Nazev:    6_export_mapy.py
# Autor:    Karolina Fenclova
# Popis:    Skript načte již vytvořené mxd a vyexportuje mapu do PDF
#
# Vstup:    .mxd soubory
#
# Vystup:   pdf soubor

##########################################################################################################
print "Start 6_export_mapy.py:"

# Merim cas vypoctu
import time
t1 = time.time()

import arcpy, os, config, sys

arcpy.env.workspace = config.workspace
arcpy.env.overwriteOutput = True

ctverce_cursor = arcpy.da.SearchCursor(config.ctverce, ["poradi", "SHAPE@"])

for ctverec in ctverce_cursor:
    poradi = ctverec[0]
    shape = ctverec[1]

    # zmenit cisla, když je poradi menši než 10, př. 002 a menší než 100, př. 089
    if poradi < 10:
        poradi = "00" + str(poradi)
    elif poradi < 100:
        poradi = "0" + str(poradi)
    else:
        poradi = poradi

    print "\n exp c.: {0}".format(poradi)

    # načtení dílčího mxd
    mxd = arcpy.mapping.MapDocument(os.path.join(config.dilci_mxd, "zadani{}.mxd".format(poradi)))

    # data frame
    df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]

    # zoom na prislusne uzemi
    zoom = arcpy.mapping.ListLayers(mxd)[0]
    df.extent = shape.extent
    df.scale = 25000
    arcpy.RefreshActiveView()
    arcpy.RefreshTOC()

    # export mapy
    arcpy.mapping.ExportToPDF(mxd, os.path.join(config.pdf_zadani, "zadani_{0}.pdf".format(poradi)), colorspace="CMYK", image_compression="LZW")
    print "vyexportovano"

del ctverce_cursor

# Vysledny cas vypoctu
t2 = time.time()
TimeTakenSecs = str(t2 - t1)
print ("cas vypoctu: " + TimeTakenSecs + "sekund")

print "Konec 5_tvorba_mxd.py"

sys.exit(777)
