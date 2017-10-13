#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket, sys, os
import szasar
import signal
import random
import string
import time

class State:
    LoggedOut, LoggedIn = range(2)


class Command:
    Register, Indentificate, Message, Read, Exit = (
        "RG", "ID", "MS", "RD", "XT")

PORT = 6012
FILES_PATH = "files"
MAX_FILE_SIZE = 10 * 1 << 20  # 10 MiB
SPACE_MARGIN = 50 * 1 << 20  # 50 MiB
USERS = ["anonimous", "sar", "sza"]
PASSWORDS = ["", "sar", "sza"]
EMAILS = ["anonimous@gmail.com", "sar@gmail.com", "sza@gmail.com"]
CODE_TIME = {}
MESSAGES = {}
loggedUsername = ""
state = State.LoggedOut

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

def sendMessage(sender, receiver, message):
    if receiver in MESSAGES:
        MESSAGES[receiver].append((sender, message))
    else:
        MESSAGES[receiver] = [(sender, message)]

def session(s, buffer, address):
    while True:
        message = buffer.decode("ascii")
        if not message:
            return

        params = message[2:]

        if message.startswith(Command.Register):
            if (state != State.LoggedOut):
                sendER(s, 11, address)
                continue

            splitedParameters = params.split("#")
            if len(splitedParameters) > 3:
                sendER(s, address, 2)
            elif len(splitedParameters) < 3:
                sendER(s, address, 3)

            user, password, email = splitedParameters

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

                splitedParameters = params.split("#")
                if len(splitedParameters) > 2:
                    sendER(s, address, 2)
                elif len(splitedParameters) < 2:
                    sendER(s, address, 3)

            user, password = splitedParameters
            if not existsuser(user):
                sendER(s, 8, address)

            if not checkpassword(user, password):
                sendER(s, 8, address)
                continue

            code_time = generateandregistercodetime()

            loggedUsername = user
            state = State.LoggedIn

            sendOK(s, address, code_time)

        elif message.startswith(Command.Message):
            if state != State.LoggedIn:
                sendER(s, 11, address)
                continue

                splitedParameters = params.split("#")
                if len(splitedParameters) > 3:
                    sendER(s, address, 2)
                elif len(splitedParameters) < 3:
                    sendER(s, address, 3)

            code, user, sentmessage = splitedParameters
            if not isvalidcode(code):
                sendER(s, 5, address)
                continue
            if not existsuser(user):  # receiver
                sendER(s, 9, address)
                continue

            if not checksentmessagelength(sentmessage):
                sendER(s, 10, address)
                continue

                sendMessage(loggedUsername, user, sentmessage)
                sendOK(s, address)
                continue

        elif message.startswith(Command.Read):
            if state != State.LoggedIn:
                sendER(s, 11, address)
                continue

            splitedParameters = params.split("#")
            if len(splitedParameters) > 1:
                sendER(s, address, 2)
            elif len(splitedParameters) < 1:
                sendER(s, address, 3)

            code = params
            if not isvalidcode(code):
                sendER(s, 5, address)
                continue

            messageQuantity = len(MESSAGES[loggedUsername])
            sendOK(s, address, messageQuantity)
            if MESSAGES[loggedUsername]:
                for item in MESSAGES[loggedUsername]:
                    s.sendto(item[0] + "#" + item[1], address)

        elif message.startswith(Command.Exit):
            if state != State.LoggedIn:
                sendER(s, 11, address)
                continue

            splitedParameters = params.split("#")
            if len(splitedParameters) > 1:
                sendER(s, address, 2)
            elif len(splitedParameters) < 1:
                sendER(s, address, 3)

            code = params
            if not isvalidcode(code):
                sendER(s, 5, address)
                continue

            del CODE_TIME[code]
            loggedUsername = ""
            State.LoggedOut
            continue
        else:
            sendER(s, address, 1)


if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    s.bind(('', PORT))

    signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    while True:
        buffer, address = s.recvfrom(1024)
        print("Conexión aceptada del socket {0[0]}:{0[1]}.".format(address))

        if not os.fork():
            if buffer:
                session(s, buffer, address)  # tiene que ser concurrente
