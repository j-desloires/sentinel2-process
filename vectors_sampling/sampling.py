import geopandas as gpd
import pandas as pd
import Sentinel2Theia.split_AOI as split_AOI
from shapely.geometry import *
import numpy as np
import shapely.wkt
import os


def random_sample_vector(vector_file, alpha, column_index = 'index', column_class = 'Class'):
    #An column 'index' for each grid cell
    vector_file = split_AOI.get_gridded_boundary(vector_file, cell_size=5000)
    #Pivot table of the Class from ground truth data
    vector_file['Count'] = 1
    pivot = pd.pivot_table(vector_file[[column_class,column_index,'Count']],
                           index = column_index,
                           columns = [column_class],
                           aggfunc='count')

    pivot = pd.DataFrame(pivot)
    pivot.columns = [k[1] for k in pivot.columns]
    pivot.reset_index(inplace = True)
    pivot[column_index] = pivot[column_index].astype(int)

    res = []
    for index_grid in pivot[column_index]:
        for Class in list(vector_file[column_class].unique()):
            N = np.sum(pivot[column_class])
            theoretical_number = N / len(pivot[column_index].unique()) * alpha
            if vector_file.loc[(vector_file[column_index] == index_grid) & (vector_file[column_class] == Class)].shape[0] > theoretical_number:
                sample = vector_file.loc[(vector_file[column_index] == index_grid) & (vector_file[column_class] == Class)].sample(int(theoretical_number+1))
            else:
                sample = vector_file.loc[(vector_file[column_index] == index_grid) & (vector_file[column_class] == Class)]

            res.append(sample)

    output = pd.concat(res,axis = 0)

    return output