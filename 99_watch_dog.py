# -*- coding: utf-8 -*-
# ....................................................................................................
# Name:         watch_dog.py
# Author:       Karolina Fenclova
# Description:  Script will call another script until a set "condition"
#               To solve the problem with a prematurely terminated calculation.


import subprocess
print "watch_dog.py started:"

while True:
    # Call a script until exit code is 777
    return_code = subprocess.call([r"C:\Python27\ArcGIS10.5\python.exe", r"C:\fenclova\diplomka\analyza\git_diplomka\12_hypsometrie_pocet_povodi.py"])
    print ("navratovy kod pythonu.")
    if return_code == 777:
        break