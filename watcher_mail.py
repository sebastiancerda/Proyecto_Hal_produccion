__author__ = 'sbea'
import sys
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import glob

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import os
import re

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


class MyHandler(PatternMatchingEventHandler):
    patterns = ["*.log"]

    def process(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        # the file will be processed there
        print event.src_path, event.event_type  # print now only for degug
        if event.event_type == 'moved':
            time.sleep(0.5)
            lista = glob.glob('timed_test.log.*')
            lista.sort(key=tokenize)
            print lista
            sendMail(['Hal3270-Loggers <sebastian.cerda@pypchile.cl>'],
                     'PypChile Hal3270-Loggers <sebastian.cerda@pypchile.cl>',
                     'Loggers!',
                     'Heya buddy! Say hello to Python! :)',
                     [lista[len(lista) - 1]])



    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

    def on_deleted(self, event):
        self.process(event)

    def on_any_event(self, event):
        self.process(event)

if __name__ == '__main__':
    args = sys.argv[1:]
    observer = Observer()
    observer.schedule(MyHandler(), path=args[0] if args else '.')
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
