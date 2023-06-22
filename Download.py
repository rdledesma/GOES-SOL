

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  5 09:41:36 2023

@author: ruben dario ledesma
@email: rdledesma@exa.unsa.edu.ar
"""

# Required modules
import os                                       # Miscellaneous operating system interfaces
from osgeo import osr                           # Python bindings for GDAL
from osgeo import gdal                          # Python bindings for GDAL
from goes2go import GOES                        # Python package that makes it easy to find and download the files you want to your local computer with some additional helpers to look at and understand the data.

class Downloader:
    def __init__(self, start, end, domain, bands, satellite, product, save_dir ):
        
        self.G = GOES(
            satellite=satellite, 
            product=product, 
            bands = [2],
            domain=domain)
        self.data = self.G.timerange(start=start, end=end, download=False)
        
        for item in range(len(self.data)):
            file = self.G.timerange(start= self.data.iloc[item].start, 
                                    end=self.data.iloc[item].end, download=True,
                                    save_dir = save_dir
                                    )
            path = file.iloc[0].file 
            self.recortar(path)
        
        
            
    def recortar(self, path):
        
        
        
        
        
        
        var = 'CMI'
        img = gdal.Open(f'NETCDF:{path}:' + var)
        
        
        try:
            metadata = img.GetMetadata()
            scale = float(metadata.get(var + '#scale_factor'))
            offset = float(metadata.get(var + '#add_offset'))
            undef = float(metadata.get(var + '#_FillValue'))
            dtime = metadata.get('NC_GLOBAL#time_coverage_start')
            ds = img.ReadAsArray(0, 0, img.RasterXSize, img.RasterYSize).astype(float)
            
            # Read the original file projection and configure the output projection
            source_prj = osr.SpatialReference()
            source_prj.ImportFromProj4(img.GetProjectionRef())
            target_prj = osr.SpatialReference()
            target_prj.ImportFromProj4("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
            
            # Reproject the data
            GeoT = img.GetGeoTransform()
            driver = gdal.GetDriverByName('MEM')
            raw = driver.Create('raw', ds.shape[0], ds.shape[1], 1, gdal.GDT_Float32)
            raw.SetGeoTransform(GeoT)
            raw.GetRasterBand(1).WriteArray(ds)
            raw.SetMetadata({'time_coverage_start': dtime}) 
        	     
            
            extent = [-70.0, -40.0, -50.0, -20.0] # Min lon, Max lon, Min lat, Max lat
            
            # Define the parameters of the output file  
            options = gdal.WarpOptions(format = 'netCDF', 
    		srcSRS = source_prj, 
    		dstSRS = target_prj,
    		outputBounds = (extent[0], extent[3], extent[2], extent[1]), 
    		outputBoundsSRS = target_prj, 
    		outputType = gdal.GDT_Float32, 
    		srcNodata = undef, 
    		dstNodata = 'nan', 
    		xRes = 0.02, 
    		yRes = 0.02, 
    		resampleAlg = gdal.GRA_NearestNeighbour)
            gdal.Warp(f'{var}/{dtime}.cn', raw, options=options)
        except Exception:
            pass
        
        
        os.remove(path)
        
        

dw = Downloader(start = '2020-11-01 08:00',
                end = '2020-11-30 23:59', 
                domain='F', 
                bands = [2], 
                satellite = 16, 
                product='ABI-L2-CMIP',
                save_dir = '.').data
        
        