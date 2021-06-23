import rasterio
import numpy as np
import os
import pandas as pd
import pickle
import pathlib


class TrainingSet:
    def __init__(self,
                 path_images,
                 dates,
                 band_names,
                 saving_path,
                 reference_file,
                 ObjectID,
                 LabelID):
        '''
        Prepare the training set given different input paths, obtained from the output of previous functions
        Args:
            path_images (str): Path where tif images obtained from stack_data.py are saved
            dates (pd.DataFrame): Dataframe with dates, automatically saved in stack_data.py
            band_names (list): name of the features that we want to keep in our training set
            saving_path (str): path where to store the training files
            reference_file (str): path of a .tif reference file at 10 meters scale
            ObjectID (str): path for the.tif that corresponds to the object ids of LULC
            LabelID (str): path for the .tif files which class to predict
        '''

        self.path_images = path_images
        self.band_names = band_names
        self.dates = dates
        self.reference_file = reference_file

        if not os.path.exists(saving_path):
            pathlib.Path(saving_path).mkdir(parents=True, exist_ok=True)

        self.saving_path = saving_path
        self.file_bands = []

        for band in band_names:
            for k in os.listdir(path_images):
                if band in k.split('_'):
                    self.file_bands.append(os.path.join(path_images, k))

        self.ObjectID = ObjectID
        self.LabelID = LabelID

    @staticmethod
    def make_directory(path):
        if os.path.exists(path) is False:
            os.makedirs(path)

    def reformat_labels(self, target, file_reference):
        target_to_mask = rasterio.open(target)
        meta = target_to_mask.meta
        target_to_mask = target_to_mask.read(1)

        raster_ref = rasterio.open(file_reference)
        raster_ref = raster_ref.read(1)
        mask = (raster_ref == 0)

        arr0 = np.ma.array(target_to_mask,
                           dtype=np.uint16,
                           mask=mask,
                           fill_value=0)

        target_to_mask = arr0.filled()
        name_output = target.split('.')
        name_output[-2] += '_' + '2019'
        os.remove(target)

        with rasterio.open('.'.join(name_output), 'w', **meta) as dst:
            dst.write_band(1, target_to_mask)

        self.target = name_output

    def prepare_training_set(self):

        self.reformat_labels(self.LabelID, self.reference_file)
        self.reformat_labels(self.ObjectID, self.reference_file)

        array_target1 = rasterio.open(self.LabelID)
        array_target1 = array_target1.read(1)

        h, w = array_target1.shape
        array_target1 = array_target1.flatten()

        array_target2 = rasterio.open(self.ObjectID)
        array_target2 = array_target2.read(1)
        array_target2 = array_target2.flatten()

        filter_observation = np.where(array_target1 > 0)

        x = np.linspace(0, h, h).astype(np.int16)
        y = np.linspace(0, w, w).astype(np.int16)
        xv, yv = np.meshgrid(x, y)

        dictionary_bands = {}
        dictionary_meta_info = {'coordinates_x': xv.flatten()[filter_observation],
                                'coordinates_y': yv.flatten()[filter_observation],
                                'LabelID': array_target1[filter_observation],
                                'ObjectID': array_target2[filter_observation], 'bands': self.file_bands,
                                'dates': list(self.dates.dates)}

        # scaling
        for index_band in self.file_bands:
            dictionary_meta_info[index_band] = {}
            band_name = index_band.split('/')[-1].split('_')[-2]
            print(band_name)
            band = rasterio.open(index_band)

            array_time = []
            bands_filtered = []

            for array_index in range(1, band.count+1):
                band_read = band.read(array_index)
                array_time.append(band_read)

                band_read = band_read.flatten()
                band_read = band_read[filter_observation]
                bands_filtered.append(band_read)

            # Get statistics from the image
            array_time = np.stack(array_time, axis=0)
            if band_name not in self.band_names:
                lb = -1
            else:
                lb = 0

            dictionary_meta_info[index_band]['max'] = np.max(array_time[array_time > lb])
            dictionary_meta_info[index_band]['min'] = np.min(array_time[array_time > lb])
            dictionary_meta_info[index_band]['mean'] = np.mean(array_time[array_time > lb])
            dictionary_meta_info[index_band]['median'] = np.median(array_time[array_time > lb])
            dictionary_meta_info[index_band]['std'] = np.std(array_time[array_time > lb])

            bands_filtered = np.stack(bands_filtered, axis=1)
            dictionary_bands[band_name] = bands_filtered

        dictionary_bands['LabelID'] = array_target1[filter_observation]
        dictionary_bands['ObjectID'] = array_target2[filter_observation]

        bands_concatenated = []

        for key in dictionary_bands.keys():
            if key in ['ObjectID', 'LabelID']:
                cols = [key]
                df_array = pd.DataFrame(dictionary_bands[key], columns=cols)
                print(df_array.shape)
            else:
                cols = [key + '_' + self.dates.dates[id_] for id_ in range(self.dates.shape[0])]
                df_array = pd.DataFrame(dictionary_bands[key], columns=cols)
                print(df_array.shape)

            bands_concatenated.append(df_array)

        bands_concatenated = pd.concat(bands_concatenated, axis=1)

        bands_concatenated.to_csv(os.path.join(self.saving_path, 'training_set.csv'), index=False)

        with open(os.path.join(self.saving_path, 'dictionary_meta_info.pickle'), 'wb') as d:
            pickle.dump(dictionary_meta_info, d, protocol=pickle.HIGHEST_PROTOCOL)
