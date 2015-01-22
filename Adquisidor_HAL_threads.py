__author__ = 'seba'
import glob
import serial
from tram_to_HW import Tram_to_Serial
from Dicc_to_Serial import Dic_to_serial
from tram_to_socket import Tram_to_Socket
import threading
import time
import Queue
import socket
import logging

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

    def __init__(self, serial):
        self.serial = serial
        self.filename_loggers = '/home/Adquisidor/Logs/events.log'
        self.filename_config = config_files = '/home/Adquisidor/librerias/config.ini'
        self.salto_de_linea = '\r'

    def inicializacion(self):
        logging.info('Inicia programa')
        self.inicializacion_serial()

    def inicializacion_serial(self):
        time.sleep(10)
        self.serial.port = '/dev/ttyxuart2'
        self.serial.baudrate = 38400
        self.serial.timeout = 2
        self.serial.open()
        logging.info('Creada instancia de comunicacion con el Hardware')
        self.serial.write('palabra' + self.salto_de_linea)
        trama = self.serial.readline()
        print trama


if __name__ == '__main__':
    ser = serial.Serial()
    filename = '/home/Adquisidor/Logs/events.log'
    logging.info('Inicio de programa')
    logging.basicConfig(filename = filename,
                    format = '%(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
    logging.info('Logger iniciado')
    R = Redirector(ser)
    R.inicializacion()
