# -*- coding: utf-8 -*-

print "start"

import time
t1 = time.time()

import arcpy, os, config, csv

arcpy.env.workspace = config.workspace
arcpy.env.overwriteOutput = True

#sr = arcpy.SpatialReference(32633)
# arcpy.CheckOutExtension("Spatial")
# arcpy.CheckOutExtension("3D")


# if not arcpy.Exists("VodniToky.gdb"):
#     outDatabase = str(arcpy.CreateFileGDB_management(out_folder_path= config.workspace, out_name="VodniToky", out_version="CURRENT"))
# else:
#     outDatabase = "VodniToky.gdb"
#
# if not arcpy.Exists(os.path.join(outDatabase, "VybranyVodniTok")):
#     FCDataset_VybranyVodniTok = str(arcpy.CreateFeatureDataset_management(outDatabase, "VybranyVodniTok", sr))
# else:
#     FCDataset_VybranyVodniTok = os.path.join(outDatabase, "VybranyVodniTok")

ctverce_cursor = arcpy.da.UpdateCursor(config.ctverce, ["Id", "poradi"])

for ctverec in ctverce_cursor:
    ID = ctverec[0]
    print "\n ID: {0}".format(ID)

    reka = os.path.join(config.vodni_toky, "VodniToky.gdb", "VybranyVodniTok", "v{0}_vodni_tok".format(ID))
    arcpy.CopyFeatures_management(reka, os.path.join(r"C:\fenclova\diplomka\vystupy\kartografie_250zadani.gdb", "VybranyVodniTok", "v{0}_vodni_tok".format(ctverec[1])))

del ctverce_cursor



# Vysledny cas vypoctu
t2 = time.time()
TimeTakenSecs = str(t2 - t1)
print ("cas vypoctu: " + TimeTakenSecs + "sekund")


print "konec"