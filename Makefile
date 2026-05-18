CC = gcc
CFLAGS = -Wall -Wextra -O3 -Iinclude
SRC_CRYPTO = src/chacha20.c src/openssl_chacha20.c
SRC_TESTS = tests/test_vectors.c tests/test_nonce_reuse.c tests/demo_basic.c tests/test_interactive.c tests/test_8kb.c tests/test_openssl.c
BIN_DIR = bin
EXTRA_ARGS = -l crypto

all: $(BIN_DIR)/chacha20_tui

$(BIN_DIR)/chacha20_tui: main.c $(SRC_CRYPTO) $(SRC_TESTS)
	@mkdir -p $(BIN_DIR)
	$(CC) $(CFLAGS) $^ -o $@ $(EXTRA_ARGS)

clean:
	rm -rf $(BIN_DIR)

.PHONY: all clean
