import os
import pandas as pd
import unzip_data as unzip_data
import stack_data as stack_data
import GapFilling as GapFilling
import GFSuperImpose as GFSuperImpose
import VegetationIndices as VegetationIndices
import training_set as training_set

otb_path = '/home/johanndesloires/Documents/OTB-7.2.0-Linux64/bin'
folder_theia = '/home/johanndesloires/Documents/theia_download'
os.path.exists(folder_theia)
path_output = '/home/johanndesloires/Documents/Sentinel2/GEOTIFFS/TEST'

vector_path = './Vectors/DATABASE_SAMPLED/DATABASE_SAMPLED.shp'
mask_data = './Vectors/INTERSECTION_TILE_DEPARTMENT/INTERSECTION_TILE_DEPARTMENT.shp'
mask_feature = 'DN'

##################################################################################

download = unzip_data.TheiaDownload(folder_theia,
                                    tile_name="T31TCJ",
                                    start_date="2018-11-20",
                                    end_date="2018-12-01")

download.download_data()
download.unzip_data()

##################################################################################
# Get GEOTIFFS from Sentinel-2 and Theia

reference_file = stack_data.GetRandomTheiaFile(folder_theia, band_name='B2')

rasterize_labels = stack_data.RasterLabels(vector_path=vector_path,
                                           reference_file=reference_file,
                                           extent_vector=mask_data,
                                           saving_path=path_output,
                                           ObjectID='Class_ID',
                                           LabelID='Label_Code')

rasterize_labels.rasterize_labels()

concatenate_images = stack_data.StackFoldersSentinel2(extent_vector=mask_data,
                                                      bands=['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11',
                                                             'B12'],
                                                      res_bands=[10, 10, 10, 20, 20, 20, 10, 20, 20, 20],
                                                      saving_path=path_output,
                                                      folder_theia=folder_theia,
                                                      name_mask_feature='DN')

concatenate_images.ExtractImagesFolder()
concatenate_images.CropImages()

###############################################################################################################

GapFilling.GapFill(otb_path,
                   path_output,
                   bands=['B2', 'B3', 'B4', 'B8'],
                   res=10)

GapFilling.GapFill(otb_path,
                   path_output,
                   bands=['B5', 'B6', 'B7', 'B8A', 'B11', 'B12'],
                   res=20)

GFSuperImpose.GFSuperImpose(otb_path,
                            path_output,
                            bands_20=['B5', 'B6', 'B7', 'B8A', 'B11', 'B12'])

##################################################################################################################

vis = VegetationIndices.VegetationIndices(saving_path=path_output,
                                          band_names=['B2', 'B4', 'B8', 'B11'])

vis.compute_VIs()

##################################################################################################################

features = ['B2', 'B3', 'B4', 'NDVI', 'GNDVI', 'NDWI']
dates = pd.read_csv(os.path.join(path_output, 'dates.csv'))
path_ts = '/home/johanndesloires/Documents/Sentinel2/FinalDB'
reference_file = os.path.join(path_output, 'GFstack_B2_crop.tif')

output_files = training_set.TrainingSet(path_images=path_output,
                                        band_names=features,
                                        dates=dates,
                                        saving_path=path_ts,
                                        reference_file=reference_file,
                                        ObjectID=os.path.join(path_output, 'Class_ID_crop.tif'),
                                        LabelID=os.path.join(path_output, 'Label_Code_crop.tif'))

output_files.prepare_training_set()
