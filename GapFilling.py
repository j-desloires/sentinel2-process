#####################################################################################################
#####################################################################################################
# must do first : download .run file on otb
# then ' chmod +x /home/s999379/OTB-7.2.0-Linux64.run'
# then /home/s999379/OTB-7.2.0-Linux64.run
# then go to the directory and do source otbenv.profile

import subprocess
import os
import pandas as pd
import numpy as np
import rasterio


def GapFill(otb_path, path_root, bands=['B2', 'B3', 'B4', 'B8'], res=10):
    '''
    Gapfilling given a folder outputs from the script stack_data.py.
    Args:
        path_root (str): Path where .tif files to gap fill are stored
        bands (list of str) : bands selected with same resolution to gap fill
        res int : resolution of the bands defined in the parameter bands
    '''

    for band in bands:
        file = os.path.join(path_root, 'stack_' + band + '_crop.tif')

        mask = os.path.join(path_root, 'stack_' + str(res) + 'm_crop.tif')
        out = os.path.join(path_root, 'GFstack_' + band + '_crop.tif')

        cmd = [os.path.join(otb_path, "otbcli_ImageTimeSeriesGapFilling"),
               "-in", "%s" % file,
               "-mask", "%s" % mask,
               "-out", "%s" % out,
               "-comp", "1",
               "-it", "linear",
               "-ram", "8000",
               ]

        shell = False
        subprocess.call(cmd, shell=shell)
        os.remove(file)


# GapFill(bands = ['B2','B3','B4','B8'], res = 10) #,
# GapFill(bands =['B5', 'B6', 'B7', 'B8A','B11','B12'], res=20)


def subset_time_series(path_output, band_names, year='2019'):
    dates = pd.read_csv('/'.join(path_output.split('/')[:-1]) + '/dates.csv')
    dates = np.array(dates['dates'])
    # filter over 2019
    dates_id = [id for id, k in enumerate(dates) if year in k]
    tif_files = os.listdir(path_output)
    tif_files = [os.path.join(path_output, k) for k in tif_files
                 if np.any([x in k for x in band_names]) and
                 year not in k]

    for tif_file in tif_files:
        print(tif_file)
        name_output = tif_file.split('.')
        name_output[1] += '_' + year
        name_output = '.'.join(name_output)
        img = rasterio.open(tif_file)
        meta = img.meta
        meta.update(count=len(dates_id) + 1)

        with rasterio.open(name_output, 'w', **meta) as dst:
            for id, id_d in enumerate(dates_id):
                array = img.read(id_d + 1)
                dst.write_band(id + 1, array)

        os.remove(tif_file)
