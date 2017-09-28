#! /usr/bin/env python
#coding=utf-8
import string
import pymongo
from pymongo import MongoClient
import arcpy
import datetime
from arcpy.sa import *
from arcpy import env
import arcgisscripting
import os
import math
from numpy import *
import random
import numpy as np

def rmse(predict, obs):
    n = len(predict)
    arr_pre=array(predict)
    arr_obs=array(obs)
    dy = arr_pre - arr_obs
    return math.sqrt(sum(dy**2)/n) 

def txt_shp(in_path, out_path):
    gp = arcgisscripting.create()
    inSep = "."
    gp.CreateFeaturesFromTextFile(in_path, inSep, out_path, r"D:\article\solar_data\shp\china54.shp")
#    print 'shp : %s' %out_path

def shp_raster(in_path, out_path):
#    env.workspace=r"D:\article\solar_data\shp"
#    arcpy.env.extent=arcpy.Extent(69.75, 16.083, 135.2, 55.75)
    env.mask=r"D:\article\solar_data\shp\china54.shp"
    #arcpy.env.extent=arcpy.Extent(75.183, 16.083, 132.933, 53.483)
#    inFeatures = "prj_points.shp"
    field = "Shape.Z"
    cellSize=0.25
    kModelOrdinary = KrigingModelOrdinary("CIRCULAR")#, lagSize, majorRange, partialSill, nugget)
    arcpy.CheckOutExtension("Spatial")
    outKriging = Kriging(in_path, field, kModelOrdinary, cellSize)#, kRadius, outVarRaster)
    outKriging.save(out_path)
    print 'Kriging : %s' %out_path
def shp_raster_IDW(in_path, out_path):
    env.mask=r"D:\article\solar_data\shp\china54.shp"
    #arcpy.env.extent=arcpy.Extent(75.183, 16.083, 132.933, 53.483)
#    inFeatures = "prj_points.shp"
    field = "Shape.Z"
    cellSize=0.25
    arcpy.CheckOutExtension("Spatial")
    out_idw=Idw(in_path, field, cellSize)
    out_idw.save(out_path)

def extract_shp(point_shp, raster, i):
    res=[]
    outPointFeatures = r"D:\article\allsolar\extract\ep%s.shp" %i
    arcpy.CheckOutExtension("Spatial")
    ExtractValuesToPoints(point_shp, raster, outPointFeatures,"INTERPOLATE", "VALUE_ONLY")
    
    fields=['RASTERVALU']
    with arcpy.da.SearchCursor(outPointFeatures, fields) as cursor:
        for row in cursor:
            solar=u'{0}'.format(row[0])
            if solar==u'-9999.0':
                solar=u'0'            
            res.append(string.atof(solar))
    print 'extract: '+i
    return res

def modeling(mod_txt_path, i):
    out_shp=r"D:\article\allsolar\shp\m%s.shp" %i
    out_raster=r"D:\article\allsolar\raster\%s" %i
    txt_shp(mod_txt_path, out_shp)
    shp_raster_IDW(out_shp, out_raster)
    return out_raster
    
def validation(val_txt_path, mod_raster, i):
    obs=[]
    f=open(val_txt_path)
    for line in f.readlines():
        value=line.split()
        if(len(value)==4):
            obs.append(string.atof(value[3]))
    f.close()        
    val_shp=r"D:\article\allsolar\shp\vp%s.shp" %i
    txt_shp(val_txt_path, val_shp)
    mod=extract_shp(val_shp, mod_raster, i)
    rmse_val=rmse(mod, obs)
    return rmse_val

def write_txt(con, txt_path, name):
    path=r"%s\%s.txt" %(txt_path, name)
    end = 'END'
    f=open(path, 'w')
    f.write('Point\n' + con + end)
    f.close()
    return path

def test_val(val_txt_path,ext_path):
    obs=[]
    mod=[]
    f=open(val_txt_path)
    for line in f.readlines():
        value=line.split()
        if(len(value)==4):
            obs.append(string.atof(value[3]))
    f.close()        
    fields=['RASTERVALU']
    with arcpy.da.SearchCursor(ext_path, fields) as cursor:
        for row in cursor:
            solar=u'{0}'.format(row[0])
#            print type(solar)
            if solar==u'-9999.0':
                solar=u'0'
            mod.append(string.atof(solar))
    print mod
    rmse_val=rmse(mod, obs)
    return rmse_val

def kfold_test_kri(txt_path, tspan, int):
    """txt_path是包含solar的总的数据TXT文件，tspan是时间点生成文件名
    Int是插值类型，可选为kriging和idw"""
    k=10; allsite=[]
    file=r'%s\%s.txt' %(txt_path, tspan)
    f=open(file,'r')
    site_info=f.readlines()
    f.close()
    for info in site_info:
        value=info.split()
        if len(value)==4:
            allsite.append(info)
    random.shuffle(allsite)
    n=len(allsite)
    nlist = [int(n*i*1.0/k) for i in range(1,k+1)]
    nlist.insert(0, 0)
    rmse_list=[] 
    for i in range(k):
        mlist=''; vlist=''
        for j in range(n):
            content=allsite[j]
            ai=string.atoi(allsite[j].split(' ')[0])
#            if ai==n-1:
#                content=allsite[j]+'\n'
            if ((j<nlist[i])|(j>=nlist[i+1])):
                mlist=mlist + content
            else:
                vlist=vlist + content
        txt_path=r'D:\article\allsolar\txt'
        post_i=tspan+str(i)+int
        mod_path=write_txt(mlist, txt_path, 'm'+post_i)
        val_path=write_txt(vlist, txt_path, 'v'+post_i)
#        ext_path=r"D:\article\allsolar\extract\extract.shp"
        print mod_path, val_path
        mod_raster = modeling(mod_path, post_i)
        rmse_list.append(validation(val_path, mod_raster, post_i))
        np_rm=np.array(rmse_list)
    print rmse_list
    print np.average(rmse_list)


if __name__=='__main__':
#    kfold_test_kri(r"D:\article\allsolar", '2003_01_01', 'kri')
    
    k=10; allsite=[]
    f=open(r"D:\article\allsolar\2003_01_01.txt",'r')
    site_info=f.readlines()
    f.close()
    for info in site_info:
        value=info.split()
        if len(value)==4:
            allsite.append(info)
    random.shuffle(allsite)
    n=len(allsite)
    nlist = [int(n*i*1.0/k) for i in range(1,k+1)]
    nlist.insert(0, 0)
    rmse_list=[] 
    for i in range(k):
        mlist=''; vlist=''
        for j in range(n):
            content=allsite[j]
            ai=string.atoi(allsite[j].split(' ')[0])
#            if ai==n-1:
#                content=allsite[j]+'\n'
            if ((j<nlist[i])|(j>=nlist[i+1])):
                mlist=mlist + content
            else:
                vlist=vlist + content
        txt_path=r'D:\article\allsolar\txt'
        post_i='20030101'+str(i)+'idw'
        mod_path=write_txt(mlist, txt_path, 'm'+post_i)
        val_path=write_txt(vlist, txt_path, 'v'+post_i)
#        ext_path=r"D:\article\allsolar\extract\extract.shp"
        print mod_path, val_path
        mod_raster = modeling(mod_path, post_i)
        rmse_list.append(validation(val_path, mod_raster, post_i))
        np_rm=np.array(rmse_list)
    print rmse_list
    print np.average(rmse_list)
        
    
#    print test_val(val_path,ext_path)
#    obs=[]
#    f=open(val_path)
#    for line in f.readlines():
#        value=line.split()
#        if(len(value)==4):
#            obs.append(string.atof(value[3]))
#    f.close()
