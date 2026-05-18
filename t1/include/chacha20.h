#ifndef CHACHA20_H
#define CHACHA20_H

/**
 * @file chacha20.h
 * @brief ChaCha20 Stream Cipher (RFC 8439) - Didactic Implementation
 * 
 * This header defines the public interface for the ChaCha20 stream cipher.
 * It provides functions for encryption/decryption (XOR) and keystream generation.
 */

#include <stdint.h>
#include <stddef.h>

/**
 * @brief XORs the input buffer with the ChaCha20 keystream.
 * 
 * This function performs both encryption and decryption (symmetric XOR).
 * It follows RFC 8439, using a 256-bit key and a 96-bit nonce.
 * 
 * @param out     Pointer to the output buffer (can be same as 'in').
 * @param in      Pointer to the input buffer (plaintext or ciphertext).
 * @param len     Length of the input buffer in bytes.
 * @param key     32-byte (256-bit) encryption key.
 * @param nonce   12-byte (96-bit) nonce (must be unique for each key).
 * @param counter Initial block counter (usually 0 or 1).
 */
void chacha20_xor(
    uint8_t *out,
    const uint8_t *in,
    size_t len,
    const uint8_t key[32],
    const uint8_t nonce[12],
    uint32_t counter
);

/**
 * @brief Generates a single 64-byte block of ChaCha20 keystream.
 * 
 * This function is primarily for didactic purposes, exposing the raw
 * keystream before it is XORed with any data.
 * 
 * @param keystream 64-byte output buffer for the generated keystream.
 * @param key       32-byte encryption key.
 * @param nonce     12-byte nonce.
 * @param counter   Block counter to use for this block.
 */
void chacha20_generate_keystream(
    uint8_t keystream[64],
    const uint8_t key[32],
    const uint8_t nonce[12],
    uint32_t counter
);

/**
 * @brief Advanced: XORs the input with a pre-initialized ChaCha20 state.
 * 
 * This function avoids repeated setup costs by working directly with a
 * 16-word state array. Useful for high-performance implementations.
 * 
 * @param out   Pointer to the output buffer.
 * @param in    Pointer to the input buffer.
 * @param len   Length in bytes.
 * @param state 16-word (64-byte) internal ChaCha20 state.
 */
void chacha20_xor_state(
    uint8_t *out,
    const uint8_t *in,
    size_t len,
    uint32_t state[16]
);

#endif // CHACHA20_H
