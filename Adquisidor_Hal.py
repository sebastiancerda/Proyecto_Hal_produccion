#!/usr/bin/env python
import sys
sys.path.insert(1, './librerias')

from Dicc_to_Serial import Dic_to_serial
from tram_to_HW import Tram_to_Serial, dicc
from tram_to_socket import Tram_to_Socket
import logging


from termcolor import colored
import time
import serial
from server_serial import SimSerial
import socket
import sys
import ConfigParser


logging.basicConfig(filename = './Logs/events.log',
                    format = '%(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

logging.warning('Logger iniciado')

generador_dicc = Dic_to_serial()
gen_tramasSerial = Tram_to_Serial()
gen_tramasocket = Tram_to_Socket()
trama_anterior = ''
contador = 0
salto_de_linea = '\r'
trama_nolan = '001,HAL3270v1,LED:1,0,0,0,0,0,0'

try:
    ser = SimSerial()
    #ser = serial.Serial('/dev/ttyxuart2')
    #ser.baudrate = 38400
    logging.info('Creada instancia de comunicacion con el Hardware')
except serial.SerialException, e:
    logging.warning('Error critico, no se puede conectar al Hardware')
    logging.warning(e)
    sys.exit(2)


contador_delysocket = 0
contador_parser_options = 45
trama_salida = gen_tramasSerial.Inicio()

contador_salida = 0
#### INICIAR COMUNICACION CON SERIAL
while True:
    ser.write(trama_salida + salto_de_linea)
    time.sleep(1.0/3)
    n = ser.inWaiting()
    if n > 0:
        respuesta_Hal = ser.readline()
        print colored(respuesta_Hal, 'red')
        logging.info('Empiezan las comunicaciones con el Hardware HAL3270')
        try:
            gen_tramasSerial.act_botones(respuesta_Hal)
            gen_tramasSerial.act_diccionario(dicc)
            break
        except IndexError:
            logging.warning('Error en trama proveniente del Hardware')
            logging.warning(respuesta_Hal)
            contador_salida += 1

    if contador_salida >= 10:
        logging.warning('Error critico integridad HardWare')
        sys.exit(2)

Config = ConfigParser.ConfigParser()

def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                print ("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


def parser_options():

    ### falta agregar error en la seccion
    Config.read('./librerias/config.ini')
    configuraciones = ConfigSectionMap('SectionOne')
    ip = configuraciones['ip']
    port = configuraciones['port']
    port = int(port)
    if len(ip.split('.')) == 4 and 0 < port < 65000:
        logging.info('Puerto configurado correctamente: ' + ip + ':' + str(port))
        lan_config = True
        return ip, port, lan_config
    else:
        logging.warning('Error archivo de configuraciones, formato incorrrecto')
        lan_config = False
        return '', 1, lan_config

host, port, lan_config = parser_options()

dato_anterior = ''
delay = 10

while True:
    try:
        trama_salida = gen_tramasSerial.director_trama()

        ser.write(trama_salida + salto_de_linea)
        trama_respuesta = ser.readline()
        pos_contador = trama_respuesta.find(',')
        respuesta_Hal = trama_respuesta[pos_contador + 1::]
        if respuesta_Hal == dato_anterior:
            pass
        else:
            print colored('Dato nuevo', 'blue')
            logging.info('Evento Hardware: ' + respuesta_Hal)
            dato_anterior = respuesta_Hal

        ### metodo para tram to socket
        gen_tramasSerial.act_botones(respuesta_Hal)

        ### empieza metodo
        time.sleep(1.0/3)
        gen_tramasocket.actualizar(respuesta_Hal.splitlines()[0])
        delay = gen_tramasocket.get_delay() * 3
        contador_delysocket += 1
        if gen_tramasSerial.ctrl_trama == 3:
            gen_tramasSerial.act_diccionario(dicc)
    except IndexError:
        print 'error en trama'
        logging.warning('Error en trama de comunicacion')
        logging.warning('Trama de respuesta de microcontrolador: ' + respuesta_Hal)
        logging.warning('Trama enviada al microcontrolador: ' + trama_salida)

    if contador_delysocket > delay and lan_config:
        mensaje_socket_salida = gen_tramasocket.Director()
        try:
            contador_delysocket = 0
            conx = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conx.settimeout(5)
            conx.connect((host, port))
            a = conx.recv(1024)
            print colored(a, 'blue')
            print len(mensaje_socket_salida)
            mensaje_socket_salida = mensaje_socket_salida.decode('ascii').encode('EBCDIC-CP-BE')
            conx.send(mensaje_socket_salida)
            respuesta = conx.recv(1024)
            respuesta = respuesta.decode('EBCDIC-CP-BE').encode('ascii')
            print colored(respuesta, 'yellow')
            gen_tramasSerial.cambiar_statuslan(1)
            gen_tramasSerial.director_leds()

        except socket.error, e:
            conx.close()
            gen_tramasSerial.cambiar_statuslan(0)
            logging.warning('Conexion perdida, inicia reconfiguracion del puerto de comunicaciones')
            logging.warning(e)
            lan_config = False

        finally:
            conx.close()

        try:
            dicc = generador_dicc.director_busqueda(respuesta)

        except IndexError:
            logging.warning('Error en trama proveniente desde el socket')
            logging.warning(respuesta)
        except NameError:
            logging.warning('No hay mensaje de respuesta por el socket')
            print colored('Aun no se conecta al socket', 'red')
        except ValueError:
            logging.warning('Error en trama proveniente desde el socket')
            logging.warning(respuesta)

    if gen_tramasSerial.status_lan == '0':
        print colored(contador_parser_options, 'red')
        if contador_parser_options == 45:
            host, port, lan_config = parser_options()
        if contador_parser_options <= 0:
            contador_parser_options = 45
        else:
            contador_parser_options -= 1

