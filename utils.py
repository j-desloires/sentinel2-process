from osgeo.gdal import *
from osgeo import gdal, ogr

import numpy as np

import gdal
import os


def Open_array_info(filename=''):
    """
    Opening a tiff info, for example size of array, projection and transform matrix.
    Keyword Arguments:
    filename -- 'C:/file/to/path/file.tif' or a gdal file (gdal.Open(filename))
        string that defines the input tiff file or gdal file
    """
    global geo_out, proj, size_X, size_Y
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
        Data = Data.astype(np.uint16)

    return Data


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
    os.remove(Dir_Raster_end)
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
