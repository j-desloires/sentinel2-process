from osgeo.gdal import *
from osgeo import gdal, ogr
import subprocess
import pandas as pd
import datetime
import skimage.morphology  # pip install scikit-image
import shutil
# conda install -c conda-forge gdal
# conda install -c conda-forge rasterio
from subprocess import call
import rasterio
import numpy as np
import geopandas as gpd
import earthpy.spatial as es
import gdal
import os
import pathlib
import shutil

def Open_array_info(filename=''):
    """
    Opening a tiff info, for example size of array, projection and transform matrix.
    Keyword Arguments:
    filename -- 'C:/file/to/path/file.tif' or a gdal file (gdal.Open(filename))
        string that defines the input tiff file or gdal file
    """
    f = gdal.Open(r"%s" % filename)
    if f is None:
        print('%s does not exists' % filename)
    else:
        geo_out = f.GetGeoTransform()
        proj = f.GetProjection()
        size_X = f.RasterXSize
        size_Y = f.RasterYSize
        f = None
    return geo_out, proj, size_X, size_Y


def Open_tiff_array(filename='', band=''):
    """
    Opening a tiff array.
    Keyword Arguments:
    filename -- 'C:/file/to/path/file.tif' or a gdal file (gdal.Open(filename))
        string that defines the input tiff file or gdal file
    band -- integer
        Defines the band of the tiff that must be opened.
    """
    f = gdal.Open(filename)
    if f is None:
        print('%s does not exists' % filename)
    else:
        if band == '':
            band = 1
        Data = f.GetRasterBand(band).ReadAsArray()
        Data = Data.astype(np.float32)
    return (Data)


def Vector_to_Raster(Dir, vector_path, reference_file, attribute):
    """
    This function creates a raster of a vector_path file

    Dir (str): path to save the rasterized labels
    vector_path (str) : Name of the shapefile
    reference_file (str): Path to an example tiff file (all arrays will be reprojected to this example)
    attrbute (str) : column name of the attribute to rasterize
    """

    geo, proj, size_X, size_Y = Open_array_info(reference_file)

    x_min = geo[0]
    x_max = geo[0] + size_X * geo[1]
    y_min = geo[3] + size_Y * geo[5]
    y_max = geo[3]
    pixel_size = geo[1]


    Basename = os.path.basename(vector_path)
    Dir_Raster_end = os.path.join(Dir, os.path.splitext(Basename)[0] + '_' + attribute + '.tif')

    # Open the data source and read in the extent
    source_ds = ogr.Open(vector_path)
    source_layer = source_ds.GetLayer()

    # Create the destination data source
    x_res = int(round((x_max - x_min) / pixel_size))
    y_res = int(round((y_max - y_min) / pixel_size))

    # Create tiff file
    target_ds = gdal.GetDriverByName('GTiff').Create(Dir_Raster_end,
                                                     x_res, y_res,
                                                     1, gdal.GDT_UInt16,
                                                     ['COMPRESS=LZW'])

    target_ds.SetGeoTransform(geo)
    srse = osr.SpatialReference()
    srse.SetWellKnownGeogCS(proj)
    target_ds.SetProjection(srse.ExportToWkt())
    band = target_ds.GetRasterBand(1)
    target_ds.GetRasterBand(1).SetNoDataValue(0)
    band.Fill(0)

    # Rasterize the shape and save it as band in tiff file
    gdal.RasterizeLayer(target_ds, [1], source_layer,
                        None, None, [1], ['ATTRIBUTE=' + attribute])
    target_ds = None

    # Open array
    Raster_out = Open_tiff_array(Dir_Raster_end)

    return Raster_out


def GetRandomTheiaFile(folder_theia, band_name='B2'):
    '''
    Find a random tif images from the folders downloaded to get informations for the rasterization.
    Args:
        folder_theia (str): Name of the folder from the git repo cloned
        band_name (str) : band name used as reference (here, B2 for 10 meters images)
    Returns:

    '''
    path_folder = [os.path.join(folder_theia, k)
                   for k in os.listdir(folder_theia)
                   if ~np.any([x in k for x in ['zip', 'cfg', 'json', 'md', 'py', 'tmp']])]

    path_random_band = [os.path.join(path_folder[0], k) for k in os.listdir(path_folder[0])
                        if np.all([x in k for x in ['FRE']]) and k.split('_')[-1] == band_name + '.tif']

    return path_random_band[0]


########################################################################################


class RasterLabels:
    '''

    '''

    def __init__(self, vector_path, reference_file, extent_vector, saving_path,
                 ObjectID='Class_ID', LabelID='Label_Code'):
        '''
        Rasterization of a vector file (.shp) to get the target variables for the project study.
        Args:
            vector_path (str): Path to the vector .shp file (e.g
            reference_file (str): Path to a .tif file that contains information for the rasterization
            extent_vector (str) : Path to vector file (.shp) that contains the polygon of the Area of Interest to crop images
            saving_path (str) : Path to save preprocessed rasterized labels
            ObjectID (str) : Name of the columns from the vector file (stored in vector_path) that contains the integers used as object identification
            LabelID (str) : Name of the column from the vector file (stored in vector_path) with integer target labels for LULC
        '''

        self.vector_path = vector_path
        if not os.path.exists(vector_path) or 'shp' not in vector_path.split('.'):
            raise ValueError('You should provide a valid path to the shapefile that contains vector IDs')

        self.reference_file = reference_file
        self.extent_vector = extent_vector
        if not os.path.exists(saving_path):
            pathlib.Path(saving_path).mkdir(parents=True, exist_ok=True)
        self.saving_path = saving_path
        self.ObjectID = ObjectID
        self.LabelID = LabelID

    @staticmethod
    def binary_erosion(array):
        mask = (array > 0).astype(int)
        disk = skimage.morphology.disk(1)
        mask = skimage.morphology.binary_erosion(mask, disk)

        arr0 = np.ma.array(array,
                           dtype=np.int16,
                           mask=(1 - mask).astype(bool),
                           fill_value=0)
        array = arr0.filled()

        return array

    def rasterize_labels(self):
        with rasterio.open(self.reference_file) as src0:
            meta = src0.meta
            meta['nodata'] = 0.0

        class_array = Vector_to_Raster(self.saving_path, self.vector_path, self.reference_file, self.ObjectID)
        class_array = self.binary_erosion(class_array)

        label_array = Vector_to_Raster(self.saving_path, self.vector_path, self.reference_file, self.LabelID)
        label_array = self.binary_erosion(label_array)

        path_class = os.path.join(self.saving_path, self.ObjectID + '.tif')
        path_labels = os.path.join(self.saving_path, self.LabelID + '.tif')

        with rasterio.open(path_class, 'w', **meta) as dst:
            dst.write_band(1, class_array.astype(np.int16))

        with rasterio.open(path_labels, 'w', **meta) as dst:
            dst.write_band(1, label_array.astype(np.int16))

        paths_output = [path_class, path_labels]
        extent = gpd.read_file(self.extent_vector)

        es.crop_all(paths_output, self.saving_path, extent, overwrite=True, all_touched=True, verbose=True)


###########################################################################################
class StackFoldersSentinel2:

    def __init__(self,
                 extent_vector,
                 folder_theia,
                 bands=['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12'],
                 res_bands=[10, 10, 10, 20, 20, 20, 10, 20, 20, 20],
                 cloud_coverage=0.5,
                 saving_path='./Sentinel2/GEOTIFFS',
                 name_mask_feature='DN'):
        '''
        Preprocessing of folders unzipped downloaded from Theia to get cloud free images, stacked into .tif files and
        croped by the geometry of the Area of Interest
        Args:
            extent_vector (str) : Path to vector file (.shp) that contains the polygon of the Area of Interest to crop images
            bands (list of str): List of the bands that we would like to save as.tif files
            res_bands (list of int): Resolution of the bands
            saving_path (str): Path to save the .tif files
            folder_theia (str): Path to the folder where there is confirure files to download images
            name_mask_feature (str) : Name of the column from the extend vector that contains the ID (integer) of the observed polygon from the AOI
        '''

        self.bands = bands
        self.res_bands = res_bands
        if len(bands) != len(res_bands):
            raise ValueError("Should have the same length for the bands and the resolution")

        self.folder_theia = folder_theia

        self.extent_vector = extent_vector
        self.name_mask_feature = name_mask_feature

        if not os.path.exists(saving_path):
            pathlib.Path(saving_path).mkdir(parents=True, exist_ok=True)
        self.saving_path = saving_path
        self.cloud_coverage = cloud_coverage

    ###########################################################################################

    def get_mask_extent(self):

        reference_raster_data_name_10 = GetRandomTheiaFile(self.folder_theia, band_name='B2')

        mask_array_10 = Vector_to_Raster(self.saving_path,
                                         self.extent_vector,
                                         reference_raster_data_name_10,
                                         self.name_mask_feature)

        reference_raster_data_name_20 = GetRandomTheiaFile(self.folder_theia, band_name='B5')

        mask_array_20 = Vector_to_Raster(self.saving_path,
                                         self.extent_vector,
                                         reference_raster_data_name_20,
                                         self.name_mask_feature)

        return mask_array_10, mask_array_20

    def array_from_dict(self, band_array, band_name):

        band_values = band_array['data']
        band_values = band_values.astype(np.int16)

        band_cloud = band_array['CLM']
        band_cloud = band_cloud.astype(np.int16)

        file_reference = GetRandomTheiaFile(self.folder_theia, band_name=band_name)
        geo, proj, size_X, size_Y = Open_array_info(file_reference)

        # Read metadata of first file
        with rasterio.open(file_reference) as src0:
            meta = src0.meta
            meta['nodata'] = 0.0

        # Update meta to reflect the number of layers
        id_bands = [ind for ind, k in enumerate(band_array['Cloud_Percent']) if k < self.cloud_coverage]
        meta.update(count=len(id_bands) + 1)

        with rasterio.open(os.path.join(self.saving_path, 'stack_' + band_name + '.tif'), 'w', **meta) as dst:
            for id, time_index in enumerate(id_bands):
                dst.write_band(id + 1, band_values[time_index, :, :].astype(np.int16))

        rsuffix = '20m' if geo[1] == 20 else '10m'

        # if os.path.exists(os.path.join(path, 'stack_' + rsuffix + '.tif')) is False:
        meta['nodata'] = None
        with rasterio.open(os.path.join(self.saving_path, 'stack_' + rsuffix + '.tif'), 'w', **meta) as dst_clm:
            for id, num_band in enumerate(id_bands):
                dst_clm.write_band(id + 1, band_cloud[num_band, :, :].astype(np.int16))

        del band_cloud
        del band_values

        if os.path.exists(os.path.join(self.saving_path, 'dates.csv')) is False:
            dates = list(band_array['dates'])
            dates = [dates[id_] for id_ in id_bands]
            dates = pd.DataFrame(dates)
            dates.columns = ['dates']
            dates['dates'] = dates['dates'].apply(lambda x: pd.to_datetime(x, format='%Y%m%d'))
            dates.to_csv(os.path.join(self.saving_path, 'dates.csv'), index=False)
            del dates
        del band_array

    def ExtractImagesFolder(self):

        folders = [k for k in os.listdir(self.folder_theia) if
                   np.any([x in k for x in ['SENTINEL']]) and ~np.any([x in k for x in ['.zip', 'tmp']])]

        dates = [k.split('_')[1].split('-')[0] for k in folders]
        dates_sorted = np.argsort(dates)
        folders = [folders[i] for i in dates_sorted]

        mask_array_10, mask_array_20 = self.get_mask_extent()
        mask_data_10 = (mask_array_10 > 0)
        mask_data_20 = (mask_array_20 > 0)

        dictionary_meta_info = {}

        folders_to_remove = []

        for band in self.bands:
            # band = 'B8'
            print(band)
            index_band = np.where(np.array(self.bands) == band)[0][0]
            mask_polygon = mask_data_10 if self.res_bands[index_band] == 10 else mask_data_20

            # Concatenate arrays into a dictionary
            dictionary_bands = {}
            dictionary_bands['data'] = []
            dictionary_bands['dates'] = []
            dictionary_bands['CLM'] = []
            dictionary_bands['Cloud_Percent'] = []
            dictionary_meta_info[band] = {}

            count = 0

            for folder in folders:
                count += 1
                if count % 20 == 0:
                    print(count)

                ##GET THE BAND
                path_list_bands = os.path.join(self.folder_theia, folder)
                list_bands = os.listdir(path_list_bands)

                image = [k for k in list_bands
                         if (np.any([x in k for x in ['FRE']])
                             and k.split('_')[-1].split('.')[0] in [band])]

                path_band = os.path.join(path_list_bands, image[0])
                array = Open_tiff_array(path_band)

                arr0 = np.ma.array(array,
                                   dtype=np.float32,
                                   mask=(1 - mask_polygon).astype(bool),
                                   fill_value=-1)

                array = arr0.filled()
                array += 1
                # if half of the images is in no data : unvalid folder => remove it
                if (np.count_nonzero(array > 0) / np.count_nonzero(mask_polygon)) < 0.5:

                    # script = "sudo rm -rf " + path_list_bands
                    # call(script,shell=True)
                    folders.remove(folder)
                    shutil.rmtree(path_list_bands)

                    pass
                else:
                    ##GET THE CLOUD
                    ref = 'R1' if self.res_bands[index_band] == 10 else 'R2'
                    file_cloud = [k for k in os.listdir(os.path.join(path_list_bands, 'MASKS')) \
                                  if (np.any([x in k for x in ['CLM']]) and \
                                      np.any([x in k for x in [ref]]))]

                    path_cloud = os.path.join(os.path.join(path_list_bands, 'MASKS'), file_cloud[0])
                    mask = Open_tiff_array(path_cloud)
                    mask = mask > 0

                    arr0 = np.ma.array(array,
                                       dtype=np.float32,
                                       mask=mask,
                                       fill_value=0)

                    array = arr0.filled()

                    clp = 1 - (np.count_nonzero(array) / np.count_nonzero(mask_polygon))

                    dictionary_bands['data'].append(array)
                    dictionary_bands['CLM'].append(mask)
                    dictionary_bands['Cloud_Percent'].append(clp)
                    date = folder.split('_')[1].split('-')[0]
                    dictionary_bands['dates'].append(date)

            dictionary_bands['data'] = np.stack(dictionary_bands['data'])
            dictionary_bands['CLM'] = np.stack(dictionary_bands['CLM'])
            # Convert into GEOTIFFS
            self.array_from_dict(dictionary_bands, band)

    def CropImages(self):

        extent = gpd.read_file(self.extent_vector)

        paths_list = [os.path.join(self.saving_path, tif_file) for tif_file in list(os.listdir(self.saving_path))
                      if 'tif' == tif_file.split('.')[-1]
                      and ~np.any([x in tif_file for x in ['crop']])]

        es.crop_all(paths_list, self.saving_path, extent, overwrite=True, all_touched=True, verbose=True)  #

        for path in paths_list:
            try:
                os.remove(path)
            except:
                script = "sudo rm " + path
                subprocess.call(script, shell=True)
