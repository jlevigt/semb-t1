#include "../include/chacha20.h"
#include <stdio.h>
#include <string.h>

/**
 * Basic demonstration of ChaCha20 encryption.
 */
void demo_encrypt() {
    printf("\n--- Basic ChaCha20 Encryption Demo ---\n\n");

    const uint8_t key[32] = {0x01, 0x02, 0x03}; // Example key
    const uint8_t nonce[12] = {0x04, 0x05, 0x06}; // Example nonce
    const uint32_t counter = 0;

    const char *plaintext = "This is a secret message for academic purposes.";
    size_t len = strlen(plaintext);
    uint8_t ciphertext[64];
    uint8_t decrypted[64];

    // 1. Show Keystream Generation (First block)
    uint8_t keystream[64];
    chacha20_generate_keystream(keystream, key, nonce, counter);
    printf("Keystream (first 16 bytes): ");
    for (int i = 0; i < 16; i++) {
        printf("%02x ", keystream[i]);
    }
    printf("...\n\n");

    // 2. Encrypt
    printf("Plaintext: %s\n", plaintext);
    chacha20_xor(ciphertext, (const uint8_t *)plaintext, len, key, nonce, counter);
    printf("Ciphertext: ");
    for (size_t i = 0; i < len; i++) {
        printf("%02x ", ciphertext[i]);
    }
    printf("\n\n");

    // 3. Decrypt
    chacha20_xor(decrypted, ciphertext, len, key, nonce, counter);
    decrypted[len] = '\0';
    printf("Decrypted: %s\n", (char *)decrypted);
}
