# -*- coding: windows-1252 -*-
import cmd, sys, traceback
from shlex import split, join

from cf import get_codice_fiscale, get_omocodici, get_ctl_chr, crc_piva, get_ufficio_iva, get_dati_cf
from iban import iban_validate, iban_gen_IT, bban_check_gen_IT
from plug_banche import banche


class Shell(cmd.Cmd):
    intro = 'Digita help o ? per un elenco dei comandi.'
    prompt = '$ '

    def _join(*args): return os.path.join(*args).replace('\\','/')

    def __init__ (p):
        super(Shell, p).__init__()

    def do_quit(p, arg):
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
            print("Non � stato indicato un codice da verificare")
            return
        # Deduce il tipo di codice
        if len(arg) == 11 and arg.isdigit():
            print('Rilevato partita IVA/codice fiscale di ente')
            Shell.viva(arg)
        elif len(arg) == 16 and arg[:6].isalpha():
            print('Rilevato codice fiscale di persona fisica')
            Shell.vcf(arg.upper())
        elif 14 < len(arg) < 33 and arg[:2].isalpha() and arg[2:4].isdigit(): # IBAN (lungh. var.)
            print('Rilevato IBAN')
            Shell.viban(arg)
        else:
            print('Non sembra n� un IBAN n� un codice fiscale/partita IVA')

    def vcf(arg):
        "Verifica un codice fiscale italiano di persona fisica"
        arg = arg.upper()
        c = get_ctl_chr(arg[:15])
        if c == arg[15]:
            print('Codice fiscale formalmente valido')
            sesso, luogo, data = get_dati_cf(arg)
            gg,mm,aa = data
            aa += 1900
            print(f'Soggetto {sesso}, nato in {luogo[0]} ({luogo[1]}) il {gg}/{mm}/{aa}')
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
        "Genera un codice fiscale formalmente valido dalle generalit�"
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
        CF = arg
        if not CF:
            if not hasattr(p,'CF'):
                print("Nessun Codice Fiscale e' stato indicato o calcolato!")
                return
        CF = p.CF
        print("127 omocodici per il Codice Fiscale:", CF)
        print(get_omocodici(CF[:-1]))

    def help_quit(p):
        print("Esce")

    def help_cf(p):
        print("""Calcola il codice fiscale del soggetto indicato.

   Uso: cf cognome nome gg mm aaaa comune_o_stato_estero sesso

      cognome, nome   vanno indicati senza spazi, apostrofi o accenti intermedi
      gg, mm, aaaa    data di nascita
      luogo           comune o stato estero di nascita (' per apostrofo o accento)
      sesso           M=maschile, F=femminile""")

    def help_omo(p):
        print ("""Calcola gli omocodici per il Codice Fiscale indicato,
        o per l'ultimo codice calcolato con cf.

   Uso: omo [codice]""")

    def help_ctl(p):
        print ("""Calcola la lettera di controllo per il Codice Fiscale indicato.
   Uso: ctl codice""")

    def help_geniban(p):
        print ("""Genera un IBAN italiano a partire dai codici ABI, CAB e dal numero di conto corrente.
   Uso: geniban ABI CAB CCN""")

    def help_ver(p):
        print ("""Verifica la validit� formale di un codice fiscale, partita IVA o IBAN.
   Uso: ver codice""")

def perr():
    print(sys.exception())
    #~ print(traceback.format_exc())

Shell().cmdloop()
