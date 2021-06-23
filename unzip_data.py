import zipfile
import os
import numpy as np
import subprocess
import shutil

class TheiaDownload:

    def __init__(self,folder_theia,
                 tile_name = None,
                 bbox = None,
                 orbit = 51,
                 start_date = "2018-12-01", end_date = "2020-01-30"):
        '''
        Function to download .zip images from theia. As we may have troubles, the program tries twice to check the folders obtained.
        Please relaunch the function as long as you are not downloading anymore files
        Args:
            folder_theia (str): Path where theia_download git repository.
            tile_name (str): Name of the file to download
            bbox (list): list of bounding box [xmin, ymin, xmax, ymax] if  tile is None
            start_date (str) : yyyy-mm-dd starting date to download
            end_date (str) : yyyy-mm-dd ending date
        '''
        self.folder_theia = folder_theia
        self.start_date = start_date
        self.end_date = end_date
        self.tile_name = tile_name
        self.bbox = bbox
        self.orbit = orbit
        #os.chdir(self.folder_theia)

    def download_data(self):

        try:
            if self.tile_name is not None:
                cmd = ['python3',os.path.join(self.folder_theia,'theia_download.py'),
                       "-t", "%s" % self.tile_name,
                       "-c", "%s" % "SENTINEL2",
                       "-w", "%s" % self.folder_theia,
                       "-a", "%s" % os.path.join(self.folder_theia,"config_theia.cfg"),
                       "-d", "%s" % self.start_date,
                       "-f", "%s" % self.end_date,
                       "-r", "%s" % self.orbit]
            else:
                cmd = ['python3',os.path.join(self.folder_theia,'theia_download.py'),
                       "--lonmin", "%s" % self.bbox[0],
                       "--latmin", "%s" % self.bbox[1],
                       "--lonmax", "%s" % self.bbox[2],
                       "--lonmax", "%s" % self.bbox[3],
                       "-c", "%s" % "SENTINEL2",
                       "-w", "%s" % self.folder_theia,
                       "-a", "%s" % os.path.join(self.folder_theia,"config_theia.cfg"),
                       "-d", "%s" % self.start_date,
                       "-f", "%s" % self.end_date,
                       "-r", "%s" % self.orbit]

            shell = False  # if run through terminal using python3 GapFilling.py
            subprocess.Popen(cmd, shell=shell)

        except:
            raise ValueError('Error in the cmd')

    def unzip_data(self):
        files = os.listdir(self.folder_theia)
        zip_file = [k for k in files if np.any([x in k for x in ['.zip','.tmp']])]

        for zipf in zip_file:
            path = os.path.join(self.folder_theia, zipf)

            try:
                with zipfile.ZipFile(path, 'r') as zip_ref:
                    zip_ref.extractall(self.folder_theia)
                os.remove(path)
                path_new_folder = [k for k in os.listdir(self.folder_theia)
                                   if np.all([x in k.split('_') for x in zipf.split('_')[:-1]])]

                path_new_folder = os.path.join(self.folder_theia,path_new_folder[0])

                if len(os.listdir(path_new_folder)) < 25:
                    os.rmdir(path_new_folder)
                    self.download_data()
                    try :
                        with zipfile.ZipFile(path, 'r') as zip_ref:
                            zip_ref.extractall(self.folder_theia)
                    except:
                        os.rmdir(path_new_folder)

            except:
                print('CANNOT UNZIP')
                os.remove(path)
                self.download_data()
                try :
                    with zipfile.ZipFile(path, 'r') as zip_ref:
                        zip_ref.extractall(self.folder_theia)
                except:
                    os.rmdir(path)


