# ChaCha20 - Implementação Didática (RFC 8439)

Este projeto fornece uma implementação limpa, bem documentada e didática do cifrador de fluxo ChaCha20, conforme definido na **RFC 8439**.

## Visão Geral

O ChaCha20 é um cifrador de fluxo de alta velocidade desenvolvido por Daniel J. Bernstein. Ele foi projetado para ser eficiente tanto em software quanto em hardware, sendo amplamente utilizado em protocolos modernos como TLS 1.3 e SSH.

### Como Funciona

1.  **Matriz de Estado**: O ChaCha20 opera em uma matriz 4x4 de palavras de 32 bits (64 bytes no total).
2.  **Quarter Round**: A operação principal (ARX: Adição-Rotação-XOR) é aplicada às colunas e diagonais da matriz.
3.  **Keystream**: Após 20 rodadas, a matriz resultante é somada ao seu estado inicial para produzir um bloco de *keystream*.
4.  **Criptografia**: O *keystream* é aplicado via operação XOR ao texto puro para produzir o texto cifrado.

## Estrutura do Projeto

- `include/chacha20.h`: API Pública (Encapsulamento).
- `src/chacha20.c`: Lógica principal (Implementação).
- `tests/test_vectors.c`: Verificação contra vetores de teste da RFC 8439.
- `tests/test_nonce_reuse.c`: Demonstração da vulnerabilidade de reuso de nonce.
- `main.c`: Demonstração simples de uso da biblioteca com interface TUI.

## A API

```c
// XOR Simétrico para criptografia/descriptografia
void chacha20_xor(uint8_t *out, const uint8_t *in, size_t len, const uint8_t key[32], const uint8_t nonce[12], uint32_t counter);

// Gera keystream bruto (Didático)
void chacha20_generate_keystream(uint8_t keystream[64], const uint8_t key[32], const uint8_t nonce[12], uint32_t counter);
```

## Compilação e Uso

Um `Makefile` na raiz do repositório gerencia a compilação deste projeto.

### Compilar:
```bash
make
```

### Executar TUI:
```bash
./t1/bin/chacha20_tui
```

## Flags de Compilação

O `Makefile` utiliza as seguintes flags do `gcc` para garantir qualidade e performance:

- `-Wall`: Habilita avisos comuns do compilador.
- `-Wextra`: Habilita avisos adicionais para maior segurança.
- `-O3`: Nível máximo de otimização para performance.
- `-It1/include`: Define o diretório de cabeçalhos.

## Aviso de Segurança: Reuso de Nonce

**NUNCA REUSE UM NONCE** com a mesma chave. Como demonstrado em `test_nonce_reuse`, se um par (Chave, Nonce) for reutilizado para duas mensagens diferentes:
1.  O XOR dos dois textos cifrados será igual ao XOR dos dois textos puros.
2.  Se um texto puro for conhecido, o outro é revelado imediatamente.

## Conformidade

Esta implementação segue rigorosamente as convenções de *little-endian* e operações ARX especificadas na RFC 8439.
