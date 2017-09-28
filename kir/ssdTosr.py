#! /usr/bin/env python
# coding=utf-8

import math
import os
import time

# day of year
def doy(dt):
    sec = time.mktime(dt.timetuple())
    t = time.localtime(sec)
    return t.tm_yday


# earth-sun distance
def dr(doy):
    return 1 + 0.033 * math.cos(2 * math.pi * doy / 365)


# declination
def dec(doy):
    return 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)

# sunset hour angle
def ws(lat, dec):
    x = 1 - math.pow(math.tan(lat), 2) * math.pow(math.tan(dec), 2)
    if x < 0:
        x = 0.00001
    # print x
    return 0.5 * math.pi - math.atan(-math.tan(lat) * math.tan(dec) / math.sqrt(x))

def Rs(doy, n, lat):
    """n is sunshine duration"""
    lat = lat * math.pi / 180.
    a = 0.25
    b = 0.5
    d = dec(doy)
    w = ws(lat, d)
    N = 24 * w / math.pi
    # Extraterrestrial radiation for daily periods
    ra = (24 * 60 * 0.082 * dr(doy) / math.pi) * (
        w * math.sin(lat) * math.sin(d) + math.cos(lat) * math.cos(d) * math.sin(w))
    return (a + b * n / N) * ra

def writeToTxt(list_name,file_path):
    try:
        fp = open(file_path,"w+")
        for item in list_name:
            fp.write(str(item)+"\n")
        fp.close()
    except IOError:
        print("fail to open file")

if __name__ == "__main__":
    f = open(r"C:\Users\Administrator\Desktop\yintan.txt")
    ssd = []
    yday = []
    LFs = ['\r\n', '\n\r', '\r', '\n']
    for line in f:
        strLine = line
        for LF in LFs:
            if LF in line:
                strLine = line.split(LF)[0]
                break
        lineList = strLine.split('\t')
        ssd.append(lineList[1])
        yday.append(lineList[0])

    lat = 31.55
    data_sr = []
    for i in range(len(yday)):
        sr = round(Rs(float(yday[i]), float(ssd[i]), lat * math.pi / 180.), 1)
        data_sr.append(sr)

    file_path = r'C:\Users\Administrator\Desktop\sr_yintan.txt'
    writeToTxt(data_sr,file_path)