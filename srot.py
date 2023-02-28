def _chrot(c, pos):
    c = ord(c.lower())
    if c not in range(97,123):
        return chr(c)
    pos %= 26
    c+=pos
    if c > 122:
        c-=26
    return chr(c)

def srot(s, n=3):
    """Avanza la posizione alfabetica delle singole lettere di una stringa di 'n' posizioni"""
    return ''.join(map(lambda x: _chrot(x,n), s))

if __name__ == '__main__':
 print (srot("ciao ciao a te!"))
