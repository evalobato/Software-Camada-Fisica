"""Testes do decodificador Morse. Rode: pytest"""

from decodificador_morse import DecodificadorMorse, texto_para_morse

DURACAO = 0.0232  # ~1024 amostras a 44100 Hz


def traduzir(padrao):
    """padrao: '.' = bloco de silêncio, 'B' = bloco com batida. Devolve o texto."""
    dec = DecodificadorMorse(DURACAO)
    texto = ""
    for c in padrao:
        for ev in dec.processar_bloco(c == "B"):
            if ev[0] == "letra":
                texto += ev[1]
            elif ev[0] == "palavra":
                texto += " "
    return texto


PONTO = "B"
TRACO = "B" + "." * 8 + "B"          # 2 batidas rápidas
ENTRE_SIMBOLOS = "." * 30            # ~0,7 s
ENTRE_LETRAS = "." * 70              # ~1,6 s
ENTRE_PALAVRAS = "." * 140           # ~3,2 s


def letra(*simbolos):
    return ENTRE_SIMBOLOS.join(simbolos)


def test_letra_e_um_ponto():
    assert traduzir(PONTO + ENTRE_LETRAS) == "E"


def test_letra_a():
    assert traduzir(letra(PONTO, TRACO) + ENTRE_LETRAS) == "A"


def test_sos():
    s = letra(PONTO, PONTO, PONTO)
    o = letra(TRACO, TRACO, TRACO)
    padrao = s + ENTRE_LETRAS + o + ENTRE_LETRAS + s + ENTRE_LETRAS
    assert traduzir(padrao) == "SOS"


def test_espaco_entre_palavras():
    e = PONTO
    t = TRACO
    padrao = e + ENTRE_PALAVRAS + t + ENTRE_LETRAS
    assert traduzir(padrao) == "E T"


def test_tres_batidas_gera_interrogacao():
    tres = "B" + "." * 8 + "B" + "." * 8 + "B"
    assert traduzir(tres + ENTRE_LETRAS) == "?"


def test_codigo_inexistente_gera_interrogacao():
    padrao = letra(*[PONTO] * 7)  # 7 pontos não existe
    assert traduzir(padrao + ENTRE_LETRAS) == "?"


def test_reiniciar_descarta_letra_em_andamento():
    dec = DecodificadorMorse(DURACAO)
    for c in "B" + "." * 30:
        dec.processar_bloco(c == "B")
    dec.reiniciar()
    eventos = []
    for _ in range(200):
        eventos += dec.processar_bloco(False)
    assert eventos == []


def test_texto_para_morse():
    assert texto_para_morse("SOS") == ([["...", "---", "..."]], [])


def test_texto_para_morse_palavras_acentos_e_ignorados():
    palavras, ignorados = texto_para_morse("Olá  mundo #")
    assert palavras == [["---", ".-..", ".-"], ["--", "..-", "-.", "-..", "---"]]
    assert ignorados == ["#"]


def test_ida_e_volta_texto_morse_texto():
    palavras, _ = texto_para_morse("OI 2026")
    padrao = ""
    for pi, palavra in enumerate(palavras):
        for li, codigo in enumerate(palavra):
            padrao += letra(*[PONTO if s == "." else TRACO for s in codigo])
            padrao += ENTRE_PALAVRAS if li == len(palavra) - 1 and pi < len(palavras) - 1 else ENTRE_LETRAS
    assert traduzir(padrao + ENTRE_PALAVRAS) == "OI 2026 "