""" Utilities to validate an IBAN and generate right check digits.

General IBAN format is SS CC BBAN where:
- SS is the country code (2 letters according to ISO 3166)
- CC two check digits
- BBAN is the country-specific Basic Bank Account Number (30 chars max)

BBAN can be a mix of (case-insensitive) letters and numbers.
Each country has a fixed length BBAN.
Some BBAN have their internal check methods.

IBAN check digits are generated according to MOD-97-10 (ISO/IEC 7064:2003).

Check digits in the ranges 00 to 96, 01 to 97, and 03 to 99 will also provide
validation of an IBAN, but the standard is silent as to whether or not these
ranges may be used. """
import sqlite3

def iban_check_gen(cc, bban):
    "Generate the IBAN 2 check digits for a given country code and BBAN (variable length)"
    size = len(bban)
    if size < 11 or size > 28:
        raise BaseException("Invalid BBAN length")
    if len(cc) != 2:
        raise BaseException("Invalid country code length")
    iban = bban + cc + '00'
    s = '' # transformed string to validate
    for c in iban.upper():
        n = ord(c)
        isletter = 0
        if n > 64 and n < 91:
            isletter = 1
        elif n < 48 or n > 57:
            raise BaseException("Invalid characters in BBAN")
        if isletter:
            s += str(n-55) # replace letter with its literal ASCII code minus 55
        else:
            s += c
    check = 98 - int(s) % 97
    return '%02d'%check

def iban_validate(iban):
    "Check IBAN validity (0=invalid)"
    iban = iban.upper()
    size = len(iban)
    if size < 15 or size > 32:
        raise BaseException("Invalid IBAN length")
    bban = iban[4:]
    check = iban_check_gen(iban[:2], bban)
    if check == iban[2:4]:
        return 1
    return 0

def crc_it_mod26t(s):
    "Same algorithm for Italian Tax ID"
    # codes related to even 0-9 digits and A-Z characters
    oddn = (1, 0, 5, 7, 9, 13, 15, 17, 19, 21)
    oddc = (*oddn, 2, 4, 18, 20, 11, 3, 6, 8, 12, 14, 16, 10, 22, 25, 24, 23)
    csum = 0
    s = s.upper()
    for i in range(len(s)):
        c = s[i]
        j = ord(c) - 65
        if not i % 2: # even position: fixed offset
            if c.isalpha():
                csum += oddc[j]
            else:
                j = ord(c) - 48
                csum += oddn[j]
        else: # odd position: natural offset
            if c.isalpha():
                csum += j
            else:
                csum += int(c)
    return chr(csum%26+65)

def bban_check_gen_IT(s):
    "Calculate IT CIN control letter on a 22-chars account number"
    if len(s) != 22:
        raise BaseException("Invalid IT ABI-CAB-NUMBER length")
    return crc_it_mod26t(s)

def iban_gen_IT(abi, cab, n):
    "Generate an Italian IBAN given ABI, CAB and account numbers"
    abi = '%05d' % abi
    cab = '%05d' % cab
    if type(n) == int:
        n = '%012d' % n
    else:
        if len(n) != 12:
            try:
                n = '%012d' % int(n)
            except:
                raise BaseException("Non-numerical account number is not 12 characters")
    acc = abi+cab+n
    if len(acc) != 22:
        raise BaseException("Invalid IT ABI-CAB-NUMBER length")
    cin = bban_check_gen_IT(acc)
    bban = cin+acc
    check = iban_check_gen('IT', bban)
    return 'IT'+check+bban
