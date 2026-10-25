CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror -pedantic -O2
OPENSSL_CFLAGS := $(shell pkg-config --cflags openssl)
OPENSSL_LIBS := $(shell pkg-config --libs openssl)
TEST_BIN := /tmp/sdllabs-access-core-test
SMS_TEST_BIN := /tmp/sdllabs-sms-test
CORE_SRC := access_core.c sms_otp.c sms_parse.c

.PHONY: test
test:
	$(CC) $(CFLAGS) $(OPENSSL_CFLAGS) -I. $(CORE_SRC) tests/access_core_test.c -o $(TEST_BIN) $(OPENSSL_LIBS)
	$(TEST_BIN)
	$(CC) $(CFLAGS) $(OPENSSL_CFLAGS) -I. $(CORE_SRC) tests/sms_test.c -o $(SMS_TEST_BIN) $(OPENSSL_LIBS)
	$(SMS_TEST_BIN)
