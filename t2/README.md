# Suíte de Testes ChaCha20 UART (STM32)

Este diretório contém uma suíte de testes em Python para validar a implementação do algoritmo ChaCha20 rodando em um microcontrolador STM32.

## Visão Geral

O projeto valida o processamento do ChaCha20 de forma eficiente em termos de memória. Como o STM32 alvo possui recursos limitados (8KB de RAM), os dados são transmitidos via UART em pequenos blocos de 64 bytes (tamanho nativo do bloco ChaCha20). O microcontrolador processa cada bloco em tempo real e envia o resultado de volta.

## O Protocolo UART

A comunicação PC-STM32 utiliza pacotes estruturados:

**Formato do Pacote:** `[CMD] [SIZE] [PAYLOAD...] [CHECKSUM]`
*   **CMD (1 byte):** Tipo de comando (INIT, DATA, END).
*   **SIZE (1 byte):** Tamanho do payload (0 a 64 bytes).
*   **PAYLOAD:** Dados brutos.
*   **CHECKSUM (1 byte):** XOR de todos os bytes anteriores do pacote.

### Comandos
1.  **CMD_INIT (0x01):** Configura a Chave (32 bytes), Nonce (12 bytes) e Contador Inicial (4 bytes).
2.  **CMD_DATA (0x02):** Envia um bloco para processamento. O STM32 retorna o bloco processado.
3.  **CMD_END (0x03):** Sinaliza o fim da sessão e limpa dados sensíveis da memória do hardware.

## Como Executar

### Pré-requisitos
*   Python 3.x.
*   Biblioteca `pyserial`: `pip install pyserial`.
*   STM32 conectado e reconhecido (ex: `/dev/ttyACM0`).

### Executando o Orquestrador
Utilize o menu interativo:

```bash
python3 t2/run_tests.py /dev/ttyACM0
```

## Cenários de Teste
1.  **Vetor de Teste RFC 8439:** Valida contra o padrão oficial IETF.
2.  **Stream Aleatório (8KB):** Valida integridade em fluxos contínuos.
3.  **Roundtrip Test:** Demonstra criptografia e descriptografia funcional (ida e volta).
4.  **Testes Negativos:** Garante que chaves ou nonces incorretos não descriptografam os dados.

## Logs
Os logs detalhados de cada execução são salvos em:
`t2/executions/logs/`
