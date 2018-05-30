# -*- coding: utf-8 -*-

# Nazev:            fce_povodi.py
# Autor:            Karolina Fenclova
# Popis:            Skript na vypocet kriterii pro mapu povodi

# VSTUP:            soubor config = nastaveni workspace + dat ke zpracovani

# VYSTUP:           jednotlive funkce vraceji pole hodnot

import arcpy, config, os
from arcpy.sa import *

arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")
arcpy.env.overwriteOutput = True

# prostredi pro ulozeni mezivypoctu pro Spatial Analyst
arcpy.env.scratchWorkspace = "in_memory"

# Funkce pocita radovost vodnich toku v uzemi
def radovost_vodnich_toku(ID, shape, workspace, data):
    cislo = ID
    sr = arcpy.SpatialReference(32633) # EPSG kod pro spatial reference

    # ....................................................................................................
    # PRIPRAVA DAT PRO DANE UZEMI

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

    buffer_voda_dissolve_clip = arcpy.Clip_analysis(buffer_voda_dissolve, shape, "buffer.shp")

    # DIBAVOD (A02 vodni toky jemne useky) pro zajmovou oblast (ctverec)
    dibA02_clip = arcpy.Clip_analysis((data + "dibavod_VodniTokyA02_rady"), buffer_voda_dissolve_clip, "dibA02_clip.shp", "")

    # VYBER a VYMAZ useky DIBAVOD, pokud linie nelezi uvnitr obalove zony
    # inFeatures = dibA02_clip
    # tempLayer = "dibA02_clip.lyr"
    # selectFeatures = buffer_voda_dissolve
    # arcpy.MakeFeatureLayer_management(inFeatures, tempLayer)
    # arcpy.SelectLayerByLocation_management(tempLayer, "WITHIN", selectFeatures, selection_type="NEW_SELECTION",
    #                                        invert_spatial_relationship="INVERT")
    # arcpy.DeleteFeatures_management(tempLayer)


    # dissolve reky podle ID - slouci tok do 1 linie
    reky_dissolve = arcpy.Dissolve_management(dibA02_clip, "reky_dissolve.shp", ["TOK_ID", "gravelius"], "", "SINGLE_PART",
                                              "DISSOLVE_LINES")

    # pridej atribut "delka"
    arcpy.AddGeometryAttributes_management(reky_dissolve, "LENGTH", Length_Unit="METERS")

    # VYBER a VYMAZ useky DIBAVOD, kratsi 500 m
    inFeatures = reky_dissolve
    tempLayer = "reky_dissolve.lyr"
    arcpy.MakeFeatureLayer_management(inFeatures, tempLayer)
    where = '"LENGTH" <= 500'
    arcpy.SelectLayerByAttribute_management(tempLayer, "NEW_SELECTION", where)
    arcpy.DeleteFeatures_management(tempLayer)

    # Delka vodnich toku DIBAVOD
    g = arcpy.Geometry()
    geometryList = arcpy.CopyFeatures_management(reky_dissolve, g)
    reky_delka = 0
    for geometry in geometryList:
        reky_delka += geometry.length

    # SPOJENI podle radu toku
    reky_rady_dissolve = arcpy.Dissolve_management(reky_dissolve, "dibA02_clip_dissolve.shp",
                                                         dissolve_field="gravelius",
                                                         statistics_fields="LENGTH SUM",
                                                         multi_part="MULTI_PART",
                                                         unsplit_lines="DISSOLVE_LINES")

    # pro kazdy rad urci delku linii
    rad_cursor = arcpy.da.SearchCursor(reky_rady_dissolve, ["gravelius", "SUM_LENGTH"])

    rady_delka = {'0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 0, '8': 0, '9': 0, '10': 0}

    for radek in rad_cursor:
        rady_delka[str(radek[0])] = round(radek[1], 2)


    # ....................................................................................................
    # uklid
    arcpy.Delete_management(vodni_plocha_clip)
    arcpy.Delete_management(vodni_toky_clip)
    arcpy.Delete_management(buffer_vodni_toky)
    arcpy.Delete_management(buffer_vodni_plochy)
    arcpy.Delete_management(buffer_voda)
    arcpy.Delete_management(buffer_voda_dissolve)
    arcpy.Delete_management(buffer_voda_dissolve_clip)
    arcpy.Delete_management(dibA02_clip)
    arcpy.Delete_management(reky_dissolve)
    arcpy.Delete_management(reky_rady_dissolve)

    # VYSLEDEK
    result = [cislo,
              round(reky_delka, 2),
              rady_delka['0'],
              rady_delka['1'],
              rady_delka['2'],
              rady_delka['3'],
              rady_delka['4'],
              rady_delka['5'],
              rady_delka['6'],
              rady_delka['7'],
              rady_delka['8'],
              rady_delka['9'],
              rady_delka['10']]

    return result

# Funkce tvori povodi, pocita delku rozvodnic a delku vyuzitych vodnich toku
def tvorba_povodi(ID, shape, workspace, data):
    print "povodi"

    cislo = ID
    sr = arcpy.SpatialReference(32633)  # EPSG kod pro spatial reference

    # ....................................................................................................
    # EXISTUJI VODNI TOKY DIBAVOD V UZEMI?
    dibA02_ctverec = arcpy.Clip_analysis((data + "dibavod_VodniTokyA02_rady"), shape, "dibA02_ctverec.shp", "")

    g = arcpy.Geometry()
    geometryList = arcpy.CopyFeatures_management(dibA02_ctverec, g)
    dibA02_ctverec_delka = 0
    for geometry in geometryList:
        dibA02_ctverec_delka += geometry.length

    # jsou v uzemi vodni toky?
    if (dibA02_ctverec_delka == 0):
        print "chybi vodni toky"
        pocet_povodi = 0
        pocet_povodi_vse = 0
        rozvodnice_delka = 0
        reky_ctverec_delka = 0

    else:
        # Zajmova oblast okolo ctverce
        buffer_ctverec = arcpy.Buffer_analysis(shape, "buffer_ctverec.shp", config.buffer_povodi)

        # Vrstevnice pro zajmovou oblast
        vrstevnice = arcpy.Clip_analysis((data + "dmu25_vrstevnice_ziv5m"), buffer_ctverec, "vrstevnice_clip.shp", "")

        # Vodni plochy pro CTVEREC
        vodni_plocha_clip = arcpy.Clip_analysis((data + "dmu25_vodni_plochy"), buffer_ctverec, "vodni_plocha_clip.shp", "")

        # Vodni toky pro CTVEREC
        vodni_toky_clip = arcpy.Clip_analysis((data + "dmu25_reka_potok"), buffer_ctverec, "vodni_toky_clip.shp", "")

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

        # orizni obalovou zonu podle okoli ctverce => aby nasledne koncevo body lezely v uzemi
        buffer_voda = arcpy.Clip_analysis(buffer_voda_dissolve, buffer_ctverec, "buffer_voda.shp")

        # Vodni toky DIBAVOD orizi podle obalove zony vodnich toku a ploch v DMU25
        reky = arcpy.Clip_analysis((data + "dibavod_VodniTokyA02_rady"), buffer_voda, "reky_clip.shp", "")

        # model reliefu pro zajmovou oblast
        inContours = "vrstevnice_clip.shp VYSKA Contour"
        inStream = "reky_clip.shp # Stream"
        inFeatures = (inContours + ";" + inStream)
        outFeature = "dmt"
        ext_pro_dmt = arcpy.Describe(buffer_ctverec)
        extent = (str(ext_pro_dmt.extent.XMin) + " " + str(ext_pro_dmt.extent.YMin) + " " + str(
                ext_pro_dmt.extent.XMax) + " " + str(ext_pro_dmt.extent.YMax))
        #arcpy.env.extent = extent
        dmt = arcpy.TopoToRaster_3d(inFeatures, outFeature, config.dmt_resolution, extent)

        #......................................................
        # PRIPRAVA REK

        # dissolve reky podle ID - slouci tok do 1 linie
        reky_dissolve = arcpy.Dissolve_management(reky, "reky_dissolve.shp", ["TOK_ID", "gravelius"], "", "SINGLE_PART", "DISSOLVE_LINES")

        # pridej atribut "delka"
        arcpy.AddGeometryAttributes_management(reky_dissolve, "LENGTH", Length_Unit = "METERS")

        # VYBER a VYMAZ useky DIBAVOD, kratsi 500 m (2 cm v mape 1 : 25 000)
        inFeatures = reky_dissolve
        tempLayer = "reky_dissolve.lyr"
        arcpy.MakeFeatureLayer_management(inFeatures, tempLayer)
        where = '"LENGTH" <= 500'
        arcpy.SelectLayerByAttribute_management(tempLayer, "NEW_SELECTION", where)
        arcpy.DeleteFeatures_management(tempLayer)

        # Spocti delku oriznutych a vybranych vodnich toku DIBAVOD (jen v uzemi čtverce)
        reky_dissolve_clip = arcpy.Clip_analysis(reky_dissolve, shape, "reky_dissolve_clip.shp")

        g = arcpy.Geometry()
        geometryList = arcpy.CopyFeatures_management(reky_dissolve_clip, g)
        reky_ctverec_delka = 0
        for geometry in geometryList:
            reky_ctverec_delka += geometry.length


        # Stale existuje vodni tok ze ktereho se pocita závěrový profil?
        if (reky_ctverec_delka != 0):

            # ZKRAT LINII O POSLEDNI USEK - pro tvorbu end pointu
            # (muzu zkratit vsechny = pocitam s buffer zonou)
            reky_dissolve_zkracene = "reky_dissolve_zkracene.shp"
            arcpy.CopyFeatures_management(reky_dissolve, reky_dissolve_zkracene)

            with arcpy.da.UpdateCursor(reky_dissolve_zkracene, ["shape@", "OID@"]) as cursor:
                for row in cursor:
                    geom = row[0]
                    oid = row[1]
                    if geom.length > 0:
                        # Vytvor pole bodu
                        arr = geom.getPart(0)

                        # odstran posledni bod
                        arr.remove(arr.count - 1)

                        # vytvor novou linii a obnov radek
                        newLine = arcpy.Polyline(arr)
                        row[0] = newLine
                        cursor.updateRow(row)

            # end pointy po zkraceni linie vodniho toku
            arcpy.Delete_management("end_point.shp")
            end_point = arcpy.FeatureVerticesToPoints_management(reky_dissolve_zkracene, "end_point.shp", "END")

            #.............................................................................
            # TVORBA POVODI

            # FILL DMR = vyplneni prohlubni
            outFill = Fill(dmt)
            outFill.save("fill.tif")

            # FLOW direction = smer odtoku
            outFlowDirection = FlowDirection(outFill, "NORMAL")
            outFlowDirection.save("flowDirection.tif")

            # FLOW accumulation = odtok
            outFlowAccumulation = FlowAccumulation(outFlowDirection)
            outFlowAccumulation.save("flowAccum.tif")

            # SNAP pour point = tvorba rastru z end pointu a prichyceni bodu na misto nejvetsi akumulace vody
            outSnapPour = SnapPourPoint(end_point, outFlowAccumulation, 5, "ORIG_FID")
            outSnapPour.save("snap.tif")

            # WaterShed = vytvor povodi RASTR > polygon
            outWatershed = Watershed(outFlowDirection, outSnapPour)
            outWatershed.save("watershed.tif")
            povodi_polygon = arcpy.RasterToPolygon_conversion(outWatershed, "povodi_polygon.shp", "NO_SIMPLIFY", "VALUE")

            # orizni povodi podle ctverce
            povodi_clip = arcpy.Clip_analysis(povodi_polygon, shape, "povodi_clip.shp", "")

            # ZAKLADNI POVODI - BASIN
            outBasin = Basin(outFlowDirection)
            outBasin.save("basin.tif")

            # Basin to polygon
            basin_polygon = arcpy.RasterToPolygon_conversion(outBasin, "basin_polygon.shp", "NO_SIMPLIFY", "VALUE")
            basin_clip = arcpy.Clip_analysis(basin_polygon, shape, "basin_clip.shp")

            # ze ctverce vymaz povodi a zbytek rozdel do single polygonu
            basin = arcpy.Erase_analysis(basin_clip, povodi_clip, "basin.shp", "")

            # spoj povodi a basin (= misto, kde se nevytvorilo povodi funkci watershed)
            povodi_basin_merge = arcpy.Merge_management([povodi_clip, basin], "povodi_basin_merge.shp")
            arcpy.AddGeometryAttributes_management(povodi_basin_merge, "AREA", Area_Unit="SQUARE_METERS")

            # pocet polygonu povodi NEeliminovanych o ty nejmensi
            pocet_povodi_vse = arcpy.GetCount_management(povodi_basin_merge)

            # ELIMINUJ povodi mensi 250*250 m (1cm2 v mape 1 : 25 000)
            povodi_basin_final = "povodi_basin_final.shp"
            arcpy.CopyFeatures_management(povodi_basin_merge, povodi_basin_final)

            inFeatures = povodi_basin_final
            tempLayer = "povodi_basin_final.lyr"
            arcpy.MakeFeatureLayer_management(inFeatures, tempLayer)
            where = '"POLY_AREA" <= 62500'
            arcpy.SelectLayerByAttribute_management(tempLayer, "NEW_SELECTION", where)
            arcpy.DeleteFeatures_management(tempLayer)

            # pocet polygonu povodi eliminovanych o ty nejmensi
            pocet_povodi = arcpy.GetCount_management(povodi_basin_final)

            # Tvorba rozvodnic + delka
            rozvodnice = arcpy.PolygonToLine_management(povodi_basin_final, "rozvodnice.shp", "IGNORE_NEIGHBORS")
            rozvodnice_dissolve = arcpy.Dissolve_management(rozvodnice, "rozvodnice_dissolve.shp")

            arcpy.AddGeometryAttributes_management(rozvodnice_dissolve, "LENGTH", "METERS")
            g = arcpy.Geometry()
            geometryList = arcpy.CopyFeatures_management(rozvodnice_dissolve, g)
            rozvodnice_delka = 0
            for geometry in geometryList:
                rozvodnice_delka += geometry.length

            # uklid po povodi
            arcpy.Delete_management(outSnapPour)
            arcpy.Delete_management(povodi_polygon)
            arcpy.Delete_management(povodi_clip)
            arcpy.Delete_management(basin)
            arcpy.Delete_management(basin_clip)
            arcpy.Delete_management(basin_polygon)
            arcpy.Delete_management(povodi_basin_merge)
            arcpy.Delete_management(povodi_basin_final)
            arcpy.Delete_management(rozvodnice)
            arcpy.Delete_management(rozvodnice_dissolve)

            arcpy.Delete_management(outFill)
            arcpy.Delete_management(outFlowDirection)
            arcpy.Delete_management(outFlowAccumulation)
            arcpy.Delete_management(outWatershed)
            arcpy.Delete_management(outBasin)
            arcpy.Delete_management(outSnapPour)

            arcpy.Delete_management("basin.tif")
            arcpy.Delete_management("fill.tif")
            arcpy.Delete_management("flowDirection.tif")
            arcpy.Delete_management("flowAccum.tif")
            arcpy.Delete_management("snap.tif")
            arcpy.Delete_management("watershed.tif")


        else:
            print "Chybi vodni tok."

            # v uzemi neni vodni tok = 0 povodi, 0 delka rozvodnice
            pocet_povodi = 0
            pocet_povodi_vse = 0
            rozvodnice_delka = 0

        #..................................................
        # uklid celkovy:

        arcpy.Delete_management(buffer_ctverec)
        arcpy.Delete_management(vrstevnice)
        arcpy.Delete_management(vodni_plocha_clip)
        arcpy.Delete_management(vodni_toky_clip)
        arcpy.Delete_management(buffer_vodni_toky)
        arcpy.Delete_management(buffer_vodni_plochy)
        arcpy.Delete_management(buffer_voda)
        arcpy.Delete_management(buffer_voda_dissolve)
        arcpy.Delete_management(reky)
        arcpy.Delete_management(dmt)
        arcpy.Delete_management(reky_dissolve)
        arcpy.Delete_management(reky_dissolve_clip)
        arcpy.Delete_management(reky_dissolve_zkracene)
        arcpy.Delete_management(end_point)

    # Automaticke mazani rastru z workspace (= nefunguje, na datech je zámek)
    # r = arcpy.ListRasters('t_t*')
    #
    # for i in r:
    #     try:
    #         arcpy.Delete_management(i)
    #     except:
    #         pass

    arcpy.Delete_management(dibA02_ctverec)

    # funkce vrací výsledek
    return [cislo, pocet_povodi, pocet_povodi_vse, round(rozvodnice_delka, 2), round(reky_ctverec_delka, 2)]