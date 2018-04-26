

import subprocess
print "ahoj"

while True:
    return_code = subprocess.call([r"C:\Python27\ArcGIS10.5\python.exe", r"C:\fenclova\diplomka\analyza\skripty\0_predvyber_uzemi.py"])
    print ("navratovy kod pythonu.")
    if return_code == 777:
        break