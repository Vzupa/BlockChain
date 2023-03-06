import time
import traceback
from threading import Thread
import hashlib
import json
import math
import select
import socket
import tkinter
from datetime import datetime
from tkinter import *
import Blok

povezave = []

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("localhost", 8080))

blockchain: list[Blok] = []
interval_generiranja = 10
interval_popravljanja = 10
pricakovan_cas = interval_popravljanja * interval_generiranja


def validiraj(nov_blok):
    if time.time() - nov_blok.timestamp > 60:
        raise Exception("Prestar")

    if nov_blok.timestamp - blockchain[-1].timestamp < 1:
        raise Exception("Prehitro rudaris")

    for blok in reversed(blockchain):
        if not nov_blok.previous_hash == blok.hash:
            raise Exception("Hash ne stima")
        nov_blok = blok


def rudari():
    tezavnost = 4

    if len(blockchain) == 0:
        blockchain.append(Blok.Blok(0, "Zaceten", 0))

    prejsni_blok = blockchain[-1]

    if len(blockchain) > interval_popravljanja:
        print("popravljam")
        prejsni_popravek = blockchain[len(blockchain) - interval_popravljanja]

        porabljen_cas = prejsni_blok.timestamp - prejsni_popravek.timestamp

        if (pricakovan_cas / 2) > porabljen_cas:
            tezavnost = tezavnost + 1
        elif (pricakovan_cas * 2) < porabljen_cas:
            tezavnost = tezavnost - 1

    index = len(blockchain)
    data = f"Blok: {index}"
    nov_blok = Blok.Blok(index, data, tezavnost, previous_hash=prejsni_blok.hash)
    nov_blok.mine_block()

    try:
        validiraj(nov_blok)
        blockchain.append(nov_blok)
        # broadcast(blockchain)
    except Exception:
        traceback.print_exc()
    print(blockchain)


# random utility
def checkaj_chain(bloki):
    global blockchain
    njegov_blockchain = []

    for blok in bloki:
        njegov_blockchain.append(Blok.Blok(
            int(blok["index"]), blok["data"], int(blok["diff"]), float("timestamp"),
            blok["previous_hash"], int(blok["nounce"])
        ))

    moja_tezina = 0
    njegova_tezina = 0

    for blok in blockchain:
        moja_tezina = moja_tezina + math.pow(2, blok.diff)

    for blok in njegov_blockchain:
        njegova_tezina = njegova_tezina + math.pow(2, blok.diff)

    if njegova_tezina > moja_tezina:
        blockchain = njegov_blockchain


# server

def zazeni_server():
    s.listen()
    Thread(target=poslusaj_za_odjemalce).start()


def zrihtaj_odjemalce(conn, addr):
    povezave.append(conn)


def poslusaj_za_odjemalce():
    while True:
        try:
            conn, addr = s.accept()
            Thread(target=zrihtaj_odjemalce, args=(conn, addr)).start()
        except Exception:
            traceback.print_exc()


def broadcast(sporocilo):
    try:
        for povezava in povezave:
            povezava.send(bytes(sporocilo))

        rudari()
    except Exception:
        traceback.print_exc()


def pridobi_od_odjemalca():
    while True:
        try:
            for povezava in povezave:
                readable, _, _ = select.select([povezava], [], [], 1)

                if readable:
                    sporocilo = povezava.recv(4096).decode()
                    sporocilo = sporocilo.split(" ", 1)
                    bloki = json.loads(sporocilo[1])

                    checkaj_chain(bloki)
        except Exception:
            traceback.print_exc()


# Odjemalec

def zazeni_odjemalca():
    Thread(target=pridobi).start()


def pridobi():
    while True:
        try:
            sporocilo = c.recv(4096).decode()
            sporocilo = sporocilo.split("", 1)
            bloki = json.loads(sporocilo[1])

            checkaj_chain(bloki)
        except Exception:
            traceback.print_exc()


def povezi():
    port = 1000
    c.connect(("localhost", 8080))
    povezave.append(c)
    zazeni_odjemalca()