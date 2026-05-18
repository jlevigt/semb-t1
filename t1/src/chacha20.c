#include "../include/chacha20.h"
#include <string.h>

/* Utility Macros and Constants */
#define CHACHA20_ROUNDS 20
#define CHACHA20_STATE_WORDS 16
#define CHACHA20_BLOCK_BYTES 64

/**
 * @brief Left circular rotation of a 32-bit word.
 * @param x The 32-bit word to rotate.
 * @param n The number of bits to rotate.
 * @return The rotated value.
 */
static inline uint32_t rotl32(uint32_t x, int n) {
    // Standard left rotation: (x << n) handles high bits, 
    // (x >> (32 - n)) handles low bits that wrap around.
    return (x << n) | (x >> (32 - n));
}

/**
 * @brief Loads a 32-bit word from a byte buffer in little-endian.
 * @param src Pointer to the input byte buffer (at least 4 bytes).
 * @return The 32-bit word in host byte order.
 */
static inline uint32_t load32_le(const uint8_t src[4]) {
    // ChaCha20 uses little-endian byte ordering for its internal arithmetic.
    // Each byte contributes 8 bits to the word.
    return (uint32_t)src[0] | 
          ((uint32_t)src[1] << 8) | 
          ((uint32_t)src[2] << 16) | 
          ((uint32_t)src[3] << 24);
}

/**
 * @brief Stores a 32-bit word into a byte buffer in little-endian.
 * @param dst Pointer to the output byte buffer.
 * @param val The 32-bit word to store.
 */
static inline void store32_le(uint8_t dst[4], uint32_t val) {
    // Converts a host-order word into little-endian bytes.
    dst[0] = (uint8_t)(val & 0xFF);
    dst[1] = (uint8_t)((val >> 8) & 0xFF);
    dst[2] = (uint8_t)((val >> 16) & 0xFF);
    dst[3] = (uint8_t)((val >> 24) & 0xFF);
}

/**
 * @brief The ChaCha20 Quarter Round operation.
 * 
 * Operates on four 32-bit words in the internal state matrix.
 * It uses ARX (Addition, Rotation, XOR) logic.
 */
static void quarter_round(uint32_t *a, uint32_t *b, uint32_t *c, uint32_t *d) {
    *a += *b; *d ^= *a; *d = rotl32(*d, 16);
    *c += *d; *b ^= *c; *b = rotl32(*b, 12);
    *a += *b; *d ^= *a; *d = rotl32(*d, 8);
    *c += *d; *b ^= *c; *b = rotl32(*b, 7);
}

/**
 * @brief Generates a ChaCha20 block from an input state.
 * 
 * Performs 20 rounds of quarter-round operations on the 4x4 matrix,
 * then adds the initial state to the results.
 */
static void chacha20_block(const uint32_t input_state[16], uint8_t keystream[64]) {
    uint32_t x[CHACHA20_STATE_WORDS];
    
    // Copy initial state to working state
    memcpy(x, input_state, sizeof(x));

    // 10 iterations of double rounds (column round + diagonal round) = 20 total rounds
    for (int i = 0; i < 10; i++) {
        // Column rounds (vertical)
        quarter_round(&x[0], &x[4], &x[8],  &x[12]);
        quarter_round(&x[1], &x[5], &x[9],  &x[13]);
        quarter_round(&x[2], &x[6], &x[10], &x[14]);
        quarter_round(&x[3], &x[7], &x[11], &x[15]);

        // Diagonal rounds
        quarter_round(&x[0], &x[5], &x[10], &x[15]);
        quarter_round(&x[1], &x[6], &x[11], &x[12]);
        quarter_round(&x[2], &x[7], &x[8],  &x[13]);
        quarter_round(&x[3], &x[4], &x[9],  &x[14]);
    }

    // Add working state to initial state and store as little-endian bytes
    for (int i = 0; i < CHACHA20_STATE_WORDS; i++) {
        store32_le(&keystream[i * 4], x[i] + input_state[i]);
    }

    // Security: Securely zero working state
    // Isso pode afetar o desempenho
    memset(x, 0, sizeof(x));
}

void chacha20_xor_state(uint8_t *out, const uint8_t *in, size_t len, uint32_t state[16]) {
    uint8_t keystream[CHACHA20_BLOCK_BYTES];
    size_t offset = 0;

    while (offset < len) {
        chacha20_block(state, keystream);
        
        // Counter is always the 13th word (word 12) in the RFC 8439 state.
        state[12]++;

        size_t block_len = (len - offset > CHACHA20_BLOCK_BYTES) ? 
                           CHACHA20_BLOCK_BYTES : (len - offset);

        for (size_t i = 0; i < block_len; i++) {
            out[offset + i] = in[offset + i] ^ keystream[i];
        }

        offset += block_len;
    }

    // Security: Securely zero keystream
    memset(keystream, 0, sizeof(keystream));
}

void chacha20_xor(
    uint8_t *out,
    const uint8_t *in,
    size_t len,
    const uint8_t key[32],
    const uint8_t nonce[12],
    uint32_t counter
) {
    uint32_t state[CHACHA20_STATE_WORDS];

    // 1. Constants: "expand 32-byte k" in little-endian words
    state[0] = 0x61707865;
    state[1] = 0x3320646e;
    state[2] = 0x79622d32;
    state[3] = 0x6b206574;

    // 2. Key: 256 bits (8 words)
    for (int i = 0; i < 8; i++) {
        state[4 + i] = load32_le(&key[i * 4]);
    }

    // 3. Counter: 32 bits (1 word)
    state[12] = counter;

    // 4. Nonce: 96 bits (3 words)
    for (int i = 0; i < 3; i++) {
        state[13 + i] = load32_le(&nonce[i * 4]);
    }

    // Run the XOR transformation
    chacha20_xor_state(out, in, len, state);

    // Security: Clear state
    memset(state, 0, sizeof(state));
}

void chacha20_generate_keystream(
    uint8_t keystream[64],
    const uint8_t key[32],
    const uint8_t nonce[12],
    uint32_t counter
) {
    uint32_t state[CHACHA20_STATE_WORDS];

    // Re-initialize state (same logic as chacha20_xor)
    state[0] = 0x61707865;
    state[1] = 0x3320646e;
    state[2] = 0x79622d32;
    state[3] = 0x6b206574;

    for (int i = 0; i < 8; i++) {
        state[4 + i] = load32_le(&key[i * 4]);
    }

    state[12] = counter;

    for (int i = 0; i < 3; i++) {
        state[13 + i] = load32_le(&nonce[i * 4]);
    }

    // Generate just one block
    chacha20_block(state, keystream);

    // Security: Clear state
    memset(state, 0, sizeof(state));
}
