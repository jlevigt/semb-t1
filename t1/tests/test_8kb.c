#include "../include/chacha20.h"
#include <stdio.h>
#include <string.h>

/**
 * Encrypts and decrypts 8KB (8192 bytes) of dummy data using stack-allocated arrays.
 */
void test_8kb() {
    printf("\n--- 8KB Data Encryption/Decryption Test ---\n");

    const size_t size = 8192;
    static uint8_t original[8192];
    static uint8_t ciphertext[8192];
    static uint8_t decrypted[8192];

    // Fill with a repeating pattern
    for (size_t i = 0; i < size; i++) {
        original[i] = (uint8_t)(i % 256);
    }

    const uint8_t key[32] = {0x11, 0x22, 0x33, 0x44};
    const uint8_t nonce[12] = {0x55, 0x66, 0x77, 0x88};
    const uint32_t counter = 0;

    printf("Encrypting 8KB of data...\n");
    chacha20_xor(ciphertext, original, size, key, nonce, counter);

    printf("Decrypting 8KB of data...\n");
    chacha20_xor(decrypted, ciphertext, size, key, nonce, counter);

    if (memcmp(original, decrypted, size) == 0) {
        printf("[PASS] 8KB encryption and decryption successful.\n");
    } else {
        printf("[FAIL] Data mismatch after decryption!\n");
    }
}
