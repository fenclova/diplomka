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

    # Vodni plochy pro CTVEREC
    vodni_plocha_clip = arcpy.Clip_analysis((data + "dmu25_vodni_plochy"), shape, "vodni_plocha_clip.shp", "")

    # Vodni toky pro CTVEREC
    vodni_toky_clip = arcpy.Clip_analysis((data + "dmu25_reka_potok"), shape, "vodni_toky_clip.shp", "")

    # Obalova zona okolo dat dmu25 - pro vyber dibavod
    buffer_vodni_toky = arcpy.Buffer_analysis(vodni_toky_clip, "buffer_vodni_toky.shp", config.buffer_vodni_toky,
                                              "FULL",
                                              "ROUND", "ALL")
    buffer_vodni_plochy = arcpy.Buffer_analysis(vodni_plocha_clip, "buffer_vodni_plochy.shp",
                                                config.buffer_vodni_plochy, "FULL",
                                                "ROUND", "ALL")

    # Spoj obalove zony reky a vodni plochy
    inMerge = "buffer_vodni_toky.shp;buffer_vodni_plochy.shp"
    buffer_voda = arcpy.Merge_management(inMerge, "buffer_voda.shp", "")
    buffer_voda_dissolve = arcpy.Dissolve_management(buffer_voda, "buffer_voda_dissolve.shp", "", "", "SINGLE_PART",
                                                     "DISSOLVE_LINES")

    # DIBAVOD (A02 vodni toky jemne useky) pro zajmovou oblast (ctverec)
    dibA02_clip = arcpy.Clip_analysis((data + "dibavod_VodniTokyA02_rady"), shape, "dibA02_clip.shp", "")

    # VYBER a VYMAZ useky DIBAVOD, pokud linie nelezi uvnitr obalove zony
    inFeatures = dibA02_clip
    tempLayer = "dibA02_clip.lyr"
    selectFeatures = buffer_voda_dissolve
    arcpy.MakeFeatureLayer_management(inFeatures, tempLayer)
    arcpy.SelectLayerByLocation_management(tempLayer, "WITHIN", selectFeatures, selection_type="NEW_SELECTION",
                                           invert_spatial_relationship="INVERT")
    arcpy.DeleteFeatures_management(tempLayer)

    # VYBER a VYMAZ useky DIBAVOD, pokud rad vodniho toku = 0
    arcpy.SelectLayerByAttribute_management(tempLayer, "NEW_SELECTION", "gravelius = 0")
    arcpy.CopyFeatures_management(tempLayer, "grav0.shp")
    arcpy.DeleteFeatures_management(tempLayer)


    # TODO vymaz useky kratsi nez 2 km > merge dibavod podle tok_id?
    # nejdrive vyberu dibavod data a pak je spojim - hrozi, ze spojeny nebude lezet v obalove zone vodniho toku
    # !!! pokud start point linie neni koncem jine (pocatecni usek)

    # Delka vodnich toku DIBAVOD
    arcpy.AddGeometryAttributes_management(dibA02_clip, "LENGTH", "METERS")
    g = arcpy.Geometry()
    geometryList = arcpy.CopyFeatures_management(dibA02_clip, g)
    dibA02_delka = 0
    for geometry in geometryList:
        dibA02_delka += geometry.length

    # Delka neurcenych vodnich toku
    arcpy.AddGeometryAttributes_management("grav0.shp", "LENGTH", "METERS")
    g = arcpy.Geometry()
    geometryList = arcpy.CopyFeatures_management("grav0.shp", g)
    grav0_delka = 0
    for geometry in geometryList:
        grav0_delka += geometry.length

    # SPOJENI podle radu toku
    dibA02_clip_dissolve = arcpy.Dissolve_management(dibA02_clip, "dibA02_clip_dissolve.shp",
                                                         dissolve_field="gravelius",
                                                         statistics_fields="LENGTH SUM",
                                                         multi_part="MULTI_PART",
                                                         unsplit_lines="DISSOLVE_LINES")

    # pro kazdy rad urci delku linii
    rad_cursor = arcpy.da.SearchCursor(dibA02_clip_dissolve, ["gravelius", "SUM_LENGTH"])

    for radek in rad_cursor:
        rad_toku = radek[0]
        delka = radek[1]
        print "Rad: {0}, Delka: {1}".format(rad_toku, delka)

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
    #arcpy.Delete_management(vrstevnice_clip)

    # VYSLEDEK
    result = [cislo,
              round(dibA02_delka, 2),
              round(grav0_delka, 2)]
    return result
# ------------------------------------------------------