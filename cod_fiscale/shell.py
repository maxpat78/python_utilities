# -*- coding: windows-1252 -*-
import cmd, sys, traceback, json
from shlex import split, join
from datetime import date

from cf import get_codice_fiscale, get_omocodici, get_ctl_chr, crc_piva, get_ufficio_iva, get_dati_cf
from iban import iban_validate, iban_gen_IT, bban_check_gen_IT

banche = json.load(open('banche.json'))


class Shell(cmd.Cmd):
    intro = 'Digita help o ? per un elenco dei comandi.'
    prompt = '$ '

    def _join(*args): return os.path.join(*args).replace('\\','/')

    def __init__ (p):
        super(Shell, p).__init__()

    def do_exit(p, arg):
        "Esce"
        sys.exit(0)

    def do_geniban(p, arg):
        "Genera un IBAN italiano"
        abi, cab, n = arg.split()
        try:
            iban = iban_gen_IT(int(abi), int(cab), n)
        except:
            perr()
            return
        print(iban)

    def do_ver(p, arg):
        "Verifica IBAN, codice fiscale o partita IVA, deducendo il tipo di argomento"
        if not arg:
            print("Non è stato indicato un codice da verificare")
            return
        arg = arg.replace(' ', '').upper() # elimina eventuali spazi
        # Deduce il tipo di codice
        if len(arg) == 11 and arg.isdigit():
            print(f'Rilevato partita IVA/codice fiscale di ente {arg}')
            Shell.viva(arg)
        elif len(arg) == 16 and arg[:6].isalpha():
            print(f'Rilevato codice fiscale di persona fisica {arg}')
            Shell.vcf(arg.upper())
        elif 14 < len(arg) < 33 and arg[:2].isalpha() and arg[2:4].isdigit(): # IBAN (lungh. var.)
            print(f'Rilevato IBAN {arg}')
            Shell.viban(arg)
        else:
            print('Non sembra né un IBAN né un codice fiscale/partita IVA')

    def vcf(arg):
        "Verifica un codice fiscale italiano di persona fisica"
        arg = arg.upper()
        c = get_ctl_chr(arg[:15])
        if c == arg[15]:
            print('Codice fiscale formalmente valido')
            sesso, luogo, data = get_dati_cf(arg)
            gg,mm,aa = data
            aa += 1900
            print(f'Soggetto {sesso}, nato in {luogo[0]} ({luogo[1]}) il {gg:02d}/{mm:02d}/{aa}')
            if aa+100 <= date.today().year:
                print(f"Nota: l'anno potrebbe essere anche {aa+100}")
        else:
            print('Codice fiscale NON valido')
        
    def viva(arg):
        "Verifica una partita IVA italiana"
        crc = crc_piva(arg[:-1])
        if crc != arg:
            print(f'Codice invalido, la cifra di controllo dovrebbe essere {crc[-1]}')
        else:
            print('Codice formalmente valido')
            try:
                prov = get_ufficio_iva(arg)
                print(f'Matricola {arg[:7]}, ufficio {arg[7:10]} ({prov})')
            except:
                perr()

    def viban(arg):
        "Verifica un codice IBAN, dando ulteriori informazioni sulla filiale italiana"
        arg = arg.upper()
        arg = arg.split()
        if len(arg) == 1:
            arg = arg[0]
        else:
            arg = ''.join(arg)
        try:
            if iban_validate(arg):
                quartetti = [arg[i:i+4] for i in range(0, len(arg), 4)]
                print(f'IBAN {arg} ({' '.join(quartetti)}) formalmente valido')
                if arg.startswith('IT'):
                    c = bban_check_gen_IT(arg[5:])
                    if c == arg[4] and arg[5:10].isdigit() and arg[10:15].isdigit() :
                        print('BBAN italiano formalmente valido')
                        abi = arg[5:10]
                        banca = banche.get(abi)
                        if banca:
                            print(f'ABI {abi} designa {banca[0]}')
                            cab = arg[10:15]
                            filiale = banca[1].get(cab)
                            if filiale:
                                print(f'Filiale {cab} in {filiale[1]}, comune di {filiale[0]}')
                            else:
                                print(f'Nessuna filiale con CAB {cab}')
                        else:
                            print(f'Nessun intemerdiario con ABI {abi}')
                    else:
                        print('BBAN italiano NON valido')
            else:
                print('IBAN NON valido')
        except:
            perr()

    def do_ctl(p, arg):
        "Genera il codice di controllo dai 15 caratteri di un codice fiscale"
        c = get_ctl_chr(arg)
        p.CF = (arg+c).upper()
        print(p.CF)

    def do_cf(p, arg):
        "Genera un codice fiscale formalmente valido dalle generalità"
        L = split(arg)
        try:
            cognome,nome,gg,mm,aa,luogo,sesso = L
            gg,mm,aa = int(gg),int(mm),int(aa)
            p.CF = get_codice_fiscale(nome, cognome, sesso, (gg,mm,aa), luogo)
        except:
            perr()
            return
        print (p.CF)

    def do_omo(p, arg):
        "Genera i 127 omocodici corrispondenti a un codice fiscale base"
        if arg:
           p.CF = arg 
        elif not hasattr(p,'CF'):
            print("Nessun codice fiscale è stato indicato o calcolato!")
            return
        print("127 omocodici per il codice fiscale:", p.CF)
        L = get_omocodici(p.CF[:-1])
        for i, s in enumerate(L):
            print(s.ljust(17), end="\n" if (i + 1) % 4 == 0 else "")
        print()

    def help_exit(p):
        print("Esce.")

    def help_cf(p):
        print("""Calcola il possibile codice fiscale di una persona fisica.

  Uso: cf cognome nome gg mm aaaa comune_o_stato_estero sesso

     cognome, nome   senza spazi, apostrofi o accenti intermedi
     gg, mm, aaaa    data di nascita
     luogo           comune o stato estero di nascita (' per apostrofo o
                     accento)
     sesso           M=maschile, F=femminile

Vedere il comando omo per altri possibili codici in caso di omocodia
(conflitto di codici fiscali).""")

    def help_omo(p):
        print ("""Calcola gli omocodici per un codice fiscale di persona fisica
o per l'ultimo codice calcolato con cf.

  Uso: omo [codice]
   
Sono possibili 127 omocodici sostituendo una o più delle 7 cifre con le
corrispondenti lettere""")

    def help_ctl(p):
        print ("""Calcola la lettera di controllo per un codice fiscale di
persona fisica.

  Uso: ctl codice""")

    def help_geniban(p):
        print ("""Genera un IBAN italiano a partire dai codici ABI, CAB e dal numero di conto corrente.
  Uso: geniban ABI CAB CCN""")

    def help_ver(p):
        print ("""Verifica la validità formale di un codice fiscale, partita IVA o IBAN.
  Uso: ver codice""")

def perr():
    print(sys.exception())
    #~ print(traceback.format_exc())

Shell().cmdloop()
