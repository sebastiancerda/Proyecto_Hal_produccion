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
# from server_serial import SimSerial
from termcolor import colored


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

    def __init__(self, serial, logger, config, lock, socket):
        self.serial = serial
        self.lock = lock
        self.logger = logger
        self.socket = socket
        self.config = config
        self.filename_config = '/home/Adquisidor/librerias/config.ini'
        self.salto_de_linea = '\r'
        self.interfaz_socket = 'eth0'
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
        self.salida_socket = ''
        self.tarea_serial = None
        self.tarea_socket = None
        self.trama_valida = False

        self.no_configlan = True
        self.config_lan = True

        self.togle_lan = True
        self.togle_nolan = True

    def inicializacion(self):

        self.logger.info('Inician las tareas socket y serial')
        self.inicializacion_serial()
        self.parser_status_socket()
        self.tarea_serial = threading.Thread(target=self.adquisidor_serial)
        self.tarea_serial.start()

    def adquisidor_serial(self):
        while True:
            time.sleep(1.0/3)
            self.contador_delaysocket += 1

            # falta exception serial timeoyt y desconexion
            '''
            Manejo del puerto serial
            '''
            self.trama_salida = tram_to_serial.director_trama()
            self.serial.write(self.trama_salida + self.salto_de_linea)
            trama_respuesta = self.serial.readline().splitlines()[0]
            pos_contador = trama_respuesta.find(',')
            self.respuesta_hal = trama_respuesta[pos_contador + 1::]
            if not(self.respuesta_hal == self.dato_anterior):
                self.logger.info('Evento Hardware: ' + self.respuesta_hal)
                self.dato_anterior = self.respuesta_hal
            try:
                tram_to_serial.act_botones(self.respuesta_hal)
                self.trama_valida = True

            except IndexError:
                self.trama_valida = False
                self.logger.warning('Error en trama de comunicacion')
                self.logger.warning('Trama de respuesta de microcontrolador: ' + self.respuesta_hal)
                self.logger.warning(trama_respuesta)
                self.logger.warning('Trama enviada al microcontrolador: ' + self.trama_salida)
                self.serial.write(self.trama_salidaInicial + self.salto_de_linea)
                self.logger.info('Reiniciando microcontrolador')
                self.respuesta_hal = ser.readline()
                self.logger.info('Evento Hardware: ' + self.respuesta_hal)
                tram_to_serial.act_botones(self.respuesta_hal)

            if self.trama_valida:
                try:
                    tram_to_socket.actualizar(self.respuesta_hal)
                    self.delay = tram_to_socket.get_delay()*3
                except IndexError:
                    self.logger.warn('Trama no valida: '+self.respuesta_hal)

                if self.contador_delaysocket > self.delay:
                    if not self.lan_config:
                        self.parser_status_socket()
                    if self.lan_config:
                        self.contador_delaysocket = 0
                        self.tarea_socket = threading.Thread(target=self.adquisidor_socket,
                                                             args=(self.ip, self.port, self.respuesta_hal))
                        self.tarea_socket.start()

            if not(to_serial.empty()):
                try:
                    self.respuesta_socket = to_serial.get()
                    self.dicc = dic_to_serial.director_busqueda(self.respuesta_socket)
                    self.logger_errormsjesocket(self.respuesta_socket)
                    print self.dicc
                except IndexError:
                    self.logger.warning('Error en trama proveniente desde el socket')
                    self.logger.warning(self.respuesta_socket)
                except NameError:
                    self.logger.warning('No hay mensaje de respuesta por el socket')
                except ValueError:
                    self.logger.warning('Error en trama proveniente desde el socket')

            if tram_to_serial.ctrl_trama == 3:
                tram_to_serial.act_diccionario(self.dicc)

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
        self.logger.info('Creada instancia de comunicacion con el Hardware')
        print 'iniciacializacion terminada'

    def configuracion_socket(self, section):
        dict1 = {}
        options = self.config.options(section)
        for option in options:
            try:
                dict1[option] = self.config.get(section, option)
                if dict1[option] == -1:
                    self.logger.info('Saltado %s' % option)
            except KeyError:
                self.logger.info('Error en el formato de configuracion')
                self.logger.info('Exception en %s' % option)
        return dict1

    def parser_status_socket(self):
        stauts_ethernet = self.estado_ethernet(self.interfaz_socket)
        if stauts_ethernet == 'DOWN':
            msje_logger = 'Cable desconectado'
            self.lan_config = False
            self.port = 1
            self.ip = ''
            self.togle_loggers_configfiles(msje_logger)
        elif stauts_ethernet == 'UP':
            self.config.read(self.filename_config)
            configuraciones = self.configuracion_socket('SectionOne')
            ip = configuraciones['ip']
            port = configuraciones['port']
            port = int(port)
            if len(ip.split('.')) == 4 and 0 < port < 65000:
                if not self.ip == ip or not self.port == port:
                    self.logger.info('Archivo de configuracion cambiado, nuevo puerto de comunicacion')
                    self.logger.info(ip + ':' + str(port))
                msje_logger = 'Puerto configurado correctamente: ' + ip + ':' + str(port)
                self.lan_config = True
                self.port = port
                self.ip = ip
                self.togle_loggers_configfiles(msje_logger)
            else:
                msje_logger = 'Error en el archivo de configuraciones, formato incorrecto'
                self.lan_config = False
                self.port = 1
                self.ip = ''
                self.togle_loggers_configfiles(msje_logger)
        else:
            msje_logger = stauts_ethernet
            self.lan_config = False
            self.port = 1
            self.ip = ''
            self.togle_loggers_configfiles(msje_logger)

    def togle_loggers_configfiles(self, msje):
        if self.lan_config and self.config_lan:
            self.logger.info(msje)
            self.config_lan = False
            self.no_configlan = True
        if not self.lan_config and not self.config_lan:
            self.logger.warning(msje)
            self.config_lan = True
            self.no_configlan = False


    def estado_ethernet(self, ethx):
        c = Popen(['/sbin/ip', 'link', 'show', ethx], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        c2, err = c.communicate()
        up = c2.find(' UP ')
        down = c2.find(' DOWN ')
        if up != -1:
            return c2[up+1:up+3]
        if down != -1:
            return c2[down+1:down+5]
        if err:
            return err

    def logger_errormsjesocket(self, respuesta):
        if not(respuesta[6:9] == '000'):
            self.logger.warning('Error general')
            self.logger.warning(respuesta)
        else:
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
    # ser = SimSerial()
    filename = '/home/Adquisidor/Logs/events.log'
    logger = logging.getLogger('root')
    logging.basicConfig(filename=filename,
                        format='%(asctime)s - %(funcName)s - %(levelname)s: %(message)s ',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.DEBUG)
    logging.info('Logger iniciado')
    logging.info('Modulo principal iniciado')

    Config = ConfigParser.ConfigParser()
    lock = Lock()

    R = Redirector(ser, logger, Config, lock, socket)
    R.inicializacion()
    R.adquisidor_serial().join()
