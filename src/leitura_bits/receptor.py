"""Etapa 1 do Método 1: detecta batidas captadas pelo microfone e as converte em bits."""

import queue
import sys
import threading

import sounddevice as sd

from decodificador_bits import DecodificadorDeBits
from detector_batidas import DetectorDeBatidas

# ---------------- Parâmetros ajustáveis ----------------
TAXA_AMOSTRAGEM = 44100     # amostras por segundo
TAMANHO_BLOCO = 1024        # janela de análise (amostras por bloco, ~23 ms)
SEGUNDOS_CALIBRACAO = 2.0   # tempo medindo o ruído ambiente no início
MULTIPLICADOR_RUIDO = 4.0   # limiar = ruído ambiente x este valor
LIMIAR_MINIMO = 0.02        # limiar nunca fica abaixo disto (escala 0.0 a 1.0)
INTERVALO_MINIMO_S = 0.15   # tempo mínimo entre duas detecções (segundos)
SILENCIO_FIM_BIT_S = 0.6    # silêncio após as batidas que fecha o bit (segundos)
DISPOSITIVO = None          # None = microfone padrão; ou número do dispositivo
MOSTRAR_NIVEIS = False      # True: mostra nível e limiar (útil para ajustar)
BITS_POR_GRUPO = 8          # separa a sequência em grupos (8 = bytes)
# --------------------------------------------------------

# Cores ANSI: 0 em azul, 1 em verde
COR = {0: "\033[1;97;44m", 1: "\033[1;30;42m"}
RESET = "\033[0m"

# Dígitos grandes (5 linhas x 5 colunas)
DIGITOS = {
    0: ["█████", "█   █", "█   █", "█   █", "█████"],
    1: ["  █  ", " ██  ", "  █  ", "  █  ", "█████"],
}

fila_de_blocos = queue.Queue()
pedido_reiniciar = threading.Event()


def esperar_tecla_reiniciar():
    """Thread que espera o usuário apertar ENTER (ou digitar 'r' + ENTER) para reiniciar."""
    while True:
        try:
            input()
        except EOFError:
            return
        pedido_reiniciar.set()


def callback_audio(indata, frames, time_info, status):
    """Chamada pelo sounddevice a cada bloco. Deve ser rápida: só copia e enfileira."""
    if status:
        print(status, file=sys.stderr)
    fila_de_blocos.put(indata[:, 0].copy())  # canal 0 (mono)


def mostrar_bit_grande(bit):
    """Desenha o bit recebido em tamanho grande e colorido."""
    print()
    for linha in DIGITOS[bit]:
        print(f"    {COR[bit]}  {linha}  {RESET}")


def formatar_sequencia(bits):
    """Sequência colorida, separada em grupos de BITS_POR_GRUPO."""
    partes = []
    for i, b in enumerate(bits):
        if i and i % BITS_POR_GRUPO == 0:
            partes.append("  ")
        partes.append(f"{COR[b]} {b} {RESET}")
    return "".join(partes)


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
    decodificador = DecodificadorDeBits(
        duracao_bloco=TAMANHO_BLOCO / TAXA_AMOSTRAGEM,
        silencio_fim_s=SILENCIO_FIM_BIT_S,
    )
    bits = []

    threading.Thread(target=esperar_tecla_reiniciar, daemon=True).start()

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

                if pedido_reiniciar.is_set():
                    pedido_reiniciar.clear()
                    apagados = len(bits)
                    bits.clear()
                    decodificador.reiniciar()
                    print(f"\n\033[1;97;41m REINICIADO \033[0m  {apagados} bit(s) apagado(s). Pode começar de novo.\n")
                    continue

                if detector.calibrado and not aviso_escutando:
                    print(f"Limiar definido: {detector.limiar:.4f}")
                    print("Escutando o microfone... (ENTER = reiniciar bits, Ctrl+C = sair)\n")
                    aviso_escutando = True

                if not detector.calibrado:
                    continue

                if MOSTRAR_NIVEIS:
                    print(f"\rnível={detector.ultimo_nivel:.4f}  limiar={detector.limiar:.4f}   ",
                          end="", flush=True)

                resultado = decodificador.processar_bloco(batida)
                if resultado is None:
                    continue

                contagem, bit = resultado
                if bit is None:
                    print(f"\nGrupo com {contagem} batidas ignorado (use 1 batida = 0, 2 batidas = 1).")
                else:
                    bits.append(bit)
                    mostrar_bit_grande(bit)
                    print(f"\n    Bit #{len(bits)}: {bit}")
                    print(f"    Sequência: {formatar_sequencia(bits)}\n")
    except KeyboardInterrupt:
        print("\nReceptor encerrado.")
        if bits:
            print(f"Bits recebidos: {formatar_sequencia(bits)}")
    except sd.PortAudioError as erro:
        print(f"Erro ao acessar o microfone: {erro}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()