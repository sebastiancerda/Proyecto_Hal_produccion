import glob
import serial
from tram_to_HW import Tram_to_Serial
from Dicc_to_Serial import Dic_to_serial
from tram_to_socket import Tram_to_Socket
from threading import Timer, Lock
import Queue
to_serial = Queue.Queue()
tram_to_serial = Tram_to_Serial()
dic_to_serial = Dic_to_serial()
tram_to_socket = Tram_to_Socket()
salto_de_linea = '\r'


class Redirector:
    '''
    Objeto que controla las comunicaciones con tareas tipo Timer, 
    estas se reinician al final de cada ciclo y tienen las mismos
    metodos que las tareas simples.
    '''
    def __init__(self, serial, lock):
        self.serial = serial
        self.HOST = '192.168.2.140'
        self.PORT = 3030
        self.lock = lock

    def inicializacion(self):
	'''
	Obtencion de las variables iniciales como botones
	y luces de funcionamiento, ademas de setear las tareas 
	Timer
	'''
        trama_inicial = tram_to_serial.Inicio()
        self.serial.write(trama_inicial + salto_de_linea)
        respuesta_micro = self.serial.readline()
        tram_to_serial.act_botones(respuesta_micro)
        tram_to_socket.actualizar(respuesta_micro)
        delay_socket = tram_to_socket.get_delay()
        timer_serial = Timer(0.3333, self.consumidor_serial)
        timer_socket = Timer(delay_socket, self.consumidor_socket)
        timer_serial.start()
        timer_socket.start()
        print 'Secuencia de inicializacion terminada'

    def consumidor_serial(self):
        '''
	Tarea que maneja las comunicaciones via puerto serial
	'''
        if not(to_serial.empty()):
            dicc = to_serial.get()
            tram_to_serial.act_diccionario(dicc)
        trama_salida = tram_to_serial.director_trama()
        self.serial.write(trama_salida + salto_de_linea)
        datos = self.serial.readline()
        self.lock.acquire()
        try:
            tram_to_socket(datos)
        finally:
            self.lock.release()
        timer_serial = Timer(0.3333, self.consumidor_serial)
        timer_serial.start()

    def consumidor_socket(self):
	'''
	Tarea que maneja las comunicaciones via puerto Socket 		Ethernet
	'''        
	import socket
        try:
            conx = socket.socket()
            conx.settimeout(2)
            conx.setblocking(False)
            self.lock.acquire()
            try:
                delay_socket = tram_to_socket.get_delay()
                tram_salida = tram_to_socket.Director()
            finally:
                self.lock.release()
            # falta header
            conx.send(tram_salida)
            dato = conx.recv(2048)
            dato = dato.decode('EBCDIC-CP-BE')
            conx.close()
            dicc = dic_to_serial(dato)
            to_serial.put(dicc)
        except:
            print 'metodo para los socket'
        timer_socket = Timer(delay_socket, self.consumidor_socket)
        timer_socket.start()
        

if __name__ == '__main__':
    lock = Lock()
    ser = serial.Serial()
    ser.port = glob.glob('/dev/ttyUSB*')[0]
    ser.baudrate = 38400
    ser.open()
    r = Redirector(ser)
    r.inicializacion()
    

    
