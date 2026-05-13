# ChaCha20 UART Test Suite (STM32)

Este diretório contém uma suíte de testes em Python para validar a implementação do algoritmo de criptografia de fluxo **ChaCha20** rodando em um microcontrolador STM32.

## Visão Geral

O projeto implementa o processamento do ChaCha20 de forma eficiente em termos de memória. Como o STM32 alvo possui apenas 8KB de RAM, os dados (como um payload de 8KB de teste) são transmitidos via UART em pequenos blocos de 64 bytes (o tamanho nativo do bloco ChaCha20). O microcontrolador processa cada bloco "on-the-fly" e envia o resultado de volta, garantindo que o uso de RAM permaneça constante independentemente do tamanho total do arquivo.

## O Protocolo UART

A comunicação PC-STM32 utiliza pacotes estruturados para garantir a integridade:

**Formato do Pacote:** `[CMD] [SIZE] [PAYLOAD...] [CHECKSUM]`
*   **CMD (1 byte):** Tipo de comando (INIT, DATA, END).
*   **SIZE (1 byte):** Tamanho do payload (0 a 64 bytes).
*   **PAYLOAD:** Os dados brutos.
*   **CHECKSUM (1 byte):** XOR de todos os bytes anteriores do pacote.

### Comandos
1.  **CMD_INIT (0x01):** Configura a Chave (32 bytes), Nonce (12 bytes) e Contador Inicial (4 bytes).
2.  **CMD_DATA (0x02):** Envia um bloco para ser processado. O STM32 retorna o bloco processado e incrementa seu contador interno.
3.  **CMD_END (0x03):** Sinaliza o fim da sessão e limpa os dados sensíveis da memória do STM32.

## Como Executar

### Pré-requisitos
*   Python 3.x instalado.
*   Biblioteca `pyserial`: `pip install pyserial`
*   STM32 conectado via USB (reconhecido como `/dev/ttyACM0` ou similar).

### Executando o Orquestrador
Para facilitar a avaliação, utilize o script `run_tests.py`, que provê um menu interativo:

```bash
python3 run_tests.py /dev/ttyACM0
```

### Entendendo os Cenários de Teste
1.  **Vetor de Teste RFC 8439 (Happy Path):** Valida a implementação contra o padrão oficial da IETF. Utiliza uma chave/nonce conhecidos e verifica se o STM32 produz o texto cifrado exato esperado pela especificação.
2.  **Stream Aleatório (8KB):** Gera 8KB de dados aleatórios e valida se o processamento em blocos via UART mantém a integridade dos dados comparando com uma implementação de referência em Python.
3.  **Roundtrip Test:** Demonstra a propriedade do algoritmo. Envia 8KB de caracteres 'A', salva o resultado criptografado em arquivo, e depois o envia de volta para o STM32. O sucesso é confirmado se o texto original ('A's) for recuperado.
4.  **Testes Negativos:** Tenta descriptografar dados válidos usando a chave, nonce ou contador incorretos, validando que o sistema não recupera o texto original nessas condições.

## Logs de Execução
Todos os logs detalhados (incluindo timestamps e dumps hexadecimais de cada pacote TX/RX) são salvos automaticamente na pasta:
`python_tools/executions/logs/`
