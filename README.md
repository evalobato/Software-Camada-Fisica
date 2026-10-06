# Software-Camada-Física

## As sete camadas do modelo ISO/OSI

O **modelo ISO/OSI** é um modelo de referência utilizado para compreender como ocorre a comunicação entre dispositivos em uma rede. Ele é dividido em 7 camadas, cada uma responsável por funções específicas durante a comunicação.

### 1. Camada Física

A **camada física** do modelo ISO/OSI é responsável pela transmissão de dados brutos, convertendo os bits em sinais adequados ao meio de comunicação. Quando o meio é elétrico, a camada converte os bits em sinais elétricos que serão transmitidos pelo cabo; e se for óptico, transforma-se em sinais luminosos.

---

### 2. Camada de Enlace

A **camada de enlace** é responsável pela comunicação entre dispositivos conectados ao mesmo enlace, utilizando a camada física para transmitir os dados na forma de quadros (frames).

Entre suas principais funções estão:

* **Controle de acesso ao meio físico**;
* **Detecção de erros**;
* **Endereçamento físico**;
* **Controle de fluxo**, evitando que um host mais rápido envie informações em uma velocidade maior do que um host mais lento consegue processar.

---

### 3. Camada de Rede

A **camada de rede** é responsável pelo endereçamento, roteamento e encaminhamento dos dados em uma rede ou entre várias redes conectadas. Ela determina como os pacotes serão encaminhados desde a origem até o destino, além de poder estar relacionada ao controle de congestionamento e à qualidade de serviço.

---

### 4. Camada de Transporte

A **camada de transporte** é responsável pela comunicação fim a fim entre aplicações, podendo oferecer uma comunicação orientada ou não orientada à conexão.

* **Orientada à conexão**

Estabelece uma conexão antes da transmissão dos dados e pode utilizar mecanismos de confirmação, controle de erros, retransmissão e controle de fluxo.

Um exemplo é o TCP (Transmission Control Protocol).

* **Não orientada à conexão**

Não estabelece uma conexão antes da transmissão e não oferece garantias de entrega, ordem ou retransmissão dos dados.

Um exemplo é o UDP (User Datagram Protocol).

---

### 5. Camada de Sessão

A **camada de sessão** gerencia o início, a manutenção e o término das sessões entre aplicações, além de tratar mecanismos relacionados ao controle e à sincronização da comunicação.

Segundo Tanenbaum, essa camada estabelece sessões entre usuários de diferentes máquinas e oferece serviços como:

* **Controle de diálogo:** controla quem pode transmitir em determinado momento;
* **Gerenciamento de token:** impede que as duas partes executem determinadas operações simultaneamente;
* **Sincronização:** estabelece pontos de sincronização durante a transmissão, permitindo que, em caso de falha, a comunicação possa ser retomada a partir de um ponto em que parou.

---

### 6. Camada de Apresentação

A **camada de apresentação**, também chamada de camada de tradução, é responsável pela representação dos dados, tratando de sua sintaxe e semântica. Ela permite a tradução entre diferentes formatos de dados e pode realizar funções como:

* Codificação;
* Compressão;
* Criptografia;
* Conversão de formatos.

Dessa forma, possibilita que as informações sejam representadas de maneira adequada para as aplicações.

---

### 7. Camada de Aplicação

A **camada de aplicação** é a mais próxima das aplicações utilizadas pelos usuários. Ela fornece serviços de rede diretamente aos programas e contém protocolos utilizados pelas aplicações para realizar diferentes tipos de comunicação.

Alguns exemplos de protocolos associados à camada de aplicação são:

* **HTTP:** utilizado para acesso a páginas e recursos da Web;
* **DNS:** utilizado para resolução de nomes de domínio;
* **SMTP:** utilizado para envio de e-mails.

---

## Camada Física do Modelo ISO/OSI

### 1. Camada Física: suas funções

A **Camada Física** é a **camada 1 do modelo OSI**, responsável pela transmissão e recepção de **fluxos de bits brutos** por meio de um meio físico. Ela define características elétricas, ópticas ou de radiofrequência dos sinais, como níveis de tensão, temporização, modulação e especificações de conectores.

A camada física não trabalha com o significado ou a organização dos bits. Sua função está relacionada à conversão entre os valores digitais `0` e `1` e os sinais físicos que percorrem fios, fibras ópticas ou o ar.

#### Principais funções

* **Codificação de linha:** técnicas como Manchester, 8b/10b e 4D-PAM5 mapeiam bits em níveis de sinal ou transições.
* **Multiplexação:** técnicas como FDM(Multiplexação por Divisão de Frequência) e WDM(Multiplexação por Divisão de Comprimento de Onda), permitem transportar diferentes canais utilizando o mesmo meio.
* **Transmissão física:** utiliza meios como par trançado, cabo coaxial, fibra óptica e rádio.
* **Conectores e transceptores:** dispositivos como módulos SFP fazem a interface entre os equipamentos e o meio físico.
* **Padronização:** especificações são definidas por organizações como IEEE, ITU e 3GPP.

#### Exemplos de padrões

| Padrão      | Aplicação                     |
| ----------- | ----------------------------- |
| IEEE 802.3  | Ethernet                      |
| IEEE 802.11 | Wi-Fi                         |
| IEEE 802.15 | Bluetooth e Zigbee            |
| 3GPP LTE    | Comunicação móvel 4G          |
| 5G NR       | Comunicação móvel 5G          |
| USB         | Interconexão de curto alcance |
| HDMI        | Transmissão de áudio e vídeo  |
| PCIe        | Comunicação entre componentes |
| DisplayPort | Transmissão de áudio e vídeo  |

Esses padrões permitem a comunicação entre equipamentos de diferentes fabricantes e especificam características relacionadas à sinalização e à interface física.

#### Aplicações

A Camada Física está presente em diversas tecnologias, como:

* Redes locais Ethernet e Wi-Fi;
* Telefonia celular 4G e 5G;
* Fibra óptica de longa distância;
* Redes industriais;
* Sistemas de comunicação via satélite;
* Sistemas de radar.

---

### 2. Sinais analógicos e digitais

#### Sinais analógicos

Em uma transmissão analógica, o sinal pode sofrer degradação conforme percorre o meio físico. Quando o sinal enfraquece, torna-se mais difícil diferenciá-lo do ruído.

Um problema importante é que, ao amplificar um sinal analógico, o ruído presente nele também é amplificado. Com o aumento da distância, isso pode comprometer a qualidade da comunicação.

#### Sinais digitais

Os sinais digitais utilizam dois estados principais, representados por `0` e `1`. Essa característica facilita a separação entre o sinal e o ruído.

Por isso, sistemas digitais apresentam maior facilidade para recuperar a informação transmitida e foram amplamente utilizados na evolução dos sistemas de comunicação.

#### Conversão analógico → digital

Um exemplo é o PCM (Modulação por Código de Pulso), utilizado na codificação de voz. O processo de conversão possui as seguintes etapas:

```text
Sinal analógico
      ↓
Filtragem
      ↓
Amostragem (PAM)
      ↓
Quantização
      ↓
Codificação
      ↓
Dados digitais
```

Na origem existe um conversor A/D (analógico-digital). No destino, um conversor D/A (digital-analógico) para reconstruir o sinal.

---

### 3. Largura de banda

A largura de banda  representa a faixa de frequências que pode ser utilizada por um sistema de comunicação.

#### Voz

A maior parte da energia da fala está aproximadamente entre 200–300 Hz e 2.700–2.800 Hz. O material também apresenta uma largura de banda de 4.000 Hz para comunicação de voz padrão.

#### Filtragem

A filtragem remove componentes de frequência mais alta do sinal e facilita as etapas seguintes da conversão. Um dos objetivos do filtro limitador de banda é evitar a sobreposição espectral causada por uma amostragem inadequada, gerando o aliasing(falseamento do sinal), que ocorre quando as amostras coletadas são baixas em comparação com a velocidade da variação do sinal origial.

#### Largura de banda e meio físico

O meio utilizado na transmissão influencia diretamente as características da comunicação. Como nas aplicações seguintes:

* **Fibra monomodo:** pode alcançar dezenas de quilômetros com taxas superiores a 100 Gbps, trasmite apenas um único feixe ou modo de luz por vez.
* **Cat 6A:** suporta Ethernet de 10 Gbps em distâncias de até 100 metros.

---

### 4. Taxa de amostragem

A amostragem consiste em representar um sinal analógico por meio de amostras obtidas em determinados intervalos de tempo. No processo apresentado, a amostragem utiliza PAM (PModulação por Amplitude de Pulso), no qual os dados são codificados na aplitude de uma série de pulsos elétricos ou ópticos em intervalos de tempo regulares.

#### Critério de Nyquist

Para que um sinal possa ser reconstruído corretamente, a frequência de amostragem deve ser superior ao dobro da largura de banda do sinal:

```text
Fs > 2 × BW
```

Onde:

* `Fs` = frequência de amostragem;
* `BW` = largura de banda do sinal.

#### Aliasing

O aliasing ocorre quando a frequência de amostragem é insuficiente:

```text
Fs < 2 × BW
```

Nesse caso, ocorre sobreposição entre os componentes espectrais das amostras e do sinal de entrada. O resultado pode ser um sinal falso, que não corresponde ao sinal original.

##### Exemplo: telefonia

Na telefonia, são utilizadas:

```text
8.000 amostras/s × 8 bits
= 64.000 bits/s
= 64 kbps
```
---

### 5. Modulação do pulso 

A modulação altera determinadas características de uma onda ou portadora para representar informações.

**Modulação digital**

* **ASK (Amplitude Shift Keying):** utiliza variações de amplitude;
* **PSK (Phase Shift Keying):** utiliza variações de fase;
* **QAM (Quadrature Amplitude Modulation):** utiliza variações de amplitude e fase.

A ordem da modulação determina quantos bits por símbolo podem ser transmitidos.

**Modulação de pulso**

* **PAM:** modula a amplitude de um trem de pulsos;
* **PCM:** transforma cada amostra em uma palavra binária;
* **Quantização:** transforma amplitudes contínuas em valores discretos.

---

#### Quantização

A quantização transforma cada amostra analógica em um valor discreto. Na quantização uniforme, os intervalos possuem espaçamento igual dentro da faixa dinâmica. Cada amostra é associada ao intervalo que apresenta a amplitude mais próxima.

De forma simplificada:

```text
Sinal analógico
      ↓
   Amostragem
      ↓
   Quantização
      ↓
Valor discreto
      ↓
 Código binário
```

---

### 7. Companding

Companding é formado pela combinação de:

* **Compressão**, realizada na origem, ntes de o sinal analógico ser convertido em digital, ele passa por um circuito ou algoritmo que comprime a faixa dinâmica.  Dessa forma, os sons de baixa intensidade são amplificados, enquanto os sons de alta intensidade são atenuados ou mantidos estáveis.;
* **Expansão**, realizada no destino, após receber o sinal digitalizado e convertê-lo de volta para o analógico, o receptor faz o processo inverso,aplica uma expansão matemática para restaurar os volumes originais do sinal.

---

### 8. DPCM

O **DPCM (Differential Pulse Code Modulation)** funciona de maneira semelhante ao PCM, porém transmite a diferença entre a amostra atual e a amostra anterior, em vez de transmitir a amostra completa.

#### Funcionamento

```text
Amostra atual
      ↓
   Diferença
      ↓
 Quantização
      ↓
 Codificação
      ↓
 Transmissão
```

O sistema utiliza um **preditor**, que mantém uma amostra, e um **diferenciador**, responsável pelo cálculo da diferença.

O DPCM pode reduzir a taxa para até **48 kbps**.

Uma limitação apresentada é que a quantização uniforme da diferença pode resultar em qualidade diferente para sinais de diferentes amplitudes.

---

### 9. ADPCM

O ADPCM (Adaptive Differential Pulse Code Modulation), definido no padrão **ITU-T G.726**, utiliza adaptação dos níveis de quantização de acordo com o tamanho do sinal de diferença.

O material apresenta como características:

* redução da taxa para **32 kbps**;
* utilização de realimentação;
* adaptação do quantizador;
* geração de SNR uniforme ao longo da faixa dinâmica.

#### Passos para 32 kbps

1. Converter a amostra PCM A-law/μ-law para PCM linear.
2. Calcular o valor previsto da próxima amostra.
3. Calcular a diferença entre a amostra real e a prevista.
4. Codificar a diferença em 4 bits.
5. Enviar os 4 bits ao preditor.
6. Enviar os 4 bits ao quantizador.

---

### 10. Ruído

O **ruído** é qualquer interferência que prejudique a representação ou recuperação do sinal transmitido.

#### Ruído de quantização

O **ruído de quantização** surge devido à diferença entre o valor real da amostra e o intervalo de quantização ao qual ela foi associada.

Quanto maior esse ruído, maior a degradação da qualidade do sinal.

#### SNR — Relação sinal-ruído

A **SNR (Signal-to-Noise Ratio)** representa a relação entre a intensidade do sinal e a intensidade do ruído.

A fórmula apresentada é:

```text
S/N = 20 × log₁₀(Vs / Vn)
```

Onde:

* `Vs` = tensão do sinal;
* `Vn` = tensão do ruído.

A SNR normalmente é expressa em **decibéis (dB)**. Quanto maior a SNR, melhor a qualidade do sinal de voz.

#### Quantização uniforme

Na quantização uniforme, os intervalos possuem o mesmo tamanho em toda a faixa dinâmica.

Isso produz uma SNR menor para sinais fracos e maior para sinais fortes. Como grande parte da voz apresenta níveis baixos, essa característica pode ser ineficiente.

#### Companding como solução

O **companding** utiliza compressão logarítmica para fazer o ruído de quantização acompanhar o nível do sinal, mantendo uma SNR mais uniforme na faixa dinâmica.

---

### 11. Ruído e meio físico

O meio físico utilizado na comunicação impõe limitações relacionadas à **atenuação** e ao **ruído**.

No caso de sinais analógicos, o enfraquecimento do sinal torna mais difícil separá-lo do ruído, e a amplificação também amplifica o ruído.

O aliasing também pode ser considerado um problema relacionado ao processo de transmissão e conversão, ocorrendo quando a taxa de amostragem é inadequada.

---

### 12. Métricas de desempenho

Algumas métricas utilizadas para avaliar sistemas de comunicação são:

| Métrica                 | Significado                                                  |
| ----------------------- | ------------------------------------------------------------ |
| **BER**                 | Taxa de erro de bit                                          |
| **SNR**                 | Relação sinal-ruído                                          |
| **Capacidade do canal** | Quantidade de informação que pode ser transmitida pelo canal |

A capacidade do canal está relacionada ao **teorema de Shannon-Hartley**.

---

### 13. Resumo

A **Camada Física** é responsável pela transmissão dos bits através de um meio físico. Para isso, envolve características como sinalização, codificação, modulação, largura de banda, amostragem, quantização e controle dos efeitos do ruído.

O processo de comunicação pode ser representado de forma simplificada:

```text
Informação
    ↓
Codificação
    ↓
Modulação / Sinalização
    ↓
Meio físico
    ↓
Ruído e atenuação
    ↓
Recepção
    ↓
Demodulação / Decodificação
    ↓
Informação recuperada
```
---



