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

fieldnames = ["ID"]
filename = config.workspace + "99_chybi_vodni_tok"
chybi = []

ctverce_cursor = arcpy.da.UpdateCursor(config.ctverce, ["Id"])

with open(filename, "wb") as vysledky_file:
    csv_writer = csv.writer(vysledky_file)
    csv_writer.writerow(fieldnames)

    for ctverec in ctverce_cursor:
        ID = ctverec[0]
        print "\n ID: {0}".format(ID)

        if arcpy.Exists(os.path.join(config.vodni_toky, "VodniTok_1a.gdb", "VybranyVodniTok",
                                     "v{0}_vodni_tok".format(ID))):
            print "1a"
            # TODO až budu mít výběr 2000 řek, mohu si je nakopírovat do jiné databáze
            # reka = os.path.join(config.vodni_toky, "VodniTok_1a.gdb", "VybranyVodniTok", "v{0}_vodni_tok".format(ID))
            # arcpy.CopyFeatures_management(reka, os.path.join("VodniToky.gdb", "VybranyVodniTok", "v{0}_vodni_tok".format(ID)))

        elif arcpy.Exists(
                os.path.join(config.vodni_toky, "VodniTok_1b.gdb", "VybranyVodniTok", "v{0}_vodni_tok".format(ID))):
            print "1b"

        elif arcpy.Exists(
                os.path.join(config.vodni_toky, "VodniTok_2a.gdb", "VybranyVodniTok", "v{0}_vodni_tok".format(ID))):
            print "2a"

        elif arcpy.Exists(
                os.path.join(config.vodni_toky, "VodniTok_2c.gdb", "VybranyVodniTok", "v{0}_vodni_tok".format(ID))):
            print "2c"

        elif arcpy.Exists(
                os.path.join(config.vodni_toky, "VodniTok_2d.gdb", "VybranyVodniTok", "v{0}_vodni_tok".format(ID))):
            print "2d"

        elif arcpy.Exists(
                os.path.join(config.vodni_toky, "VodniTok_2d_co.gdb", "VybranyVodniTok", "v{0}_vodni_tok".format(ID))):
            print "2d_co"

        elif arcpy.Exists(
                os.path.join(config.vodni_toky, "VodniTok_2e.gdb", "VybranyVodniTok", "v{0}_vodni_tok".format(ID))):
            print "2e"

        elif arcpy.Exists(
                os.path.join(config.vodni_toky, "VodniTok_3a.gdb", "VybranyVodniTok", "v{0}_vodni_tok".format(ID))):
            print "3a"

        elif arcpy.Exists(
                os.path.join(config.vodni_toky, "VodniTok_3b.gdb", "VybranyVodniTok", "v{0}_vodni_tok".format(ID))):
            print "3b"

        elif arcpy.Exists(
                os.path.join(config.vodni_toky, "VodniTok_4.gdb", "VybranyVodniTok", "v{0}_vodni_tok".format(ID))):
            print "4"

        else:
            # zapis vysledek do csv souboru
            chybi.append(ID)

    del ctverce_cursor

    csv_writer.writerow(chybi)
    vysledky_file.flush()

vysledky_file.close()


# Vysledny cas vypoctu
t2 = time.time()
TimeTakenSecs = str(t2 - t1)
print ("cas vypoctu: " + TimeTakenSecs + "sekund")


print "konec"