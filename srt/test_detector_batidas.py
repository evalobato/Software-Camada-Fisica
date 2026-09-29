"""Testes com sinais sintéticos (não precisam de microfone). Rode: pytest"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from detector_batidas import DetectorDeBatidas  # noqa: E402

TAXA = 44100
BLOCO = 1024
CALIBRACAO = 10
rng = np.random.default_rng(0)


def ruido():
    return rng.normal(0, 0.005, BLOCO)   # ruído ambiente fraco


def batida():
    return rng.normal(0, 0.3, BLOCO)     # bloco com som forte


def novo_detector():
    return DetectorDeBatidas(TAXA, BLOCO, CALIBRACAO, 4.0, 0.02, 0.15)


def contar(blocos):
    detector = novo_detector()
    return sum(detector.processar_bloco(b) for b in blocos)


def test_ruido_constante_nao_gera_batida():
    assert contar([ruido() for _ in range(200)]) == 0


def test_tres_batidas_separadas_sao_tres_deteccoes():
    blocos = [ruido() for _ in range(CALIBRACAO)]
    for _ in range(3):
        blocos.append(batida())
        blocos.extend(ruido() for _ in range(20))   # ~0,46 s de silêncio
    assert contar(blocos) == 3


def test_intervalo_minimo_ignora_repique():
    blocos = [ruido() for _ in range(CALIBRACAO)]
    blocos += [batida(), ruido(), batida()]          # ~46 ms entre elas
    blocos += [ruido() for _ in range(20)]
    assert contar(blocos) == 1