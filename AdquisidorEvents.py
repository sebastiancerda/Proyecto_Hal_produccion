__author__ = 'seba'

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

import subprocess
from subprocess import Popen
from server_serial import SimSerial
from termcolor import colored
import sched


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

    def __init__(self, serial, logger, config, lock, socket, scheduler):
        self.serial = serial
        self.lock = lock
        self.logger = logger
        self.socket = socket
        self.config = config
        self.scheduler = scheduler
        self.filename_config = './librerias/config.ini'
        self.salto_de_linea = '\r'
        self.interfaz_socket = 'wlan0'
        self.lan_config = False
        self.port = 1
        self.ip = ''
        self.dato_anterior = ''
        self.delay = 10
        self.contador_parser_options = 45
        self.trama_salida = tram_to_serial.Inicio()
        self.respuesta_hal = ''
        self.trama_salidaInicial = tram_to_serial.Inicio()
        self.contador_salida = 0
        self.dato_anterior = ''
        self.dicc = dicc
        self.respuesta_socket = ''
        self.salida_socket = ''
        self.tarea_serial = None
        self.tarea_socket = None
        self.trama_valida = False

        self.no_configlan = True
        self.config_lan = True

        self.togle_lan = True
        self.togle_nolan = True

        self.thread_alive = False
        self.thread_bajoadquisicion = None

    def inicializacion(self):

        self.logger.info('Inician las tareas socket y serial')
        self.inicializacion_serial()
        self.thread_bajoadquisicion = threading.Thread(target=self.modo_bajoadquisicion)
        self.thread_bajoadquisicion.start()

    def modo_bajoadquisicion(self):
        while True:
            time.sleep(0.1)
            trama_salida = tram_to_serial.lcd_return()
            n = self.serial.inWaiting()
            if n == 0:
                self.serial.write(trama_salida + self.salto_de_linea)

            self.respuesta_hal = self.serial.readline()
            self.respuesta_hal = self.adaptacion_datosserial(self.respuesta_hal)

            if not(self.respuesta_hal == self.dato_anterior):
                print 'dato nuevo'
                self.dato_anterior = self.respuesta_hal



    def adquisidor_socket(self, ip, port, trama_salida):
        print colored(ip, 'red')
        print colored(port, 'red')
        print 'socket'
        self.salida_socket = trama_salida
        conx = self.socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conx.settimeout(3)
        try:
            conx.connect((ip, port))
            print conx.recv(1024)
            conx.send(self.salida_socket.decode('ascii').encode('EBCDIC-CP-BE'))
            respuesta_socket = conx.recv(1024).decode('EBCDIC-CP-BE').encode('ascii')
            tram_to_serial.cambiar_statuslan(1)
            tram_to_serial.director_leds()
            if self.togle_lan:
                self.logger.info('Comunicacion establecida: ' + self.ip + ':' + str(self.port))
                self.togle_lan = False
                self.togle_nolan = True
            to_serial.put(respuesta_socket)
        except socket.error, e:
            conx.close()
            tram_to_serial.cambiar_statuslan(0)
            print 'togle lan ' + str(self.togle_lan)
            print 'togle_nolan' + str(self.togle_nolan)
            if self.togle_nolan:
                self.togle_lan = True
                self.togle_nolan = False
                self.logger.warning(e)
                self.logger.warning('Conexion perdida, inicia reconfiguracion del puerto de comunicaciones')
                self.logger.warning('Conexion a :' + self.ip + ':'+str(self.port) + ' inalcanzable')
            self.lan_config = False
        finally:
            conx.close()
            self.thread_alive = not self.thread_alive

    def adaptacion_datosserial(self, trama):
        trama_respuesta = trama.splitlines()[0]
        pos_contador = trama_respuesta.find(',')
        return trama_respuesta[pos_contador + 1::]

    def inicializacion_serial(self):
            time.sleep(10)
            self.serial.port = '/dev/ttyxuart2'
            self.serial.baudrate = 38400
            self.serial.timeout = 2
            self.serial.open()

            self.serial.write(self.trama_salida + self.salto_de_linea)
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

            print 'inicializacion serial'


if __name__ == '__main__':
    ser = serial.Serial()
    #ser = SimSerial()
    filename = './Logs/events.log'
    logger = logging.getLogger('root')
    logging.basicConfig(filename=filename,
                        format='%(asctime)s - %(funcName)s - %(levelname)s: %(message)s ',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.DEBUG)
    logging.info('Logger iniciado')
    logging.info('Modulo principal iniciado')

    Config = ConfigParser.ConfigParser()
    lock = Lock()

    R = Redirector(ser, logger, Config, lock, socket, scheduler=sched.scheduler(time.time, time.sleep))
    R.inicializacion()