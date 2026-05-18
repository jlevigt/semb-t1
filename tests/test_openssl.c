#include "../include/chacha20.h"
#include "../include/openssl_chacha20.h"

#include <string.h>
#include <stdio.h>
#define INPUT_SIZE_CAP 256

void test_openssl()
{
    printf("\n--- Running RFC 8439 Test Vectors + OpenSSL version ---\n");

    const uint8_t key[32] = {
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f,
        0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17,
        0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f};

    const uint8_t nonce[12] = {
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x4a,
        0x00, 0x00, 0x00, 0x00};

    const uint32_t counter = 1;

    const char plaintext[] = "Ladies and Gentlemen of the class of '99: If I could offer you only one tip for the future, sunscreen would be it.";
    const uint8_t expected_ciphertext[] = {
        0x6e, 0x2e, 0x35, 0x9a, 0x25, 0x68, 0xf9, 0x80, 0x41, 0xba, 0x07, 0x28, 0xdd, 0x0d, 0x69, 0x81,
        0xe9, 0x7e, 0x7a, 0xec, 0x1d, 0x43, 0x60, 0xc2, 0x0a, 0x27, 0xaf, 0xcc, 0xfd, 0x9f, 0xae, 0x0b,
        0xf9, 0x1b, 0x65, 0xc5, 0x52, 0x47, 0x33, 0xab, 0x8f, 0x59, 0x3d, 0xab, 0xcd, 0x62, 0xb3, 0x57,
        0x16, 0x39, 0xd6, 0x24, 0xe6, 0x51, 0x52, 0xab, 0x8f, 0x53, 0x0c, 0x35, 0x9f, 0x08, 0x61, 0xd8,
        0x07, 0xca, 0x0d, 0xbf, 0x50, 0x0d, 0x6a, 0x61, 0x56, 0xa3, 0x8e, 0x08, 0x8a, 0x22, 0xb6, 0x5e,
        0x52, 0xbc, 0x51, 0x4d, 0x16, 0xcc, 0xf8, 0x06, 0x81, 0x8c, 0xe9, 0x1a, 0xb7, 0x79, 0x37, 0x36,
        0x5a, 0xf9, 0x0b, 0xbf, 0x74, 0xa3, 0x5b, 0xe6, 0xb4, 0x0b, 0x8e, 0xed, 0xf2, 0x78, 0x5e, 0x42,
        0x87, 0x4d};

    size_t len = strlen(plaintext);
    uint8_t ciphertext[INPUT_SIZE_CAP], open_ciphertext[INPUT_SIZE_CAP],
        decrypted[INPUT_SIZE_CAP], open_decrypted[INPUT_SIZE_CAP],
        crossdecrypt[INPUT_SIZE_CAP], open_crossdecrypt[INPUT_SIZE_CAP];

    chacha20_xor(ciphertext, (const uint8_t *)plaintext, len, key, nonce, counter);
    openssl_chacha20_xor(open_ciphertext, (const uint8_t *)plaintext, len, key, nonce, counter);
    printf("Ciphertext: \n");
    for (size_t i = 0; i < len; i++)
    {
        printf("%02x ", ciphertext[i]);
    }
    printf("\n\n");

    printf("OpenSSL Ciphertext: \n");
    for (size_t i = 0; i < len; i++)
    {
        printf("%02x ", open_ciphertext[i]);
    }
    printf("\n\n");

    if (memcmp(ciphertext, open_ciphertext, len) == 0)
        printf("[PASS] Texto cifrado igual\n");
    else
        printf("[FAIL] Texto cifrado diferente\n");

    // 3. Decrypt
    chacha20_xor(decrypted, ciphertext, len, key, nonce, counter);
    openssl_chacha20_xor(open_decrypted, open_ciphertext, len, key, nonce, counter);
    open_decrypted[len] = '\0';
    printf("OpenSSL Decrypted: %s\n", (char *)open_decrypted);

    if (memcmp(expected_ciphertext, open_ciphertext, len) == 0)
        printf("[PASS] encryption matches RFC 8439 vector.\n");
    else
        printf("[FAIL] encryption mismatch!\n");


    // 4. Cross-decrypt
    openssl_chacha20_xor(crossdecrypt, open_ciphertext, len, key, nonce, counter);
    chacha20_xor(open_crossdecrypt, ciphertext, len, key, nonce, counter);
    crossdecrypt[len] = '\0';
    open_crossdecrypt[len] = '\0';
    printf("\nCross-Decryption:\n%s\n%s\n", crossdecrypt, open_crossdecrypt);

    if (memcmp(crossdecrypt, open_crossdecrypt, len) == 0)
        printf("[PASS] cross-decryption worked :D");
    else
        printf("[FAIL] cross-decryption failed :(");
}
