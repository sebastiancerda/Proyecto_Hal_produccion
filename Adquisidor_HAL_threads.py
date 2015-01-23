__author__ = 'seba'
import glob
import serial
from tram_to_HW import Tram_to_Serial, dicc
from Dicc_to_Serial import Dic_to_serial
from tram_to_socket import Tram_to_Socket
import threading
import time
import Queue
import socket
import logging
import ConfigParser
import sys
import subprocess
from subprocess import Popen


'''
Inicializacion de los objetos importados
'''
to_serial = Queue.Queue()
tram_to_serial = Tram_to_Serial()
dic_to_serial = Dic_to_serial()
tram_to_socket = Tram_to_Socket()
salto_de_linea = '\r'

exitFlag = 0


class Redirector(object):

    def __init__(self, serial, logger, config):
        self.serial = serial
        self.filename_config = '/home/seba/Copy/HAL3270/sw/Adquisidor/librerias/config.ini'
        self.salto_de_linea = '\r'
        self.logger = logger
        self.config = config
        self.interfaz_socket = 'wlan0'
        self.lan_config = False
        self.port = 1
        self.ip = ''
        self.dato_anterior = ''
        self.delay = 10
        self.contador_salida = 0
        self.contador_delaysocket = 0
        self.contador_parser_options = 45
        self.trama_salida = Tram_to_Serial.Inicio()
        self.respuesta_hal = ''
        self.trama_salidaInicial = Tram_to_Serial.Inicio()
        self.contador_salida = 0

    def inicializacion(self):
        self.logger.info('Inicia programa')
        self.inicializacion_serial()
        self.parser_status_socket()
        self.tarea_serial = threading.Thread(target = self.Adquisidor_serial())
        self.tarea_socket = threading.Thread(target = self.Adquisidor_socket())
        self.tarea_serial.start()
        self.tarea_socket.start()

    def Adquisidor_serial(self):
        while True:
            print 'Corriendo tarea serial'
            time.sleep(1.0/3)


    def Adquisidor_socket(self):
        print 'socket'


    def inicializacion_serial(self):
        time.sleep(1)
        #self.serial.port = '/dev/ttyxuart2'
        #self.serial.baudrate = 38400
        #self.serial.timeout = 2
        #self.serial.open()
        '''self.serial.write(self.trama_salida + self.salto_de_linea)
        time.sleep(1.0/3)
        n = self.serial.inWaiting()
        if n > 0:
            self.respuesta_hal = self.serial.readline()
            self.logger.info('Empiezan las comunicaciones con el Hardware')
            try:
                tram_to_serial.act_botones(self.respuesta_hal)
                tram_to_serial.act_diccionario(dicc)
            except IndexError, e:
                self.logger.warning('Error en trama proveniente del Hardware')
                self.logger.warning(self.respuesta_hal)
                self.logger.warning(e)
                self.contador_salida += 1
        '''
        print 'inicializacion serial'


        self.logger.info('Creada instancia de comunicacion con el Hardware')

        print 'iniciacializacion terminada'

    def configuracion_socket(self, section):
        dict1 = {}
        options = self.config.options(section)
        for option in options:
            try:
                dict1[option] = self.config.get(section, option)
                if dict1[option] == -1:
                    self.logger.info('Saltado %s' %option)
            except KeyError:
                self.logger.info('Error en el formato de configuracion')
                self.logger.info('Exception en %s' %option)
        return dict1

    def parser_status_socket(self):
        stauts_ethernet = self.estado_ethernet(self.interfaz_socket)
        if stauts_ethernet == 'DOWN':
            self.logger.warn('Cable desconectado')
            self.lan_config = False
            self.port = 1
            self.ip = ''

        elif stauts_ethernet == 'UP':
            self.config.read(self.filename_config)
            configuraciones = self.configuracion_socket('SectionOne')
            ip = configuraciones['ip']
            port = configuraciones['port']
            port = int(port)
            print ip
            print port
            if len(ip.split('.')) == 4 and 0 < port < 65000:
                self.logger.info('Puerto configurado correctamente: ' + ip + ':' + str(port))
                self.lan_config = True
                self.port = port
                self.ip = ip

            else:
                self.logger.warning('Error en el archivo de configuraciones, formato incorrecto')
                self.lan_config = False
                self.port = 1
                self.ip = ''

        else:
            self.logger.warn(stauts_ethernet)
            self.lan_config = False
            self.port = 1
            self.ip = ''

    def estado_ethernet(self, ethx):
        c = Popen(['/sbin/ip', 'link', 'show', ethx], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        c2, err = c.communicate()
        up = c2.find(' UP ')
        down = c2.find(' DOWN ')
        if up != -1: return c2[up+1:up+3]
        if down!= -1: return c2[down+1:down+5]
        if err: return err


if __name__ == '__main__':
    ser = serial.Serial()
    filename = '/home/seba/Copy/HAL3270/sw/Adquisidor/Logs/events.log'
    logging.basicConfig(filename = filename,
                    format = '%(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
    logging.info('Logger iniciado')
    logging.info('Inicio de programa')
    logger = logging.getLogger(__name__)
    Config = ConfigParser.ConfigParser()
    R = Redirector(ser, logger, Config)
    R.inicializacion()
