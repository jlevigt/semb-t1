#include "../include/openssl_chacha20.h"
#include <openssl/evp.h>
#include <string.h>

/**
 * Adapter to openssl standard
 * https://docs.openssl.org/3.0/man3/EVP_chacha20/#description
 */
void openssl_chacha20_xor(
    uint8_t *out,
    const uint8_t *in,
    size_t len,
    const uint8_t key[32],
    const uint8_t nonce[12],
    uint32_t counter)
{
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    int outlen;
    uint8_t iv[17];
    memcpy(iv, (uint8_t *)&counter, 4);
    memcpy(iv + 4, nonce, 12);
    iv[16] = '\0';

    EVP_EncryptInit_ex(ctx, EVP_chacha20(), NULL, key, iv);
    EVP_EncryptUpdate(ctx, out, &outlen, in, len);
    EVP_EncryptFinal_ex(ctx, out + outlen, &outlen);
    EVP_CIPHER_CTX_free(ctx);
}
