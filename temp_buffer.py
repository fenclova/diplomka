print "start"

import arcpy, os
path_config = os.path.dirname(os.path.abspath(__file__))

workspace = os.path.join(os.path.dirname(path_config), r'data\vyber_fenclova.gdb\\')
ctverce = workspace + 'stavajici_mapy'

buffer = arcpy.Buffer_analysis(ctverce, workspace + 'stavajici_mapy_buffer', '2000 Meters')

obalka = arcpy.FeatureEnvelopeToPolygon_management(buffer, workspace + 'stavajici_mapy_ctverce')

print 'konec'
