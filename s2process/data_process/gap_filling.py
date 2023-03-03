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
import gdal


def GapFill(otb_path, path_root, bands=None, res=10):
    """
    Gapfilling given a folder outputs from the script stack_data.py.
    Args:
        path_root (str): Path where .tif files to gap fill are stored
        bands (list of str) : bands selected with same resolution to gap fill
        res int : resolution of the bands defined in the parameter bands
    """

    if bands is None:
        bands = ["B2", "B3", "B4", "B8"]
    for band in bands:
        file = os.path.join(path_root, "stack_" + band + "_crop.tif")

        mask = os.path.join(path_root, "stack_" + str(res) + "m_crop.tif")
        out = os.path.join(path_root, "TempoGFstack_" + band + "_crop.tif")

        cmd = [
            os.path.join(otb_path, "otbcli_ImageTimeSeriesGapFilling"),
            "-in",
            "%s" % file,
            "-mask",
            "%s" % mask,
            "-out",
            "%s" % out,
            "-comp",
            "1",
            "-it",
            "linear",
            "-ram",
            "8000",
        ]

        shell = False
        subprocess.call(cmd, shell=shell)
        os.remove(file)
        # Compress the image
        src_ds = gdal.Open(out)
        output = os.path.join(path_root, "GFstack_" + band + "_crop.tif")
        topts = gdal.TranslateOptions(
            format="GTiff",
            outputType=gdal.GDT_UInt16,
            creationOptions=["COMPRESS=LZW", "GDAL_PAM_ENABLED=NO"],
            bandList=list(range(1, src_ds.RasterCount + 1)),
        )  # gdal.GDT_Byte

        gdal.Translate(output, src_ds, options=topts)

        os.remove(out)


def subset_time_series(path_output, band_names, year="2019"):
    dates = pd.read_csv(os.path.join(path_output, "dates.csv"))
    # filter over 2019
    dates_id = [id for id, k in enumerate(dates.dates) if year in k]
    dates = dates.iloc[dates_id, :]
    dates.to_csv(os.path.join(path_output, "dates.csv"), index=False)
    tif_files = os.listdir(path_output)
    tif_files = [
        os.path.join(path_output, k)
        for k in tif_files
        if np.any([x in k for x in band_names]) and year not in k
    ]

    for tif_file in tif_files:
        print(tif_file)
        name_output = tif_file.split(".")
        name_output[1] += "_" + year
        name_output = ".".join(name_output)

        src_ds = gdal.Open(tif_file)
        # Compress the image
        topts = gdal.TranslateOptions(
            format="GTiff",
            outputType=gdal.GDT_UInt16,
            creationOptions=["COMPRESS=LZW", "GDAL_PAM_ENABLED=NO"],
            bandList=dates_id,
        )  # gdal.GDT_Byte

        gdal.Translate(name_output, src_ds, options=topts)

        os.remove(tif_file)
