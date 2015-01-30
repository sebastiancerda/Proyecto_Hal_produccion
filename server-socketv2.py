__author__ = 'seba'


import socket
import sys
from random import randint
from thread import *
from termcolor import colored
import time
import datetime
import random
from random import randint

HOST = ''   # Nombre simbolico localhost
PORT = 8888 # puerto arbitrario

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print 'Socket creado'

#Enlaza el objeto socket con las direcciones entregadas
try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print 'Error al enlazar. Codigo de error : ' + str(msg[0]) + ' Mensaje ' + msg[1]
    sys.exit()

print 'Enlace creado'

#Iniciar escucha del server
s.listen(10)
print 'Socket escuchando puerto'
data = ''

def prob_err():
    randoms = random.random()
    if randoms > 0.995:
        return True
    else:
        return False



#Funcion para manejar las conecciones. Maneja la tarea
def clientthread(conn):
    #Manda un mensaje al cliente conectado.
    global data, dato_anterior
    conn.send('Bienvenido al sebiserver,mande un mensaje y luego return \n') #send only takes string
    dato_anterior = ''
    header = '<--- <'
    header_online = ' O/'
    header_batch = ' B/'
    header_mp32 = ' M/'
    header_fecha = ' F/'
    header_proceso = 'CICLDA'
    numero_proceso = '21/'

    #Loop infinito que no termina hasta que data es vacio.
    while True:

        #Recive desde el cliente
        data = conn.recv(1024)
        data = str(data).decode('EBCDIC-CP-BE').encode('ascii')
        if not data:
            break

        if data == dato_anterior:
            pass
        else:
            print 'trama nueva:  ' + data
            dato_anterior = data
        x = datetime.datetime.now()
        fecha = ''.join([str(x.year), time.strftime('%m'), time.strftime('%d')])
        hora = time.strftime('%H:%M:%S')

        if not(prob_err()):
            codd_err = '000>'
        else:
            codd_err = str(randint(1, 999))
            codd_err = '0'* (3 - len(codd_err)) + codd_err + '>'

        trama_header = header + codd_err

        n_online = str(randint(0, 99999999))
        n_online = '0'*(8 - len(n_online)) + n_online  + '/'

        if not(prob_err()):
            err = 'OK /000'
        else:
            err = 'ERR/' + str(randint(100, 999))
        trama_online = header_online + n_online + err

        n_batch = str(randint(0, 99999999))
        n_batch = '0'*(8 - len(n_batch)) + n_batch + '/'
        if not(prob_err()):
            err = 'OK /000'
        else:
            err = 'ERR/' + str(randint(100, 999))
        trama_batch = header_batch + n_batch + err

        n_mp43 = str(randint(0, 99999999))
        n_mp43 = '0'*(8 - len(n_mp43)) + n_mp43 + '/'
        if not(prob_err()):
            err = 'OK /000'
        else:
            err = 'ERR/' + str(randint(100, 999))
        trama_mp32 = header_mp32 + n_mp43 + err

        trama_fecha = header_fecha + fecha + '/' + hora + '/'

        if not(prob_err()):
            trama_proceso = header_proceso + numero_proceso
        else:
            numero_proceso = str(randint(10, 99)) + '/'
            trama_proceso = header_proceso + numero_proceso

        if not(prob_err()):
            tiempo_respuesta = str(randint(0, 4999))
            tiempo_respuesta = '0'*(5 - len(tiempo_respuesta)) + tiempo_respuesta+ '/'
        else:
            tiempo_respuesta = str(randint(5000, 15000))
            tiempo_respuesta = '0'*(5 - len(tiempo_respuesta)) + tiempo_respuesta+ '/'

        if not(prob_err()):
            tasa_rechazo = str(randint(0, 59))
            tasa_rechazo = '0'*(3 - len(tasa_rechazo)) + tasa_rechazo
        else:
            tasa_rechazo = str(randint(60, 100))
            tasa_rechazo = '0'*(3 - len(tasa_rechazo)) + tasa_rechazo



        trama = trama_header + trama_online + trama_batch + trama_mp32 + trama_fecha + trama_proceso + \
                tiempo_respuesta + tasa_rechazo
        print colored(fecha + ' | ' + hora + trama,  'yellow')

        msje_salida = trama.decode('ascii').encode('EBCDIC-CP-BE')
        conn.sendall(msje_salida)

    #Si se sale del loop la coneccion se cierra
    conn.close()

#Para mantenerse hablando con el server
while 1:
    #Espera para aceptar una coneccion
    now = time.time()
    conn, addr = s.accept()
    print 'Conectado con : ' + addr[0] + ':' + str(addr[1])
    ahora = time.time()
    print colored(ahora - now, 'red')
    #Inicia una nueva tarea tomando el primer argumento ccomo el nombre de la funcion para correr
    #el segundo argumento es una tupla para la funcion
    start_new_thread(clientthread ,(conn,))

s.close()