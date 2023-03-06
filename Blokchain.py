import json
import time
from Blok import Blok


class Blockchain:
    def __init__(self, ali=True, veriga=None, tezavnost=3, interval_generiranja=3, interval_popravka=3):
        if ali:
            self.veriga = [self.ustvari_zaceten_blok()]
        else:
            self.veriga = veriga
        self.tezavnost = tezavnost
        self.interval_generiranja = interval_generiranja
        self.interval_popravka = interval_popravka
        self.pricakova_cas = self.interval_popravka * self.interval_generiranja

    @staticmethod
    def ustvari_zaceten_blok():
        return Blok(0, "Zaceten blok")

    def pridobi_zadnji_blok(self):
        return self.veriga[-1]

    def dodaj_blok(self, index: int, data: str):
        nov_blok = Blok(index, data)

        nov_blok.previous_hash = self.pridobi_zadnji_blok().hash
        potreben_cas = self.tezavnost_v_omrezju(nov_blok)
        # ne apendas takoj ampak ga posles se drugemu da ga validira?
        if self.validiraj(nov_blok):
            self.veriga.append(nov_blok)
            return potreben_cas, nov_blok
        return potreben_cas

    def validiraj(self, nov_blok):
        # Preveri ce je index pravilen, potem pa gre skozi celotno verigo in preveri pri vsakem hashi ce stimajo
        prejsni_blok = self.pridobi_zadnji_blok()

        if not (nov_blok.index - 1) == prejsni_blok.index:
            raise Exception("Index ne matcha")

        # rudarit more nehat pred manj kot minuto
        if time.time() - nov_blok.timestamp > 60:
            raise Exception("Prestar blok")

        # nov blok lahko dodajamo le na eno min
        if nov_blok.timestamp - self.pridobi_zadnji_blok().timestamp < 1:
            raise Exception("Prehitro rudaris")

        trenutni_blok = nov_blok

        # cekira vse hash vrednosti
        for blok in reversed(self.veriga):
            if not trenutni_blok.previous_hash == blok.hash:
                raise Exception("Hash ne stima")
            trenutni_blok = blok

        return True

    def tezavnost_v_omrezju(self, nov_blok):
        cas_zacetka = time.time()

        nov_blok.mine_block(self.tezavnost)

        pricakovan_cas = self.pricakova_cas
        cas_konca = time.time()
        potreben_cas = cas_konca - cas_zacetka

        if potreben_cas < (pricakovan_cas / 2) and self.tezavnost != 6:
            self.tezavnost += 1
        elif potreben_cas > (pricakovan_cas * 2) and self.tezavnost != 1:
            self.tezavnost -= 1

        print(f"Tezavnost: {self.tezavnost}, pricakovan_cas: {pricakovan_cas}, potreben_cas: {potreben_cas}")
        return potreben_cas

    def pridobi_zadnji_spremenjen_blok(self):
        # Ce je veriga prekratka, vrne zacetni element
        if len(self.veriga) < self.interval_popravka:
            return self.veriga[0]
        else:
            return self.veriga[-self.interval_popravka]

    def __repr__(self) -> json:
        veriga = [
            {
                "index": block.index,
                "timestamp": block.timestamp,
                "data": block.data,
                "previous_hash": block.previous_hash,
                "nonce": block.nonce,
                "hash": block.hash
            }
            for block in self.veriga
        ]

        blockchain = {
            "veriga": veriga,
            "tezavnost": self.tezavnost,
            "interval_generiranja": self.interval_generiranja,
            "interval_popravka": self.interval_popravka,
            "pricakovan_cas": self.pricakova_cas,
        }

        return json.dumps(blockchain, indent=1)
