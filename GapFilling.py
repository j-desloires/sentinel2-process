#####################################################################################################
#####################################################################################################
# must do first : download .run file on otb
# then ' chmod +x /home/s999379/OTB-7.2.0-Linux64.run'
# then /home/s999379/OTB-7.2.0-Linux64.run
# then go to the directory and do source otbenv.profile

import subprocess
import os



def GapFill(otb_path,path_root,bands = ['B2', 'B3', 'B4', 'B8'], res = 10):
    '''
    Gapfilling given a folder outputs from the script stack_data.py.
    Args:
        path_root (str): Path where .tif files to gap fill are stored
        bands (list of str) : bands selected with same resolution to gap fill
        res int : resolution of the bands defined in the parameter bands
    '''

    for band in bands:
        file = os.path.join(path_root, 'stack_' + band + '_crop.tif')

        mask = os.path.join(path_root, 'stack_' + str(res) + 'm_crop.tif')
        out = os.path.join(path_root, 'GFstack_' + band + '_crop.tif')

        cmd = [os.path.join(otb_path,"otbcli_ImageTimeSeriesGapFilling"),
               "-in", "%s" % file,
               "-mask", "%s" % mask,
               "-out", "%s" % out,
               "-comp", "1",
               "-it", "linear",
               "-ram", "8000",
               ]

        shell = False
        subprocess.call(cmd, shell=shell)
        os.remove(file)


#GapFill(bands = ['B2','B3','B4','B8'], res = 10) #,
#GapFill(bands =['B5', 'B6', 'B7', 'B8A','B11','B12'], res=20)





