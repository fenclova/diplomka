# -*- coding: utf-8 -*-

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


# Funkce vypocte zakladni kriteria predvyberu
def zakladni_kriteria(ID, shape, workspace, data):
    sr = arcpy.SpatialReference(32633)  # EPSG kod pro spatial reference

    # PRIPRAVA DAT PRO DANE UZEMI
    print "data.."

    # Zeleznice pro CTVEREC
    zeleznice_clip = arcpy.Clip_analysis((data + "dmu25_drazni_komunikace"), shape, "zeleznice_clip.shp", "")

    # Vrstevnice pro zajmovou oblast
    vrstevnice_clip = arcpy.Clip_analysis((data + "dmu25_vrstevnice_ziv5m"), shape, "vrstevnice_clip.shp", "")

    # Rozvodnice DIBAVOD A08 pro zajmovou oblast
    rozvodnice_clip = arcpy.Clip_analysis((data + "dibavod_Povodi_III_A08"), shape, "rozvodnice_clip.shp", "")

    # Vodni plochy pro CTVEREC
    vodni_plocha_clip = arcpy.Clip_analysis((data + "dmu25_vodni_plochy"), shape, "vodni_plocha_clip.shp", "")

    # Vodni plochy pro CTVEREC
    vodni_nadrz_clip = arcpy.Clip_analysis((data + "dmu25_vodni_plocha_nadrz"), shape, "vodni_nadrz_clip.shp", "")

    # Vodni toky pro CTVEREC
    dibA02_clip = arcpy.Clip_analysis((data + "dibavod_VodniTokyA02_rady"), shape, "A02_clip.shp", "")

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

    # Delka vrstevnic
    arcpy.AddGeometryAttributes_management(vrstevnice_clip, "LENGTH", "METERS")
    g = arcpy.Geometry()
    geometryList = arcpy.CopyFeatures_management(vrstevnice_clip, g)
    vrstevnice_delka = 0
    for geometry in geometryList:
        vrstevnice_delka += geometry.length

    # Délka rozvodnice 3. radu (podle dibavod)
    arcpy.AddGeometryAttributes_management(rozvodnice_clip, "LENGTH", "METERS")
    g = arcpy.Geometry()
    geometryList = arcpy.CopyFeatures_management(rozvodnice_clip, g)
    rozvodniceIII_delka = 0
    for geometry in geometryList:
        rozvodniceIII_delka += geometry.length

    # Rozloha vodni plochy
    arcpy.AddGeometryAttributes_management(vodni_plocha_clip, "AREA")
    g = arcpy.Geometry()
    geometryList = arcpy.CopyFeatures_management(vodni_plocha_clip, g)
    vodni_plohy_rozloha = 0
    for geometry in geometryList:
        vodni_plohy_rozloha += geometry.area

    # Rozloha vodních nádrží
    arcpy.AddGeometryAttributes_management(vodni_nadrz_clip, "AREA")
    g = arcpy.Geometry()
    geometryList = arcpy.CopyFeatures_management(vodni_nadrz_clip, g)
    vodni_nadrz_rozloha = 0
    for geometry in geometryList:
        vodni_nadrz_rozloha += geometry.area

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
                   round(vrstevnice_delka, 2),
                   round(rozvodniceIII_delka, 2),
                   round(vodni_plohy_rozloha, 2),
                   round(vodni_nadrz_rozloha, 2),
                   round(dibA02_delka, 2),
                   round(relief_rozloha, 2),
                   round(zastavba_rozloha, 2)]

    # ....................................................................................................
    # UKLID
    arcpy.Delete_management(zeleznice_clip)
    arcpy.Delete_management(vrstevnice_clip)
    arcpy.Delete_management(rozvodnice_clip)
    arcpy.Delete_management(vodni_plocha_clip)
    arcpy.Delete_management(vodni_nadrz_clip)
    arcpy.Delete_management(dibA02_clip)
    arcpy.Delete_management(relief_clip)
    arcpy.Delete_management(zastavba_clip)

    return result_info

# Funkce na vyber hlavniho toku, ktery deli uzemi v nejlepsim pomeru ploch
def vyber_vodni_tok(ID, shape, workspace, data, FCDataset_VybranyVodniTok):

    sr = arcpy.SpatialReference(32633)  # EPSG kod pro spatial reference

    # ....................................................................................................
    # PRIPRAVA DAT PRO DANE UZEMI

    # Vrstevnice pro zajmovou oblast
    vrstevnice_clip = arcpy.Clip_analysis((data + "dmu25_vrstevnice_ziv5m"), shape, "vrstevnice_clip.shp", "")

    # Vodni plochy pro CTVEREC
    vodni_plocha_clip = arcpy.Clip_analysis((data + "dmu25_vodni_plochy"), shape, "vodni_plocha_clip.shp", "")

    # Vodni toky pro CTVEREC
    vodni_toky_clip = arcpy.Clip_analysis((data + "dmu25_reka_potok"), shape, "vodni_toky_clip.shp", "")


    # ....................................................................................................
    # TVORBA MRIZKY a UHLOPRICEK

    # Zakladni ctvercova mrizka po 1 kilometru
    desc = shape
    XMin = desc.extent.XMin
    YMax = desc.extent.YMax
    mrizka = arcpy.CreateFishnet_management("mrizka_1km.shp", str(desc.extent.lowerLeft),
                                            str(XMin) + " " + str(YMax + 10), "1000", "1000",
                                            "0", "0", str(desc.extent.upperRight), "LABELS", "#", "POLYGON")
    centroidy = "mrizka_1km_label.shp"

    # vytvor soubor pro uhlopricky v dane mrizce
    uhlopricky = arcpy.CreateFeatureclass_management(workspace, "uhlopricky.shp", "POLYLINE", "#", "#", "#", sr)

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
    # VYBER 1 VODNI TOK, KTERY PROTINA CELE UZEMI A DELI HO NA 2 PRIBLIZNE SHODNE CASTI
    print "Vybiram vodni tok..."

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
    # spojeny buffer orizni podle ctverce
    # buffer_voda_dissolve_clip = arcpy.Clip_analysis(buffer_voda_dissolve, shape, "buffer.shp")


    # DIBAVOD (A02 vodni toky jemne useky) pro zajmovou oblast (ctverec)
    dibA02_clip = arcpy.Clip_analysis((data + "dibavod_VodniTokyA02"), shape, "dibA02_clip.shp", "")

    # VYBER a VYMAZ useky DIBAVOD, pokud linie nelezi uvnitr obalove zony
    inFeatures = dibA02_clip
    tempLayer = "dibA02_clip.lyr"
    selectFeatures = buffer_voda_dissolve
    arcpy.MakeFeatureLayer_management(inFeatures, tempLayer)
    arcpy.SelectLayerByLocation_management(tempLayer, "WITHIN", selectFeatures, selection_type="NEW_SELECTION",
                                           invert_spatial_relationship="INVERT")
    arcpy.DeleteFeatures_management(tempLayer)


    # Vytvor databazi, dataset a network
    print "river gdb, network..."

    # Create database and dataset
    if not arcpy.Exists("RiverNetwork.gdb"):
        RiverDatabase = str(
            arcpy.CreateFileGDB_management(out_folder_path=workspace, out_name="RiverNetwork", out_version="CURRENT"))
        NetworkDataset = arcpy.CreateFeatureDataset_management(RiverDatabase, "NetworkDataset", sr)
    else:
        RiverDatabase = "RiverNetwork.gdb"
        arcpy.Delete_management(os.path.join(RiverDatabase, "NetworkDataset"))
        NetworkDataset = arcpy.CreateFeatureDataset_management(RiverDatabase, "NetworkDataset", sr)

    # Save selected DIBAVOD to Feature dataset
    edges = arcpy.FeatureClassToFeatureClass_conversion(dibA02_clip, NetworkDataset, "edges")

    # Create geometric network
    network = arcpy.CreateGeometricNetwork_management(NetworkDataset, "network", "edges SIMPLE_EDGE NO",
                                                      preserve_enabled_values="PRESERVE_ENABLED")

    # create polygon boundary
    obrys = arcpy.PolygonToLine_management(shape, "obrys")

    # create start points
    start_points = arcpy.FeatureVerticesToPoints_management(edges, "start_points", "START")

    # select and delete all start points not intersect polygon boundary
    tempLayer = "start_points.lyr"
    arcpy.MakeFeatureLayer_management(start_points, tempLayer)
    arcpy.SelectLayerByLocation_management(tempLayer, "INTERSECT", obrys, "", "NEW_SELECTION", "INVERT")
    arcpy.DeleteFeatures_management(tempLayer)

    # create end points
    end_points = arcpy.FeatureVerticesToPoints_management(edges, "end_points", "END")

    # select and delete all end points not intersect polygon boundary
    tempLayer = "end_points.lyr"
    arcpy.MakeFeatureLayer_management(end_points, tempLayer)
    arcpy.SelectLayerByLocation_management(tempLayer, "INTERSECT", obrys, "", "NEW_SELECTION", "INVERT")
    arcpy.DeleteFeatures_management(tempLayer)

    # ....................................................................................................

    # local variable for selecting the most appropriate path
    deviation = []  # to store deviation from the "ideal" division of polygon (== 1.0)
    polygon_division_options = 0  # to store how many options for dividing polygon
    find_path_problem = 0  # to count how many path problems
    end_start_options = 0  # to store how many combinations of start and end points

    print "zacinam hledat..."
    # all end points
    with arcpy.da.SearchCursor(end_points, "SHAPE@") as curEnd:
        for e in curEnd:
            inGeomEnd = e[0]
            partEnd = inGeomEnd.getPart(0)

            # all start points
            curStart = arcpy.da.SearchCursor(start_points, "SHAPE@")

            for s in curStart:
                # add 1 to count this option
                end_start_options += 1

                inGeomStart = s[0]
                partStart = inGeomStart.getPart(0)
                #print partEnd, partStart

                # create flags (all combination for start and end points)
                if arcpy.Exists(os.path.join(RiverDatabase, str(NetworkDataset), "flags")):
                    flags = os.path.join(RiverDatabase, str(NetworkDataset), "flags")
                    arcpy.DeleteFeatures_management(flags)
                else:
                    flags = arcpy.CreateFeatureclass_management(NetworkDataset, "flags", "POINT", spatial_reference=sr)

                with arcpy.da.InsertCursor(flags, "SHAPE@") as insCur:
                    insCur.insertRow(inGeomEnd)
                    insCur.insertRow(inGeomStart)
                del insCur

                # !!! Zde byl probelem uvnitr funkce, nebehala fce TraceGeometricNetwork_management
                # Trace Geometric Network function == selected edges and junctions
                try:
                    print "c"
                    # zkus najit cestu v siti
                    arcpy.TraceGeometricNetwork_management(network, "result_set", flags, "FIND_PATH",
                                                           in_trace_ends="NO_TRACE_ENDS",
                                                           in_trace_indeterminate_flow="NO_TRACE_INDETERMINATE_FLOW")
                    # Create a Mapping Layer out of the Group Layer
                    groupLayer = arcpy.mapping.Layer("result_set")

                    # Get a list of all the mappping layers, the first return will be the Group Layer itself
                    newLyrs = arcpy.mapping.ListLayers(groupLayer)

                    # EXPORT selected EDGES (dibA02_clip v databazi)
                    selected_path = arcpy.CopyFeatures_management(newLyrs[2], "selected_path.shp")

                    # Feature to Polygon
                    in_features = "selected_path.shp; obrys.shp"
                    dvojice = arcpy.FeatureToPolygon_management(in_features, "FeatureToPolygon.shp",
                                                                config.tolerance_FeatureToPolygon,
                                                                "NO_ATTRIBUTES", "")
                    area = []

                    # spocti plochu pro 2 dily
                    with arcpy.da.SearchCursor(dvojice, ['OID@', 'SHAPE@AREA']) as cursor:
                        for row in cursor:
                            area.append(row[1])
                            #print('Feature {} has an area of {}'.format(row[0], row[1]))
                    del cursor

                    # if a polygon divided into 2 parts
                    if len(area) == 2:
                        podil_ploch = max(area) / min(area)
                        #print "-- Podil ploch = {}".format(podil_ploch)
                        deviation.append(podil_ploch - 1)
                        #print "Deviation = {}".format(podil_ploch - 1)

                        if polygon_division_options == 0:
                            # first selection of river
                            selected_path_dissolve = arcpy.Dissolve_management(selected_path,
                                                                               "selected_path_dissolve.shp",
                                                                               "", "", "SINGLE_PART", "DISSOLVE_LINES")
                            fullPath_VybranyVodniTok = os.path.join(FCDataset_VybranyVodniTok,
                                                                    "v{0}_vodni_tok".format(ID))
                            arcpy.CopyFeatures_management(selected_path_dissolve,
                                                          fullPath_VybranyVodniTok)
                            nejlepsi_podil_ploch = podil_ploch
                            print "Prvni vyber vodniho toku."

                        else:
                            #print "Minimum deviation = {}".format(min(deviation))

                            # select if deviation is smaller
                            if (podil_ploch - 1) <= min(deviation):
                                selected_path_dissolve = arcpy.Dissolve_management(selected_path,
                                                                                   "selected_path_dissolve.shp", "", "",
                                                                                   "SINGLE_PART", "DISSOLVE_LINES")
                                fullPath_VybranyVodniTok = os.path.join(FCDataset_VybranyVodniTok,
                                                                        "v{0}_vodni_tok".format(ID))
                                arcpy.CopyFeatures_management(selected_path_dissolve,
                                                              fullPath_VybranyVodniTok)
                                nejlepsi_podil_ploch = podil_ploch
                                print "v"

                            else:
                                # vybrany vodni tok ma vyssi odchylku od idealniho rozdeleni plochy nez predesly
                                print "n"

                        polygon_division_options += 1
                    else:
                        # vybrana kombinace nedeli plochu
                        print "-"

                except:
                    #print "Problem s hledanim cesty"
                    find_path_problem += 1

            del curStart
    del curEnd

    try:
        arcpy.Delete_management(buffer_voda)
        arcpy.Delete_management(buffer_vodni_plochy)
        arcpy.Delete_management(buffer_vodni_toky)
        arcpy.Delete_management(buffer_voda_dissolve)
        #arcpy.Delete_management(buffer_voda_dissolve_clip)
        arcpy.Delete_management(dibA02_clip)
        arcpy.Delete_management(start_points)
        arcpy.Delete_management(end_points)
        arcpy.Delete_management(flags)
        arcpy.Delete_management(selected_path)
        arcpy.Delete_management(selected_path_dissolve)
        arcpy.Delete_management(dvojice)
        arcpy.Delete_management(RiverDatabase)
    except:
        print "."

    # Existuje vodni tok, ktery deli uzemi na 2 casti?
    fullPath_VybranyVodniTok = os.path.join(FCDataset_VybranyVodniTok,
                                            "v{0}_vodni_tok".format(ID))

    if arcpy.Exists(fullPath_VybranyVodniTok):
        # PRUSECIKY VYBRANEHO VODNIHO TOKU A MRIZKY A UHLOPRICEK
        in_features = fullPath_VybranyVodniTok + ";" + "mrizka_uhlopricky.shp"
        body_intersect = arcpy.Intersect_analysis(in_features, "intersect.shp", "ONLY_FID", "-1 Unknown", "POINT")
        arcpy.DeleteIdentical_management(body_intersect, "Shape", "", "0")  # mazu identicke body
        body_intersect_single = arcpy.MultipartToSinglepart_management(body_intersect, "body_intersect_single.shp")
        pocet_pruseciku = int(arcpy.GetCount_management(body_intersect_single).getOutput(0))

    else:
        # Neni vodni tok = plocha nejde delit, nejsou pruseciky s mrizkou
        pocet_pruseciku = 0
        nejlepsi_podil_ploch = 0

    result_info = [ID,
                   find_path_problem,
                   end_start_options,
                   round(nejlepsi_podil_ploch, 2),
                   pocet_pruseciku]

    # ....................................................................................................
    # uklid
    arcpy.Delete_management(mrizka)
    arcpy.Delete_management(obrys)
    arcpy.Delete_management(centroidy)
    arcpy.Delete_management(mrizka_linie)
    arcpy.Delete_management(mrizka_uhlopricky)
    arcpy.Delete_management(uhlopricky)
    arcpy.Delete_management(vrstevnice_clip)
    arcpy.Delete_management(vodni_plocha_clip)
    arcpy.Delete_management(vodni_toky_clip)

    try:
        arcpy.Delete_management(body_intersect)
        arcpy.Delete_management(body_intersect_single)

    except:
        print "."


    return result_info