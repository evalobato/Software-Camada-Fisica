"""Ajustes para o programa rodar igual em Windows, Linux e macOS.

Usado por receptor.py (bits) e receptor_morse.py (Morse).
"""

import argparse
import os
import sys


def configurar_saida():
    """Terminal pronto para as cores e símbolos do programa.

    - Força UTF-8 (troca por '?' o que não puder mostrar, em vez de cair).
    - No Windows, liga o suporte a cores ANSI do console (cmd e PowerShell antigos).
    """
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if os.name == "nt":
        os.system("")  # efeito colateral conhecido: ativa as sequências ANSI no console


def ler_argumentos(descricao):
    """Opções de linha de comando, para trocar de microfone/alto-falante sem editar o código."""
    p = argparse.ArgumentParser(description=descricao)
    p.add_argument("--listar", action="store_true",
                   help="lista os dispositivos de áudio (com seus números) e sai")
    p.add_argument("--entrada", type=int, metavar="N",
                   help="número do microfone a usar (padrão: o do sistema)")
    p.add_argument("--saida", type=int, metavar="N",
                   help="número do alto-falante a usar (padrão: o do sistema)")
    return p.parse_args()


def listar_dispositivos(sd):
    print(sd.query_devices())
    print("\n'>' = microfone padrão, '<' = alto-falante padrão.")
    print("Use o número da esquerda: python <programa> --entrada N --saida N")


def _aceita(verificar, **argumentos):
    try:
        verificar(**argumentos)
        return True
    except Exception:
        return False


def escolher_taxa(sd, entrada, saida, preferida):
    """Taxa de amostragem aceita pelo microfone (e, se possível, pelo alto-falante).

    Começa pela preferida (44100 Hz). Se o dispositivo não aceitar, tenta 48000 Hz e as
    taxas padrão dos próprios dispositivos. Isso evita o erro "Invalid sample rate" em
    placas que só trabalham em 48000 Hz.
    """
    candidatas = [preferida]
    for dispositivo, tipo in ((entrada, "input"), (saida, "output")):
        try:
            candidatas.append(int(sd.query_devices(dispositivo, tipo)["default_samplerate"]))
        except Exception:
            pass
    candidatas += [48000, 44100]
    vistas = []
    for taxa in candidatas:
        if taxa not in vistas:
            vistas.append(taxa)

    na_entrada = [t for t in vistas if _aceita(
        sd.check_input_settings, device=entrada, channels=1, dtype="float32", samplerate=t)]
    if not na_entrada:
        return preferida  # deixa a abertura do microfone mostrar o erro de verdade
    na_saida = [t for t in na_entrada if _aceita(
        sd.check_output_settings, device=saida, channels=1, samplerate=t)]
    escolhida = (na_saida or na_entrada)[0]
    if escolhida != preferida:
        print(f"Taxa de amostragem ajustada para {escolhida} Hz "
              f"(o dispositivo não aceita {preferida} Hz).")
    return escolhida