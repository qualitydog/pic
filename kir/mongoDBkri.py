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
import ssdToSrTest as ss2so
import math

def get_file_name(date_time):
    name=str(date_time).split(' ')[0]
    name=name.replace('-','_')
    return name
    
def get_solar(store_path, tspan, site_id, db):
#    ctime=datetime.datetime.strptime(t_str, '%Y-%m-%d %H:%M:%S')
    file_name=r'%s\txt\%s.txt' %(store_path, get_file_name(tspan))
#    file_name=r'%s\%s.txt' %(storePath, get_file_name(tspan))
    meta_line='Point\n'
    con=''
    i=0
    metatype=storePath.split('\\')[-1]
    print metatype 
    typedict={'hummin':'Hum_Min','humavg':'Hum_Avg','sol':'Solar','ssd':'Solar'}
    for sll in site_id:
        id=sll.split(',')[0]
        lat=sll.split(',')[1]
        lon=sll.split(',')[2].split('\n')[0]
#        print id,lat,lon
        cursor=db.DataValuesM.find({"SiteID":string.atoi(id),"Date":tspan})
        for content in cursor:
#            print content
            if metatype == 'sol' and 'Solar' not in content:
                continue
                       
            solindex=typedict[metatype]
            sol=content[solindex]
            if sol=='null' or abs(string.atof(sol)-3276.6)<0.01: #abs(string.atof(sol)-3276.6)<0.01:
                continue
            if metatype == 'humavg' and abs(string.atof(sol)-0)<0.001:
                continue 
            if metatype == 'sol':
                sol=round(ss2so.Rs(ss2so.doy(tspan), string.atof(sol), string.atof(lat) * math.pi / 180),2)
            con=con+str(i)+' '+lon+' '+lat+' '+str(sol)+'\n'
        i=i+1
#    print con
    f=open(file_name,'w')
    f.write(meta_line)
    f.write(con)
    f.write('END')
    f.close()
    
def txt_to_shp(root_path, date_time):
    shp_name=get_file_name(date_time)
    outFile=r"%s\shp\%s.shp" %(root_path,shp_name)
    gp = arcgisscripting.create()
    #Set up inputs to tool
    inTxt = r"%s\txt\%s.txt" %(root_path,shp_name)
    inSep = "."
    #Run tool
    gp.CreateFeaturesFromTextFile(inTxt, inSep, outFile, r"D:\article\solar_data\shp\china54.shp")
#    print 'shapefile %s done!' %shp_name

def shp_to_raster(root_path, date_time):
    shp_name=get_file_name(date_time)
    env.workspace=r"%s\shp" %root_path
    arcpy.env.extent=arcpy.Extent(69.75, 16.083, 135.2, 55.75) #指定的范围
#    env.mask=r"D:\article\solar_data\shp\china54.shp"
#    arcpy.env.extent=arcpy.Extent(75.183, 16.083, 132.933, 53.483)
    inFeatures = "%s.shp" %(shp_name)
    field = "Shape.Z"
    cellSize = 0.25
#    lagSize = 0.44
#    majorRange = 2.7
#    partialSill = 0.011
#    nugget = 0
    kModelOrdinary = KrigingModelOrdinary("CIRCULAR")#, lagSize, majorRange, partialSill, nugget)
    arcpy.CheckOutExtension("Spatial")
    outKriging = Kriging(inFeatures, field, kModelOrdinary, cellSize)
    raster_path=r'%s\raster0\%s.img' %(root_path,shp_name)
#    if os.path.exists(raster_path)==False:
#        os.mkdir(raster_path)
#    raster_path=r'%s\raster\%s\%s' %(root_path,shp_name,shp_name)
    outKriging.save(raster_path)
#    print 'krging raster %s done!' %shp_name

def settle_zero(workPath, tspan): #1976.1.22
    filename=get_file_name(tspan)
    filenamein=r"%s\raster0\%s.img" %(workPath,filename)
    out_path=r"%s\raster\%s.img" %(workPath,filename)
    arcpy.CheckOutExtension("Spatial")
    exp='Con("%s" < 0,0,"%s")' %(filenamein, filenamein)
    arcpy.gp.RasterCalculator_sa(exp, out_path)
    print '%s has settle 0!' %filename

def Time_inter_raster(root_path, stime, etime, site_id, db):
    stime=datetime.datetime.strptime(stime, '%Y-%m-%d %H:%M:%S')
    etime=datetime.datetime.strptime(etime, '%Y-%m-%d %H:%M:%S')
    tspan=stime
    while tspan<etime:
        get_solar(root_path, tspan, site_id, db)
        txt_to_shp(root_path, tspan)
        shp_to_raster(root_path,tspan)
        settle_zero(root_path, tspan)
        tspan=tspan+datetime.timedelta(days=1)
#    print "from %s to %s krging complete!" %(stime,etime)
    
def update_solar(db, solar_root):
    for year in range(1961,2014):
        for mon in range(1,13):
            str_mon=''
            if mon<10:
                str_mon='0'+str(mon)
            else:
                str_mon=str(mon)
            solar_path=r"%s\SURF_CLI_CHN_MUL_DAY-SSD-14032-%s.TXT" %(solar_root, str(year)+str_mon)
            f=open(solar_path)
            for line in f.readlines():
                items=line.split()
                str_date="%s-%s-%s 0:0:0" %(items[4],items[5],items[6])
                tspan=datetime.datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S')
                id=items[0]
                solar=items[7]
                if solar=='32766':
                    solar="null"
                    print 'site %s %s updated!' %(id, str(year)+str_mon)
                    print line
                try:
                    db.DataValuesM.update({"SiteID":string.atoi(id),"Date":tspan},{'$set':{"Solar":(string.atof(solar)*0.1)}})
                except Exception,e:
                    print Exception, ':', e
            f.close()
if __name__=='__main__':
    
    client=MongoClient("localhost",27017)
    db=client["meteorData"]

    storePath=r"D:\article\7679\ssd"
    site_path=r'D:\article\solar_data\site.txt'
    f=open(site_path,'r')
    site_id=f.readlines()
    f.close()
    #'1980-1-1 0:0:0' '1993-9-9 0:0:0'  '2007-5-19 0:0:0' '2014-1-1 0:0:0'
#    stime='1976-1-1 0:0:0'
#    etime="1976-2-1 0:0:0"
    stime='1976-1-1 0:0:0'
    etime="1980-1-1 0:0:0"

    #站点查询
#    print storePath.split('\\')[-1]
    Time_inter_raster(storePath, stime, etime, site_id, db)
    
    
#    tspan=datetime.datetime.strptime('1980-1-1 0:0:0', '%Y-%m-%d %H:%M:%S')
#    get_solar(r"D:\article", tspan, site_id, db)
#    get_solar(r"D:\article\solar_data", tspan, site_id, db)
    
#    update_solar(db, r'D:\article\SSD61_13')
    
#    db.DataValuesM.update({"SiteID":50246,"Date":tspan},{'$set':{"Solar":"null"}})
#    db.DataValuesM.update({"SiteID":55299,"Date":tspan},{'$set':{"Solar":6.5}})
#    cursor=db.DataValuesM.find({"SiteID":55299,"Date":tspan})
#    for c in cursor:
#        print c["Solar"]

#    for sll in site_id:
#        id=sll.split(',')[0]
#        lat=sll.split(',')[1]
#        lon=sll.split(',')[2].split('\n')[0]
##        print id,lat,lon
##        if id=='50247':
#        cursor=db.DataValuesM.find({"SiteID":string.atoi(id),"Solar":0,"Date":{'$gt':tspan}})
##        cursor=db.DataValuesM.find({"SiteID":string.atoi(id),"Date":tspan})
#        
##        print 'unfind'
#        print id, cursor.count()
    
#    
#    
    print 'completed!'
