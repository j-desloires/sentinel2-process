The purpose of this module is to download and preprocess Sentinel-2 data directly from Theia-land from given dates and tile name.

## Prerequisites

- Configure an account on Theia https://sso.theia-land.fr/theia/register/register.xhtml to configure credentials and pull https://github.com/olivierhagolle/theia_download. The folder _theia_download_ available on this git repository is an example of what you should get.
- Download OTB https://www.orfeo-toolbox.org/CookBook/Installation.html for data preprocessing.

## Environment configuration 

Using anaconda, create the environment using :

```
cd Sentinel2PP
conda env create -f environment.yml
conda activate Sentinel2PP
```

## Usage

Code to download and preprocess a tile for Land Use and Land Cover analysis is summarized into the script main.py. 

You must provide the following paths to execute a code from the following files :
- Folder theia_download obtained from the git repository pulled (cf prerequisites)
- A vector folder where you have :
    - Ground truth shapefile : Objects ID and labels to use for land cover training. The projection should be in your UTM (e.g _'espg:32631'_ for the tile _TC31J_ (France)).
    - Polygon of the Area of Interest : shapefile that we be used to cropping the images with respect to your study zone.
  
- Folder where Orfeo Toolbox is installed
- Path to save the output GEOTIFFS images




