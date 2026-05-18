#include "../include/chacha20.h"
#include <stdio.h>
#include <string.h>

/**
 * Demonstrates why reusing a (Key, Nonce) pair is catastrophic for stream ciphers.
 */
void demo_nonce_reuse() {
    printf("\n--- Nonce Reuse Vulnerability Demonstration ---\n\n");

    const uint8_t key[32] = {0xAA, 0xAA}; // Static key
    const uint8_t nonce[12] = {0xBB, 0xBB}; // REUSED NONCE (Dangerous!)
    const uint32_t counter = 0;

    const char *p1 = "Keep this secret: 123456";
    const char *p2 = "Another secret: password";
    size_t len = strlen(p1);

    uint8_t c1[64], c2[64];
    memset(c1, 0, sizeof(c1));
    memset(c2, 0, sizeof(c2));

    // Encrypt both with same key and nonce
    chacha20_xor(c1, (const uint8_t *)p1, len, key, nonce, counter);
    chacha20_xor(c2, (const uint8_t *)p2, len, key, nonce, counter);

    printf("P1: %s\n", p1);
    printf("P2: %s\n\n", p2);

    // XOR the ciphertexts
    uint8_t c1_xor_c2[64];
    for (size_t i = 0; i < len; i++) {
        c1_xor_c2[i] = c1[i] ^ c2[i];
    }

    // XOR the plaintexts
    uint8_t p1_xor_p2[64];
    for (size_t i = 0; i < len; i++) {
        p1_xor_p2[i] = (uint8_t)p1[i] ^ (uint8_t)p2[i];
    }

    printf("Comparing (C1 XOR C2) with (P1 XOR P2)...\n");
    if (memcmp(c1_xor_c2, p1_xor_p2, len) == 0) {
        printf("[SUCCESS] C1 XOR C2 == P1 XOR P2\n");
        printf("The keystream K was completely eliminated!\n");
    } else {
        printf("[FAILURE] Something went wrong.\n");
    }

    printf("\nRecovering P2 from C1, C2, and knowledge of P1:\n");
    uint8_t recovered_p2[64];
    for (size_t i = 0; i < len; i++) {
        // P2 = (C1 XOR C2) XOR P1
        recovered_p2[i] = c1_xor_c2[i] ^ (uint8_t)p1[i];
    }
    recovered_p2[len] = '\0';
    printf("Recovered P2: %s\n", (char *)recovered_p2);
}
