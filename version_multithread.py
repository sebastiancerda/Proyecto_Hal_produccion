import glob
import serial
from tram_to_HW import Tram_to_Serial
from Dicc_to_Serial import Dic_to_serial
from tram_to_socket import Tram_to_Socket
import threading
import time
from threading import Lock
import Queue
import socket


'''
Inicializacion de los objetos importados
'''
to_serial = Queue.Queue()
tram_to_serial = Tram_to_Serial()
dic_to_serial = Dic_to_serial()
tram_to_socket = Tram_to_Socket()
salto_de_linea = '\r'

exitFlag = 0


def director_socket():

    conx = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conx.settimeout(5)
    conx.connect(('', 1000))
    conx.recv(1024)
    conx.send('sadfdsfasfd'.decode('ascii').encode('EBCDIC-CP-BE'))
    cola.put(conx.recv(1024))
    conx.close()


while True:
    print contador
    contador +=1
    contador_delay +=1
    if contador_delay >delay:
        print 'Inicia tarea socket'
        tarea_socket = threading.Thread(target = director_socket)
        tarea_socket.start()
        contador_delay = 0
    time.sleep(1)
    if not(cola.empty()):
        trama = cola.get()
        trama = trama.decode('EBCDIC-CP-BE').encode('ascii')
        print trama
        obj_dicc.director_busqueda(trama)



class Redirector:
    '''
    Redirige, gestiona y alimenta las comunicaciones desifrando
    y reestructurando los datos, es una clase con dos tareas en 
    paralelo, el serial funciona con un sleep fijo de 0.333 y la
    tarea socket funciona con un delay variable designado por el 
    hardware. Un lock simple previene la lectura del objeto 
    tram_to_socket por parte de las dos tareas al mismo tiempo.
    '''

    def __init__(self, serial, lock, socket):
        '''
        Se manejan las opciones y hereda el objeto serial y 
        socket al objeto redirector
        '''
        self.serial = socket
        self.serial = serial
        self.HOST = '192.168.2.140'
        self.PORT = 3030
        self.lock = lock
        self.contador_serial = 1
        self.contador_socket = 1
        self.delay_socket = 0 

    def inicializacion(self):
        '''
        Inicia las rutinas de inicializacion, establece las primeras
        comunicaciones e inicia las tareas.
        '''

        self.alive = True
        trama_inicial = tram_to_serial.Inicio()
        self.serial.write(trama_inicial + salto_de_linea)
        respuesta_micro = self.serial.readline()
        tram_to_serial.act_botones(respuesta_micro)
        tram_to_socket.actualizar(respuesta_micro)
        self.delay_socket = tram_to_socket.get_delay()
        self.thread_serial = threading.Thread(target=self.consumidor_serial)
        self.thread_socket = threading.Thread(target=self.consumidor_socket)
        self.thread_serial.setDaemon(1)
        self.thread_serial.start()
        self.thread_socket.start()
        print 'Secuencia de iniciacion terminada'

    def consumidor_serial(self):
        '''
        Tarea que controla la comunicacion via puerto Serial,
        Mientras el objeto principal se mantenga vivo, el loop
        seguira andando, en caso de haber un quiebre en la tarea
        el objeto general se reinicia.
        '''
        while self.alive:
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
            time.sleep(0.333333)
        self.alive = False
                                   
    def consumidor_socket(self):
        '''
        Tarea que controla la comunicacion via Socket.Mientras
        la tarea comsumidor_serial se mantenga viva, esta seguira andando
        si se cae la comunicacion, simplemente esta se reinicia
        '''

        while self.thread_serial.isAlive():
            conx = self.socket.socket()
            conx.settimeout(2)
            conx.setblocking(False)
            conx.connect((self.HOST, self.PORT))
            self.lock.acquire()
            try:
                delay_socket = tram_to_socket.get_delay()
                tram_salida = tram_to_socket.Director()
            finally:
                self.lock.release()
            conx.send(tram_salida)
            dato = dato.decode('EBCDIC-CP-BE')
            conx.close()
            dicc = dic_to_serial(dato)
            to_serial.put(dicc)
            time.sleep(delay_socket)
        self.alive = False
        self.thread_serial.join()
            
if __name__ == '__main__':
    ser = serial.Serial()
    ser.port = glob.glob('/dev/ttyUSB*')[0]
    ser.baudrate = 9600
    ser.open()
    soquete = socket

    lock = Lock()
    while True:
        r = Redirector(lock, ser, soquete)
        r.inicializacion()
        r.thread_serial.join()
        print "Desconectado"
        
        
    
