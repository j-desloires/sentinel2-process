##
import os
import numpy as np
import rasterio
import matplotlib.pyplot as plt
import gdal


class VegetationIndices:
    def __init__(self,
                 saving_path = 'Sentinel2/GEOTIFFS'):

        self.saving_path = saving_path

    @staticmethod
    def MetaInfos(saving_path,times):
        random_band = os.listdir(saving_path)[0]

        with rasterio.open(os.path.join(saving_path, random_band)) as src0:
            meta = src0.meta
            meta['nodata'] = np.nan
            meta['dtype'] = 'float32'

        meta.update(count=times)
        meta.update(nodata=np.nan)

        return meta


    def WriteTiff(self,array,variable_name,dimT,meta):

        path_tempo_file = os.path.join(self.saving_path, 'TempoGFstack_' + variable_name + '_crop_2019.tif')
        with rasterio.open(path_tempo_file, 'w', **meta) as dst:
            for id in range(dimT):
                dst.write_band(id + 1, array[id, :, :].astype(np.float32))
        del array
        src_ds = gdal.Open(path_tempo_file)
        topts = gdal.TranslateOptions(format='GTiff',
                                      outputType=gdal.GDT_Float32,
                                      creationOptions=['COMPRESS=LZW','GDAL_PAM_ENABLED=NO'],
                                      bandList=list(range(1,src_ds.RasterCount)))  # gdal.GDT_Byte

        gdal.Translate(os.path.join(self.saving_path, 'GFstack_' + variable_name + '_crop_2019.tif'), src_ds, options=topts)
        os.remove(path_tempo_file)

    def compute_VIs(self,ECNorm = False):

        B3 = gdal.Open(os.path.join(self.saving_path, 'GFstack_B3_crop_2019.tif')).ReadAsArray()
        B4 = gdal.Open(os.path.join(self.saving_path, 'GFstack_B4_crop_2019.tif')).ReadAsArray()
        B8 = gdal.Open(os.path.join(self.saving_path, 'GFstack_B8_crop_2019.tif')).ReadAsArray()

        times = B3.shape[0]
        meta = self.MetaInfos(self.saving_path,times)

        #Euclidean Norm
        if ECNorm:
            array_bands = [B3, B4, B8]
            array_bands = [k.astype(np.int16) for k in array_bands]
            array_bands = np.stack(array_bands,axis = -1)
            array_bands_EC = np.sqrt(np.sum((array_bands+1**2), axis=-1))
            array_bands_EC += -1
            self.WriteTiff(array_bands_EC, 'ECNorm', times,meta)

        # Vegetation indices
        NDVI= (B8-B4)/(B8+B4)
        del B4
        self.WriteTiff(NDVI,'NDVI',times,meta)
        del NDVI

        NDWI = (B3-B8)/(B3+B8)
        del B3
        del B8
        self.WriteTiff(NDWI, 'NDWI', times, meta)


