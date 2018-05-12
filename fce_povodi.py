# Nazev:            fce_povodi.py
# Autor:            Karolina Fenclova
# Popis:            Skript na vypocet kriterii pro mapu povodi

# VSTUP:

# VYSTUP:

import arcpy, config, os

arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")
arcpy.env.overwriteOutput = True

# Funkce linearni interpolace
def fce_povodi(ID, shape, workspace, data):
    cislo = ID
    sr = arcpy.SpatialReference(32633) # EPSG kod pro spatial reference

    # ....................................................................................................
    # PRIPRAVA DAT PRO DANE UZEMI
    print "Pripravuji data..."

    # Vrstevnice pro zajmovou oblast
    vrstevnice_clip = arcpy.Clip_analysis((data + "dmu25_vrstevnice_ziv5m"), shape, "vrstevnice_clip.shp", "")
    vrstevnice_pocet = int(arcpy.GetCount_management(vrstevnice_clip).getOutput(0))

    # # Vodni plochy pro zajmovou oblast
    # vodni_plocha_clip = arcpy.Clip_analysis((data + "dmu25_vodni_plochy"), buffer_ctverec, "vodni_plocha_clip.shp", "")
    #
    # # Vodni toky pro zajmovou oblast
    # vodni_toky_clip = arcpy.Clip_analysis((data + "dmu25_reka_potok"), buffer_ctverec, "vodni_toky_clip.shp", "")

    #....................................................................................................
    # OPRAVA SMERU VODNICH TOKU - podle Digitalniho modelu terenu (jen z vrstevnic)

    # # Digitalni model terenu pouze z vrstevnic = slouzi k urceni vysky pocatku a konce vodniho toku
    # print "Tvorim DMT jen z vrstevnic..."
    # inContours = "vrstevnice_clip.shp VYSKA Contour"
    # outFeature = "dmt"
    # ext_pro_dmt = arcpy.Describe(hranice)
    # extent = (str(ext_pro_dmt.extent.XMin) + " " + str(ext_pro_dmt.extent.YMin) + " " + str(
    #     ext_pro_dmt.extent.XMax) + " " + str(ext_pro_dmt.extent.YMax))
    # dmt = arcpy.TopoToRaster_3d(inContours, outFeature, config.dmt_resolution, extent)



    # ....................................................................................................
    print "uklizim po sobe..."
    arcpy.Delete_management(vrstevnice_clip)

    # VYSLEDEK = list listu
    result = [cislo, vrstevnice_pocet]
    return result
# ------------------------------------------------------