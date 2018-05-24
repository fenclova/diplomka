print "start"
import arcpy, config
from arcpy.sa import *

arcpy.env.workspace = r'C:\fenclova\diplomka\analyza\mezivysledky\\'
arcpy.env.overwriteOutput = True
sr = arcpy.SpatialReference(32633)
arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")

ctverec = r"C:\fenclova\diplomka\analyza\data\ctverce.gdb\fishnet_365"
data = r"C:\fenclova\diplomka\analyza\data\vstupni_data.gdb\\"


sr = arcpy.SpatialReference(32633)  # EPSG kod pro spatial reference

# ....................................................................................................
# PRIPRAVA DAT PRO DANE UZEMI

# Zajmova oblast okolo ctverce
buffer_ctverec = arcpy.Buffer_analysis(ctverec, "buffer_ctverec.shp", "1000 meters")

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
buffer_voda = arcpy.Clip_analysis(buffer_voda_dissolve, buffer_ctverec, "buffer_voda.shp")

# Vodni toky DIBAVOD orizunute podle obalove zony DMU25
reky = arcpy.Clip_analysis((data + "dibavod_VodniTokyA02_rady"), buffer_voda, "reky_clip.shp", "")

# model reliefu pro zajmovou oblast
inContours = "vrstevnice_clip.shp VYSKA Contour"
inStream = "reky_clip.shp # Stream"
inFeatures = (inContours + ";" + inStream)
outFeature = "dmt"
ext_pro_dmt = arcpy.Describe(buffer_ctverec)
extent = (str(ext_pro_dmt.extent.XMin) + " " + str(ext_pro_dmt.extent.YMin) + " " + str(
    ext_pro_dmt.extent.XMax) + " " + str(ext_pro_dmt.extent.YMax))
arcpy.env.extent = extent
dmt = arcpy.TopoToRaster_3d(inFeatures, outFeature, config.dmt_resolution, extent)

# ......................................................
# PRIPRAVA REK

# dissolve reky podle ID - slouci tok do 1 linie
reky_dissolve = arcpy.Dissolve_management(reky, "reky_dissolve.shp", ["TOK_ID", "gravelius"], "", "SINGLE_PART",
                                          "DISSOLVE_LINES")

# pridej atrubut "delka"
arcpy.AddGeometryAttributes_management(reky_dissolve, "LENGTH", Length_Unit="METERS")  # spocti delku linie

# VYBER a VYMAZ useky DIBAVOD, kratsi 500 m
inFeatures = reky_dissolve
tempLayer = "reky_dissolve.lyr"
arcpy.MakeFeatureLayer_management(inFeatures, tempLayer)
where = '"LENGTH" <= 500'
arcpy.SelectLayerByAttribute_management(tempLayer, "NEW_SELECTION", where)
arcpy.DeleteFeatures_management(tempLayer)

# Spocti delku vybranych vodnich toku
g = arcpy.Geometry()
geometryList = arcpy.CopyFeatures_management(reky_dissolve, g)
reky_delka = 0
for geometry in geometryList:
    reky_delka += geometry.length

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

            # odstran podledni bod
            arr.remove(arr.count - 1)

            # vytvor novou linii a obnov radek
            newLine = arcpy.Polyline(arr)
            row[0] = newLine
            cursor.updateRow(row)

# end pointy po zkraceni linie vodniho toku
end_point = arcpy.FeatureVerticesToPoints_management(reky_dissolve_zkracene, "end_point_PoZkraceni.shp", "END")

# .........................................
# TVORBA POVODI
print "povodi.."

# FILL DMR = vyplneni prohlubni
outFill = Fill(dmt)
outFill.save("fill")

# FLOW direction = smer odtoku
outFlowDirection = FlowDirection(outFill, "NORMAL")
outFlowDirection.save("flowDir")

# FLOW accumulation = odtok
outFlowAccumulation = FlowAccumulation(outFlowDirection)
outFlowAccumulation.save("flowAccum")

# SNAP pour point = tvorba rastru z end pointu a prichyceni bodu na misto nejvetsi akumulace vody
outSnapPour = SnapPourPoint(end_point, outFlowAccumulation, 5, "ORIG_FID")

# WaterShed = vytvor povodi RASTR
outWatershed = Watershed(outFlowDirection, outSnapPour)
povodi_polygon = arcpy.RasterToPolygon_conversion(outWatershed, "povodi_polygon.shp", "NO_SIMPLIFY", "VALUE")

# orizni povodi podle ctverce
povodi_clip = arcpy.Clip_analysis(povodi_polygon, ctverec, "povodi_clip.shp", "")

# ze ctverce vymaz povodi a zbytek rozdel do single polygonu
okoli = arcpy.Erase_analysis(ctverec, povodi_clip, "okoli.shp", "")
okoli_single = arcpy.MultipartToSinglepart_management(okoli, "okoli_single.shp")

# spoj povodi a okoli (= misto, kde se nevytvorilo povodi funkci watershed)
povodi_merge = arcpy.Merge_management([povodi_clip, okoli_single], "povodi_okoli_merge.shp")
arcpy.AddGeometryAttributes_management(povodi_merge, "AREA", Area_Unit="SQUARE_METERS")

# ELIMINUJ povodi mensi 250*250 m (1cm2 v mape 1 : 25 000)
povodi_final = "povodi_final.shp"
arcpy.CopyFeatures_management(povodi_merge, povodi_final)

inFeatures = povodi_final
tempLayer = "povodi_final.lyr"
arcpy.MakeFeatureLayer_management(inFeatures, tempLayer)
where = '"POLY_AREA" <= 62500'
arcpy.SelectLayerByAttribute_management(tempLayer, "NEW_SELECTION", where)
arcpy.DeleteFeatures_management(tempLayer)

# Delka rozvodnic
print "rozvodnice.."
rozvodnice = arcpy.PolygonToLine_management(povodi_final, "rozvodnice.shp", "IGNORE_NEIGHBORS")
rozvodnice_dissolve = arcpy.Dissolve_management(rozvodnice, "rozvodnice_dissolve.shp")

arcpy.AddGeometryAttributes_management(rozvodnice_dissolve, "LENGTH", "METERS")
g = arcpy.Geometry()
geometryList = arcpy.CopyFeatures_management(rozvodnice_dissolve, g)
rozvodnice_delka = 0
for geometry in geometryList:
    rozvodnice_delka += geometry.length

# pocet polygonu povodi eliminovanych o ty nejmensi
pocet_povodi = arcpy.GetCount_management(povodi_final)

#............................................................................................................
# BASIN
outBasin = Basin(outFlowDirection)
outBasin.save("basin")

# Basin to polygon
basin_polygon = arcpy.RasterToPolygon_conversion(outBasin, "basin_polygon.shp", "NO_SIMPLIFY", "VALUE")
basin_clip = arcpy.Clip_analysis(basin_polygon, ctverec, "basin_clip.shp")

# ze ctverce vymaz povodi a zbytek rozdel do single polygonu
basin = arcpy.Erase_analysis(basin_clip, povodi_clip, "basin.shp", "")

# spoj povodi a basin (= misto, kde se nevytvorilo povodi funkci watershed)
povodi_basin_merge = arcpy.Merge_management([povodi_clip, basin], "povodi_basin_merge.shp")
arcpy.AddGeometryAttributes_management(povodi_basin_merge, "AREA", Area_Unit="SQUARE_METERS")

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
pocet_povodi_basin = arcpy.GetCount_management(povodi_basin_final)

# ..................................................
# uklid:
# arcpy.Delete_management(buffer_ctverec)
# arcpy.Delete_management(vrstevnice)
# arcpy.Delete_management(vodni_plocha_clip)
# arcpy.Delete_management(vodni_toky_clip)
# arcpy.Delete_management(buffer_vodni_toky)
# arcpy.Delete_management(buffer_vodni_plochy)
# arcpy.Delete_management(buffer_voda)
# arcpy.Delete_management(buffer_voda_dissolve)
# arcpy.Delete_management(reky)
# arcpy.Delete_management(dmt)
# arcpy.Delete_management(reky_dissolve)
# arcpy.Delete_management(reky_dissolve_zkracene)
# arcpy.Delete_management(end_point)
# arcpy.Delete_management(outSnapPour)
# arcpy.Delete_management(povodi_polygon)
# arcpy.Delete_management(povodi_clip)
# arcpy.Delete_management(okoli)
# arcpy.Delete_management(okoli_single)
# arcpy.Delete_management(povodi_merge)
# arcpy.Delete_management(povodi_final)

arcpy.Delete_management("fill")
arcpy.Delete_management("flowDir")
arcpy.Delete_management("flowAccum")

# ..................................................

print pocet_povodi
print pocet_povodi_basin