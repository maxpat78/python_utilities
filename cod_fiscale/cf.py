"Funzioni per il calcolo del codice fiscale italiano secondo il D.M. Finanze n.13813 del 23/12/1976 e della partita IVA"
from difflib import SequenceMatcher
from plug_iva import uffici
from plug_comuni_stati import comuni

def islike(a, b):
    "Testa la somiglianza tra le stringhe a e b; o tra una parola a e una parte di altra stringa b"
    b1 = b.split()
    if len(b1) > 1:
        for bx in b1:
            if SequenceMatcher(None, a, bx).ratio() > 0.74: return True
        return False
    else:
        return SequenceMatcher(None, a, b).ratio() > 0.74

def get_cod_comune(nome):
    "Ricava il codice catastale di 4 caratteri corrispondente a un comune o stato estero"
    nome = nome.upper()
    r = []
    for o in comuni:
        if nome == comuni[o][0]: r += [o]
    if len(r) > 1:
        print(f"ATTENZIONE: risultati multipli per '{nome}'! Usato il primo.")
        for n in r: print(f"{n} {comuni[n][0]} ({comuni[n][1]})")
        return r[0]
    if not r:
        print(f"Nessun Comune o Stato Estero '{nome}'")
        print(f"Nomi simili:")
        for o in comuni:
            simile = comuni[o][0]
            if nome in simile or islike(nome, simile):
                r += [o]
                print(simile)
        if len(r) == 1:
            print("Assunto l'unico nome simile")
            return r[0]
        raise BaseException("Non trovato")
    return r[0]

def get_omocodici(cf, pos=(14,13,12,10,9,7,6)):
    "Ricava 127 omocodici sostituendo una o piu' delle 7 cifre"
    cf = cf.upper()
    if len(cf) > 15: cf = cf[:15] # ignora il codice di controllo
    OMO = []
    s = 'LMNPQRSTUV'
    # Per ogni posizione, sostituisce cifra con lettera
    for i in range(len(pos)):
        L = list(cf)
        j = pos[i]
        if not cf[j].isdigit(): continue
        L[j] = s[int(cf[j])]
        z = ''.join(L)
        OMO+=[z+get_ctl_chr(z)]
        OMO += get_omocodici(z, pos[1:])
    return set(OMO)

def get_cf_base(omocodice):
    "Ricava il codice fiscale base da uno dei 127 omocodici"
    cf = ''
    s = 'LMNPQRSTUV'
    if len(omocodice) > 15:
        omocodice = omocodice[:15]
    omocodice = omocodice.upper()
    for i in range(len(omocodice)):
        c = omocodice[i]
        if i in (14,13,12,10,9,7,6):
            if c.isdigit():
                cf += c
                continue
            j = s.index(c)
            if j > -1:
                cf += str(j)
                continue
            raise BaseException(f"Omocodice invalido: lettera {c} non ammessa in posizione {i}")
        else:
            cf += c
    return cf[:15] + get_ctl_chr(cf[:15])

def get_dati_cf(cf):
    "Determina se un codice fiscale sia valido e restituisce sesso, luogo e data di nascita"
    if len(cf) != 16: return None
    check = get_ctl_chr(cf[:15])
    if check != cf[15]:
        print('Carattere di controllo invalido')
        return None
    ncf = get_cf_base(cf)
    if ncf != cf:
        print(f"nota: {cf} omocodice di {ncf}")
    cod = ncf[-5:-1]
    aa = int(ncf[6:8]) # nota: ambiguo, +1900 o +2000? p.e. 20 -> 1920 o 2020?
    mm = ncf[8]
    gg = int(ncf[9:11])
    if gg > 40:
        sesso = 'F'
        gg-=40
    else:
        sesso = 'M'
    return sesso, comuni[cod], (gg, 'ABCDEHLMPRST'.index(mm)+1, aa)

def get_data_di_nascita(data, F=0):
    "Ricava 5 caratteri da data di nascita (gg,mm,aaaa) e sesso"
    s, g = 'ABCDEHLMPRST', data[0]
    if F: g += 40
    return  '%s%c%02d' % (str(data[2])[-2:], s[data[1]-1], g)

def get_ctl_chr(cf):
    "Ricava la lettera finale di controllo"
    sum = 0
    dispar = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ','BAKPLCQDREVOSFTGUHMINJWZYX','0123456789', '10   2 3 4   5 6 7 8 9')
    if len(cf) != 15:
        raise RuntimeException("Il codice fiscale non ha 15 cifre")
    cf = cf.upper()
    for c in range(15):
        i = 0
        if c % 2 == 0: i = 1
        if cf[c].isdigit(): i += 2
        sum += dispar[i].index(cf[c])
    return dispar[0][sum%26]

def get_cod_cognome(cognome):
    "Ricava tre lettere dal cognome"
    cognome = cognome.upper()
    cc, vv = [], []
    for c in cognome:
        if c in 'AEIOU': vv+=[c]
        else: cc+=[c]
    cl, vl = len(cc), len(vv)
    if cl >= 3: return cc[0]+cc[1]+cc[2]
    if cl == 2 and vl >= 1: return cc[0]+cc[1]+vv[0]
    if cl == 1 and vl >= 2: return cc[0]+vv[0]+vv[1]
    if cl == 2 and vl == 0: return cc[0]+cc[1]+'X'
    if cl == 1 and vl == 1: return cc[0]+vv[1]+'X'
    if cl == 0 and vl  > 2: return vv[0]+vv[1]+vv[2]
    if cl == 0 and vl == 2: return vv[0]+vv[1]+'X'

def get_cod_nome(nome):
    "Ricava tre lettere dal nome"
    nome = nome.upper()
    cc, vv = [], []
    for c in nome:
        if c in 'AEIOU': vv+=[c]
        else: cc+=[c]
    cl, vl = len(cc), len(vv)
    if cl >= 4: return cc[0]+cc[2]+cc[3]
    if cl == 3: return cc[0]+cc[1]+cc[2]
    if cl == 2 and vl >= 1: return cc[0]+cc[1]+vv[0]
    if cl == 1 and vl >= 2: return cc[0]+vv[0]+vv[1]
    if cl == 1 and vl == 1: return cc[0]+vv[1]+'X'
    if cl == 0 and vl  > 2: return vv[0]+vv[1]+vv[2]
    if cl == 0 and vl == 2: return vv[0]+vv[1]+'X'

def get_codice_fiscale(nome, cognome, sesso, data_nascita, luogo_nascita):
    "Genera un codice fiscale formalmente valido dai dati personali [data_nascita: tuple(gg,mm,aaaa)]"
    c = get_cod_cognome(cognome)
    n = get_cod_nome(nome)
    d = get_data_di_nascita(data_nascita, {'M':0,'F':1}[sesso.upper()])
    co = get_cod_comune(luogo_nascita) # comune o stato estero
    k = get_ctl_chr(c+n+d+co)
    return c+n+d+co+k

# Tabella Uffici finanziari, settore: V
# https://www1.agenziaentrate.gov.it/servizi/codici/ricerca/VisualizzaTabella.php?ArcName=UFFICI#
def crc_piva(n):
    "Genera la cifra di controllo di una partita IVA/codice fiscale numerico a 10 cifre (codice di Luhn)"
    if len(n) != 10 or not n.isdigit():
        raise ValueError("Deve avere 10 cifre")
    cifre = [int(c) for c in n]
    # Somma le cifre dispari
    a = sum(cifre[i] for i in range(0, 10, 2))
    # Raddoppia le cifre pari, sommando se >9
    b = sum(sum(divmod(cifre[i] * 2, 10)) for i in range(1, 10, 2))
    # Somma totale
    c = a+b
    # Calcolo della cifra di controllo (complemento a 10 dell'ultima cifra)
    check = (10 - (c % 10)) % 10
    return n + str(check)

def get_ufficio_iva(n):
    cod = n[7:10]
    uff = uffici.get(cod) or 'UFFICIO INESISTENTE'
    return uff
