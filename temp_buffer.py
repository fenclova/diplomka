print "start"

import arcpy, os
path_config = os.path.dirname(os.path.abspath(__file__))

workspace = os.path.join(os.path.dirname(path_config), r'data\vyber_fenclova.gdb\\')

ctverce = r'C:\fenclova\diplomka\analyza\vysledky\vysledek_SHP\250nej_centroid_lokace.shp'

buffer = arcpy.Buffer_analysis(ctverce, workspace + 'stavajici_mapy_buffer3', '2000 Meters')

obalka = arcpy.FeatureEnvelopeToPolygon_management(buffer, workspace + 'topsis250nej_lokace')

print 'konec'
