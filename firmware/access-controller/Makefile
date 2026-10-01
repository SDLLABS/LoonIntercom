CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror -pedantic -O2
OPENSSL_CFLAGS := $(shell pkg-config --cflags openssl)
OPENSSL_LIBS := $(shell pkg-config --libs openssl)
TEST_BIN := /tmp/sdllabs-access-core-test

.PHONY: test
test:
	$(CC) $(CFLAGS) $(OPENSSL_CFLAGS) -I. access_core.c tests/access_core_test.c -o $(TEST_BIN) $(OPENSSL_LIBS)
	$(TEST_BIN)
