import math
import hashlib
import tkinter
import select
import socket
import json
from Blok import Blok, ustvari_zacetni_blok
from tkinter import *
from threading import Thread
from datetime import datetime

povezave = []
veriga_blokov: list[Blok] = []
tezavnost = 4

host = "localhost"
port = int(input("port?\n"))
user_name = input("ime?\n")

Interval_generiranja = 10
Interval_popravljanja = 10
pricakovan_cas = Interval_generiranja * Interval_popravljanja

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, port))
c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def izpisi_blok(blok):
    list_sporocil.insert(tkinter.END, "Block")

    za_not = f"Index: {blok.index}, Timestamp: {blok.timestamp}, Data: {blok.data}, Nonce: {blok.nonce}, " \
             f"tezavnosticulty: {blok.tezavnost}, Previous hash: {blok.previous_hash}, Hash: {blok.hash}"
    list_sporocil.insert(tkinter.END, za_not)
    list_sporocil.insert(tkinter.END, "")

    print("~~TRENUTNA VERIGA~~")
    print(veriga_blokov)


def validiraj(hash, tezavnost, previous_hash, prejsni_blok, timestamp):
    # validira hash in cas, ce je karkoli narobe ga vrze ven
    if hash[:tezavnost] != "0" * tezavnost:
        return False

    if previous_hash != prejsni_blok.hash:
        return False

    if datetime.timestamp(datetime.now()) + 60 <= timestamp:
        return False

    if timestamp <= prejsni_blok.timestamp - 60:
        return False

    return True


def mine():
    global tezavnost

    # ustvari zacetni blok
    if len(veriga_blokov) == 0:
        prvi_blok = ustvari_zacetni_blok()
        veriga_blokov.append(prvi_blok)

    prejsni_blok = veriga_blokov[-1]

    # oni pogoji za spreminjanje tezavnosti glede na potreben cas
    if len(veriga_blokov) > Interval_popravljanja:
        prevAdjustmentBlock = veriga_blokov[len(veriga_blokov) - Interval_popravljanja]
        time_taken = prejsni_blok.timestamp - prevAdjustmentBlock.timestamp

        if (pricakovan_cas / 2) > time_taken:
            tezavnost = tezavnost + 1
        elif (pricakovan_cas * 2) < time_taken:
            tezavnost = tezavnost - 1

    data = ""
    nonce = 0

    # Bassicaly glavni del rudarjenja
    while True:
        timestamp = datetime.timestamp(datetime.now())
        previous_hash = prejsni_blok.hash
        index = len(veriga_blokov)
        hash = hashlib.sha256((str(index) + str(timestamp) + str(data) + str(previous_hash) + str(tezavnost) + str(
            nonce)).encode()).hexdigest()

        if validiraj(hash, tezavnost, previous_hash, prejsni_blok, timestamp):
            break
        else:
            nonce += 1

    nov_blok = Blok(index, data, timestamp, hash, previous_hash, nonce, tezavnost)
    veriga_blokov.append(nov_blok)
    izpisi_blok(nov_blok)
    broadcast(veriga_blokov)
    nafilaj_blockchain_list()


def checkaj_blockchain(bloki):
    global veriga_blokov
    pridobljena_veriga = []

    for blok in bloki:
        pridobljena_veriga.append(Blok(
            int(blok["index"]), str(blok["data"]), float(blok["timestamp"]),
            str(blok["hash"]), str(blok["previous_hash"]), int(blok["nonce"]), int(blok["tezavnost"])
        ))

    moja_tezavnost = 0
    njegova_tezavnost = 0

    for blok in veriga_blokov:
        moja_tezavnost = moja_tezavnost + math.pow(2, blok.tezavnost)

    for blok in pridobljena_veriga:
        njegova_tezavnost = njegova_tezavnost + math.pow(2, blok.tezavnost)

    print(f"njegova tezina: {njegova_tezavnost}\nmoja tezina: {moja_tezavnost}")

    if njegova_tezavnost > moja_tezavnost:
        veriga_blokov = pridobljena_veriga

    nafilaj_blockchain_list()


# Server


def zazeni_server():
    list_sporocil.insert(tkinter.END, f"Poslusam na portu: {port}")

    s.listen()
    Thread(target=poslusaj_za_odjemalci).start()


def upravljanje_odjemalcev(conn, addr):
    ime = conn.recv(1024).decode()
    povezave.append(conn)
    list_sporocil.insert(tkinter.END, f"povezal se je {addr}")
    receive_from_client()


def poslusaj_za_odjemalci():
    while True:  # Sprejem povezave odjemalca
        try:
            conn, addr = s.accept()
            Thread(target=upravljanje_odjemalcev, args=(conn, addr,)).start()
        except Exception:
            print("Napaka pri povezavi odjemalca.")


# Pošlje sporočilo vsem odjemalcem
def broadcast(msg):
    try:
        for povezava in povezave:
            message = f"{user_name}: {msg}"
            povezava.send(bytes(message, "utf-8"))
    except Exception:
        print("Napaka pri pošiljanju vsem odjemalcem.")


# Poslušanje vseh odjemalcev
def receive_from_client():
    global veriga_blokov

    while True:
        try:
            for povezava in povezave:
                readable, _, _ = select.select([povezava], [], [], 1)
                if readable:
                    message = povezava.recv(8192).decode()
                    msg = message.split(" ", 1)
                    bloki = json.loads(msg[1])

                    checkaj_blockchain(bloki)

                    list_sporocil.insert(tkinter.END, message)
                else:
                    pass
        except Exception:
            print("Napaka pri prejemanju od vseh odjemalcev")
            return


# Odjemalec

def zazeni_odjemalca():
    c.send(user_name.encode())
    Thread(target=pridobi).start()


def pridobi():
    global veriga_blokov

    while True:
        try:
            message = c.recv(8192).decode()  # Sprejem sporočil
            msg = message.split(" ", 1)
            bloki = json.loads(msg[1])

            checkaj_blockchain(bloki)

            list_sporocil.insert(tkinter.END, message)
        except Exception:
            print("Napaka v prejemanju sporočila!")
            return

        # Pošiljanje sporočil


def send():
    odgovor = sporocilo.get()
    sporocilo.set("")
    list_sporocil.insert(tkinter.END, f"{user_name}: {odgovor}")
    broadcast(odgovor)


def povezi():
    njegov_port = int(sporocilo.get())
    sporocilo.set("")
    list_sporocil.insert(tkinter.END, f"Povezal na {njegov_port}")
    c.connect((host, njegov_port))
    povezave.append(c)
    zazeni_odjemalca()


# UI
root = Tk()
root.title("Blockchain")
root.configure(bg="grey20")

main_window = Frame(root, height=300, width=300, bg='gray20')
main_window.pack()

sporocilo = StringVar()
sporocilo.set("")

list_sporocil = Listbox(main_window, width=75, height=20, bg="grey25", fg="white")
list_sporocil.pack(side=LEFT, fill=BOTH)

blockchain_list = Listbox(main_window, width=15, height=20, bg="grey25", fg="white")
blockchain_list.pack(side=LEFT)


def nafilaj_blockchain_list():
    blockchain_list.delete(0, END)

    for blok in veriga_blokov:
        blockchain_list.insert(END, f"{blok.index}. blok")


def pokazi_blok(event):
    index = blockchain_list.curselection()[0]
    blok = veriga_blokov[index]

    info_window = Toplevel(root)
    info_window.title(f"{index}. blok")

    for kljuc, vrednost in blok.__dict__.items():
        Label(info_window, text=f"{kljuc}: {vrednost}").pack()


def zazeni_mine_v_odzadju():
    thread = Thread(target=mine)
    thread.start()
    rudari.config(state=DISABLED)
    thread.join()
    rudari.config(state=NORMAL)


blockchain_list.bind("<Double-Button-1>", pokazi_blok)

Label(root, text="Sporočilo", bg="grey20", fg="white").pack(pady=15, padx=5, side=LEFT)
Entry(root, textvariable=sporocilo, fg="black", width=75).pack(pady=15, padx=5, side=LEFT)
Button(root, text="Poveži", font="Aerial", command=povezi).pack(pady=15, padx=5, side=LEFT)
rudari = Button(root, text="Mine", font="Aerial", command=mine)
rudari.pack(pady=15, padx=5, side=LEFT)

zazeni_server()

mainloop()
