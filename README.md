# Projeto semb

Este repositório contém dois projetos distintos relacionados à implementação e teste do algoritmo de criptografia de fluxo **ChaCha20**.

## Estrutura do Repositório

O repositório está organizado em duas partes principais:

- **[t1/](./t1/):** Implementação didática e performática do ChaCha20 em linguagem C. Inclui uma interface de usuário em terminal (TUI) e testes de vetores oficiais (RFC 8439).
- **[t2/](./t2/):** Suíte de testes e ferramentas em Python para validação da implementação C rodando em hardware (STM32) via comunicação UART.

## Objetivo

O objetivo deste repositório é fornecer uma implementação de referência do ChaCha20 que seja ao mesmo tempo fácil de entender (didática) e validada contra padrões industriais, permitindo testes tanto em ambiente local quanto em sistemas embarcados.

---
Para instruções detalhadas de cada projeto, consulte os arquivos README em suas respectivas pastas.
