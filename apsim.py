#! /usr/bin/env python
#coding=utf-8
import types
import numpy as np
import xml_modify
import os
import sys
import subprocess

basedir=r'd:/apsim'
def apsim_res(X):
#    strX=[]
#    for x in X:
#        if(type(x) != types.StringType):
#            strX.append(str(x))
#            print 'asd'
#        else:
#            strX.append(x)
    
    model=r'%s/rice.apsim' %basedir
    oryza=r'E:\Program Files (x86)\Apsim78-r3867\Model\Oryza.xml'
    outfile=r'%s/Rice Output.out' %basedir
    pm=['DVRJ','DVRP','DVRR']
    po=['SummerCona','SummerU'] #,'WinterCona','WinterU']
    m_cmd='start Apsim.exe && d: && cd /apsim && apsim rice.apsim'
    xml_modify.mod_apsim(oryza,'Model/experimental',pm,X)
    os.popen(m_cmd)
#    pro=subprocess.Popen(m_cmd,  shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#    pro.wait()
    simulation=read_res_file(outfile) #输出要修改readfile函数
    return simulation
    
def read_res_file(filename):
    sim=[]
#    days=[]
    wso=[]
    wagt=[]
    rlai=[]
    wst=[]
    f = open(filename, 'r')
    lines = f.readlines()
    f.close()
    for line in lines:
        if line.split()[1]=='2005':
            wso.append(float(line.split()[6]))
#            days.append(float(line.split()[3]))
            wagt.append(float(line.split()[5]))
            rlai.append(float(line.split()[7]))
            wst.append(float(line.split()[10]))
#        dat = line.split()[0]
#        if  dat == '06/08/2005' or dat == '05/09/2005':
#            sim.append(float(line.split()[7]))
##    days=np.array(days)
#    sim.append(np.max(days)/50)
    wso=np.array(wso);
#    days=np.array(days);
    wagt=np.array(wagt);
    rlai=np.array(rlai);
    wst=np.array(wst)
    
    sim.append(np.max(wso))
#    sim.append(np.max(days))
    sim.append(np.max(wagt))
    sim.append(np.max(rlai))
    sim.append(np.max(wst))      
    return sim

if __name__=='__main__':
    v1=[8.39338562e-04 ,  5.29015246e-04 ,  8.48562505e-04 ,  1.85326201e-03,
    3.74762099e+00 ,  4.15696750e+00]

#    v2=[ 0.00070195  ,  7.58e-04 , 0.00067345 , 0.00253987,
#   2.59737176e+00 ,  4.15402237e+00]
    v2=[ 0.00070195  ,0.00067345 , 0.00253987]

    print apsim_res(v2)
