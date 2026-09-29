"""Etapa 1 do Método 1: detecta batidas captadas pelo microfone."""

import queue
import sys

import sounddevice as sd

from detector_batidas import DetectorDeBatidas

# ---------------- Parâmetros ajustáveis ----------------
TAXA_AMOSTRAGEM = 44100     # amostras por segundo
TAMANHO_BLOCO = 1024        # janela de análise (amostras por bloco, ~23 ms)
SEGUNDOS_CALIBRACAO = 2.0   # tempo medindo o ruído ambiente no início
MULTIPLICADOR_RUIDO = 4.0   # limiar = ruído ambiente x este valor
LIMIAR_MINIMO = 0.02        # limiar nunca fica abaixo disto (escala 0.0 a 1.0)
INTERVALO_MINIMO_S = 0.15   # tempo mínimo entre duas detecções (segundos)
DISPOSITIVO = None          # None = microfone padrão; ou número do dispositivo
MOSTRAR_NIVEIS = False      # True: mostra nível e limiar (útil para ajustar)
# --------------------------------------------------------

fila_de_blocos = queue.Queue()


def callback_audio(indata, frames, time_info, status):
    """Chamada pelo sounddevice a cada bloco. Deve ser rápida: só copia e enfileira."""
    if status:
        print(status, file=sys.stderr)
    fila_de_blocos.put(indata[:, 0].copy())  # canal 0 (mono)


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

    print("Iniciando receptor...")
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
                    print("Escutando o microfone... (Ctrl+C para sair)\n")
                    aviso_escutando = True

                if MOSTRAR_NIVEIS and detector.calibrado:
                    print(f"\rnível={detector.ultimo_nivel:.4f}  limiar={detector.limiar:.4f}   ",
                          end="", flush=True)

                if batida:
                    print("\n[batida detectada]\n")
                    print("Batida detectada!\n")
    except KeyboardInterrupt:
        print("\nReceptor encerrado.")
    except sd.PortAudioError as erro:
        print(f"Erro ao acessar o microfone: {erro}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()