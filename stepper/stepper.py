#!/usr/bin/python

#-*- encoding:utf-8 -*-
import tornado.web
import tornado.ioloop
from tornado.ioloop import IOLoop, PeriodicCallback
import tornado.process
import tornado.template
import tornado.httpserver
import json
import sys
import serial.tools.list_ports as ls
import os,time
import serial
import textwrap
import binascii
i=0
def encrypt(string, length):
    a=textwrap.wrap(string,length)
    return a


from configparser import ConfigParser
os.chdir(os.path.dirname(os.path.realpath(__file__)))
configfile_name = "config.ini"
if not os.path.isfile(configfile_name):
    # Create the configuration file as it doesn't exist yet
    cfgfile = open(configfile_name, 'w')
    # Add content to the file
    Config = ConfigParser()
    Config.add_section('api')
    Config.set('api', 'port', '3018')
    Config.add_section('stepper')
    Config.set('stepper', 'sr_port', 'COM7')
    Config.set('stepper', 'baudrate', '9600')
    Config.set('stepper', 'timeout', '1')
    Config.add_section('data')
    Config.set('data', 'start', '01 88 01 00 00 00 00 00 8A') # clk1
    Config.set('data', 'ror', '01 01 00 00 00 00 C3 50 15') # clk1 50000
    Config.set('data', 'rol', '01 02 00 00 00 00 C3 50 16') # anticlk
    Config.set('data', 'stop', '01 03 00 00 00 00 00 00 04') # stop
    Config.write(cfgfile)
    cfgfile.close()
configReader = ConfigParser()
configReader.read('config.ini')
sr_port = configReader['stepper']['sr_port']
baudrate = configReader['stepper'].getint('baudrate')
sr_timeout = configReader['stepper']['timeout']
api_port = configReader['api'].getint('port')

print(sr_port,baudrate)
def checksum2561(_str):
    return reduce(lambda x,y:x+y, map(ord, _str)) % 256
def ROR(dt):
    print(hex(dt))
    data1 = hex(dt)[2:]
    if(len(data1) == 2):
        datal = data1
        datah = ''
    elif(len(data1)<4):
        datal = data1[1:]
        datah = '0'+data1[:1]
    else:
        datal = data1[2:]
        datah = data1[:2]
    final = ' '+datah+' '+datal+' 01'
    return final
def ROL(dt):
    data1 = hex(dt)[2:]
    if(len(data1) == 2):
        datal = data1
        datah = ''
    elif(len(data1)<4):
        datal = data1[1:]
        datah = '0'+data1[:1]
    else:
        datal = data1[2:]
        datah = data1[:2]
    final = ' '+datah+' '+datal+' 01'
    return final
def stepper(data):
    os.system('python -m serial.tools.list_ports -v')
    sr=serial.Serial()
    sr.port=str(sr_port)
    sr.baudrate=baudrate
    sr.timeout=1
    sr.stopbits=1
    sr.open()
    if sr.is_open:
        print("port is open",data)
        data=sr.write(data)
        time.sleep(1)
        response = sr.readline()
        print("resp",str(response))
        # return response
        # data=sr.readline(bytes.fromhex(data))
    else:
        print("port is not open")
        return 0
class STEPPER(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')
class STEPPERStart(tornado.web.RequestHandler):
    def get(self):
        data = configReader['data']['start']
        resp = stepper(bytes.fromhex(data))
        self.write({'Start': 'start'})
        # print(resp)  
class STEPPERRor(tornado.web.RequestHandler):
    def get(self):
        dt1 = '01 01 00 00 00 00'
        ror = int(self.get_argument("stp"))
        print(ror)
        fdata = dt1+ROR(ror)
        fdata2 = bytes.fromhex(fdata)
        _checksum = hex(checksum2561(str(fdata2)))[2:]
        if len(_checksum) is 1:
            _corrected_checksum = '0' + _checksum
        else:
            _corrected_checksum = _checksum
        final = fdata[:-2]+_corrected_checksum
        print("final ",final)
        pantilt(bytes.fromhex(final))
        self.write({'items': 'rotate right side '+str(ror)})
        # data = configReader['data']['ror']
        # resp = stepper(bytes.fromhex(data))
        # self.write({'Ror': 'ror'})
        # print(resp)  

class STEPPERRol(tornado.web.RequestHandler):
    def get(self):
        dt1 = '01 02 00 00 00 00'
        ror = float(self.get_argument("ROL"))
        print(rol)
        if(rol<0):
            rol= int(abs(rol))*100
        # if(h_ang>0):
        #     h_ang = 30+h_ang
        # if(h_ang==0):
        #     h_ang = 30
        else:
            rol = int((360-rol)*100)
        print(rol)
        fdata = dt1+ROL(rol)
        fdata2 = bytearray.fromhex(fdata)
        _checksum = hex(checksum2561(str(fdata2)))[2:]
        if len(_checksum) is 1:
            _corrected_checksum = '0' + _checksum
        else:
            _corrected_checksum = _checksum
        final = fdata[:-2]+_corrected_checksum
        print("final ",final)
        pantilt(bytearray.fromhex(final))
        self.write({'items': 'rotate left side '+str((rol /100))+' deg'})
        # steps= int(self.get_argument("stp"))
        # data = configReader['data']['rol']
        # resp = stepper(bytes.fromhex(data))
        # self.write({'Rol': 'rol'})
class STEPPERStop(tornado.web.RequestHandler):
    def get(self):
        data = configReader['data']['stop']
        resp = stepper(bytes.fromhex(data))
        self.write({'Stop': 'stop'})
       

def make_app():
    return tornado.web.Application([("/", STEPPER),("/start", STEPPERStart),("/ror", STEPPERRor),("/rol", STEPPERRol),("/stop", STEPPERStop)],template_path=os.path.join(os.path.dirname(__file__), "templates"))

if __name__ == '__main__':
    app = make_app()
    app.listen(api_port)
    print("Stepper is listening for commands on port: "+str(api_port))
    IOLoop.instance().start()
