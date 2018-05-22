# ....................................................................................................
# Nazev:    fce_predvyber.py
# Autor:    Karolina Fenclova
# Popis:    Skript na vypocet hodnot kriterii, ktere slouzi k prvotnimu vyberu vhodnych variant

# VSTUP:    vektorova data:
#               dmu25_vrstevnice_ziv5m, dmu25_vodni_plochy, dmu25_reka_potok, dmu25_drazni_komunikace, dmu25_zastavba, dmu25_relief
#               dibavod_Povodi_III_A08, dibavod_VodniTokyA02

# VYSTUP:   hodnoty kriterii:
#               nejlepsi_podil_ploch = podil ploch ctverce (max/min) pro vybrany vodni tok
#               pocet_pruseciku = pocet pruseciku vybraneho vodniho toku a mrizky i diagonalni
#               zeleznice_delka, rozvodnice_delka = delka linii v 1 ctverci
#               vodni_plohy_rozloha, relief_rozloha, zastavba_rozloha = rozloha polygonu v 1 ctverci
# ....................................................................................................

import arcpy, os, config

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True


# Funkce predvyber uzemi
def fce_predvyber(ID, shape, workspace, data):
    sr = arcpy.SpatialReference(32633)  # EPSG kod pro spatial reference

    # PRIPRAVA DAT PRO DANE UZEMI
    print "data.."

    # Vrstevnice pro zajmovou oblast
    vrstevnice_clip = arcpy.Clip_analysis((data + "dmu25_vrstevnice_ziv5m"), shape, "vrstevnice_clip.shp", "")

    # Vodni plochy pro CTVEREC
    vodni_plocha_clip = arcpy.Clip_analysis((data + "dmu25_vodni_plocha_nadrz"), shape, "vodni_plocha_clip.shp", "")

    # ...................VYPOCET HODNOT KRITERII............................
    # Delka vrstevnic
    arcpy.AddGeometryAttributes_management(vrstevnice_clip, "LENGTH", "METERS")
    g = arcpy.Geometry()
    geometryList = arcpy.CopyFeatures_management(vrstevnice_clip, g)
    vrstevnice_delka = 0
    for geometry in geometryList:
        vrstevnice_delka += geometry.length

    # Rozloha vodni plochy
    arcpy.AddGeometryAttributes_management(vodni_plocha_clip, "AREA")
    g = arcpy.Geometry()
    geometryList = arcpy.CopyFeatures_management(vodni_plocha_clip, g)
    vodni_plohy_rozloha = 0
    for geometry in geometryList:
        vodni_plohy_rozloha += geometry.area


    # VYSLEDKY
    result_info = [ID,
                   round(vodni_plohy_rozloha, 2),
                   round(vrstevnice_delka, 2)]

    # ....................................................................................................
    # UKLID
    arcpy.Delete_management(vrstevnice_clip)
    arcpy.Delete_management(vodni_plocha_clip)
    # ....................................................................................................

    return result_info

# ------------------------------------------------------