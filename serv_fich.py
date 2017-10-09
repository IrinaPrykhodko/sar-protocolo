#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket, sys, os
import szasar
import signal

PORT = 6012
FILES_PATH = "files"
MAX_FILE_SIZE = 10 * 1 << 20  # 10 MiB
SPACE_MARGIN = 50 * 1 << 20  # 50 MiB
USERS = ["anonimous", "sar", "sza"]
PASSWORDS = ["", "sar", "sza"]
EMAILS = ["anonimous@gmail.com", "sar@gmail.com", "sza@gmail.com"]
CODE_TIME = {}

CODE_TIME


class State:
    LoggedOut, LoggedIn = range(2)


class Command:
    Register, Indentificate, Message, Read, Exit = (
        "RG", "ID", "MS", "RD", "XT")


def sendOK(s, address, params=""):
    s.sendto(("OK{}".format(params)).encode("ascii"), address)


def sendER(s, address, code=1):
    s.sendto(("ER{}".format(code)).encode("ascii"), address)

def existsUser(user):
    for username in USERS:
        if username == user:
            return True
    return False

def existsEmail(email):
    for emailaddress in EMAILS:
        if emailaddress == email:
            return True
    return False

def registerUser(username, password, email):
    USERS.append(username)
    PASSWORDS.append(password)
    EMAILS.append(email)


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

            if existsUser(user):
                sendER(s, 6, address)
                continue

            if existsEmail(email):
                sendER(s, 7, address)
                continue

            registerUser(user, password, email)
            sendOK(s, address)
        elif message.startswith(Command.Indentificate):
            if state != State.LoggedOut:
                sendER(s, 11, address)
                continue

            user, password = message.split("#")
            if not checkPassword(user, password):
                sendER(s, 8, address)
            elif
                code_time = generateandregistercodetime()  # "f6df5#003"
                sendOK(s, address, code_time)


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
