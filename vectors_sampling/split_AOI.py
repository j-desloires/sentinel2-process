import geopandas as gpd
import sentinelhub
import numpy as np
from sentinelhub import BBoxSplitter
from shapely.geometry import Polygon, MultiPolygon, Point
import matplotlib.pyplot as plt


def get_gridded_boundary(shapefile, cell_size=1000):
    # Get its bounds from new projected
    bbox = shapefile.geometry.bounds
    # Get the bounding box of the area
    area_bbox = sentinelhub.BBox(bbox=[(bbox['minx'], bbox['miny']), (bbox['maxx'], bbox['maxy'])],
                                 crs=sentinelhub.CRS.WGS84)

    # Convert into UTM projection (in meters)
    area_bbox = sentinelhub.geo_utils.to_utm_bbox(area_bbox)
    shapefile = shapefile.to_crs(str(area_bbox.crs))
    bbox = shapefile.geometry.bounds

    ###Build the grid
    def get_shape_area(bbox, distance=cell_size):
        ##Would like division into 100*100 patches
        # Number of vertical patch xmin - xmax
        c1 = int((bbox['maxx'] - bbox['minx']) / distance)  # + int((bbox['maxx'] - bbox['minx'])%distance)
        # Number of horizontal patch xmin - xmax
        c2 = int((bbox['maxy'] - bbox['miny']) / distance)  # + int((bbox['maxy'] - bbox['miny'])%distance)
        return ((c1, c2))

    split_shape = get_shape_area(bbox, distance=cell_size)

    bbox_splitter = BBoxSplitter([area_bbox.geometry], area_bbox.crs, split_shape)

    bbox_list = np.array(bbox_splitter.get_bbox_list())
    info_list = np.array(bbox_splitter.get_info_list())

    # Prepare info of selected EOPatches
    geometry = [Polygon(bbox.get_polygon()) for bbox in bbox_list]
    # idxs = [info['index'] for info in info_list]
    idxs_x = [info['index_x'] for info in info_list]
    idxs_y = [info['index_y'] for info in info_list]

    gdf = gpd.GeoDataFrame({'index_x': idxs_x, 'index_y': idxs_y},
                           crs=shapefile.crs,
                           geometry=geometry)
    gdf.reset_index(inplace=True)

    # Get the intersection of the contours from shapefile with the grid
    gdf['results'] = gdf.geometry.apply(lambda x: shapefile.geometry.intersection(x))
    # Construct a boolean associated
    booleans = np.array([(1 - k.is_empty) for k in gdf.results])
    gdf['check'] = booleans
    valid_obs = gdf.check.astype(bool)
    gdf = gdf.drop(['check'], axis = 1)

    return gdf[valid_obs]
