"""Morse por batidas: recebe pelo microfone, traduz para texto e também emite em som.

Receber (microfone):
  1 batida = ponto (.)   |   2 batidas = traço (-)
  pausa curta fecha o símbolo, pausa média fecha a letra, pausa longa fecha a palavra.
  Cada símbolo reconhecido é confirmado com um som próprio (como nos bits).
  ENTER apaga a mensagem.

Emitir (depois de Ctrl+C):
  r = toca a mensagem recebida em Morse, para outro computador (rodando este mesmo código) ler.
  e = digite um texto qualquer e ele é emitido em Morse.
"""

import os
import queue
import sys
import threading
import time
import traceback

import numpy as np
import sounddevice as sd

from decodificador_morse import MORSE, DecodificadorMorse, texto_para_morse
from detector_batidas import DetectorDeBatidas
import plataforma

# ---------------- Parâmetros ajustáveis ----------------
TAXA_AMOSTRAGEM = 44100     # amostras por segundo
TAMANHO_BLOCO = 1024        # janela de análise (amostras por bloco, ~23 ms)
SEGUNDOS_CALIBRACAO = 2.0   # tempo medindo o ruído ambiente no início
MULTIPLICADOR_RUIDO = 4.0   # limiar = ruído ambiente x este valor
LIMIAR_MINIMO = 0.02        # limiar nunca fica abaixo disto (escala 0.0 a 1.0)
INTERVALO_MINIMO_S = 0.15   # tempo mínimo entre duas detecções (segundos)
SILENCIO_SIMBOLO_S = 0.6    # silêncio que fecha um ponto/traço
SILENCIO_LETRA_S = 2.2      # silêncio que fecha uma letra
SILENCIO_PALAVRA_S = 4.5    # silêncio que fecha uma palavra (espaço)
DISPOSITIVO = None          # None = microfone padrão; ou número do dispositivo
MOSTRAR_NIVEIS = False      # True: mostra nível e limiar (útil para ajustar)
SOM_ATIVO = True            # toca um som de confirmação a cada símbolo
VOLUME = 0.5                # volume do som (0.0 a 1.0)
SAIDA = None                # None = alto-falante padrão; ou número do dispositivo de saída
MARGEM_SOM_S = 0.25         # tempo extra sem escutar depois do som (evita eco)
ESPERA_INICIAL_S = 2.0      # na emissão: tempo antes do primeiro símbolo
FOLGA_S = 0.3               # na emissão: folga extra somada às pausas
# --------------------------------------------------------

# Sons: lista de (frequência em Hz, duração em s); frequência 0 = pausa.
# Os mesmos sons dos bits: ponto = bit 0, traço = bit 1.
SONS = {
    ".": [(440, 0.30)],                            # ponto: um bipe grave e longo
    # A pausa entre os dois bipes do traço precisa ser maior que INTERVALO_MINIMO_S
    # e menor que SILENCIO_SIMBOLO_S para o outro PC contar duas batidas.
    "-": [(988, 0.12), (0, 0.20), (988, 0.12)],    # traço: dois bipes agudos e curtos
    "erro": [(180, 0.35)],                         # grupo inválido: zumbido grave
}

AZUL = "\033[1;97;44m"
VERDE = "\033[1;30;42m"
AMARELO = "\033[1;30;43m"
VERMELHO = "\033[1;97;41m"
RESET = "\033[0m"

fila_de_blocos = queue.Queue()
pedido_reiniciar = threading.Event()
encerrado = threading.Event()        # ligado quando o receptor é encerrado (Ctrl+C)
fila_comandos = queue.Queue()        # comandos digitados depois de encerrar

SONS_PRONTOS = {}
DURACAO_SONS = {}


def ler_teclado():
    """Thread única que lê o teclado.

    Durante a escuta, ENTER apaga a mensagem. Depois de encerrado, o que for
    digitado vai para a fila de comandos (menu final).
    """
    seguidos = 0
    while True:
        try:
            linha = input()
            seguidos = 0
        except EOFError:
            # No Windows, o Ctrl+C aborta a leitura em andamento e isso chega como EOFError.
            # Só é fim de entrada de verdade se o erro se repetir.
            seguidos += 1
            if seguidos >= 3:
                fila_comandos.put(None)
                return
            time.sleep(0.2)
            continue
        if encerrado.is_set():
            fila_comandos.put(linha.strip())
        else:
            pedido_reiniciar.set()


def callback_audio(indata, frames, time_info, status):
    """Chamada pelo sounddevice a cada bloco. Deve ser rápida: só copia e enfileira."""
    if status:
        print(status, file=sys.stderr)
    fila_de_blocos.put(indata[:, 0].copy())  # canal 0 (mono)


# ---------------------------- Sons ----------------------------

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


# --------------------------- Emissão ---------------------------

def pausas_de_emissao():
    """Silêncio (em s) entre o fim de um som e o início do seguinte.

    O outro PC fecha o símbolo após SILENCIO_SIMBOLO_S, toca a confirmação e fica surdo
    por MARGEM_SOM_S, então o próximo símbolo só pode começar depois disso. Para a letra
    e a palavra, a pausa precisa passar do limite que o receptor usa para fechá-las.
    """
    simbolo = SILENCIO_SIMBOLO_S + max(DURACAO_SONS["."], DURACAO_SONS["-"]) + MARGEM_SOM_S + FOLGA_S
    letra = SILENCIO_LETRA_S + FOLGA_S
    palavra = SILENCIO_PALAVRA_S + FOLGA_S
    return simbolo, letra, palavra


def plano_de_emissao(palavras):
    """Lista de itens {espera, simbolo, letra, inicio_de_letra} na ordem em que tocam."""
    p_simbolo, p_letra, p_palavra = pausas_de_emissao()
    itens = []
    for pi, palavra in enumerate(palavras):
        for li, codigo in enumerate(palavra):
            for si, simbolo in enumerate(codigo):
                if not itens:
                    espera = ESPERA_INICIAL_S
                elif si > 0:
                    espera = p_simbolo
                elif li > 0:
                    espera = p_letra
                else:
                    espera = p_palavra
                itens.append({
                    "espera": espera,
                    "simbolo": simbolo,
                    "letra": MORSE.get(codigo, "?"),
                    "codigo": codigo,
                    "inicio_de_letra": si == 0,
                    "inicio_de_palavra": si == 0 and li == 0 and pi > 0,
                })
    return itens


def duracao_da_emissao(plano):
    return sum(i["espera"] + DURACAO_SONS[i["simbolo"]] for i in plano)


def emitir(palavras):
    """Toca a mensagem em Morse, um símbolo por vez (o outro PC lê pelo microfone)."""
    plano = plano_de_emissao(palavras)
    if not plano:
        print("Nada para emitir.")
        return
    texto = " ".join("".join(MORSE.get(c, "?") for c in p) for p in palavras)
    print(f"\nEmitindo: {texto}")
    print(f"Duração estimada: {duracao_da_emissao(plano):.0f} s. Começa em {ESPERA_INICIAL_S:.0f} s. "
          "Para outro PC ler, ele deve estar escutando e perto do alto-falante. (Ctrl+C interrompe)\n")
    try:
        for item in plano:
            sd.sleep(int(item["espera"] * 1000))
            if item["inicio_de_palavra"]:
                print("  (espaço)")
            if item["inicio_de_letra"]:
                print(f"\n  Letra {AMARELO} {item['letra']} {RESET}  {item['codigo']}")
            print(f"    {desenhar_codigo(item['simbolo'])}")
            sd.play(SONS_PRONTOS[item["simbolo"]], samplerate=TAXA_AMOSTRAGEM, device=SAIDA)
            sd.wait()
    except KeyboardInterrupt:
        sd.stop()
        print("\nEmissão interrompida.")
        return
    except sd.PortAudioError as erro:
        print(f"Não consegui tocar o som: {erro}", file=sys.stderr)
        return
    print("\nFim da emissão.")


def menu_final(texto):
    """Depois de encerrar: reemitir a mensagem recebida, emitir outro texto ou sair."""
    if texto.strip():
        print(f"\nMensagem recebida: {texto.strip()}")
    else:
        print("\nNenhuma mensagem foi recebida.")
    ajuda = "r = emitir a mensagem recebida | e = digitar um texto e emitir | s = sair  (depois ENTER)"
    print(f"\nComandos:  {ajuda}")
    while True:
        try:
            comando = fila_comandos.get()
        except KeyboardInterrupt:
            return
        if comando is None:
            print("Entrada do teclado indisponível; encerrando.")
            return
        if comando.lower() in ("s", "sair"):
            return
        if comando.lower() in ("r", "reproduzir"):
            palavras, _ = texto_para_morse(texto)
            if palavras:
                emitir(palavras)
            else:
                print("Não há mensagem recebida para emitir. Use 'e' para digitar um texto.")
        elif comando.lower() in ("e", "escrever"):
            print("Digite o texto e aperte ENTER:")
            try:
                digitado = fila_comandos.get()
            except KeyboardInterrupt:
                return
            if digitado is None:
                return
            palavras, ignorados = texto_para_morse(digitado)
            if ignorados:
                print(f"Caracteres sem código Morse, ignorados: {' '.join(sorted(set(ignorados)))}")
            emitir(palavras)
        else:
            print("Comando não reconhecido. Use r, e ou s.")
            continue
        print(f"\nComandos:  {ajuda}")


# --------------------------- Recepção ---------------------------

def desenhar_codigo(codigo):
    """Ponto e traço em blocos coloridos."""
    return " ".join(f"{AZUL} • {RESET}" if s == "." else f"{VERDE} ━━ {RESET}" for s in codigo)


def preparar_plataforma():
    """Terminal, argumentos de linha de comando e taxa de amostragem. False = nada mais a fazer."""
    global DISPOSITIVO, SAIDA, TAXA_AMOSTRAGEM
    plataforma.configurar_saida()
    args = plataforma.ler_argumentos(__doc__.strip().splitlines()[0])
    if args.listar:
        plataforma.listar_dispositivos(sd)
        return False
    if args.entrada is not None:
        DISPOSITIVO = args.entrada
    if args.saida is not None:
        SAIDA = args.saida
    TAXA_AMOSTRAGEM = plataforma.escolher_taxa(sd, DISPOSITIVO, SAIDA, TAXA_AMOSTRAGEM)
    return True


def main():
    if not preparar_plataforma():
        return
    preparar_sons()
    p_simbolo, p_letra, _ = pausas_de_emissao()
    if p_simbolo >= SILENCIO_LETRA_S - 0.3:
        print(f"Aviso: a pausa entre símbolos na emissão ({p_simbolo:.1f} s) está perto de "
              f"SILENCIO_LETRA_S ({SILENCIO_LETRA_S:.1f} s). Aumente SILENCIO_LETRA_S.", file=sys.stderr)

    blocos_calibracao = int(SEGUNDOS_CALIBRACAO * TAXA_AMOSTRAGEM / TAMANHO_BLOCO)
    detector = DetectorDeBatidas(
        taxa_amostragem=TAXA_AMOSTRAGEM,
        tamanho_bloco=TAMANHO_BLOCO,
        blocos_calibracao=blocos_calibracao,
        multiplicador_ruido=MULTIPLICADOR_RUIDO,
        limiar_minimo=LIMIAR_MINIMO,
        intervalo_minimo_s=INTERVALO_MINIMO_S,
    )
    duracao_bloco = TAMANHO_BLOCO / TAXA_AMOSTRAGEM
    decodificador = DecodificadorMorse(
        duracao_bloco=duracao_bloco,
        silencio_simbolo_s=SILENCIO_SIMBOLO_S,
        silencio_letra_s=SILENCIO_LETRA_S,
        silencio_palavra_s=SILENCIO_PALAVRA_S,
    )
    texto = ""
    codigo_atual = ""
    blocos_mudo = 0   # blocos a ignorar enquanto o som toca (o microfone o ouviria como batida)

    threading.Thread(target=ler_teclado, daemon=True).start()

    print("Iniciando Morse...")
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
            maior_nivel = 0.0   # maior nível ouvido na calibração
            while True:
                bloco = fila_de_blocos.get()
                if blocos_mudo > 0 and detector.calibrado:
                    # Som tocando: alimenta o detector com silêncio para o tempo seguir correndo
                    blocos_mudo -= 1
                    bloco = np.zeros_like(bloco)
                batida = detector.processar_bloco(bloco)
                if not aviso_escutando:
                    maior_nivel = max(maior_nivel, detector.ultimo_nivel)

                if detector.calibrado and not aviso_escutando:
                    print(f"Limiar definido: {detector.limiar:.4f}")
                    if maior_nivel == 0.0:
                        print("AVISO: o microfone entregou só silêncio absoluto. Verifique a permissão de "
                              "microfone do sistema e o dispositivo (python <programa> --listar).",
                              file=sys.stderr)
                    print("Escutando o microfone...")
                    print("  1 batida = ponto | 2 batidas = traço")
                    print("  pausa média = nova letra | pausa longa = nova palavra")
                    print("  ENTER = apagar tudo | Ctrl+C = encerrar (depois dá para emitir em som)\n")
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

                dur = 0.0
                for evento in decodificador.processar_bloco(batida):
                    tipo = evento[0]
                    if tipo == "simbolo":
                        dur = tocar(evento[1])   # som próprio de ponto e de traço
                        codigo_atual += evento[1]
                        print(f"  {desenhar_codigo(evento[1])}   letra em montagem: {codigo_atual}")
                    elif tipo == "invalido":
                        dur = tocar("erro")
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
                if dur:
                    blocos_mudo = int((dur + MARGEM_SOM_S) / duracao_bloco) + 1
    except KeyboardInterrupt:
        encerrado.set()
        print("\nEscuta encerrada.")
        if codigo_atual:   # letra ainda aberta (faltou a pausa que a fecha): inclui na mensagem
            texto += MORSE.get(codigo_atual, "?")
        menu_final(texto)
    except sd.PortAudioError as erro:
        print(f"Erro ao acessar o microfone: {erro}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    codigo_de_saida = 0
    try:
        main()
    except SystemExit as saida:
        codigo_de_saida = saida.code if isinstance(saida.code, int) else 1
    except Exception:
        traceback.print_exc()
        codigo_de_saida = 1
    finally:
        # A thread do teclado fica parada em input(); sair direto evita o erro
        # "Fatal Python error ... daemon threads" ao encerrar.
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(codigo_de_saida)