"""Converte batidas em código Morse e traduz para texto.

1 batida  = ponto (.)
2 batidas = traço (-)

Pausas (silêncio depois da última batida):
  curta   (>= silencio_simbolo_s) fecha o ponto/traço
  média   (>= silencio_letra_s)   fecha a letra
  longa   (>= silencio_palavra_s) fecha a palavra (espaço)
"""

MORSE = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E", "..-.": "F",
    "--.": "G", "....": "H", "..": "I", ".---": "J", "-.-": "K", ".-..": "L",
    "--": "M", "-.": "N", "---": "O", ".--.": "P", "--.-": "Q", ".-.": "R",
    "...": "S", "-": "T", "..-": "U", "...-": "V", ".--": "W", "-..-": "X",
    "-.--": "Y", "--..": "Z",
    "-----": "0", ".----": "1", "..---": "2", "...--": "3", "....-": "4",
    ".....": "5", "-....": "6", "--...": "7", "---..": "8", "----.": "9",
    ".-.-.-": ".", "--..--": ",", "..--..": "?", "-.-.--": "!", "-....-": "-",
    "-..-.": "/",
}


class DecodificadorMorse:
    def __init__(
        self,
        duracao_bloco,
        silencio_simbolo_s=0.6,
        silencio_letra_s=1.5,
        silencio_palavra_s=3.0,
    ):
        self.duracao_bloco = duracao_bloco
        self.silencio_simbolo_s = silencio_simbolo_s
        self.silencio_letra_s = silencio_letra_s
        self.silencio_palavra_s = silencio_palavra_s
        self.reiniciar()

    def reiniciar(self):
        """Descarta tudo o que estava sendo montado (batidas, símbolos e letra)."""
        self._batidas = 0        # batidas do símbolo em andamento
        self._silencio = 0.0     # silêncio desde a última batida
        self._codigo = ""        # símbolos da letra em andamento
        self._invalida = False   # letra com algum símbolo inválido
        self._houve_letra = False  # já saiu letra desde o último espaço

    def processar_bloco(self, batida):
        """Chame uma vez por bloco (True se houve batida).

        Devolve uma lista de eventos (quase sempre vazia):
          ("simbolo", ".")            ponto ou traço reconhecido
          ("invalido", n)             grupo com n batidas (só 1 ou 2 valem)
          ("letra", "A", ".-")        letra completa (ou "?" se não existe)
          ("palavra",)                fim de palavra
        """
        eventos = []

        if batida:
            self._batidas += 1
            self._silencio = 0.0
            return eventos

        anterior = self._silencio
        self._silencio += self.duracao_bloco
        atual = self._silencio

        if self._batidas and anterior < self.silencio_simbolo_s <= atual:
            n = self._batidas
            self._batidas = 0
            if n == 1:
                self._codigo += "."
                eventos.append(("simbolo", "."))
            elif n == 2:
                self._codigo += "-"
                eventos.append(("simbolo", "-"))
            else:
                self._invalida = True
                eventos.append(("invalido", n))

        if (self._codigo or self._invalida) and anterior < self.silencio_letra_s <= atual:
            letra = "?" if self._invalida else MORSE.get(self._codigo, "?")
            eventos.append(("letra", letra, self._codigo))
            self._codigo = ""
            self._invalida = False
            self._houve_letra = True

        if self._houve_letra and anterior < self.silencio_palavra_s <= atual:
            self._houve_letra = False
            eventos.append(("palavra",))

        return eventos