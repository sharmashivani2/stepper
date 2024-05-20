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
    Config.set('api', 'port', '3016')
    Config.add_section('servo')
    Config.set('servo', 'sr_port', 'COM4')
    Config.set('servo', 'baudrate', '9600')
    Config.set('servo', 'timeout', '1')
    Config.add_section('data')
    # Config.set('data', 'clockwise1', '40 31 39 39 3a 4d 6f 74 6f 72 3a 48 6f 6d 65 3a') # clk1
    Config.set('data', 'start','ff 03 03 00 00 01 91 90') # start
    Config.set('data', 'clk','7f 03 00 00 00 01 8e 14') # clk1
    Config.set('data', 'anticlk','7f 06 02 10 00 0c 83 ac') # anticlk
    Config.set('data', 'stop','7f 03 00 00 00 01 8e 14') # stop
    Config.write(cfgfile)
    cfgfile.close()
configReader = ConfigParser()
configReader.read('config.ini')
sr_port = configReader['servo']['sr_port']
baudrate = configReader['servo'].getint('baudrate')
sr_timeout = configReader['servo']['timeout']
api_port = configReader['api'].getint('port')

print(sr_port,baudrate)
os.system('python -m serial.tools.list_ports -v')
sr=serial.Serial()
sr.port=str(sr_port)
sr.baudrate=baudrate
sr.timeout=1
sr.stopbits=1
sr.open()
if sr.is_open:
    print("port is open")
    sr.write(bytes.fromhex('7f 03 03 0a 00 02 ee 53'))  #@199:*IDN
    print("data")
    resp = sr.readline().decode('utf-8')
    print(resp)
    sr.write(bytes.fromhex('7f 10 03 0a 00 02 04 00 01 00 00 a8 c9')) #@199:Program:Int 
    time.sleep(1)
    resp = sr.readline()
    if(resp == '7f 10 03 0a 00 02 6b 90'):
    	print('success')
    # sr.write('7f 06 02 10 00 0c 83 ac') #@199:Program:MInt
    # time.sleep(1)
    # resp = sr.readline()
    # print(resp)
    # sr.write(''.encode('ascii'))  #@199:Program:EStop
    # # time.sleep(1)
    # resp = sr.readline().decode('utf-8')
    # print(resp) 
    # sr.write(''.encode('ascii'))  #@199:Program:EStop
    # time.sleep(1)
    # resp = sr.readline().decode('utf-8')
    # print(resp)
    # sr.write(''.encode('ascii'))  #@199:Program:EStop
    # time.sleep(1)
    # resp = sr.readline().decode('utf-8')
    # print(resp)    
    # sr.write('@199:Motor:Run:M1 -1000\r\n'.encode('ascii'))  #@199:Program:EStop
    # time.sleep(1)
    # resp = sr.readline().decode('utf-8')
    sr.write(bytes.fromhex('7f 03 00 00 00 01 8e 14'))  #@199:Program:EStop
    # time.sleep(1)
    resp = sr.readline()
    print(resp) 

    sr.close()
    # return response.decode('utf-8')
else:
    print("port is not open")
    # return 0
# def servo(data):
 
   
    

class SERVO(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')
class SERVOStart(tornado.web.RequestHandler):
    def get(self):
        data = configReader['data']['start']
        resp = sr.write(data.encode('ascii'))
        sr.read(resp)
class SERVOClk(tornado.web.RequestHandler):
    def get(self):
        data = configReader['data']['clk']
        resp = sr.write(data.encode('ascii'))
        sr.read(resp)
class SERVOAntiClk(tornado.web.RequestHandler):
    def get(self):
        data = configReader['data']['anticlk']
        # resp = servo(data)
        self.write({'AntiClk': 'anticlk'})
class SERVOStop(tornado.web.RequestHandler):
    def get(self):
        data = configReader['data']['stop']
        resp = servo(data)
        self.write({'Stop': 'stop'})
       

def make_app():
    return tornado.web.Application([("/", SERVO),("/start", SERVOStart),("/clk", SERVOClk),("/anticlk", SERVOAntiClk),("/stop", SERVOStop)],template_path=os.path.join(os.path.dirname(__file__), "templates"))

if __name__ == '__main__':
    app = make_app()
    app.listen(api_port)
    # print("Servo is listening for commands on port: "+str(api_port))
    IOLoop.instance().start()
