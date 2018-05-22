import arcpy
print 'start'

arcpy.CheckOutExtension("Spatial")
arcpy.env.workspace = r'C:\fenclova\diplomka\analyza\mezivysledky\\'

arcpy.env.overwriteOutput = True

print 'nacitam data'
fishnet = r'C:\fenclova\diplomka\analyza\mezivysledky\znovu_vse.gdb\fishnet1234'
hranice = r'C:\fenclova\diplomka\data_zdroj\dmu25\hranice.shp'
zeleznice = r'C:\fenclova\diplomka\analyza\data\vstupni_data.gdb\dmu25_drazni_komunikace'
data = r'C:\fenclova\diplomka\analyza\mezivysledky\znovu_vse.gdb\\'
vstupni_data = r'C:\fenclova\diplomka\analyza\data\vstupni_data.gdb\\'

# # vymaz ty uzemi, ktera lezi mimo pas utm 33
# print 'vybiram vne pasu...'
# inFeatures = arcpy.CopyFeatures_management(fishnet, "fishnet_copy")
# tempLayer = "fishnet.lyr"
# selectFeatures = data + 'mimo_zobrazeni' # polygon reprezentuje uzemi, kde dochazi ke zkresleni souradnicove site
# arcpy.MakeFeatureLayer_management(inFeatures, tempLayer)
# arcpy.SelectLayerByLocation_management(tempLayer, "COMPLETELY_WITHIN", selectFeatures, selection_type="NEW_SELECTION",
#                                            invert_spatial_relationship="NOT_INVERT")
# arcpy.DeleteFeatures_management(tempLayer)
# arcpy.CopyFeatures_management(tempLayer, (data + "fishnet_zobrazeni_OK"))
#
# # vymaz ty, ktera nelezi kompletne uvnitr Ceska
# print 'vybiram vne republiky...'
# selectFeatures = hranice
# arcpy.SelectLayerByLocation_management(tempLayer, "COMPLETELY_WITHIN", selectFeatures, selection_type="NEW_SELECTION",
#                                            invert_spatial_relationship="INVERT")
# arcpy.DeleteFeatures_management(tempLayer)
# arcpy.CopyFeatures_management(tempLayer, (data + "fishnet_selectVNE"))
#
# # vymaz ty, kde neni zeleznice
# print 'vybiram se zeleznici...'
# inFeatures = data + "fishnet_selectVNE"
# tempLayer = "fishnet_zeleznice.lyr"
# selectFeatures = zeleznice
# arcpy.MakeFeatureLayer_management(inFeatures, tempLayer)
# arcpy.SelectLayerByLocation_management(tempLayer, "INTERSECT", selectFeatures, selection_type="NEW_SELECTION",
#                                            invert_spatial_relationship="INVERT")
# arcpy.DeleteFeatures_management(tempLayer)
# arcpy.CopyFeatures_management(tempLayer, (data + "fishnet_zeleznice"))

# VYMAZ TY, kde neni prusecik s vodni plochou
print 'vybiram se zastavbou...'
inFeatures = arcpy.CopyFeatures_management((data + "fishnet_zeleznice"), "fishnet_copy")
tempLayer = "fishnet.lyr"
arcpy.MakeFeatureLayer_management(inFeatures, tempLayer)

selectFeatures = vstupni_data + "dmu25_vodni_plochy"
arcpy.SelectLayerByLocation_management(tempLayer, "INTERSECT", selectFeatures, selection_type="NEW_SELECTION",
                                           invert_spatial_relationship="NOT_INVERT")
arcpy.DeleteFeatures_management(tempLayer)
arcpy.CopyFeatures_management(tempLayer, (data + "fishnet_VodniPlochy"))

# VYMAZ TY, kde neni prusecik se zastavbou
print 'vybiram bez zastavby...'
selectFeatures = vstupni_data + "dmu25_zastavba"
arcpy.SelectLayerByLocation_management(tempLayer, "INTERSECT", selectFeatures, selection_type="NEW_SELECTION",
                                           invert_spatial_relationship="NOT_INVERT")
arcpy.DeleteFeatures_management(tempLayer)
arcpy.CopyFeatures_management(tempLayer, (data + "fishnet_zastavba"))


print 'KONEC'
