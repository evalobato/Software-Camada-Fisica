"""Detecta batidas captadas pelo microfone e as converte em bits, com verificação de erros.

Detecção de erros (Método 2): paridade par. A cada 8 bits de dados vem 1 bit de paridade,
formando quadros de 9 bits. O receptor confere cada quadro assim que ele fecha.
"""

import queue
import sys
import threading

import numpy as np
import sounddevice as sd

from decodificador_bits import DecodificadorDeBits
from detector_batidas import DetectorDeBatidas
from paridade import BITS_DADOS, BITS_POR_QUADRO, analisar_ultimo, dados_para_texto

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
SOM_ATIVO = True            # toca um som de confirmação a cada bit
VOLUME = 0.5                # volume do som (0.0 a 1.0)
SAIDA = None                # None = alto-falante padrão; ou número do dispositivo de saída
MARGEM_SOM_S = 0.25         # tempo extra sem escutar depois do som (evita eco)
ESPERA_INICIAL_S = 2.0      # na reprodução: tempo antes do primeiro bit (o outro PC já deve estar escutando)
FOLGA_ENTRE_BITS_S = 0.3    # na reprodução: folga extra entre um bit e o próximo
# --------------------------------------------------------

# Sons de confirmação: lista de (frequência em Hz, duração em s); frequência 0 = pausa.
# Cada bit tem o seu som, fácil de distinguir de ouvido.
SONS = {
    0: [(440, 0.30)],                              # bit 0: um bipe grave e longo
    # A pausa entre os dois bipes do bit 1 precisa ser maior que INTERVALO_MINIMO_S (0,15 s)
    # e menor que SILENCIO_FIM_BIT_S (0,6 s) para outro PC contar duas batidas.
    1: [(988, 0.12), (0, 0.20), (988, 0.12)],      # bit 1: dois bipes agudos e curtos
    "erro": [(180, 0.35)],                         # grupo inválido: zumbido grave
}
# Bit que fecha um quadro com paridade errada: o som do bit seguido do zumbido de erro
for _b in (0, 1):
    SONS[f"{_b}erro"] = SONS[_b] + [(0, 0.10)] + SONS["erro"]

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
encerrado = threading.Event()        # ligado quando o receptor é encerrado (Ctrl+C)
fila_comandos = queue.Queue()        # comandos digitados depois de encerrar


def ler_teclado():
    """Thread única que lê o teclado.

    Durante a escuta, ENTER reinicia os bits. Depois de encerrado, o que for
    digitado vai para a fila de comandos (menu final).
    """
    while True:
        try:
            linha = input()
        except EOFError:
            fila_comandos.put(None)
            return
        if encerrado.is_set():
            fila_comandos.put(linha.strip().lower())
        else:
            pedido_reiniciar.set()


def callback_audio(indata, frames, time_info, status):
    """Chamada pelo sounddevice a cada bloco. Deve ser rápida: só copia e enfileira."""
    if status:
        print(status, file=sys.stderr)
    fila_de_blocos.put(indata[:, 0].copy())  # canal 0 (mono)


def montar_som(partes):
    """Gera as amostras de um som a partir de uma lista de (frequência, duração)."""
    pedacos = []
    for freq, dur in partes:
        n = int(TAXA_AMOSTRAGEM * dur)
        if freq == 0:
            pedacos.append(np.zeros(n, dtype=np.float32))
            continue
        t = np.arange(n) / TAXA_AMOSTRAGEM
        onda = np.sin(2 * np.pi * freq * t)
        rampa = min(n // 2, int(0.008 * TAXA_AMOSTRAGEM))  # fade curto: evita estalos
        if rampa:
            envelope = np.ones(n)
            envelope[:rampa] = np.linspace(0, 1, rampa)
            envelope[-rampa:] = np.linspace(1, 0, rampa)
            onda *= envelope
        pedacos.append((VOLUME * onda).astype(np.float32))
    return np.concatenate(pedacos)


SONS_PRONTOS = {}
DURACAO_SONS = {}


def preparar_sons():
    for nome, partes in SONS.items():
        SONS_PRONTOS[nome] = montar_som(partes)
        DURACAO_SONS[nome] = sum(dur for _, dur in partes)


def tocar(nome):
    """Toca o som sem travar o programa. Devolve a duração (0 se não tocou)."""
    global SOM_ATIVO
    if not SOM_ATIVO:
        return 0.0
    try:
        sd.play(SONS_PRONTOS[nome], samplerate=TAXA_AMOSTRAGEM, device=SAIDA)
    except sd.PortAudioError as erro:
        print(f"Sem som de confirmação ({erro}).", file=sys.stderr)
        SOM_ATIVO = False
        return 0.0
    return DURACAO_SONS[nome]


def reproduzir_bits(bits):
    """Toca, um a um, o som de cada bit recebido (o mesmo da confirmação)."""
    # Pausa entre bits: o outro PC só fecha o bit após SILENCIO_FIM_BIT_S de silêncio, depois
    # toca o próprio som de confirmação e fica surdo por MARGEM_SOM_S. O próximo bit só pode
    # começar depois disso tudo.
    pausa = (SILENCIO_FIM_BIT_S + max(DURACAO_SONS.values())
             + MARGEM_SOM_S + FOLGA_ENTRE_BITS_S)
    print(f"\nReproduzindo {len(bits)} bit(s)... (Ctrl+C interrompe)")
    print(f"Começa em {ESPERA_INICIAL_S:.0f} s; {pausa:.1f} s entre os bits. "
          "Para outro PC ler, ele deve estar escutando e perto do alto-falante.\n")
    try:
        sd.sleep(int(ESPERA_INICIAL_S * 1000))
        for i, bit in enumerate(bits, start=1):
            print(f"  {i:>3}/{len(bits)}  {COR[bit]} {bit} {RESET}")
            sd.play(SONS_PRONTOS[bit], samplerate=TAXA_AMOSTRAGEM, device=SAIDA)
            sd.wait()
            if i < len(bits):
                sd.sleep(int(pausa * 1000))
    except KeyboardInterrupt:
        sd.stop()
        print("\nReprodução interrompida.")
        return
    except sd.PortAudioError as erro:
        print(f"Não consegui tocar o som: {erro}", file=sys.stderr)
        return
    print("\nFim da reprodução.")


def menu_final(bits):
    """Depois de encerrar: aceita comandos para reproduzir os bits ou sair."""
    print(f"\nBits recebidos ({len(bits)}): {formatar_sequencia(bits)}")
    for linha in descrever_quadros(bits):
        print(linha)
    print("\nComandos:  r + ENTER = reproduzir/enviar os bits   |   s + ENTER = sair")
    while True:
        try:
            comando = fila_comandos.get()
        except KeyboardInterrupt:
            return
        if comando in (None, "s", "sair"):
            return
        if comando in ("r", "reproduzir"):
            reproduzir_bits(bits)
            print("\nComandos:  r + ENTER = reproduzir de novo   |   s + ENTER = sair")
        else:
            print("Comando não reconhecido. Use r (reproduzir) ou s (sair).")


def mostrar_bit_grande(bit):
    """Desenha o bit recebido em tamanho grande e colorido."""
    print()
    for linha in DIGITOS[bit]:
        print(f"    {COR[bit]}  {linha}  {RESET}")


def formatar_sequencia(bits):
    """Sequência colorida, em quadros de 9 bits; o bit de paridade (o 9º) aparece sublinhado."""
    partes = []
    for i, b in enumerate(bits):
        if i and i % BITS_POR_QUADRO == 0:
            partes.append("  ")
        sublinhado = "\033[4m" if i % BITS_POR_QUADRO == BITS_DADOS else ""
        partes.append(f"{COR[b]}{sublinhado} {b} {RESET}")
    return "".join(partes)


def descrever_quadros(bits):
    """Resumo de cada quadro completo (e do quadro incompleto no fim, se houver)."""
    linhas = []
    for ini in range(0, len(bits) - BITS_POR_QUADRO + 1, BITS_POR_QUADRO):
        quadro = bits[ini:ini + BITS_POR_QUADRO]
        info = analisar_ultimo(bits[:ini + BITS_POR_QUADRO])
        dados, ok = info["quadro"]
        valor, letra = dados_para_texto(dados)
        txt = f" '{letra}'" if letra else ""
        estado = "\033[1;30;42m OK \033[0m" if ok else "\033[1;97;41m ERRO \033[0m"
        linhas.append(f"  Quadro {ini // BITS_POR_QUADRO + 1}: {''.join(map(str, dados))}"
                      f" (valor {valor}{txt}) paridade={quadro[-1]}  {estado}")
    sobra = len(bits) % BITS_POR_QUADRO
    if sobra:
        linhas.append(f"  Quadro incompleto: faltam {BITS_POR_QUADRO - sobra} bit(s) "
                      "para fechar o último (não foi verificado).")
    return linhas


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
    preparar_sons()
    duracao_bloco = TAMANHO_BLOCO / TAXA_AMOSTRAGEM
    blocos_mudo = 0   # blocos a ignorar enquanto o som toca (o microfone o ouviria como batida)

    threading.Thread(target=ler_teclado, daemon=True).start()

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
                if blocos_mudo > 0 and detector.calibrado:
                    # Som tocando: alimenta o detector com silêncio para o tempo seguir correndo
                    blocos_mudo -= 1
                    bloco = np.zeros_like(bloco)
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
                    dur = tocar("erro")
                else:
                    bits.append(bit)
                    info = analisar_ultimo(bits)
                    quadro_com_erro = info["quadro"] is not None and not info["quadro"][1]
                    # som próprio de cada bit; se o quadro falhou na paridade, vem o zumbido junto
                    dur = tocar(f"{bit}erro" if quadro_com_erro else bit)
                    mostrar_bit_grande(bit)
                    papel = ("PARIDADE" if info["eh_paridade"]
                             else f"dado {info['posicao']}/{BITS_DADOS}")
                    print(f"\n    Bit #{len(bits)}: {bit}   ({papel})")
                    print(f"    Sequência: {formatar_sequencia(bits)}")

                    if info["paridade_esperada"] is not None:
                        p = info["paridade_esperada"]
                        print(f"    Próximo bit = PARIDADE. Valor correto: {p} "
                              f"({'2 batidas' if p else '1 batida'}).")
                    if info["quadro"] is not None:
                        dados, ok = info["quadro"]
                        valor, letra = dados_para_texto(dados)
                        txt = f" '{letra}'" if letra else ""
                        if ok:
                            print(f"    \033[1;30;42m QUADRO OK \033[0m {''.join(map(str, dados))}"
                                  f" (valor {valor}{txt})")
                        else:
                            print(f"    \033[1;97;41m ERRO DE PARIDADE \033[0m quadro "
                                  f"{''.join(map(str, dados))} é suspeito. "
                                  "Retransmita (ENTER reinicia e realinha os quadros).")
                    print()

                if dur:
                    blocos_mudo = int((dur + MARGEM_SOM_S) / duracao_bloco) + 1
    except KeyboardInterrupt:
        encerrado.set()
        print("\nReceptor encerrado.")
        if bits:
            menu_final(bits)
        else:
            print("Nenhum bit foi recebido.")
    except sd.PortAudioError as erro:
        print(f"Erro ao acessar o microfone: {erro}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()