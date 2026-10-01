# Software-Camada-Física

## Modelo ISO/OSI

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

## 5. Camada de Sessão

A **camada de sessão** gerencia o início, a manutenção e o término das sessões entre aplicações, além de tratar mecanismos relacionados ao controle e à sincronização da comunicação.

Segundo Tanenbaum, essa camada estabelece sessões entre usuários de diferentes máquinas e oferece serviços como:

* **Controle de diálogo:** controla quem pode transmitir em determinado momento;
* **Gerenciamento de token:** impede que as duas partes executem determinadas operações simultaneamente;
* **Sincronização:** estabelece pontos de sincronização durante a transmissão, permitindo que, em caso de falha, a comunicação possa ser retomada a partir de um ponto em que parou.

---

## 6. Camada de Apresentação

A **camada de apresentação**, também chamada de camada de tradução, é responsável pela representação dos dados, tratando de sua sintaxe e semântica. Ela permite a tradução entre diferentes formatos de dados e pode realizar funções como:

* Codificação;
* Compressão;
* Criptografia;
* Conversão de formatos.

Dessa forma, possibilita que as informações sejam representadas de maneira adequada para as aplicações.

---

## 7. Camada de Aplicação

A **camada de aplicação** é a mais próxima das aplicações utilizadas pelos usuários. Ela fornece serviços de rede diretamente aos programas e contém protocolos utilizados pelas aplicações para realizar diferentes tipos de comunicação.

Alguns exemplos de protocolos associados à camada de aplicação são:

* **HTTP:** utilizado para acesso a páginas e recursos da Web;
* **DNS:** utilizado para resolução de nomes de domínio;
* **SMTP:** utilizado para envio de e-mails.

---


