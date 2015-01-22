
import subprocess
from subprocess import Popen

def estado_ethernet(ethx):
    c= Popen (['/sbin/ip', 'link', 'show', ethx], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    c2, err = c.communicate()
    up = c2.find(' UP ')
    down = c2.find(' DOWN ')
    if up != -1: return c2[up+1:up+3]
    if down!= -1: return c2[down+1:down+5]
    if err: raise Exception (err)

