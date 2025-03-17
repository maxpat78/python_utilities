"Crea una tabella di codici ufficio IVA riportati da Wikipedia (alcuni mancano dall'Agenzia delle Entrate)"
from openpyxl import load_workbook

print ('Carico i codici ufficio IVA...')
wb = load_workbook('uffici_IVA_wikipedia.xlsx')
ws = wb[wb.sheetnames[0]]

rows = ws.rows
next(rows)

uffici = {}
for row in rows:
    try:
        cod = '%03d' % int(row[0].value)
        uffici[cod] = row[1].value.upper()
    except:
        pass

f = open('plug_iva.py', 'w')
f.write('# -*- coding: windows-1252 -*-\nuffici = ')
f.write(str(uffici))
f.close()
print('Elenco degli uffici IVA generato in plug_iva.py')
