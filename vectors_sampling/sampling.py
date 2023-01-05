import geopandas as gpd
import pandas as pd
import Sentinel2Theia.split_AOI as split_AOI
from shapely.geometry import *
import numpy as np
import shapely.wkt
import os


def random_sample_vector(vector_file, alpha, column_class="Class"):
    # An column 'index' for each grid cell
    gridded_hg = split_AOI.get_gridded_boundary(hg, 5000)
    gridded_hg = gridded_hg[gridded_hg.check]
    gridded_hg = gridded_hg[["index", "index_x", "index_y", "geometry"]]
    gridded_hg["cell_geometry"] = gridded_hg["geometry"]

    vector_file = gpd.sjoin(vector_file, gridded_hg, how="left", op="within")
    # Pivot table of the Class from ground truth data
    vector_file["Count"] = 1
    pivot = pd.pivot_table(
        vector_file[[column_class, "index", "Count"]],
        index="index",
        columns=[column_class],
        aggfunc="count",
    )

    pivot = pd.DataFrame(pivot)
    pivot.columns = [k[1] for k in pivot.columns]
    pivot.reset_index(inplace=True)
    pivot["index"] = pivot["index"].astype(int)

    res = []
    for index_grid in pivot["index"]:
        for Class in list(vector_file[column_class].unique()):
            N = np.sum(pivot[column_class])
            theoretical_number = N / len(pivot["index"].unique()) * alpha
            if (
                vector_file.loc[
                    (vector_file["index"] == index_grid)
                    & (vector_file[column_class] == Class)
                ].shape[0]
                > theoretical_number
            ):
                sample = vector_file.loc[
                    (vector_file["index"] == index_grid)
                    & (vector_file[column_class] == Class)
                ].sample(int(theoretical_number + 1))
            else:
                sample = vector_file.loc[
                    (vector_file["index"] == index_grid)
                    & (vector_file[column_class] == Class)
                ]

            res.append(sample)

    output = pd.concat(res, axis=0)

    return output
