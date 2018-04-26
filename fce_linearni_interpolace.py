# Nazev:            fce_linearni_interpolace.py
# Autor:            Karolina Fenclova
# Popis:            Skript na vypocet linearni interpolace u mapy hypsometrie. vystupem pocet vrstevnic v dilcich ctvercich

# VSTUP: fce_linearni_interpolace(ctverec, ID, workspace, data, povodi)
#     ctverec = uzemi 4x4 km
#     ID = ID ctverce
#     workspace = adresar pro ukladani mezivysledku, ktere se budou mazat
#     data = cesta k datum dmu25, vlastni vektorizaci atd.
#     povodi = cesta k datum o vode

# VYSTUP: result = [ZIV5, ZIV10, ZIV20]
#    pro kazdy interval ZIV je zapsano: id, pocet_vrstevnic, vzniklych linearni interpolaci a 16krat pocet vrstevnic v dilcich ctvercich

import arcpy, config, os

arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")
arcpy.env.overwriteOutput = True

# Funkce linearni interpolace
def fce_linearni_interpolace(ID, shape, workspace, data, FCDataset_VybranyVodniTok, FCDataset_HypsoVrstevnice):

    sr = arcpy.SpatialReference(32633) # EPSG kod pro spatial reference

    # ....................................................................................................
    # PRIPRAVA DAT PRO DANE UZEMI
    print "Pripravuji data..."

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
    print "Tvorim DMT jen z vrstevnic..."
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
            print "linie byla otocena"

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

    print "Tvorim hydrologicky spravne DMT..."
    dmt = arcpy.TopoToRaster_3d(inFeatures, "dmt", config.dmt_resolution, extent)

    #....................................................................................................
    # TVORBA MRIZKY, ROHOVYCH BODU, CENTROIDU A ZJISTOVANI VYSKY

    # Zakladni ctvercova mrizka po 1 kilometru
    print "Tvorim mrizku a rohove body..."
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

    # Pro rohove body mrizky urcuji vysku
    print "Pro 25 rohovych bodu mrizky odecitam vysku a zaokrouhluji..."
    body25_vyska = arcpy.sa.ExtractValuesToPoints(body25, dmt, "body25_vyska.shp", "NONE", "VALUE_ONLY")
    arcpy.AddField_management(body25_vyska, "VYSKA", "DOUBLE")
    arcpy.CalculateField_management(body25_vyska, "VYSKA", "round( !RASTERVALU! , 0)",
                                    "PYTHON")  # RASTERVALU = hodnota bez zaokrouhleni

    # Spocteni minima a maxima v dilcich ctvercich -> vyska centroidu = (MIN+MAX)/2
    print "pocitam rozsah pro centralni body mrizky..."
    zonal_min = arcpy.gp.ZonalStatistics_sa(mrizka, "FID", dmt, "dmt_min", "MINIMUM", "DATA")
    zonal_max = arcpy.gp.ZonalStatistics_sa(mrizka, "FID", dmt, "dmt_max", "MAXIMUM", "DATA")
    zonal_vypocet = (arcpy.sa.CellStatistics([zonal_min, zonal_max], "SUM", "DATA")) / 2
# !!!!! potreba zaokrouhlit MIN a MAX pred prumerovanm (zaokrouhlit pred i po prumerovani)

    # Centroidy mrizky a jejich vyska
    centroidy = "mrizka_1km_label.shp"
    centroidy_vyska = arcpy.sa.ExtractValuesToPoints(centroidy, zonal_vypocet, "centroidy_vyska.shp", "NONE", "VALUE_ONLY")

    # Zaokrouhli vysku
    arcpy.AddField_management(centroidy_vyska, "VYSKA", "DOUBLE")
    arcpy.CalculateField_management(centroidy_vyska, "VYSKA", "round( !RASTERVALU! , 0)", "PYTHON")

    # ....................................................................................................
    # TVORBA UHLOPRICEK

    print "tvorim uhlopricky pro mrizku..."
    uhlopricky = arcpy.CreateFeatureclass_management(arcpy.env.workspace, "uhlopricky.shp", "POLYLINE", "#", "#", "#", sr)
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

    # # ....................................................................................................
    # # VYBER 1 VODNI TOK, KTERY PROTINA CELE UZEMI A DELI HO NA 2 PRIBLIZNE SHODNE CASTI
    #
    # print "vybiram 1 vodni tok..."
    #
    # buffer_vodni_toky = arcpy.Buffer_analysis(vodni_toky_clip, "buffer_vodni_toky.shp", config.buffer_vodni_toky,
    #                                           "FULL",
    #                                           "ROUND", "ALL")
    # buffer_vodni_plochy = arcpy.Buffer_analysis(vodni_plocha_clip, "buffer_vodni_plochy.shp",
    #                                             config.buffer_vodni_plochy, "FULL",
    #                                             "ROUND", "ALL")
    #
    # # Spoj obalove zony reky a vodni plochy
    # inMerge = "buffer_vodni_toky.shp;buffer_vodni_plochy.shp"
    # buffer_voda = arcpy.Merge_management(inMerge, "buffer_voda.shp", "")
    # buffer_voda_dissolve = arcpy.Dissolve_management(buffer_voda, "buffer_voda_dissolve.shp", "", "", "SINGLE_PART",
    #                                                  "DISSOLVE_LINES")
    #
    # # DIBAVOD (A02 vodni toky jemne useky) pro zajmovou oblast (ctverec)
    # print "orezavam DIBAVOD..."
    # dibA02 = data + "dibavod_VodniTokyA02"
    # dibA02_clip = arcpy.Clip_analysis(dibA02, shape, "dibA02_clip.shp", "")
    #
    # # VYBER a VYMAZ useky DIBAVOD, pokud linie nelezi uvnitr obalove zony
    # print "vybiram data DIBAVOD within Buffer vody..."
    # inFeatures = dibA02_clip
    # tempLayer = "dibA02_clip.lyr"
    # selectFeatures = buffer_voda
    # arcpy.MakeFeatureLayer_management(inFeatures, tempLayer)
    # arcpy.SelectLayerByLocation_management(tempLayer, "WITHIN", selectFeatures, selection_type="NEW_SELECTION",
    #                                        invert_spatial_relationship="INVERT")
    # arcpy.DeleteFeatures_management(tempLayer)
    #
    # # ....................................................................................................
    # print "creating database, dataset, network..."
    # # Create database
    # if not arcpy.Exists("RiverNetwork.gdb"): RiverDatabase = arcpy.CreateFileGDB_management(out_folder_path=workspace, out_name="RiverNetwork", out_version="CURRENT")
    # else: RiverDatabase = "RiverNetwork.gdb"
    #
    # # Create feature dataset
    # arcpy.Delete_management(os.path.join(RiverDatabase, "NetworkDataset"))
    # NetworkDataset = arcpy.CreateFeatureDataset_management(RiverDatabase, "NetworkDataset", sr)
    #
    # # Save selected DIBAVOD to Feature dataset
    # edges = arcpy.FeatureClassToFeatureClass_conversion(dibA02_clip, NetworkDataset, "edges")
    #
    # # Create geometric network
    # network = arcpy.CreateGeometricNetwork_management(NetworkDataset, "network", "edges SIMPLE_EDGE NO",
    #                                                   preserve_enabled_values="PRESERVE_ENABLED")
    #
    # # ....................................................................................................
    # # SELECT START AND ENDPOINTS
    # # create polygon boundary
    # obrys = arcpy.PolygonToLine_management(shape, "obrys")
    #
    # # create start points
    # print "creating start points..."
    # start_points = arcpy.FeatureVerticesToPoints_management(edges, "start_points", "START")
    #
    # tempLayer = "start_points.lyr"
    # arcpy.MakeFeatureLayer_management(start_points, tempLayer)
    #
    # # select and delete all start points not closer than tolerance from polygon boundary
    # arcpy.SelectLayerByLocation_management(tempLayer, "INTERSECT", obrys, "", "NEW_SELECTION", "INVERT")
    # arcpy.DeleteFeatures_management(tempLayer)
    #
    # # create end points
    # print "creating end points..."
    # end_points = arcpy.FeatureVerticesToPoints_management(edges, "end_points", "END")
    #
    # tempLayer = "end_points.lyr"
    # arcpy.MakeFeatureLayer_management(end_points, tempLayer)
    #
    # # select and delete all end points not closer than tolerance from polygon boundary
    # #arcpy.SelectLayerByLocation_management(tempLayer, "WITHIN_A_DISTANCE", obrys, config.tolerance_end,
    # #                                       "NEW_SELECTION", "INVERT")
    # arcpy.SelectLayerByLocation_management(tempLayer, "INTERSECT", obrys, "", "NEW_SELECTION", "INVERT")
    # arcpy.DeleteFeatures_management(tempLayer)
    #
    # # ....................................................................................................
    # # create all combination for start and end points
    # flags = arcpy.CreateFeatureclass_management(NetworkDataset, "flags", "POINT", spatial_reference=sr)
    #
    # # local variable for selecting the most appropriate path
    # deviation = []  # to store deviation from the "ideal" division (== 1.0)
    # i = 0
    #
    # # all end points
    # with arcpy.da.SearchCursor(end_points, "SHAPE@") as curEnd:
    #     for e in curEnd:
    #         inGeomEnd = e[0]
    #         partEnd = inGeomEnd.getPart(0)
    #
    #         # all start points
    #         curStart = arcpy.da.SearchCursor(start_points, "SHAPE@")
    #         for s in curStart:
    #             inGeomStart = s[0]
    #             partStart = inGeomStart.getPart(0)
    #             print partEnd, partStart
    #
    #             # flags = 2 points
    #             print "creating flags..."
    #             arcpy.DeleteFeatures_management(flags)
    #             insCur = arcpy.da.InsertCursor(flags, "SHAPE@")
    #             insCur.insertRow(inGeomEnd)
    #             insCur.insertRow(inGeomStart)
    #             del insCur
    #
    #             # Trace Geometric Network function == selected edges and junctions
    #             print "finding path..."
    #             arcpy.TraceGeometricNetwork_management(network, "result_set", flags, "FIND_PATH",
    #                                                    in_trace_ends="NO_TRACE_ENDS",
    #                                                    in_trace_indeterminate_flow="NO_TRACE_INDETERMINATE_FLOW")
    #
    #             # Create a Mapping Layer out of the Group Layer
    #             groupLayer = arcpy.mapping.Layer("result_set")
    #
    #             # Get a list of all the mappping layers, the first return will be the Group Layer itself
    #             newLyrs = arcpy.mapping.ListLayers(groupLayer)
    #
    #             # EXPORT selected EDGES (dibA02_clip v databazi)
    #             selected_path = arcpy.CopyFeatures_management(newLyrs[2], "selected_path.shp")
    #
    #             # Feature to Polygon
    #             print "dividing polygons with selected paths..."
    #
    #             in_features = "selected_path.shp; obrys.shp"
    #             dvojice = arcpy.FeatureToPolygon_management(in_features, "FeatureToPolygon.shp", config.tolerance_FeatureToPolygon,
    #                                                         "NO_ATTRIBUTES", "")
    #             area = []
    #
    #             # spocti plochu pro 2 dily
    #             with arcpy.da.SearchCursor(dvojice, ['OID@', 'SHAPE@AREA']) as cursor:
    #                 for row in cursor:
    #                     area.append(row[1])
    #                     print('Feature {} has an area of {}'.format(row[0], row[1]))
    #             del cursor
    #
    #             # if a polygon divided into 2 parts
    #             if len(area) == 2:
    #                 podil_ploch = max(area) / min(area)
    #                 print "-- Podil ploch = {}".format(podil_ploch)
    #                 deviation.append(podil_ploch - 1)
    #                 print "Deviation = {}".format(podil_ploch - 1)
    #
    #                 if i == 0:
    #                     # first selection of river
    #                     selected_path_dissolve = arcpy.Dissolve_management(selected_path, "selected_path_dissolve.shp",
    #                                                                        "", "", "SINGLE_PART", "DISSOLVE_LINES")
    #                     fullPath_VybranyVodniTok = os.path.join(FCDataset_VybranyVodniTok,
    #                                                             "vybrany_vodni_tok_{0}".format(ID))
    #                     arcpy.CopyFeatures_management(selected_path_dissolve,
    #                                                                       fullPath_VybranyVodniTok)
    #                     nejlepsi_podil_ploch = podil_ploch
    #                     print "Prvni vyber vodniho toku."
    #
    #                 else:
    #                     print "Minimum deviation = {}".format(min(deviation))
    #
    #                     # select if deviation is smaller
    #                     if (podil_ploch - 1) <= min(deviation):
    #                         selected_path_dissolve = arcpy.Dissolve_management(selected_path,
    #                                                                            "selected_path_dissolve.shp", "", "",
    #                                                                            "SINGLE_PART", "DISSOLVE_LINES")
    #                         fullPath_VybranyVodniTok = os.path.join(FCDataset_VybranyVodniTok,
    #                                                                 "vybrany_vodni_tok_{0}".format(ID))
    #                         arcpy.CopyFeatures_management(selected_path_dissolve,
    #                                                                           fullPath_VybranyVodniTok)
    #                         nejlepsi_podil_ploch = podil_ploch
    #                         print "Vybrano jako vodni tok."
    #
    #                     else:
    #                         print "Odchylka neni mensi nez doposud minimalni."
    #
    #                 i = +1
    #
    #             else:
    #                 print "Nelze vybrat vodni tok a delit plochu."
    #
    #         del curStart
    # del curEnd
    #
    # print "Odchylky od 1 u VSECH moznych dvojic ploch = {}".format(deviation)
    #
    # try:
    #     arcpy.Delete_management(buffer_voda)
    #     arcpy.Delete_management(buffer_vodni_plochy)
    #     arcpy.Delete_management(buffer_vodni_toky)
    #     arcpy.Delete_management(buffer_voda_dissolve)
    #     arcpy.Delete_management(dibA02_clip)
    #     arcpy.Delete_management(start_points)
    #     arcpy.Delete_management(end_points)
    #     arcpy.Delete_management(flags)
    #     arcpy.Delete_management(obrys)
    #     arcpy.Delete_management(selected_path)
    #     arcpy.Delete_management(selected_path_dissolve)
    #     arcpy.Delete_management(dvojice)
    #     arcpy.Delete_management(RiverDatabase)
    # except:
    #     print "Neco nelze smazat :-)"

    # Existuje vodni tok, ktery deli uzemi na 2 casti
    fullPath_VybranyVodniTok = os.path.join(FCDataset_VybranyVodniTok,
                                            "v{0}_vodni_tok".format(ID))

    if arcpy.Exists(fullPath_VybranyVodniTok):
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

        print "tvorim start a end pointy..."
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

        print "mazu centroidy, pokud jsou v tesne blizkosti pruseciky s rekou..."
        inFeatures = centroidy_vyska        # vybiram a mazu
        tempLayer = "centroidy_vyska.lyr"
        selectFeatures = "body_intersect_single.shp"
        arcpy.MakeFeatureLayer_management(inFeatures, tempLayer)

        arcpy.SelectLayerByLocation_management(tempLayer, "WITHIN_A_DISTANCE", selectFeatures, config.centroid_tolerance, "NEW_SELECTION", "NOT_INVERT")
        arcpy.DeleteFeatures_management(tempLayer)

        # ....................................................................................................
        # PRO PRUSECIKY REKY A MRIZKY ODECITAM Z VYSKU Z DEM
        print "pro X pruseciku reky a mrizky odecitam vysku a zaokrouhluji..."
        body_intersect_single_vyska = arcpy.sa.ExtractValuesToPoints(body_intersect_single, dmt, "body_intersect_vyska.shp", "NONE", "VALUE_ONLY")
        arcpy.AddField_management(body_intersect_single_vyska, "VYSKA", "DOUBLE")
        arcpy.CalculateField_management(body_intersect_single_vyska, "VYSKA", "round( !RASTERVALU! , 0)", "PYTHON") # RASTERVALU = hodnota bez zaokrouhleni

        # ....................................................................................................
        # TVORBA TINu z 25 + 16 + X bodu
        print "tvorim TIN z 25 + 16 + X bodu..."
        inFeatures = "body25_vyska.shp VYSKA Mass_Points <None>;body_intersect_vyska.shp VYSKA Mass_Points <None>;centroidy_vyska.shp VYSKA Mass_Points <None>;vodni_tok_3D.shp Shape.Z Hard_Line <None>"
        tin = arcpy.CreateTin_3d("TIN", sr, inFeatures, "constrained_delaunay")

    else:
        # TVORBA TINu z 25 + 16 bodu
        print "Neni vodni tok, tvorim TIN jen z 25 + 16 bodu..."
        inFeatures = "body25_vyska.shp VYSKA Mass_Points <None>;centroidy_vyska.shp VYSKA Mass_Points <None>"
        tin = arcpy.CreateTin_3d("TIN", sr, inFeatures, "constrained_delaunay")

    # TVORBA VRSTEVNIC z TIN
    print "Generuji vrstevnice..."

    fullPath5 = os.path.join(FCDataset_HypsoVrstevnice, "c{0}_ziv5".format(ID))
    hypso5 = arcpy.SurfaceContour_3d(tin, fullPath5, "5", "0")

    fullPath10 = os.path.join(FCDataset_HypsoVrstevnice, "c{0}_ziv10".format(ID))
    hypso10 = arcpy.SurfaceContour_3d(tin, fullPath10, "10", "0")

    fullPath20 = os.path.join(FCDataset_HypsoVrstevnice, "c{0}_ziv20".format(ID))
    hypso20 = arcpy.SurfaceContour_3d(tin, fullPath20, "20", "0")

    # Pocet vrstevnic v celem uzemi 4x4 km
    hypso5_pocet = int(arcpy.GetCount_management(hypso5).getOutput(0))
    hypso10_pocet = int(arcpy.GetCount_management(hypso10).getOutput(0))
    hypso20_pocet = int(arcpy.GetCount_management(hypso20).getOutput(0))

    print "Zadani cislo: {0}, ZIV 5 m = {1} vrstevnic, ZIV 10 m = {2} vrstevnic, ZIV 20 m = {3} vrstevnic.".format(
        ID, hypso5_pocet, hypso10_pocet, hypso20_pocet)

    ZIV5 = [ID, hypso5_pocet]
    ZIV10 = [ID, hypso10_pocet]
    ZIV20 = [ID, hypso20_pocet]

    # Pocet vrstevnic v dilcich ctvercich 1x1 km
    print "pocitam vrstevnice v dilcich ctvercich..."
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
    print "uklizim po sobe..."
    arcpy.Delete_management(buffer_ctverec)
    arcpy.Delete_management(dmt)
    arcpy.Delete_management(tin)
    arcpy.Delete_management(centroidy)
    arcpy.Delete_management(centroidy_vyska)    # asi ulozeit do databaze
    arcpy.Delete_management(body25)
    arcpy.Delete_management(body25_vyska)       # asi ulozit do databaze
    arcpy.Delete_management(zonal_min)
    arcpy.Delete_management(zonal_max)
    arcpy.Delete_management(zonal_vypocet)
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
        print "Uklizeno."

    # ....................................................................................................
    # VYSLEDEK = list listu
    result = [ZIV5, ZIV10, ZIV20]

    print "konec funkce linearni interpolace"

    return result
# ------------------------------------------------------