The purpose of this module is to download and preprocess Sentinel-2 satellite imagery data directly from Theia-land from given dates and a tile name or bounding box.

## Prerequisites

- Configure an account on Theia https://sso.theia-land.fr/theia/register/register.xhtml to configure credentials and pull https://github.com/olivierhagolle/theia_download. The folder _theia_download_ available on this git repository is an example of what you should get.
- Download OTB https://www.orfeo-toolbox.org/CookBook/Installation.html for data preprocessing.

## Environment configuration 

Using anaconda, create the environment using :

```
cd sentinel2-process
conda env create -f environment.yml
conda activate sentinel2-process
```

## Usage

Code to download and preprocess a tile for Land Use and Land Cover analysis is summarized into the script [pipeline_land_cover.py](/examples/pipeline_land_cover.py). 

You must provide the following paths to execute a code from the following files :
- A vector folder where you have :
    - Ground truth shapefile : Objects ID and labels to use for land cover training. The projection should be in your UTM (e.g _'espg:32631'_ for the tile _TC31J_ (France)).
    - Polygon of the Area of Interest : shapefile that we be used to cropping the images with respect to your study zone.
  
- Folder where Orfeo Toolbox is installed
- Path to save the output GEOTIFFS images



## Description of the outputs

The tile is cropped with respect to the extent of a given shapefile (script main.py, with Haute-Garonne as example in the variable mask_data) :
- mask_R10_crop.tif : Binary cloud masks at 10 meters (int16)
- mask_R20_crop.tif : Binary cloud masks at 20 meters (int16)
- GFstack_X_crop.tif : Gap filled images with a given band X at 10 meters using linear interpolation (OTB) (float32)
- GFstack_SI_X_crop.tif : Gap filled images with a given band X at 20 meters, superimposed at 10 meters, using linear interpolation (OTB) (float32)
- Class_ID_crop.tif : ID of the class from the training dataset to predict for supervised task (script main.py) (int16)
- Object_ID_crop.tif : ID of the objects from the training dataset (int16)
- dates.csv : Csv file with acquisition dates that corresponds to the time index of each .tif image (except Class_ID and Objects_ID)

