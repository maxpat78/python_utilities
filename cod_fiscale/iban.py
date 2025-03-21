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

def mod_97_32(n):
    "Calculate IBAN mod 97 if MP integers unavailable (n is a string)"
    n9='' # a 9 digit number (32-bit max)
    while 1:
        i = min(9, len(n)) # process at most 9 digits at a time
        n9 += n[:i]
        n = n[i:]
        m = int(n9) % 97
        if not n: return m
        n9 = str(m)

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
    #~ assert mod_97_32(s) == int(s) % 97
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

def ckc_it(s):
    "Generate check code (1 character) for IT BBAN (len=22+1)"
    "BBAN=check letter(1)+bank code(5)+branch code(5)+bank account nr.(12)"
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

def ckc_fr(s):
    "Generate check code (2 digits) for FR and MC BBAN (len=21+2)"
    V = 2*[i for i in range(1,10)] + [i for i in range(2,10)] # values of the 26 letters
    bban = ''
    for c in s.upper():
        if c.isdigit():
            bban += c
        elif c.isalpha():
            bban += str(V[ord(c)-65])
        else:
            raise BaseException("Invalid FR BBAN character")
    # Range 01-97. See https://fr.wikipedia.org/wiki/Cl%C3%A9_RIB
    return '%02d' % (97 - ((89 * int(bban[:5]) + 15 * int(bban[5:10]) + 76 * int(bban[10:16]) + 3 * int(bban[16:])) % 97))

ckc_mc = ckc_fr

def ckc_si(s):
    "Generate check code (2 digits) for SI BBAN (len=15+2)"
    "BBAN=bank code(2)+branch code(3)+bank account nr.(8)+check digits(2)"
    s += '00'
    if len(s) != 15:
        raise BaseException("Invalid SI BBAN, must have 13 digits")
    if not s.isdigit():
        raise BaseException("Invalid SI BBAN, must be numerical")
    return '%02d' % (98 - mod_97_32(s))

def ckc_es(s):
    "Generate check code (2 digits) for ES BBAN (len=18+2)"
    "BBAN=bank code(4)+branch code(4)+chek digits(2)+bank account nr.(10)"
    if not s.isdigit():
        raise BaseException("Invalid ES BBAN, must be numerical")
    if len(s) != 20:
        raise BaseException("Invalid ES BBAN, must have 20 digits")
    V = (1, 2, 4, 8, 5, 10, 9, 7, 3, 6)
    s1 = '00'+s[:8]
    s2 = s[10:]
    sum1=0
    sum2=0
    for i in range(10):
        sum1 += int(s1[i]) * V[i]
        sum2 += int(s2[i]) * V[i]
    c1 = 11 - sum1%11
    """From EUROPEAN COMMITTEE FOR BANKING STANDARDS
    (cfr. https://www.ecbs.org/Download/Tr201v3.9.pdf):
    If the remainder of the subtraction should be either 10 or 11, it is
    agreed that the check digit becomes 1 if the remainder is 10 and 0 if the
    remainder is 11"""
    if c1 == 10: c1 = 1
    if c1 == 11: c1 = 0
    c2 = 11 - sum2%11
    if c2 == 10: c2 = 1
    if c2 == 11: c2 = 0
    return '%d%d' % (c1,c2)

def ckc_de(s):
    "Too long to implement. See the Bundesbank Jun 2018 88-pag. pruefzifferberechnungsmethoden-data.pdf"
    "BBAN=bank code(8)+bank account nr.(10)"
    pass

def bban_check_gen_IT(s):
    "Calculate IT CIN control letter on a 22-chars account number"
    if len(s) != 22:
        raise BaseException("Invalid IT ABI-CAB-NUMBER length")
    return ckc_it(s)

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
