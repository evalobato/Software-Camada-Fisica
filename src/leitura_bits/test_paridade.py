"""Testes da verificação por paridade. Rode: pytest"""

from paridade import (
    BITS_POR_QUADRO,
    analisar_ultimo,
    bit_paridade,
    dados_para_texto,
    montar_quadro,
    quadro_valido,
)

H = [0, 1, 0, 0, 1, 0, 0, 0]  # 'H' = 72, tem dois 1s


def test_paridade_de_quantidade_par_e_zero():
    assert bit_paridade(H) == 0


def test_paridade_de_quantidade_impar_e_um():
    assert bit_paridade([1, 0, 0, 0, 0, 0, 0, 0]) == 1


def test_quadro_montado_e_valido():
    for valor in range(256):
        dados = [int(b) for b in format(valor, "08b")]
        assert quadro_valido(montar_quadro(dados))


def test_um_bit_trocado_e_detectado_em_qualquer_posicao():
    quadro = montar_quadro(H)
    for i in range(BITS_POR_QUADRO):
        errado = list(quadro)
        errado[i] ^= 1
        assert not quadro_valido(errado)


def test_dois_bits_trocados_nao_sao_detectados():
    # Limite conhecido da paridade simples
    errado = montar_quadro(H)
    errado[0] ^= 1
    errado[1] ^= 1
    assert quadro_valido(errado)


def test_dados_para_texto():
    assert dados_para_texto(H) == (72, "H")
    assert dados_para_texto([0] * 8) == (0, None)


def test_montar_quadro_exige_8_bits():
    try:
        montar_quadro([0, 1])
    except ValueError:
        return
    raise AssertionError("deveria ter levantado ValueError")


def test_analisar_ultimo_ao_longo_do_quadro():
    quadro = montar_quadro(H)
    bits = []
    for i, b in enumerate(quadro, start=1):
        bits.append(b)
        info = analisar_ultimo(bits)
        assert info["posicao"] == i
        assert info["eh_paridade"] == (i == 9)
        if i == 8:
            assert info["paridade_esperada"] == quadro[8]
        else:
            assert info["paridade_esperada"] is None
        if i == 9:
            assert info["quadro"] == (H, True)
        else:
            assert info["quadro"] is None


def test_analisar_ultimo_marca_quadro_errado_e_segue_para_o_proximo():
    bits = montar_quadro(H)
    bits[3] ^= 1
    assert analisar_ultimo(bits)["quadro"][1] is False
    bits.append(0)  # primeiro bit do segundo quadro
    assert analisar_ultimo(bits)["posicao"] == 1