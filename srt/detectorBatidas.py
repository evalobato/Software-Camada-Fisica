"""Detecção de batidas a partir de blocos de áudio (sem depender do microfone)."""

import numpy as np


def calcular_rms(bloco):
    """Devolve o RMS (energia média) de um bloco de amostras."""
    bloco = np.asarray(bloco, dtype=np.float64)
    return float(np.sqrt(np.mean(np.square(bloco))))


class DetectorDeBatidas:
    def __init__(
        self,
        taxa_amostragem,
        tamanho_bloco,
        blocos_calibracao,
        multiplicador_ruido,
        limiar_minimo,
        intervalo_minimo_s,
    ):
        self.duracao_bloco = tamanho_bloco / taxa_amostragem
        self.blocos_calibracao = blocos_calibracao
        self.multiplicador_ruido = multiplicador_ruido
        self.limiar_minimo = limiar_minimo
        self.intervalo_minimo_s = intervalo_minimo_s

        self.limiar = None            # definido ao fim da calibração
        self.ultimo_nivel = 0.0       # útil para depuração
        self._niveis_calibracao = []
        self._tempo = 0.0             # tempo decorrido, em segundos
        self._tempo_ultima_batida = None
        self._acima_do_limiar = False

    @property
    def calibrado(self):
        return self.limiar is not None

    def processar_bloco(self, bloco):
        """Analisa um bloco. Devolve True se uma batida foi detectada nele."""
        nivel = calcular_rms(bloco)
        self.ultimo_nivel = nivel
        tempo_bloco = self._tempo
        self._tempo += self.duracao_bloco

        # Fase 1: calibração do ruído ambiente
        if not self.calibrado:
            self._niveis_calibracao.append(nivel)
            if len(self._niveis_calibracao) >= self.blocos_calibracao:
                ruido = float(np.median(self._niveis_calibracao))
                self.limiar = max(self.limiar_minimo, self.multiplicador_ruido * ruido)
            return False

        # Fase 2: detecção pela borda de subida
        acima = nivel > self.limiar
        subiu = acima and not self._acima_do_limiar
        self._acima_do_limiar = acima
        if not subiu:
            return False

        # Fase 3: respeitar o tempo mínimo entre detecções
        if (
            self._tempo_ultima_batida is not None
            and tempo_bloco - self._tempo_ultima_batida < self.intervalo_minimo_s
        ):
            return False

        self._tempo_ultima_batida = tempo_bloco
        return True