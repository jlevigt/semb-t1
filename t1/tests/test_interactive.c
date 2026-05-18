#include "../include/chacha20.h"
#include <stdio.h>
#include <string.h>

/**
 * Takes user plaintext from stdin and shows encryption results using stack arrays.
 */
void test_user_input() {
    printf("\n--- User Input Encryption Test ---\n");

    char input[512];
    uint8_t output[512];
    uint8_t decrypted[512];

    printf("Enter plaintext (max 511 chars): ");
    
    if (fgets(input, sizeof(input), stdin) == NULL) return;
    
    // Remove trailing newline
    input[strcspn(input, "\n")] = 0;
    size_t len = strlen(input);

    if (len == 0) {
        printf("No input provided.\n");
        return;
    }

    const uint8_t key[32] = "User specified encryption key!!";
    const uint8_t nonce[12] = "UserNonce!!";
    const uint32_t counter = 0;

    chacha20_xor(output, (const uint8_t*)input, len, key, nonce, counter);
    
    printf("\nCiphertext (hex):\n");
    for (size_t i = 0; i < len; i++) {
        printf("%02x ", output[i]);
        if ((i + 1) % 16 == 0) printf("\n");
    }
    printf("\n");

    chacha20_xor(decrypted, output, len, key, nonce, counter);
    decrypted[len] = '\0';
    printf("\nDecrypted back: %s\n", (char*)decrypted);
}
