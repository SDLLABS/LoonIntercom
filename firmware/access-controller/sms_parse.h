#ifndef SDLLABS_SMS_PARSE_H
#define SDLLABS_SMS_PARSE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "access_core.h"
#include "sms_otp.h"

/* Strict parser for an SMS body: "<COMMAND> <RESOURCE> <CODE>".
   COMMAND: ABRIR | OPEN (ASCII, case-insensitive).
   RESOURCE: decimal 1..AC_MAX_RESOURCE_ID, no leading zero.
   CODE: exactly SMS_OTP_DIGITS ASCII digits.
   Tokens separated by spaces; leading/trailing spaces, CR and LF ignored.
   Anything else, including non-ASCII or a body over SMS_MAX_BODY, fails. */

#define SMS_MAX_BODY 40u

struct sms_request {
    uint8_t command;     /* enum ac_sms_command */
    uint8_t resource_id;
    char code[SMS_OTP_DIGITS];
};

bool sms_parse(const char *body, size_t len, struct sms_request *out);

#endif
