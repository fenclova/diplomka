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

    # Zeleznice pro CTVEREC
    zeleznice_clip = arcpy.Clip_analysis((data + "dmu25_drazni_komunikace"), shape, "zeleznice_clip.shp", "")

    # Vrstevnice pro zajmovou oblast
    vrstevnice_clip = arcpy.Clip_analysis((data + "dmu25_vrstevnice_ziv5m"), shape, "vrstevnice_clip.shp", "")

    # Vodni plochy pro CTVEREC
    vodni_plocha_clip = arcpy.Clip_analysis((data + "dmu25_vodni_plochy"), shape, "vodni_plocha_clip.shp", "")

    # Vodni toky pro CTVEREC
    dibA02_clip = arcpy.Clip_analysis((data + "dmu25_reka_potok"), shape, "A02_clip.shp", "")

    # Skalnate uzemi + povrchova tezba pro CTVEREC
    relief_clip = arcpy.Clip_analysis((data + "dmu25_relief"), shape, "relief_clip.shp", "")

    # Zastavba pro CTVEREC
    zastavba_clip = arcpy.Clip_analysis((data + "dmu25_zastavba"), shape, "zastavba_clip.shp", "")

    # ...................VYPOCET HODNOT KRITERII............................
    # Delka zeleznice
    arcpy.AddGeometryAttributes_management(zeleznice_clip, "LENGTH", "METERS")
    g = arcpy.Geometry()
    geometryList = arcpy.CopyFeatures_management(zeleznice_clip, g)
    zeleznice_delka = 0
    for geometry in geometryList:
        zeleznice_delka += geometry.length

    # Pocet vrstevnic
    vrstevnice_pocet = int(arcpy.GetCount_management(vrstevnice_clip).getOutput(0))

    # Rozloha vodni plochy
    arcpy.AddGeometryAttributes_management(vodni_plocha_clip, "AREA")
    g = arcpy.Geometry()
    geometryList = arcpy.CopyFeatures_management(vodni_plocha_clip, g)
    vodni_plohy_rozloha = 0
    for geometry in geometryList:
        vodni_plohy_rozloha += geometry.area

    # Delka vodnich toku DIBAVOD
    arcpy.AddGeometryAttributes_management(dibA02_clip, "LENGTH", "METERS")
    g = arcpy.Geometry()
    geometryList = arcpy.CopyFeatures_management(dibA02_clip, g)
    dibA02_delka = 0
    for geometry in geometryList:
        dibA02_delka += geometry.length

    # Rozloha reliefu (skalnate uzemi + povrchova tezba)
    arcpy.AddGeometryAttributes_management(relief_clip, "AREA")
    g = arcpy.Geometry()
    geometryList = arcpy.CopyFeatures_management(relief_clip, g)
    relief_rozloha = 0
    for geometry in geometryList:
        relief_rozloha += geometry.area

    # Rozloha zastavby
    arcpy.AddGeometryAttributes_management(zastavba_clip, "AREA")
    g = arcpy.Geometry()
    geometryList = arcpy.CopyFeatures_management(zastavba_clip, g)
    zastavba_rozloha = 0
    for geometry in geometryList:
        zastavba_rozloha += geometry.area


    # VYSLEDKY
    result_info = [ID,
                   round(zeleznice_delka, 2),
                   round(vrstevnice_pocet, 2),
                   round(vodni_plohy_rozloha, 2),
                   round(dibA02_delka, 2),
                   round(relief_rozloha, 2),
                   round(zastavba_rozloha, 2)]

    # ....................................................................................................
    # UKLID
    arcpy.Delete_management(zeleznice_clip)
    arcpy.Delete_management(vrstevnice_clip)
    arcpy.Delete_management(vodni_plocha_clip)
    arcpy.Delete_management(dibA02_clip)
    arcpy.Delete_management(relief_clip)
    arcpy.Delete_management(zastavba_clip)
    # ....................................................................................................

    return result_info

# ------------------------------------------------------
