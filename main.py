import sys

sys.path.insert(0, '/home/johann/Topography/Sentinel2Theia/')
sys.path.append('../')  #

import os
import pandas as pd
import numpy as np
import unzip_data as unzip_data
import stack_data as stack_data
import gap_filling as gap_filling
import superimpose as superimpose
import vegetation_indices as vegetation_indices
import training_set as training_set
import utils as utils

###Input files (see readme)
#Orfeo Toolbox
path = '/media/DATA/johann/PUL/TileHG/'
os.chdir(path)
otb_path = '/home/johann/OTB-7.2.0-Linux64/bin'
os.path.exists(otb_path)
##Theia folder pulled
folder_theia = './theia_download'
os.path.exists(folder_theia)
#Folder to save images preprocessed
path_output = './Sentinel2/GEOTIFFS'
os.path.exists(path_output)
#Input vector for training process
vector_path = './data/DATABASE_SAMPLED/DATABASE_SAMPLED.shp'
os.path.exists(vector_path)
#Polygon of the Area of Interest
mask_data = './data/HG_TILE_INTERSECTION/INTERSECTION_TILE_DEPARTMENT/intersection_hg_tile.shp'
os.path.exists(mask_data)
mask_feature = 'DN'

band_names = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12']

#https://satpy.readthedocs.io/en/stable/data_download.html

##################################################################################
#Download Sentinel-2 images

download = unzip_data.TheiaDownload(folder_theia,
                                    tile_name="31TCJ",
                                    start_date="2017-01-01",
                                    end_date="2017-12-31")

download.download_data()
download.unzip_data()

##################################################################################
#Rasterize labels using a reference file from Sentinel-2 folders
reference_file = utils.get_random_file(folder_theia, band_name='B2')

rasterize_labels = stack_data.RasterLabels(vector_path=vector_path,
                                           reference_file=reference_file,
                                           extent_vector=mask_data,
                                           saving_path=path_output,
                                           ObjectID='Object_ID',
                                           LabelID='Class_ID')

rasterize_labels.rasterize_labels()

#GEOTIFFS concatenation cropped according to the AOI
concatenate_images = stack_data.StackFoldersSentinel2(extent_vector=mask_data,
                                                      bands=band_names,
                                                      res_bands=[10, 10, 10, 20, 20, 20, 10, 20, 20, 20],
                                                      saving_path=path_output,
                                                      folder_theia=folder_theia,
                                                      name_mask_feature='DN')

concatenate_images.extract_images_folder()
concatenate_images.crop_images()

###############################################################################################################
#Cloud masking interpolation
gap_filling.GapFill(otb_path,
                   path_output,
                   bands=['B2', 'B3', 'B4', 'B8'],
                   res=10)

gap_filling.GapFill(otb_path,
                   path_output,
                   bands=['B5', 'B6', 'B7', 'B8A', 'B11', 'B12'],
                   res=20)

#Put 20 meters images into 10 meters

workflow_si = superimpose.GFSuperImpose(otb_path,
                                        path_output,
                                        bands_20=['B5', 'B6', 'B7', 'B8A', 'B11', 'B12'])
workflow_si.execute_superimpose()


##################################################################################################################
#CSubset time series ; date file automatically saved into this file in the previous steps

dates = pd.read_csv('./Sentinel2/GEOTIFFS/dates.csv')

features_subset = band_names.copy()
features_subset.extend(['stack_10m_crop','stack_10m_crop'])
gap_filling.subset_time_series(path_output, features_subset, '2019')

##################################################################################################################
#Compute NDVI and NDWI

vis = vegetation_indices.VegetationIndices(saving_path=path_output)
vis.compute_VIs()

##################################################################################################################
#Built the training set for given features
features = ['B2', 'B3', 'B4', 'NDVI','NDWI']
#this file has been automatically create during StackFoldersSentinel2()
dates = pd.read_csv(os.path.join(path_output, 'dates.csv'))
#Path to save the output training set
path_ts = '/media/DATA/johann/PUL/TileHG/FinalDBPreprocessed'
#Random geotiff file created from the steps above that will be used as geo reference
reference_file = os.path.join(path_output, 'GFstack_B2_crop_2019.tif')

output_files = training_set.TrainingSet(path_images=path_output,
                                        band_names=features,
                                        dates=dates,
                                        saving_path=path_ts,
                                        reference_file=reference_file,
                                        ObjectID=os.path.join(path_output, 'Object_ID_crop.tif'),
                                        LabelID=os.path.join(path_output, 'Class_ID_crop.tif'))

output_files.prepare_training_set()
