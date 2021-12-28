import os
import numpy as np
import subprocess
import gdal

class GFSuperImpose:

    def __init__(self, otb_path, path_root, bands_20=None):
        self.otb_path = otb_path
        self.path_root = path_root
        if bands_20 is None:
            bands_20 = ['B5', 'B6', 'B7', 'B8A', 'B11', 'B12']
        self.bands_20 = bands_20

    def _get_path_names(self):
        tif_10_meters = []
        tif_20_meters = []

        for k in os.listdir(self.path_root):
            if np.any([x in k for x in ['GF']]):
                if np.any([x in k for x in self.bands_20]):
                    tif_20_meters.append(k)
                elif np.any([x in k for x in ['B2', 'B3', 'B4', 'B8']]):
                    tif_10_meters.append(k)

        return tif_10_meters, tif_20_meters

    def _apply_superimpose(self,reference, file, out):
        cmd = [os.path.join(self.otb_path, "otbcli_Superimpose"),
               "-inr", "%s" % reference,
               "-inm", "%s" % file,
               "-out", "%s" % out,
               "uint16",
               "-ram", "10000"]

        shell = False
        subprocess.call(cmd, shell=shell)
        os.remove(file)

    def _compress_output_file(self, out, band):
        src_ds = gdal.Open(out)
        output = os.path.join(self.path_root, 'GFstack_SI_' + band + '_crop.tif')
        # Compress the image
        topts = gdal.TranslateOptions(format='GTiff',
                                      outputType=gdal.GDT_UInt16,
                                      creationOptions=['COMPRESS=LZW', 'GDAL_PAM_ENABLED=NO'],
                                      bandList=list(range(1, src_ds.RasterCount + 1)))  # gdal.GDT_Byte

        gdal.Translate(output, src_ds, options=topts)

        os.remove(out)


    def execute_superimpose(self):
        '''
        Args:
            path_root (str) : folder that contains GEOTIFFS file obtained from stack_data.py
            otb_path (str) : folder where OTB is installed
            bands_20 (list) : name of the bands in 20m that will be superimposed into 10 meters
        '''

        tif_10_meters, tif_20_meters = self._get_path_names()

        for band in self.bands_20:
            file = os.path.join(self.path_root, 'GFstack_' + band + '_crop.tif')
            reference = os.path.join(self.path_root, tif_10_meters[0])
            out = os.path.join(self.path_root, 'Tempo_SI_' + band + '_crop.tif')

            self._apply_superimpose(reference, file, out)
            self._compress_output_file(out, band)

