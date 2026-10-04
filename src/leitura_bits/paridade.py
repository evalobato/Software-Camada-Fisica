"""Verificação de erros por bit de paridade (paridade PAR).

A mensagem é dividida em quadros de 9 bits: 8 bits de dados + 1 bit de paridade.
O bit de paridade é escolhido para que o total de bits 1 do quadro seja PAR.
O receptor confere cada quadro assim que o 9º bit chega.

Detecta qualquer número ÍMPAR de bits trocados no quadro (1, 3, 5...).
Não detecta um número par de bits trocados (2, 4...) e não corrige nada.
"""

BITS_DADOS = 8
BITS_POR_QUADRO = BITS_DADOS + 1


def bit_paridade(dados):
    """Bit que torna par a quantidade de 1s: 0 se já for par, 1 se for ímpar."""
    return sum(dados) % 2


def montar_quadro(dados):
    """8 bits de dados -> quadro de 9 bits (dados + paridade)."""
    if len(dados) != BITS_DADOS:
        raise ValueError(f"Um quadro tem {BITS_DADOS} bits de dados.")
    return list(dados) + [bit_paridade(dados)]


def quadro_valido(quadro):
    """True se o quadro de 9 bits tem quantidade par de 1s."""
    return len(quadro) == BITS_POR_QUADRO and sum(quadro) % 2 == 0


def dados_para_texto(dados):
    """8 bits -> (valor, caractere). O caractere é None se não for imprimível."""
    valor = int("".join(str(b) for b in dados), 2)
    return valor, (chr(valor) if 32 <= valor < 127 else None)


def analisar_ultimo(bits):
    """Descreve o papel do último bit da lista, dentro do quadro em andamento.

    Devolve um dicionário:
      posicao            1..9 (9 = bit de paridade)
      eh_paridade        True se este bit é o de paridade
      paridade_esperada  0/1 quando o PRÓXIMO bit deve ser o de paridade, senão None
      quadro             (dados, ok) quando este bit fecha um quadro, senão None
    """
    posicao = (len(bits) - 1) % BITS_POR_QUADRO + 1
    info = {
        "posicao": posicao,
        "eh_paridade": posicao == BITS_POR_QUADRO,
        "paridade_esperada": None,
        "quadro": None,
    }
    if posicao == BITS_DADOS:
        info["paridade_esperada"] = bit_paridade(bits[-BITS_DADOS:])
    elif posicao == BITS_POR_QUADRO:
        quadro = bits[-BITS_POR_QUADRO:]
        info["quadro"] = (quadro[:BITS_DADOS], quadro_valido(quadro))
    return info


def quadros_do_texto(texto):
    """Texto -> bits prontos para emitir: cada byte (UTF-8) vira um quadro de 9 bits com paridade."""
    bits = []
    for byte in texto.encode("utf-8"):
        bits += montar_quadro([int(b) for b in format(byte, "08b")])
    return bits


def quadros_de_bits_digitados(texto):
    """Bits digitados à mão ("01001000 01101001") -> quadros de 9 bits com paridade.

    Espaços são ignorados. Levanta ValueError se tiver algo além de 0 e 1 ou se o total
    não for múltiplo de 8.
    """
    limpo = "".join(texto.split())
    if not limpo:
        raise ValueError("Nenhum bit digitado.")
    if any(c not in "01" for c in limpo):
        raise ValueError("Use só 0 e 1 (espaços são permitidos).")
    if len(limpo) % BITS_DADOS:
        raise ValueError(f"A quantidade de bits precisa ser múltiplo de {BITS_DADOS} "
                         f"(você digitou {len(limpo)}).")
    bits = []
    for i in range(0, len(limpo), BITS_DADOS):
        bits += montar_quadro([int(b) for b in limpo[i:i + BITS_DADOS]])
    return bits


def texto_dos_quadros_ok(bits):
    """Junta os bytes dos quadros com paridade correta e decodifica como texto (UTF-8).

    Quadros com erro ficam de fora. Devolve (texto, quantidade_de_quadros_com_erro).
    """
    dados, erros = bytearray(), 0
    for ini in range(0, len(bits) - BITS_POR_QUADRO + 1, BITS_POR_QUADRO):
        quadro = bits[ini:ini + BITS_POR_QUADRO]
        if quadro_valido(quadro):
            dados.append(int("".join(str(b) for b in quadro[:BITS_DADOS]), 2))
        else:
            erros += 1
    return dados.decode("utf-8", errors="replace"), erros