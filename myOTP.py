# A pure-Python3 implementation of TOTP (HOTP, HMAC)

# Can synchronize current Unix time (UTC) with a NTP pool

# Given an 80-bit base32 encoded secret key on command line,
# it displays current TOTP and expiration time
import sys, struct, time, base64
from hashlib import sha1, sha256, sha512
from socket import socket, AF_INET, SOCK_DGRAM


class NTPclock:
    "Reads current time from a NTP server to provide adjusted Unix time"
    def __init__ (p):
        client = socket(AF_INET, SOCK_DGRAM) # Internet, UDP
        address = ("pool.ntp.org", 123) # NTP server & port
        data = bytearray(48); data[0] = 27 # hex message to send to the server (NTPv3)
        client.sendto(data, address)
        T = int(time.time())
        data, address = client.recvfrom(48)
        t = struct.unpack("!12I", data)[10] # unpack the binary data and get the seconds out
        t -= 2208988800 # convert from NTP (1/1/1900 <- s) to Unix (1/1/1970 <- s) timestamp
        if t < 0:
            t = T # backup function
            print('WARNING: bad time from NTP, using internal time')
        p.delta = t-T
        if p.delta: print('WARNING: internal and NTP times differ by %d second(s)' % p.delta)
    
    def time(p): return time.time() - p.delta

clock = NTPclock()

def HMAC(k, m, h):
    "Get the binary HMAC for message 'm' using key 'k' and hash 'h'. See RFCs 2104 and 2202"
    if len(k) > 64:
        k = h(k).digest()
    j = len(k)
    opad = bytearray(64*b'\x5C')
    ipad = bytearray(64*b'\x36')
    while j:
        j -= 1
        opad[j] = 0x5C ^ k[j]
        ipad[j] = 0x36 ^ k[j]
    d = h(opad)
    d.update(h(ipad+m).digest())
    return d.digest()


def HOTP(k, c, d=6, h=sha1):
    """Get 'd' digits from the HMAC-based One Time Password for key 'k' and
    counter 'c', using hash 'h'. See RFC 4226"""
    if h not in (sha1, sha256, sha512):
        raise BaseException("HOTP hash must be one of SHA-1 (default), SHA-256 or SHA-512!")
    if not (5 < d < 11):
        raise BaseException("HOTP must be from 6 to 10 decimal digits long!")
    if c < 0:
        raise BaseException("HOTP counter can't be negative!")
    # 1. Make counter 'c' a BE QWORD
    b = bytearray(8)
    struct.pack_into('>Q', b, 0, c)
    # 2. Computate HMAC for counter
    b = bytearray(HMAC(k, b, h))
    # 3. Extract a BE DWORD (32-bit) from HMAC according to its last byte
    i = b[-1] & 0xF
    b[i] &= 0x7F # Zero DWORD MSB
    # 5. Convert it into decimal
    dec = struct.unpack_from('>I', b, i)[0]
    # 6. Pick the (least significant) requested digits
    return ('%010d'%dec)[-d:]


def TOTP(k, TI=30, d=6, T=None):
    """Get the Time-based One Time Password of 'd' digits for key 'k',
    deriving the counter from a 'T' Unix timestamp (default: current time)
    and a 'TI' interval (default: 30 s). See RFC 6238"""
    if T == None: T = clock.time()
    TC = int(T) // TI
    return HOTP(k, TC, d)


def TOTPT(k, TI=30, d=6, T=None):
    "Like TOTP, but returns a tuple with a TOTP and the seconds left before its expiration"
    if T == None: T = clock.time()
    TC = int(T) // TI
    return HOTP(k, TC, d), TI - (int(T) - TC*TI)


def ValidateTOTP(totp, k, TI=30, I=1, d=6):
    """Validate a 'totp' of 'd' digits within 'I' intervals of 'TI' seconds,
    given a 'k' key. See RFC 6238"""
    T = int(clock.time()) - TI*I
    totps = [] # odd list, median == current OTP
    i = I*2+1
    while i:
        totps += [TOTP(k, TI, d, T)]
        T += TI*I
        i -= 1
    return (totp in totps)



if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Syntax: myOTP.py BASE32_KEY') # expects an 80-bit key, base32 encoded
        sys.exit(1)
    k = base64.b32decode(sys.argv[1])
    totp, s = TOTPT(k)
    print (f'Current TOTP is {totp} and will expire in {s} second(s).')
