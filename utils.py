# basic utils that don't fit into any specific class

import os
import shutil

# delete trained_LTC folder
def cleanup_last_generation():
    if os.path.exists('trained_LTC'):
        shutil.rmtree('trained_LTC')
        print('Deleted trained_LTC folder (it will be regenerated with new weights)')

# delete trained_ltc.zip
def cleanup_zip():
    if os.path.exists('trained_LTC.zip'):
        os.remove('trained_LTC.zip')
        print('Deleted trained_LTC.zip')