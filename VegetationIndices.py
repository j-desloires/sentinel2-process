##
import os
import numpy as np
import rasterio


class VegetationIndices:
    def __init__(self,
                 saving_path = './Sentinel2/GEOTIFFS/',
                 band_names = ['B2', 'B4','B8','B11']):

        self.saving_path = saving_path
        self.band_names = band_names

    @staticmethod
    def get_dictionary(saving_path,band_names):

        file_bands = []
        for band in band_names:
            for k in os.listdir(saving_path):
                if band in k.split('_'):
                    file_bands.append(os.path.join(saving_path, k))

        dictionary_bands = {}

        for index_band, band_name in enumerate(band_names) :
            print(band_name)
            band = rasterio.open(file_bands[index_band])

            array_time = []
            count = 0
            for array_index in range(1, band.count) :
                count += 1
                #if count%10 == 0:  print(count)

                band_read = band.read(array_index)
                array_time.append(band_read)

            array_time = np.stack(array_time,axis = 0)

            dictionary_bands[band_name] = array_time
            del array_time

        return dictionary_bands

    @staticmethod
    def MetaInfos(saving_path,times):
        random_band = os.listdir(saving_path)[0]

        with rasterio.open(os.path.join(saving_path, random_band)) as src0:
            meta = src0.meta
            meta['nodata'] = np.nan
            meta['dtype'] = 'float32'

        meta.update(count=times + 1)
        meta.update(nodata=np.nan)

        return meta


    def WriteTiff(self,array,variable_name,dimT,meta):

        with rasterio.open(os.path.join(self.saving_path, 'GFstack_' + variable_name + '_crop.tif'), 'w', **meta) as dst:
            for id in range(dimT):
                dst.write_band(id + 1, array[id, :, :].astype(np.float32))
        del array

    def compute_VIs(self,ECNorm = True):

        dictionary_bands = self.get_dictionary(self.saving_path,self.band_names)
        random_key = list(dictionary_bands.keys())[0]
        times = dictionary_bands[random_key].shape[0]
        meta = self.MetaInfos(self.saving_path,times)

        #Euclidean Norm
        if ECNorm:
            array_bands = []
            for key in self.band_names:
                array_bands.append(dictionary_bands[key])

            array_bands = [k.astype(np.int16) for k in array_bands]
            array_bands = np.stack(array_bands,axis = -1)
            array_bands_EC = np.sqrt(np.sum((array_bands+1**2), axis=-1))
            self.WriteTiff(array_bands_EC, 'ECNorm', times,meta)

        # Vegetation indices
        NDVI= (dictionary_bands['B8']-dictionary_bands['B4'])/(
                    dictionary_bands['B8']+dictionary_bands['B4'])
        del dictionary_bands['B4']
        self.WriteTiff(NDVI,'NDVI',times,meta)

        GNDVI = (dictionary_bands['B8']-dictionary_bands['B2'])/(
                    dictionary_bands['B8']+dictionary_bands['B2'])
        del dictionary_bands['B2']
        self.WriteTiff(GNDVI, 'GNDVI',times,meta)

        NDWI = (dictionary_bands['B8']-dictionary_bands['B11'])/(
                    dictionary_bands['B8']+dictionary_bands['B11'])
        del dictionary_bands['B8']
        del dictionary_bands['B11']
        self.WriteTiff(NDWI,'NDWI',times,meta)




