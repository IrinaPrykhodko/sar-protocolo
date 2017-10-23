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
currentstate = State.LoggedOut

def sendOK(s, address, params=""):
    print("Sending OK...")
    s.sendto(("OK{}".format(params)).encode("ascii"), address)

def sendER(s, address, code=1):
    print("Sending ER...", code)
    s.sendto(("ER{}".format(code)).encode("ascii"), address)

def existsuser(user):
    print("Checking if user", user, "exists...")
    for username in USERS:
        if username == user:
            print(user, "exists")
            return True
    print(user, "not exists")
    return False

def existsemail(email):
    print("Checking email", email, "existst...")
    for emailaddress in EMAILS:
        if emailaddress == email:
            print(email, "exists")
            return True
    print(email, "don't exists")
    return False

def registeruser(username, password, email):
    print("Registering user", username, "with password", password, "...")
    USERS.append(username)
    PASSWORDS.append(password)
    EMAILS.append(email)

def checkpassword(username, password):
    print("Checking password for user", username)
    print(USERS)
    print(PASSWORDS)
    print(EMAILS)
    indexforthatuser = USERS.index(username)

    if PASSWORDS[indexforthatuser] == password:
        print("Password matchs")
        return True
    else:
        print("Password don't match")
        return False

def generateandregistercodetime():
    print("Generating and registering a random code")
    code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    sparetime = 2000.0
    codetime = code + "#" + str(sparetime).split(".")[0]
    expirationtime = time.time() + sparetime

    CODE_TIME[code] = expirationtime

    return codetime

def isvalidcode(code):  # check code and time
    if not code:
        sendER(s, address, 2)
        return

    if not code in list(CODE_TIME.keys()):
        return False

    expirationtime = CODE_TIME[code]
    currenttime = int(time.time())
    if expirationtime < currenttime:
        print("is not valid code")
        return False
    else:
        print("is valid code")
        return True

def issamecode(code):  # check only code, not time
    if not code:
        sendER(s, address, 2)
        return

def checksentmessagelength(sentmessage):
    if len(sentmessage) > 140:
        print("Wrong message length")
        return False
    else:
        print("message length ok")
        return True

def sendMessage(sender, receiver, message):
    print("sending message", message)
    if receiver in MESSAGES:
        MESSAGES[receiver].append((sender, message))
    else:
        MESSAGES[receiver] = [(sender, message)]

def session(s, buffer, address):
    print("session()")
    global loggedUsername
    global currentstate

    message = buffer.decode("ascii")
    if not message:
        return

    print('<<<<<', message)

    params = message[2:-1]  # quitamos el salto de línea \n

    if message.startswith(Command.Register):
        print("Recibida petición de registro")

        if currentstate != State.LoggedOut:
            sendER(s, address, 1)
            return

        splitedParameters = params.split("#")
        if len(splitedParameters) > 3:
            sendER(s, address, 2)
            return
        elif len(splitedParameters) < 3:
            sendER(s, address, 3)
            return

        user, password, email = splitedParameters

        if existsuser(user):
            sendER(s, address, 6)
            return

        if existsemail(email):
            sendER(s, address, 7)
            return

        registeruser(user, password, email)
        sendOK(s, address)
    elif message.startswith(Command.Indentificate):
        print("Recibida petición de identificación")

        if currentstate != State.LoggedOut:
            sendER(s, address, 1)
            return

        splitedParameters = params.split("#")
        if len(splitedParameters) > 2:
            sendER(s, address, 2)
            return
        elif len(splitedParameters) < 2:
            sendER(s, address, 3)
            return

        user, password = splitedParameters
        if not existsuser(user):
            sendER(s, address, 8)
            return

        if not checkpassword(user, password):
            sendER(s, address, 8)
            return

        code_time = generateandregistercodetime()

        loggedUsername = user
        currentstate = State.LoggedIn

        sendOK(s, address, code_time)

    elif message.startswith(Command.Message):
        print("Recibida petición de envío de mensaje")

        if currentstate != State.LoggedIn:
            sendER(s, address, 1)
            return

        splitedParameters = params.split("#")
        if len(splitedParameters) > 3:
            sendER(s, address, 2)
            return
        elif len(splitedParameters) < 3:
            sendER(s, address, 3)
            return

        code, user, sentmessage = splitedParameters
        if not isvalidcode(code):
            sendER(s, address, 5)
            return
        if not existsuser(user):  # receiver
            sendER(s, address, 9)
            return

        if not checksentmessagelength(sentmessage):
            sendER(s, address, 10)
            return

        sendMessage(loggedUsername, user, sentmessage)
        sendOK(s, address)
        return

    elif message.startswith(Command.Read):
        print("Recibida petición de lectura de mensajes")

        if currentstate != State.LoggedIn:
            sendER(s, address, 1)
            return

        splitedParameters = params.split("#")
        if len(splitedParameters) > 1:
            sendER(s, address, 2)
            return
        elif len(splitedParameters) < 1:
            sendER(s, address, 3)
            return

        code = params
        if not isvalidcode(code):
            sendER(s, address, 5)
            return

        if loggedUsername in list(MESSAGES.keys()):
            messageQuantity = len(MESSAGES[loggedUsername])
            sendOK(s, address, messageQuantity)
            if MESSAGES[loggedUsername]:
                for item in MESSAGES[loggedUsername]:
                    s.sendto((item[0] + "#" + item[1]).encode(), address)
        else:
            messageQuantity = 0
            sendOK(s, address, messageQuantity)

    elif message.startswith(Command.Exit):
        print("Recibida petición de cierre de sesión")

        if currentstate != State.LoggedIn:
            sendER(s, address, 1)
            return

        splitedParameters = params.split("#")
        if len(splitedParameters) > 1:
            sendER(s, address, 2)
            return
        elif len(splitedParameters) < 1:
            sendER(s, address, 3)
            return

        code = params
        if not isvalidcode(code):
            sendER(s, address, 5)
            return

        del CODE_TIME[code]
        loggedUsername = ""
        currentstate = State.LoggedOut
        return
    else:
        print("Recibida una orden desconocida")
        sendER(s, address, 1)
        return

if __name__ == "__main__":
    print('Starting...')

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    s.bind(('', PORT))

    signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    print('Running...')
    while True:
        print("Dentro")
        buffer, address = s.recvfrom(1024)
        print("Despues")

        print("Conexión aceptada del socket {0[0]}:{0[1]}.".format(address))

        """if not os.fork():
            print('Hijo atendiendo...')
            if buffer:
                session(s, buffer, address)  # tiene que ser concurrente
            s.close()
            exit(0)"""
        if buffer:
            session(s, buffer, address)  # tiene que ser concurrente

    s.close()