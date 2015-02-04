__author__ = 'seba'

import logging
import logging.handlers
import glob
import time
import datetime
import re
import sys
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import os
import re

lista_antigua = []
digits = re.compile(r'(\d+)')


def sendMail(to, fro, subject, text, files=[],server="localhost"):
    assert type(to)==list
    assert type(files)==list


    msg = MIMEMultipart()
    msg['From'] = fro
    msg['To'] = COMMASPACE.join(to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach( MIMEText(text) )

    for file in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(file,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"'
                       % os.path.basename(file))
        msg.attach(part)

    smtp = smtplib.SMTP(server)
    smtp.sendmail(fro, to, msg.as_string() )
    smtp.close()


def tokenize(filename):
    return tuple(int(token) if match else token
                 for token, match in
                 ((fragment, digits.search(fragment))
                  for fragment in digits.split(filename)))

if __name__ == '__main__':
    filename = '/home/Adquisidor/Logs/sender_mail.log'
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.handlers.TimedRotatingFileHandler(filename,
                                                        when ='d',
                                                        interval=1,
                                                        backupCount=4)
    formatter = logging.Formatter('%(asctime)s -  %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('Logger iniciado')
    time.sleep(30)
    try:
        while True:
            lista_actual = glob.glob('/home/Adquisidor/Logs/Eventos_HAL3270.log.*')
            lista_actual.sort(key=tokenize)
            comparacion = cmp(lista_actual, lista_antigua)
            if comparacion != 0 and len(lista_actual) >= 1:
                logger.info('Nuevo archivo para enviar por correo')
                lista_antigua = lista_actual
                logger.info('Nombre archivo: ' + lista_actual[len(lista_actual) - 1])
                x = datetime.datetime.now()
                fecha = '/'.join([str(x.year), time.strftime('%m'), time.strftime('%d')])
                hora = time.strftime('%H:%M:%S')

                sendMail(['Hal3270-Loggers <sebastian.cerda@pypchile.cl>'],
                     'PypChile Hal3270-Loggers <sebastian.cerda@pypchile.cl>',
                     'Logger Hal3270  : ' + fecha + ' ' + hora,
                     'Loggers Hal3270' + fecha + ' ' + hora,
                     [lista_actual[len(lista_actual) - 1]])
                logger.info('E-Mail enviado')
            time.sleep(60)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception, e:
        logger.info(e)


