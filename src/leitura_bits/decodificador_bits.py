"""Converte grupos de batidas em bits.

silêncio, 1 batida,  silêncio -> 0
silêncio, 2 batidas, silêncio -> 1
"""


class DecodificadorDeBits:
    def __init__(self, duracao_bloco, silencio_fim_s=0.6):
        self.duracao_bloco = duracao_bloco
        self.silencio_fim_s = silencio_fim_s  # silêncio que encerra um grupo de batidas
        self._contagem = 0
        self._silencio = 0.0

    def reiniciar(self):
        """Descarta um grupo de batidas que ainda estava sendo contado."""
        self._contagem = 0
        self._silencio = 0.0

    def processar_bloco(self, batida):
        """Chame uma vez por bloco, com True se o bloco teve batida.

        Devolve None enquanto o grupo não terminou. Quando o silêncio depois
        das batidas é longo o bastante, devolve (contagem, bit), onde bit é
        0, 1 ou None (quantidade de batidas que não representa nenhum bit).
        """
        if batida:
            self._contagem += 1
            self._silencio = 0.0
            return None

        if self._contagem == 0:
            return None

        self._silencio += self.duracao_bloco
        if self._silencio < self.silencio_fim_s:
            return None

        contagem = self._contagem
        self._contagem = 0
        self._silencio = 0.0
        bit = {1: 0, 2: 1}.get(contagem)
        return contagem, bit