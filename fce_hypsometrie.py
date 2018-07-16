# -*- coding: utf-8 -*-
# Nazev:            fce_linearni_interpolace.py
# Autor:            Karolina Fenclova
# Popis:            Skript na vypocet linearni interpolace u mapy hypsometrie. vystupem pocet vrstevnic v dilcich ctvercich

# VSTUP: fce_linearni_interpolace(ID, ctverec, workspace, data, vodni_tok)
#     ctverec = uzemi 4x4 km
#     ID = ID ctverce
#     workspace = adresar pro ukladani mezivysledku, ktere se budou mazat
#     data = cesta k datum dmu25
#     vodni_tok = cesta k databazi halvni vodni tok

# VYSTUP: result = [ZIV5, ZIV10, ZIV20]
#    pro kazdy interval ZIV je zapsano: id, pocet_vrstevnic, vzniklych linearni interpolaci a 16krat pocet vrstevnic v dilcich ctvercich

import arcpy, config, os

arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")
arcpy.env.overwriteOutput = True

# Funkce linearni interpolace
def linearni_interpolace(ID, shape, workspace, data, FCDataset_VybranyVodniTok, FCDataset_HypsoVrstevnice):

    sr = arcpy.SpatialReference(32633) # EPSG kod pro spatial reference

    # PRIPRAVA DAT PRO DANE UZEMI
    print "hypso"

    # Zajmova oblast okolo ctverce
    buffer_ctverec = arcpy.Buffer_analysis(shape, "buffer_ctverec.shp", config.buffer_ctverec_vzdalenost)

    # Vrstevnice pro zajmovou oblast
    vrstevnice_clip = arcpy.Clip_analysis((data + "dmu25_vrstevnice_ziv5m"), buffer_ctverec, "vrstevnice_clip.shp", "")

    # Kotovane body pro zajmovou oblast
    koty_clip = arcpy.Clip_analysis((data + "vektorizace_kotovane_body"), buffer_ctverec, "kotovane_body_clip.shp", "")

    # Vodni plochy pro zajmovou oblast
    vodni_plocha_clip = arcpy.Clip_analysis((data + "dmu25_vodni_plochy"), buffer_ctverec, "vodni_plocha_clip.shp", "")

    # Vodni toky pro zajmovou oblast
    vodni_toky_clip = arcpy.Clip_analysis((data + "dmu25_reka_potok"), buffer_ctverec, "vodni_toky_clip.shp", "")

    #....................................................................................................
    # OPRAVA SMERU VODNICH TOKU - podle Digitalniho modelu terenu (jen z vrstevnic)

    # Digitalni model terenu pouze z vrstevnic = slouzi k urceni vysky pocatku a konce vodniho toku
    inContours = "vrstevnice_clip.shp VYSKA Contour"
    outFeature = "dmt"
    ext_pro_dmt = arcpy.Describe(buffer_ctverec)
    extent = (str(ext_pro_dmt.extent.XMin) + " " + str(ext_pro_dmt.extent.YMin) + " " + str(
        ext_pro_dmt.extent.XMax) + " " + str(ext_pro_dmt.extent.YMax))
    dmt = arcpy.TopoToRaster_3d(inContours, outFeature, config.dmt_resolution, extent)

    # Pocatek a konec linie vodniho toku
    start_point = arcpy.FeatureVerticesToPoints_management(vodni_toky_clip, "start_point.shp", "START")
    end_point = arcpy.FeatureVerticesToPoints_management(vodni_toky_clip, "end_point.shp", "END")

    # Pro pocatek a konec linie vodniho toku zjistuji vysku z DMT
    start_vyska = arcpy.sa.ExtractValuesToPoints(start_point, dmt, "start_vyska.shp", "NONE", "VALUE_ONLY")
    end_vyska = arcpy.sa.ExtractValuesToPoints(end_point, dmt, "end_vyska.shp", "NONE", "VALUE_ONLY")

    cursor_reka = arcpy.da.UpdateCursor(vodni_toky_clip, "SHAPE@")
    cursor_start = arcpy.da.SearchCursor(start_vyska, "RASTERVALU")
    cursor_end = arcpy.da.SearchCursor(end_vyska, "RASTERVALU")

    # Hodnoty vysek pro pocatecni a koncove body lini vodnich toku
    start_value, end_value = [], []

    # Pro kazdy bod pridam hodnotu do pole vysek
    for row in cursor_start: start_value.append(row[0])
    for row in cursor_end: end_value.append(row[0])

    # Prochazim linie vodnich toku (i slouzi k dotazu na hodnotu vysek)
    i = 0
    for row in cursor_reka:

        # Pokud linie zacina v nizsi vysce nez konci
        if start_value[i] < end_value[i]:
            # Chci body, ze kterych je slozena linie
            vertices = []
            for part in row[0]:
                for pnt in part:
                    vertices.append(pnt)

            # Tvorim novou linii s otocenym poradim bodu
            row[0] = arcpy.Polyline(arcpy.Array(vertices[::-1]))

            # Aktualizuji dany usek linie
            cursor_reka.updateRow(row)

        i = i + 1

    del cursor_reka, cursor_end, cursor_start

    # Mazu prvni dmt
    arcpy.Delete_management(dmt)

    #....................................................................................................
    # HYDROLOGICKY SPRAVNY Digitalni model terenu

    # vstup do DMT (vrstevnice, koty, vodni plochy, vodni toky spravneho smeru)
    inContours = "vrstevnice_clip.shp VYSKA Contour"
    inPointElevations = "kotovane_body_clip.shp VYSKA PointElevation"
    inLake = "vodni_plocha_clip.shp # Lake"
    inStream = "vodni_toky_clip.shp # Stream"
    inFeatures = (inPointElevations + ";" + inContours + ";" + inLake + ";" + inStream)

    dmt = arcpy.TopoToRaster_3d(inFeatures, "dmt", config.dmt_resolution, extent)

    #....................................................................................................
    # TVORBA MRIZKY, ROHOVYCH BODU, CENTROIDU A ZJISTOVANI VYSKY

    # Zakladni ctvercova mrizka po 1 kilometru
    desc = shape
    XMin = desc.extent.XMin
    YMax = desc.extent.YMax
    mrizka = arcpy.CreateFishnet_management("mrizka_1km.shp", str(desc.extent.lowerLeft),
                                                str(XMin) + " " + str(YMax + 10), "1000", "1000",
                                                "0", "0", str(desc.extent.upperRight), "LABELS", "#", "POLYGON")

    # Rohove body mrizky = 25 bodu (+ vymazu identicke)
    body25 = arcpy.FeatureVerticesToPoints_management(mrizka, "body25.shp", "ALL")
    arcpy.DeleteIdentical_management(body25, "Shape", "", "0")
    arcpy.DeleteField_management(body25, "ORIG_FID")

    # Pro 25 rohovych bodu mrizky urci vysku a zaokrouhli
    body25_vyska = arcpy.sa.ExtractValuesToPoints(body25, dmt, "body25_vyska.shp", "NONE", "VALUE_ONLY")
    arcpy.AddField_management(body25_vyska, "VYSKA", "DOUBLE")
    arcpy.CalculateField_management(body25_vyska, "VYSKA", "round( !RASTERVALU! , 0)",
                                    "PYTHON")  # RASTERVALU = hodnota bez zaokrouhleni

    # Spocteni minima a maxima v dilcich ctvercich -> vyska centroidu = (MIN+MAX)/2
    zonal_min = arcpy.gp.ZonalStatistics_sa(mrizka, "FID", dmt, "dmt_min", "MINIMUM", "DATA")
    zonal_max = arcpy.gp.ZonalStatistics_sa(mrizka, "FID", dmt, "dmt_max", "MAXIMUM", "DATA")

    # Centroidy mrizky a jejich vyska
    centroidy = "mrizka_1km_label.shp"
    centroidy_min = arcpy.sa.ExtractValuesToPoints(centroidy, zonal_min, "centroidy_min.shp", "NONE", "VALUE_ONLY")

    # Zaokrouhli vysku a vymaz pole RASTERVALU
    arcpy.AddField_management(centroidy_min, "VYSKA_MIN", "DOUBLE")
    arcpy.CalculateField_management(centroidy_min, "VYSKA_MIN", "round( !RASTERVALU! , 0)", "PYTHON")
    arcpy.DeleteField_management(centroidy_min, "RASTERVALU")

    # MAX vyska (v poli RASTERVALU)
    centroidy_vyska = arcpy.sa.ExtractValuesToPoints(centroidy_min, zonal_max, "centroidy_vyska.shp", "NONE",
                                                     "VALUE_ONLY")

    # Zaokrouhli vysku a vymaz pole RASTERVALU
    arcpy.AddField_management(centroidy_vyska, "VYSKA_MAX", "DOUBLE")
    arcpy.CalculateField_management(centroidy_vyska, "VYSKA_MAX", "round( !RASTERVALU! , 0)", "PYTHON")
    arcpy.DeleteField_management(centroidy_vyska, "RASTERVALU")

    # Spocti hodnotu centroidu
    arcpy.AddField_management(centroidy_vyska, "VYSKA", "DOUBLE")
    arcpy.CalculateField_management(centroidy_vyska, "VYSKA", "round(((!VYSKA_MIN! + !VYSKA_MAX!)/2) , 0)", "PYTHON")

    # ....................................................................................................
    # TVORBA UHLOPRICEK
    arcpy.Delete_management("uhlopricky.shp")
    uhlopricky = arcpy.CreateFeatureclass_management(config.workspace, "uhlopricky.shp", "POLYLINE", "#", "#", "#", sr)
    # Pridame atribut (VALUE <= ID)
    arcpy.AddField_management(uhlopricky, "VALUE", "SHORT")

    # Kurzor pro vkladani
    insCur = arcpy.da.InsertCursor(uhlopricky, ["SHAPE@", "VALUE"])

    # Souradnice stredu mrizky
    x = XMin + 2000
    y = YMax - 2000

    # Spojnice pro linie mrizky (ID, x1, y1, x2, y2)
    k1 = 1000
    k2 = 2000
    body = [[1, x - k2, y + k2, x + k2, y - k2],
            [2, x - k1, y + k2, x + k2, y - k1],
            [3, x, y + k2, x + k2, y],
            [4, x + k1, y + k2, x + k2, y + k1],
            [5, x - k2, y + k1, x + k1, y - k2],
            [6, x - k2, y, x, y - k2],
            [7, x - k2, y - k1, x - k1, y - k2],
            [8, x - k2, y + k1, x - k1, y + k2],
            [9, x, y + k2, x - k2, y],
            [10, x + k1, y + k2, x - k2, y - k1],
            [11, x + k2, y + k2, x - k2, y - k2],
            [12, x + k2, y + k1, x - k1, y - k2],
            [13, x + k2, y, x, y - k2],
            [14, x + k2, y - k1, x + k1, y - k2]]

    # Zacneme tvorit vystup
    geom = arcpy.Array()

    for i in body:
        value = i[0]
        part = arcpy.Array()
        part.add(arcpy.Point(i[1], i[2]))
        part.add(arcpy.Point(i[3], i[4]))
        # Pridam cast do pole geometrie
        geom.add(part)

        # Vytvorim polylini z pole geometrii
        insCur.insertRow((arcpy.Polyline(geom), value))

    del insCur

    # Obrysova linie mrizky
    mrizka_linie = arcpy.PolygonToLine_management(mrizka, "mrizka_linie.shp")

    # Spojeni mrizky a uhlopricek
    input = "mrizka_linie.shp;uhlopricky.shp"
    mrizka_uhlopricky = arcpy.Merge_management(input, "mrizka_uhlopricky.shp", "")

    # ....................................................................................................
    # NACTENI VODNIHO TOKU
    # Existuje-li vodni tok, ktery deli uzemi na 2 casti
    fullPath_VybranyVodniTok = os.path.join(FCDataset_VybranyVodniTok,
                                                "v{0}_vodni_tok".format(ID))

    if arcpy.Exists(fullPath_VybranyVodniTok):
        print "tok nacten"
        # ....................................................................................................
        # PRUSECIKY VYBRANEHO VODNIHO TOKU A MRIZKY A UHLOPRICEK
        in_features = fullPath_VybranyVodniTok + ";" + "mrizka_uhlopricky.shp"
        body_intersect = arcpy.Intersect_analysis(in_features, "intersect.shp", "ONLY_FID", "-1 Unknown", "POINT")
        arcpy.DeleteIdentical_management(body_intersect, "Shape", "", "0")      # mazu identicke body
        body_intersect_single = arcpy.MultipartToSinglepart_management(body_intersect, "body_intersect_single.shp")

        # ....................................................................................................
        # VYTVORENI 3D hrany pro TIN
        # Vybrany vodni tok se spoji (dissolve) a rozdeli podle pruseciku s mrizkou (split line)
        vodni_tok_dissolve = arcpy.Dissolve_management(fullPath_VybranyVodniTok, "vodni_tok_dissolve", "", "", "SINGLE_PART", "DISSOLVE_LINES")
        vodni_tok_split = arcpy.SplitLineAtPoint_management(vodni_tok_dissolve, body_intersect_single, "vodni_tok_split.shp", "50 Meters")

        arcpy.AddField_management(vodni_tok_split, "POCATEK", "DOUBLE")
        arcpy.AddField_management(vodni_tok_split, "KONEC", "DOUBLE")

        # vytvor start a end pointy
        arcpy.Delete_management("start_point.shp")
        start_point = arcpy.FeatureVerticesToPoints_management(vodni_tok_split, "start_point.shp", "START")
        start_vyska = arcpy.sa.ExtractValuesToPoints(start_point, dmt, "start_vyska.shp", "NONE", "VALUE_ONLY")

        arcpy.Delete_management("end_point.shp")
        end_point = arcpy.FeatureVerticesToPoints_management(vodni_tok_split, "end_point.shp", "END")
        end_vyska = arcpy.sa.ExtractValuesToPoints(end_point, dmt, "end_vyska.shp", "NONE", "VALUE_ONLY")

        cursor_start = arcpy.da.SearchCursor(start_vyska, "RASTERVALU")
        cursor_end = arcpy.da.SearchCursor(end_vyska, "RASTERVALU")

        # Z vysek budu tvorit pole hodnot
        start_value, end_value = [], []

        # Pro kazdy bod pridam hodnotu do pole vysek
        for row in cursor_start: start_value.append(row[0])
        for row in cursor_end: end_value.append(row[0])
        del cursor_end, cursor_start

        # Prochazim linie vodnich toku (i slouzi k dotazu na hodnotu vysek)
        i = 0
        with arcpy.da.UpdateCursor(vodni_tok_split, ["SHAPE@", "POCATEK", "KONEC"]) as cursor:
            for row in cursor:
                row[1] = start_value[i]
                row[2] = end_value[i]
                cursor.updateRow(row)
                i = i + 1

        vodni_tok3D = arcpy.FeatureTo3DByAttribute_3d(vodni_tok_split, "vodni_tok_3D.shp", "POCATEK", "KONEC")

        # ....................................................................................................
        # VYMAZAT Centroidy pokud je v blizkosti PRUSECIK S REKOU (ten ma prioritu)
        inFeatures = centroidy_vyska
        tempLayer = "centroidy_vyska.lyr"
        selectFeatures = "body_intersect_single.shp"
        arcpy.MakeFeatureLayer_management(inFeatures, tempLayer)

        arcpy.SelectLayerByLocation_management(tempLayer, "WITHIN_A_DISTANCE", selectFeatures, config.centroid_tolerance, "NEW_SELECTION", "NOT_INVERT")
        arcpy.DeleteFeatures_management(tempLayer)

        # ....................................................................................................
        # PRO PRUSECIKY REKY A MRIZKY ODECITAM Z VYSKU Z DEM
        body_intersect_single_vyska = arcpy.sa.ExtractValuesToPoints(body_intersect_single, dmt, "body_intersect_vyska.shp", "NONE", "VALUE_ONLY")
        arcpy.AddField_management(body_intersect_single_vyska, "VYSKA", "DOUBLE")
        arcpy.CalculateField_management(body_intersect_single_vyska, "VYSKA", "round( !RASTERVALU! , 0)", "PYTHON") # RASTERVALU = hodnota bez zaokrouhleni

        # ....................................................................................................
        # TVORBA TINu z 25 + 16 + X bodu
        inFeatures = "body25_vyska.shp VYSKA Mass_Points <None>;body_intersect_vyska.shp VYSKA Mass_Points <None>;centroidy_vyska.shp VYSKA Mass_Points <None>;vodni_tok_3D.shp Shape.Z Hard_Line <None>"
        tin = arcpy.CreateTin_3d("TIN", sr, inFeatures, "constrained_delaunay")

    else:
        # neni vodni tok >> TVORBA TINu z 25 + 16 bodu
        print "Neni vodni tok"
        inFeatures = "body25_vyska.shp VYSKA Mass_Points <None>;centroidy_vyska.shp VYSKA Mass_Points <None>"
        tin = arcpy.CreateTin_3d("TIN", sr, inFeatures, "constrained_delaunay")

    # TVORBA VRSTEVNIC z TIN

    # verze 1. chci ukladat vygenerovane vrstevnice
    fullPath5 = str(os.path.join(FCDataset_HypsoVrstevnice, "c{0}_ziv5".format(ID)))
    hypso5 = arcpy.SurfaceContour_3d(tin, fullPath5, "5", "0")

    fullPath10 = str(os.path.join(FCDataset_HypsoVrstevnice, "c{0}_ziv10".format(ID)))
    hypso10 = arcpy.SurfaceContour_3d(tin, fullPath10, "10", "0")

    fullPath20 = str(os.path.join(FCDataset_HypsoVrstevnice, "c{0}_ziv20".format(ID)))
    hypso20 = arcpy.SurfaceContour_3d(tin, fullPath20, "20", "0")

    # # verze 2. nechci ukladat vsechny vygenerovane vrstevnice
    # hypso5 = arcpy.SurfaceContour_3d(tin, "ziv5.shp", "5", "0")
    # hypso10 = arcpy.SurfaceContour_3d(tin, "ziv10.shp", "10", "0")
    # hypso20 = arcpy.SurfaceContour_3d(tin, "ziv20.shp", "20", "0")

    # Pocet vrstevnic v celem uzemi 4x4 km
    hypso5_pocet = int(arcpy.GetCount_management(hypso5).getOutput(0))
    hypso10_pocet = int(arcpy.GetCount_management(hypso10).getOutput(0))
    hypso20_pocet = int(arcpy.GetCount_management(hypso20).getOutput(0))

    ZIV5 = [ID, hypso5_pocet]
    ZIV10 = [ID, hypso10_pocet]
    ZIV20 = [ID, hypso20_pocet]

    # Pocet vrstevnic v dilcich ctvercich 1x1 km
    mrizka_cursor = arcpy.SearchCursor(mrizka)

    for row in mrizka_cursor:
        shape = row.Shape
        hypso5_clip = arcpy.Clip_analysis(hypso5, shape, "hypso5_clip.shp", "")
        hypso5_dilci_pocet = int(arcpy.GetCount_management(hypso5_clip).getOutput(0))
        ZIV5.append(hypso5_dilci_pocet)

        hypso10_clip = arcpy.Clip_analysis(hypso10, shape, "hypso10_clip.shp", "")
        hypso10_dilci_pocet = int(arcpy.GetCount_management(hypso10_clip).getOutput(0))
        ZIV10.append(hypso10_dilci_pocet)

        hypso20_clip = arcpy.Clip_analysis(hypso20, shape, "hypso20_clip.shp", "")
        hypso20_dilci_pocet = int(arcpy.GetCount_management(hypso20_clip).getOutput(0))
        ZIV20.append(hypso20_dilci_pocet)

    del mrizka_cursor

    # ....................................................................................................
    # uklid
    arcpy.Delete_management(buffer_ctverec)
    arcpy.Delete_management(dmt)
    arcpy.Delete_management(tin)
    arcpy.Delete_management(centroidy)
    arcpy.Delete_management(centroidy_vyska)
    arcpy.Delete_management(body25)
    arcpy.Delete_management(body25_vyska)
    arcpy.Delete_management(zonal_min)
    arcpy.Delete_management(zonal_max)
    arcpy.Delete_management(mrizka)
    arcpy.Delete_management(mrizka_linie)
    arcpy.Delete_management(mrizka_uhlopricky)
    arcpy.Delete_management(uhlopricky)
    arcpy.Delete_management(start_vyska)
    arcpy.Delete_management(end_vyska)
    arcpy.Delete_management(start_point)
    arcpy.Delete_management(end_point)
    arcpy.Delete_management(hypso5_clip)
    arcpy.Delete_management(hypso10_clip)
    arcpy.Delete_management(hypso20_clip)
    arcpy.Delete_management(vrstevnice_clip)
    arcpy.Delete_management(koty_clip)
    arcpy.Delete_management(vodni_plocha_clip)
    arcpy.Delete_management(vodni_toky_clip)

    try:
        arcpy.Delete_management(body_intersect)
        arcpy.Delete_management(body_intersect_single)
        arcpy.Delete_management(body_intersect_single_vyska) # asi ulozit do databaze
        arcpy.Delete_management(vodni_tok3D)
        arcpy.Delete_management(vodni_tok_split)
        arcpy.Delete_management(vodni_tok_dissolve)

    except:
        pass

    # ....................................................................................................
    # VYSLEDEK = list listu
    result = [ZIV5, ZIV10, ZIV20]

    return result
# ------------------------------------------------------

# Funkce linearni interpolace, ktera uklada vysledne linie do databaze
def ulozeni_vrstevnic(ID, poradi, shape, workspace, data, FCDataset_VybranyVodniTok, FCDataset_HypsoVrstevnice, vhodny_ziv):

    sr = arcpy.SpatialReference(32633) # EPSG kod pro spatial reference

    # PRIPRAVA DAT PRO DANE UZEMI
    print "hypso"

    # Zajmova oblast okolo ctverce
    buffer_ctverec = arcpy.Buffer_analysis(shape, "buffer_ctverec.shp", config.buffer_ctverec_vzdalenost)
    print "buffer"

    # Vrstevnice pro zajmovou oblast
    vrstevnice_clip = arcpy.Clip_analysis((data + "dmu25_vrstevnice_ziv5m"), buffer_ctverec, "vrstevnice_clip.shp", "")

    # Kotovane body pro zajmovou oblast
    koty_clip = arcpy.Clip_analysis((data + "vektorizace_kotovane_body"), buffer_ctverec, "kotovane_body_clip.shp", "")

    # Vodni plochy pro zajmovou oblast
    vodni_plocha_clip = arcpy.Clip_analysis((data + "dmu25_vodni_plochy"), buffer_ctverec, "vodni_plocha_clip.shp", "")

    # Vodni toky pro zajmovou oblast
    vodni_toky_clip = arcpy.Clip_analysis((data + "dmu25_reka_potok"), buffer_ctverec, "vodni_toky_clip.shp", "")

    #....................................................................................................
    # OPRAVA SMERU VODNICH TOKU - podle Digitalniho modelu terenu (jen z vrstevnic)

    # Digitalni model terenu pouze z vrstevnic = slouzi k urceni vysky pocatku a konce vodniho toku
    inContours = "vrstevnice_clip.shp VYSKA Contour"
    outFeature = "dmt"
    ext_pro_dmt = arcpy.Describe(buffer_ctverec)
    extent = (str(ext_pro_dmt.extent.XMin) + " " + str(ext_pro_dmt.extent.YMin) + " " + str(
        ext_pro_dmt.extent.XMax) + " " + str(ext_pro_dmt.extent.YMax))
    dmt = arcpy.TopoToRaster_3d(inContours, outFeature, config.dmt_resolution, extent)

    # Pocatek a konec linie vodniho toku
    start_point = arcpy.FeatureVerticesToPoints_management(vodni_toky_clip, "start_point.shp", "START")
    end_point = arcpy.FeatureVerticesToPoints_management(vodni_toky_clip, "end_point.shp", "END")

    # Pro pocatek a konec linie vodniho toku zjistuji vysku z DMT
    start_vyska = arcpy.sa.ExtractValuesToPoints(start_point, dmt, "start_vyska.shp", "NONE", "VALUE_ONLY")
    end_vyska = arcpy.sa.ExtractValuesToPoints(end_point, dmt, "end_vyska.shp", "NONE", "VALUE_ONLY")

    cursor_reka = arcpy.da.UpdateCursor(vodni_toky_clip, "SHAPE@")
    cursor_start = arcpy.da.SearchCursor(start_vyska, "RASTERVALU")
    cursor_end = arcpy.da.SearchCursor(end_vyska, "RASTERVALU")

    # Hodnoty vysek pro pocatecni a koncove body linie vodnich toku
    start_value, end_value = [], []

    # Pro kazdy bod pridam hodnotu do pole vysek
    for row in cursor_start: start_value.append(row[0])
    for row in cursor_end: end_value.append(row[0])

    # Prochazim linie vodnich toku (i slouzi k dotazu na hodnotu vysek)
    i = 0
    for row in cursor_reka:

        # Pokud linie zacina v nizsi vysce nez konci
        if start_value[i] < end_value[i]:
            # Chci body, ze kterych je slozena linie
            vertices = []
            for part in row[0]:
                for pnt in part:
                    vertices.append(pnt)

            # Tvorim novou linii s otocenym poradim bodu
            row[0] = arcpy.Polyline(arcpy.Array(vertices[::-1]))

            # Aktualizuji dany usek linie
            cursor_reka.updateRow(row)

        i = i + 1

    del cursor_reka, cursor_end, cursor_start

    # Mazu prvni dmt
    arcpy.Delete_management(dmt)

    #....................................................................................................
    # HYDROLOGICKY SPRAVNY Digitalni model terenu

    # vstup do DMR (vrstevnice, koty, vodni plochy, vodni toky spravneho smeru)
    inContours = "vrstevnice_clip.shp VYSKA Contour"
    inPointElevations = "kotovane_body_clip.shp VYSKA PointElevation"
    inLake = "vodni_plocha_clip.shp # Lake"
    inStream = "vodni_toky_clip.shp # Stream"
    inFeatures = (inPointElevations + ";" + inContours + ";" + inLake + ";" + inStream)

    dmt = arcpy.TopoToRaster_3d(inFeatures, "dmt", config.dmt_resolution, extent)

    #....................................................................................................
    # TVORBA MRIZKY, ROHOVYCH BODU, CENTROIDU A ZJISTOVANI VYSKY

    # Zakladni ctvercova mrizka po 1 kilometru
    desc = shape
    XMin = desc.extent.XMin
    YMax = desc.extent.YMax
    mrizka = arcpy.CreateFishnet_management("mrizka_1km.shp", str(desc.extent.lowerLeft),
                                                str(XMin) + " " + str(YMax + 10), "1000", "1000",
                                                "0", "0", str(desc.extent.upperRight), "LABELS", "#", "POLYGON")

    # Rohove body mrizky = 25 bodu (+ vymazu identicke)
    body25 = arcpy.FeatureVerticesToPoints_management(mrizka, "body25.shp", "ALL")
    arcpy.DeleteIdentical_management(body25, "Shape", "", "0")
    arcpy.DeleteField_management(body25, "ORIG_FID")

    # Pro 25 rohovych bodu mrizky urci vysku a zaokrouhli
    body25_vyska = arcpy.sa.ExtractValuesToPoints(body25, dmt, "body25_vyska.shp", "NONE", "VALUE_ONLY")
    arcpy.AddField_management(body25_vyska, "VYSKA", "DOUBLE")
    arcpy.CalculateField_management(body25_vyska, "VYSKA", "round( !RASTERVALU! , 0)",
                                    "PYTHON")  # RASTERVALU = hodnota bez zaokrouhleni

    # Spocteni minima a maxima v dilcich ctvercich -> vyska centroidu = (MIN+MAX)/2
    zonal_min = arcpy.gp.ZonalStatistics_sa(mrizka, "FID", dmt, "dmt_min", "MINIMUM", "DATA")
    zonal_max = arcpy.gp.ZonalStatistics_sa(mrizka, "FID", dmt, "dmt_max", "MAXIMUM", "DATA")

    # Centroidy mrizky a jejich vyska
    centroidy = "mrizka_1km_label.shp"
    centroidy_min = arcpy.sa.ExtractValuesToPoints(centroidy, zonal_min, "centroidy_min.shp", "NONE", "VALUE_ONLY")

    # Zaokrouhli vysku a vymaz pole RASTERVALU
    arcpy.AddField_management(centroidy_min, "VYSKA_MIN", "DOUBLE")
    arcpy.CalculateField_management(centroidy_min, "VYSKA_MIN", "round( !RASTERVALU! , 0)", "PYTHON")
    arcpy.DeleteField_management(centroidy_min, "RASTERVALU")

    # MAX vyska (v poli RASTERVALU)
    centroidy_vyska = arcpy.sa.ExtractValuesToPoints(centroidy_min, zonal_max, "centroidy_vyska.shp", "NONE",
                                                     "VALUE_ONLY")

    # Zaokrouhli vysku a vymaz pole RASTERVALU
    arcpy.AddField_management(centroidy_vyska, "VYSKA_MAX", "DOUBLE")
    arcpy.CalculateField_management(centroidy_vyska, "VYSKA_MAX", "round( !RASTERVALU! , 0)", "PYTHON")
    arcpy.DeleteField_management(centroidy_vyska, "RASTERVALU")

    # Spocti hodnotu centroidu
    arcpy.AddField_management(centroidy_vyska, "VYSKA", "DOUBLE")
    arcpy.CalculateField_management(centroidy_vyska, "VYSKA", "round(((!VYSKA_MIN! + !VYSKA_MAX!)/2) , 0)", "PYTHON")

    # ....................................................................................................
    # TVORBA UHLOPRICEK
    arcpy.Delete_management("uhlopricky.shp")
    uhlopricky = arcpy.CreateFeatureclass_management(config.workspace, "uhlopricky.shp", "POLYLINE", "#", "#", "#", sr)
    # Pridame atribut (VALUE <= ID)
    arcpy.AddField_management(uhlopricky, "VALUE", "SHORT")

    # Kurzor pro vkladani
    insCur = arcpy.da.InsertCursor(uhlopricky, ["SHAPE@", "VALUE"])

    # Souradnice stredu mrizky
    x = XMin + 2000
    y = YMax - 2000

    # Spojnice pro linie mrizky (ID, x1, y1, x2, y2)
    k1 = 1000
    k2 = 2000
    body = [[1, x - k2, y + k2, x + k2, y - k2],
            [2, x - k1, y + k2, x + k2, y - k1],
            [3, x, y + k2, x + k2, y],
            [4, x + k1, y + k2, x + k2, y + k1],
            [5, x - k2, y + k1, x + k1, y - k2],
            [6, x - k2, y, x, y - k2],
            [7, x - k2, y - k1, x - k1, y - k2],
            [8, x - k2, y + k1, x - k1, y + k2],
            [9, x, y + k2, x - k2, y],
            [10, x + k1, y + k2, x - k2, y - k1],
            [11, x + k2, y + k2, x - k2, y - k2],
            [12, x + k2, y + k1, x - k1, y - k2],
            [13, x + k2, y, x, y - k2],
            [14, x + k2, y - k1, x + k1, y - k2]]

    # Zacneme tvorit vystup
    geom = arcpy.Array()

    for i in body:
        value = i[0]
        part = arcpy.Array()
        part.add(arcpy.Point(i[1], i[2]))
        part.add(arcpy.Point(i[3], i[4]))
        # Pridam cast do pole geometrie
        geom.add(part)

        # Vytvorim polylini z pole geometrii
        insCur.insertRow((arcpy.Polyline(geom), value))

    del insCur

    # Obrysova linie mrizky
    mrizka_linie = arcpy.PolygonToLine_management(mrizka, "mrizka_linie.shp")

    # Spojeni mrizky a uhlopricek
    input = "mrizka_linie.shp;uhlopricky.shp"
    mrizka_uhlopricky = arcpy.Merge_management(input, "mrizka_uhlopricky.shp", "")

    # ....................................................................................................
    # NACTENI VODNIHO TOKU
    # Existuje-li vodni tok, ktery deli uzemi na 2 casti
    fullPath_VybranyVodniTok = os.path.join(FCDataset_VybranyVodniTok,
                                                "v{0}_vodni_tok".format(poradi))

    if arcpy.Exists(fullPath_VybranyVodniTok):
        print "tok nacten"
        # ....................................................................................................
        # PRUSECIKY VYBRANEHO VODNIHO TOKU A MRIZKY A UHLOPRICEK
        in_features = fullPath_VybranyVodniTok + ";" + "mrizka_uhlopricky.shp"
        body_intersect = arcpy.Intersect_analysis(in_features, "intersect.shp", "ONLY_FID", "-1 Unknown", "POINT")
        arcpy.DeleteIdentical_management(body_intersect, "Shape", "", "0")      # mazu identicke body
        body_intersect_single = arcpy.MultipartToSinglepart_management(body_intersect, "body_intersect_single.shp")

        # ....................................................................................................
        # VYTVORENI 3D hrany pro TIN
        # Vybrany vodni tok se spoji (dissolve) a rozdeli podle pruseciku s mrizkou (split line)
        vodni_tok_dissolve = arcpy.Dissolve_management(fullPath_VybranyVodniTok, "vodni_tok_dissolve", "", "", "SINGLE_PART", "DISSOLVE_LINES")
        vodni_tok_split = arcpy.SplitLineAtPoint_management(vodni_tok_dissolve, body_intersect_single, "vodni_tok_split.shp", "50 Meters")

        arcpy.AddField_management(vodni_tok_split, "POCATEK", "DOUBLE")
        arcpy.AddField_management(vodni_tok_split, "KONEC", "DOUBLE")

        # vytvor start a end pointy
        arcpy.Delete_management("start_point.shp")
        start_point = arcpy.FeatureVerticesToPoints_management(vodni_tok_split, "start_point.shp", "START")
        start_vyska = arcpy.sa.ExtractValuesToPoints(start_point, dmt, "start_vyska.shp", "NONE", "VALUE_ONLY")

        arcpy.Delete_management("end_point.shp")
        end_point = arcpy.FeatureVerticesToPoints_management(vodni_tok_split, "end_point.shp", "END")
        end_vyska = arcpy.sa.ExtractValuesToPoints(end_point, dmt, "end_vyska.shp", "NONE", "VALUE_ONLY")

        cursor_start = arcpy.da.SearchCursor(start_vyska, "RASTERVALU")
        cursor_end = arcpy.da.SearchCursor(end_vyska, "RASTERVALU")

        # Z vysek budu tvorit pole hodnot
        start_value, end_value = [], []

        # Pro kazdy bod pridam hodnotu do pole vysek
        for row in cursor_start: start_value.append(row[0])
        for row in cursor_end: end_value.append(row[0])
        del cursor_end, cursor_start

        # Prochazim linie vodnich toku (i slouzi k dotazu na hodnotu vysek)
        i = 0
        with arcpy.da.UpdateCursor(vodni_tok_split, ["SHAPE@", "POCATEK", "KONEC"]) as cursor:
            for row in cursor:
                row[1] = start_value[i]
                row[2] = end_value[i]
                cursor.updateRow(row)
                i = i + 1

        vodni_tok3D = arcpy.FeatureTo3DByAttribute_3d(vodni_tok_split, "vodni_tok_3D.shp", "POCATEK", "KONEC")

        # ....................................................................................................
        # VYMAZAT Centroidy pokud je v blizkosti PRUSECIK S REKOU (ten ma prioritu)
        inFeatures = centroidy_vyska
        tempLayer = "centroidy_vyska.lyr"
        selectFeatures = "body_intersect_single.shp"
        arcpy.MakeFeatureLayer_management(inFeatures, tempLayer)

        arcpy.SelectLayerByLocation_management(tempLayer, "WITHIN_A_DISTANCE", selectFeatures, config.centroid_tolerance, "NEW_SELECTION", "NOT_INVERT")
        arcpy.DeleteFeatures_management(tempLayer)

        # ....................................................................................................
        # PRO PRUSECIKY REKY A MRIZKY ODECITAM Z VYSKU Z DEM
        body_intersect_single_vyska = arcpy.sa.ExtractValuesToPoints(body_intersect_single, dmt, "body_intersect_vyska.shp", "NONE", "VALUE_ONLY")
        arcpy.AddField_management(body_intersect_single_vyska, "VYSKA", "DOUBLE")
        arcpy.CalculateField_management(body_intersect_single_vyska, "VYSKA", "round( !RASTERVALU! , 0)", "PYTHON") # RASTERVALU = hodnota bez zaokrouhleni

        # ....................................................................................................
        # TVORBA TINu z 25 + 16 + X bodu
        inFeatures = "body25_vyska.shp VYSKA Mass_Points <None>;body_intersect_vyska.shp VYSKA Mass_Points <None>;centroidy_vyska.shp VYSKA Mass_Points <None>;vodni_tok_3D.shp Shape.Z Hard_Line <None>"
        tin = arcpy.CreateTin_3d("TIN", sr, inFeatures, "constrained_delaunay")

    else:
        # neni vodni tok >> TVORBA TINu z 25 + 16 bodu
        print "Neni vodni tok"
        inFeatures = "body25_vyska.shp VYSKA Mass_Points <None>;centroidy_vyska.shp VYSKA Mass_Points <None>"
        tin = arcpy.CreateTin_3d("TIN", sr, inFeatures, "constrained_delaunay")

    # TVORBA VRSTEVNIC z TIN

    # verze 1. chci ukladat vygenerovane vrstevnice
    # zmenit cisla, když je poradi menši než 10, př. 002 a menší než 100, př. 089
    if ID < 10:
        poradi = "00" + str(poradi)
    elif ID < 100:
        poradi = "0" + str(poradi)
    else:
        poradi = poradi

    fullPath = str(os.path.join(FCDataset_HypsoVrstevnice, "c{}_hypso_ziv{}".format(poradi, vhodny_ziv)))
    hypso = arcpy.SurfaceContour_3d(tin, fullPath, "{0}".format(vhodny_ziv), "0")


    # ....................................................................................................
    # uklid
    arcpy.Delete_management(buffer_ctverec)
    arcpy.Delete_management(dmt)
    arcpy.Delete_management(tin)
    arcpy.Delete_management(centroidy)
    arcpy.Delete_management(centroidy_vyska)
    arcpy.Delete_management(body25)
    arcpy.Delete_management(body25_vyska)
    arcpy.Delete_management(zonal_min)
    arcpy.Delete_management(zonal_max)
    arcpy.Delete_management(mrizka)
    arcpy.Delete_management(mrizka_linie)
    arcpy.Delete_management(mrizka_uhlopricky)
    arcpy.Delete_management(uhlopricky)
    arcpy.Delete_management(start_vyska)
    arcpy.Delete_management(end_vyska)
    arcpy.Delete_management(start_point)
    arcpy.Delete_management(end_point)
    #arcpy.Delete_management(hypso)
    arcpy.Delete_management(vrstevnice_clip)
    arcpy.Delete_management(koty_clip)
    arcpy.Delete_management(vodni_plocha_clip)
    arcpy.Delete_management(vodni_toky_clip)

    try:
        arcpy.Delete_management(body_intersect)
        arcpy.Delete_management(body_intersect_single)
        arcpy.Delete_management(body_intersect_single_vyska) # asi ulozit do databaze
        arcpy.Delete_management(vodni_tok3D)
        arcpy.Delete_management(vodni_tok_split)
        arcpy.Delete_management(vodni_tok_dissolve)

    except:
        pass

    # ....................................................................................................
    # VYSLEDEK = list listu
    result = 1

    return result
# ------------------------------------------------------