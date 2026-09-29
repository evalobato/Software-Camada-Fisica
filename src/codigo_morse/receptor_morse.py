"""Receptor Morse: detecta batidas no microfone, forma código Morse e traduz para texto.

1 batida = ponto (.)   |   2 batidas = traço (-)
Pausa curta fecha o símbolo, pausa média fecha a letra, pausa longa fecha a palavra.
ENTER apaga tudo (mensagem e letra em andamento).
"""

import queue
import sys
import threading

import sounddevice as sd

from decodificador_morse import DecodificadorMorse
from detector_batidas import DetectorDeBatidas

# ---------------- Parâmetros ajustáveis ----------------
TAXA_AMOSTRAGEM = 44100     # amostras por segundo
TAMANHO_BLOCO = 1024        # janela de análise (amostras por bloco, ~23 ms)
SEGUNDOS_CALIBRACAO = 2.0   # tempo medindo o ruído ambiente no início
MULTIPLICADOR_RUIDO = 4.0   # limiar = ruído ambiente x este valor
LIMIAR_MINIMO = 0.02        # limiar nunca fica abaixo disto (escala 0.0 a 1.0)
INTERVALO_MINIMO_S = 0.15   # tempo mínimo entre duas detecções (segundos)
SILENCIO_SIMBOLO_S = 0.6    # silêncio que fecha um ponto/traço
SILENCIO_LETRA_S = 1.5      # silêncio que fecha uma letra
SILENCIO_PALAVRA_S = 3.0    # silêncio que fecha uma palavra (espaço)
DISPOSITIVO = None          # None = microfone padrão; ou número do dispositivo
MOSTRAR_NIVEIS = False      # True: mostra nível e limiar (útil para ajustar)
# --------------------------------------------------------

AZUL = "\033[1;97;44m"
VERDE = "\033[1;30;42m"
AMARELO = "\033[1;30;43m"
VERMELHO = "\033[1;97;41m"
RESET = "\033[0m"

fila_de_blocos = queue.Queue()
pedido_reiniciar = threading.Event()


def callback_audio(indata, frames, time_info, status):
    """Chamada pelo sounddevice a cada bloco. Deve ser rápida: só copia e enfileira."""
    if status:
        print(status, file=sys.stderr)
    fila_de_blocos.put(indata[:, 0].copy())  # canal 0 (mono)


def esperar_tecla_reiniciar():
    """Thread que espera ENTER para reiniciar."""
    while True:
        try:
            input()
        except EOFError:
            return
        pedido_reiniciar.set()


def desenhar_codigo(codigo):
    """Ponto e traço em blocos coloridos."""
    return " ".join(f"{AZUL} • {RESET}" if s == "." else f"{VERDE} ━━ {RESET}" for s in codigo)


def main():
    blocos_calibracao = int(SEGUNDOS_CALIBRACAO * TAXA_AMOSTRAGEM / TAMANHO_BLOCO)
    detector = DetectorDeBatidas(
        taxa_amostragem=TAXA_AMOSTRAGEM,
        tamanho_bloco=TAMANHO_BLOCO,
        blocos_calibracao=blocos_calibracao,
        multiplicador_ruido=MULTIPLICADOR_RUIDO,
        limiar_minimo=LIMIAR_MINIMO,
        intervalo_minimo_s=INTERVALO_MINIMO_S,
    )
    decodificador = DecodificadorMorse(
        duracao_bloco=TAMANHO_BLOCO / TAXA_AMOSTRAGEM,
        silencio_simbolo_s=SILENCIO_SIMBOLO_S,
        silencio_letra_s=SILENCIO_LETRA_S,
        silencio_palavra_s=SILENCIO_PALAVRA_S,
    )
    texto = ""
    codigo_atual = ""

    threading.Thread(target=esperar_tecla_reiniciar, daemon=True).start()

    print("Iniciando receptor Morse...")
    print(f"Calibrando ruído ambiente por {SEGUNDOS_CALIBRACAO:.0f} s (fique em silêncio)...")

    try:
        with sd.InputStream(
            samplerate=TAXA_AMOSTRAGEM,
            blocksize=TAMANHO_BLOCO,
            channels=1,
            dtype="float32",
            device=DISPOSITIVO,
            callback=callback_audio,
        ):
            aviso_escutando = False
            while True:
                bloco = fila_de_blocos.get()
                batida = detector.processar_bloco(bloco)

                if detector.calibrado and not aviso_escutando:
                    print(f"Limiar definido: {detector.limiar:.4f}")
                    print("Escutando o microfone...")
                    print("  1 batida = ponto | 2 batidas = traço")
                    print("  pausa média = nova letra | pausa longa = nova palavra")
                    print("  ENTER = apagar tudo | Ctrl+C = sair\n")
                    aviso_escutando = True

                if not detector.calibrado:
                    continue

                if MOSTRAR_NIVEIS:
                    print(f"\rnível={detector.ultimo_nivel:.4f}  limiar={detector.limiar:.4f}   ",
                          end="", flush=True)

                if pedido_reiniciar.is_set():
                    pedido_reiniciar.clear()
                    apagado = texto.strip()
                    texto = ""
                    codigo_atual = ""
                    decodificador.reiniciar()
                    detalhe = f' (mensagem apagada: "{apagado}")' if apagado else ""
                    print(f"\n{VERMELHO} REINICIADO {RESET}{detalhe} Pode começar de novo.\n")
                    continue

                for evento in decodificador.processar_bloco(batida):
                    tipo = evento[0]
                    if tipo == "simbolo":
                        codigo_atual += evento[1]
                        print(f"  {desenhar_codigo(evento[1])}   letra em montagem: {codigo_atual}")
                    elif tipo == "invalido":
                        print(f"  Grupo com {evento[1]} batidas ignorado (use 1 = ponto, 2 = traço).")
                    elif tipo == "letra":
                        _, letra, codigo = evento
                        codigo_atual = ""
                        texto += letra
                        print(f"\n  {desenhar_codigo(codigo)}  →  {AMARELO} {letra} {RESET}")
                        print(f"  Mensagem: {texto}\n")
                    elif tipo == "palavra":
                        texto += " "
                        print(f"  (espaço)  Mensagem: {texto}|\n")
    except KeyboardInterrupt:
        print("\nReceptor encerrado.")
        if texto.strip():
            print(f"Mensagem final: {texto.strip()}")
    except sd.PortAudioError as erro:
        print(f"Erro ao acessar o microfone: {erro}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()