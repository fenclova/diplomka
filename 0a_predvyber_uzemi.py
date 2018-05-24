import arcpy

arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")
arcpy.env.overwriteOutput = True

fishnet = r'C:\fenclova\diplomka\analyza\mezivysledky\znovu_vse.gdb\fishnet'
hranice = r'C:\fenclova\diplomka\data_zdroj\dmu25\hranice.shp'
mimo_zobrazeni = r'C:\fenclova\diplomka\analyza\mezivysledky\znovu_vse.gdb\mimo_zobrazeni'

# vymaz ty uzemi, ktera lezi mimo pas utm 33
inFeatures = fishnet
tempLayer = "fishnet.lyr"
selectFeatures = mimo_zobrazeni
arcpy.MakeFeatureLayer_management(inFeatures, tempLayer)
arcpy.SelectLayerByLocation_management(tempLayer, "COMPLETELY_WITHIN", selectFeatures, selection_type="NEW_SELECTION",
                                           invert_spatial_relationship="INVERT")
arcpy.DeleteFeatures_management(tempLayer)

# vymaz ty, ktea nelezi kompletne uvnitr Ceska
selectFeatures = hranice
arcpy.SelectLayerByLocation_management(tempLayer, "COMPLETELY_WITHIN", selectFeatures, selection_type="NEW_SELECTION",
                                           invert_spatial_relationship="INVERT")
arcpy.DeleteFeatures_management(tempLayer)

# uloz vyber jako novou vrstvu
arcpy.CopyFeatures_management(tempLayer, "fishnet_edit.shp")
