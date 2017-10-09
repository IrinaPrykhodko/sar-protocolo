#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket, sys, os
import szasar
import signal
import random
import string
import time

PORT = 6012
FILES_PATH = "files"
MAX_FILE_SIZE = 10 * 1 << 20  # 10 MiB
SPACE_MARGIN = 50 * 1 << 20  # 50 MiB
USERS = ["anonimous", "sar", "sza"]
PASSWORDS = ["", "sar", "sza"]
EMAILS = ["anonimous@gmail.com", "sar@gmail.com", "sza@gmail.com"]
CODE_TIME = {}

class State:
    LoggedOut, LoggedIn = range(2)


class Command:
    Register, Indentificate, Message, Read, Exit = (
        "RG", "ID", "MS", "RD", "XT")


def sendOK(s, address, params=""):
    s.sendto(("OK{}".format(params)).encode("ascii"), address)


def sendER(s, address, code=1):
    s.sendto(("ER{}".format(code)).encode("ascii"), address)


def existsuser(user):
    for username in USERS:
        if username == user:
            return True
    return False


def existsemail(email):
    for emailaddress in EMAILS:
        if emailaddress == email:
            return True
    return False


def registeruser(username, password, email):
    USERS.append(username)
    PASSWORDS.append(password)
    EMAILS.append(email)


def checkpassword(username, password):
    indexforthatuser = USERS.index(username)
    if PASSWORDS[indexforthatuser] != password:
        return False
    else:
        return True


def generateandregistercodetime():
    code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    sparetime = "020"
    codetime = code + "#" + sparetime
    expirationtime = time.time() + sparetime

    CODE_TIME[code] = expirationtime

    return codetime


def isvalidcode(code):
    expirationtime = CODE_TIME[code]
    currenttime = int(time.time())
    if expirationtime < currenttime:
        return False
    else:
        return True


def checksentmessagelength(sentmessage):
    if len(sentmessage) > 140:
        return False
    else:
        return True


def session(s, buffer, address):
    state = State.LoggedOut

    while True:
        message = buffer.decode("ascii")
        if not message:
            return

        if message.startswith(Command.Register):
            if (state != State.LoggedOut):
                sendER(s, 11, address)
                continue

            user, password, email = message.split("#")

            if existsuser(user):
                sendER(s, 6, address)
                continue

            if existsemail(email):
                sendER(s, 7, address)
                continue

            registeruser(user, password, email)
            sendOK(s, address)
        elif message.startswith(Command.Indentificate):
            if state != State.LoggedOut:
                sendER(s, 11, address)
                continue

            user, password = message.split("#")
            if not existsuser(user):
                sendER(s, 8, address)
            if not checkpassword(user, password):
                sendER(s, 8, address)
                continue

            code_time = generateandregistercodetime()
            state = State.LoggedIn
            sendOK(s, address, code_time)
        elif message.startswith(Command.Message):
            if state != State.LoggedIn:
                sendER(s, 11, address)
                continue

            code, user, sentmessage = message.split("#")
            if not isvalidcode(code):
                sendER(s, 5, address)
                continue
            if not existsuser(user):
                sendER(s, 9, address)
                continue

            if not checksentmessagelength(sentmessage):
                sendER(s, 10, address)
                continue

if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    s.bind(('', PORT))

    signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    while True:
        buffer, address = s.recvfrom(1024)
        print("Conexión aceptada del socket {0[0]}:{0[1]}.".format(address))

        if not os.fork():
            if buffer:
                session(s, buffer, address)
