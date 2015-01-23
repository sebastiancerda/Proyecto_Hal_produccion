__author__ = 'seba'
import glob
import serial
from tram_to_HW import Tram_to_Serial, dicc
from Dicc_to_Serial import Dic_to_serial
from tram_to_socket import Tram_to_Socket
import threading
from threading import Lock
import time
import Queue
import socket
import logging
import ConfigParser
import sys
import subprocess
from subprocess import Popen
from random import randint


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

    def __init__(self, serial, logger, config, lock):
        self.lock = lock
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
        self.trama_salida = tram_to_serial.Inicio()
        self.respuesta_hal = ''
        self.trama_salidaInicial = tram_to_serial.Inicio()
        self.contador_salida = 0
        self.dato_anterior = ''
        self.dicc = dicc
        self.respuesta_socket = ''
        self.tarea_serial = None
        self.tarea_socket = None

    def inicializacion(self):

        self.logger.info('Inicia programa')
        self.inicializacion_serial()
        self.parser_status_socket()
        self.tarea_serial = threading.Thread(target = self.Adquisidor_serial())
        self.tarea_serial.start()

    def adquisidor_serial(self):
        while True:
            time.sleep(1.0/3)
            self.contador_delaysocket += 1

            if self.contador_delaysocket > self.delay and self.lan_config:
                self.contador_delaysocket = 0
                self.tarea_socket = threading.Thread(target=self.adquisidor_socket(),
                                                     args=[self.ip, self.port])
                self.tarea_socket.start()

            ### falta exception serial timeoyt y desconexion
            self.trama_salida = tram_to_serial.director_trama()
            self.serial.write(self.trama_salida + self.salto_de_linea)
            trama_respuesta = self.serial.readline().splitlines()[0]
            pos_contador = trama_respuesta.find(',')
            self.respuesta_hal = trama_respuesta[pos_contador +1::]
            if not(self.respuesta_hal == self.dato_anterior):
                self.logger('Evento Hardware: ' + self.respuesta_hal)

            try:
                tram_to_serial.act_botones(self.respuesta_hal)
            except IndexError:
                self.logger.info('Error en trama de comunicacion' )
                self.logger.warning('Trama de respuesta de microcontrolador: ' + self.respuesta_Hal)
                self.logger.warning('Trama enviada al microcontrolador: ' + self.trama_salida)
                self.serial.write(self.trama_salidaInicial + self.salto_de_linea)
                self.logger.info('Reiniciando microcontrolador')
                self.respuesta_hal = ser.readline()
                self.logger('Evento Hardware: ' + self.respuesta_hal)
                tram_to_serial.act_botones(self.respuesta_hal)

            if tram_to_serial.ctrl_trama == 3:
                tram_to_serial.act_diccionario(self.dicc)

            tram_to_socket.actualizar(self.respuesta_hal)
            self.delay = tram_to_socket.get_delay()

            if tram_to_serial.status_lan == '0':
                if self.contador_parser_options == 45:
                    self.parser_status_socket()
                if self.contador_parser_options <= 0:
                    self.contador_parser_options = 45
                else:
                    self.contador_parser_options -= 1

            if not(to_serial.empty()):
                try:
                    self.respuesta_socket = to_serial.get()
                    self.dicc = Dic_to_serial.director_busqueda(self.respuesta_socket)
                except IndexError:
                    self.logger.warning('Error en trama proveniente desde el socket')
                    self.logger.warning(self.respuesta_socket)
                except NameError:
                    self.logger.warning('No hay mensaje de respuesta por el socket')
                except ValueError:
                    self.logger.warning('Error en trama proveniente desde el socket')

    def adquisidor_socket(self, ip, port):
        print ip
        print port
        print 'socket'
        self.lock.acquire()
        try:

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

    def logger_errormsjesocket(self,respuesta):
        if respuesta.find('ERR') != -1:
            pos_err = respuesta.find('ERR')
            if pos_err == 22:
                self.logger.warning('Error en proceso: ONLINE')
                self.logger.warning(respuesta)
            elif pos_err == 41:
                self.logger.warning('Error en proceso: BATCH')
                self.logger.warning(respuesta)
            elif pos_err == 60:
                self.logger.warning('Error en proceso: MP34')
                self.logger.warning(respuesta)

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
    lock = Lock()
    while True:
        try:
            R = Redirector(ser, logger, Config, lock)
            R.inicializacion()
            R.adquisidor_serial().join()
        except:
            '''falta agregar exceptiones'''
            pass

