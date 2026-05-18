CC = gcc
CFLAGS = -Wall -Wextra -O3 -It1/include
SRC_CRYPTO = t1/src/chacha20.c t1/src/openssl_chacha20.c
SRC_TESTS = t1/tests/test_vectors.c t1/tests/test_nonce_reuse.c t1/tests/demo_basic.c t1/tests/test_interactive.c t1/tests/test_8kb.c t1/tests/test_openssl.c
BIN_DIR = t1/bin
EXTRA_ARGS = -l crypto

all: $(BIN_DIR)/chacha20_tui

$(BIN_DIR)/chacha20_tui: t1/main.c $(SRC_CRYPTO) $(SRC_TESTS)
	@mkdir -p $(BIN_DIR)
	$(CC) $(CFLAGS) $^ -o $@ $(EXTRA_ARGS)

clean:
	rm -rf $(BIN_DIR)
	rm -rf t2/data

clean-data:
	rm -rf t2/data

.PHONY: all clean clean-data
