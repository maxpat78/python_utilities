"Estrae un elenco di succursali degli intermediari finanziari attivi in Italia da un report XML della Banca d'Italia"
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
import json

tree = ET.parse('2025-03-17_SUCCURSALI_BANCHE.xml') # v. https://infostat.bancaditalia.it/GIAVAInquiry-public/ng/area-download
root = tree.getroot()

# {ABI: ('ISTITUTO', {'CAB': ('COMUNE', 'VIA')}) }
intermediari = {}
for r in root.findall('.//ROW'):
    # elimina gli intermediari chiusi o cessati. Attualmente ritorna 19029 filiali valide.
    if r.find('DATA_F_OPER').text != '9999-12-31': continue
    if r.find('DATA_F_VAL').text != '9999-12-31': continue
    abi = '%05d' % int(r.find('COD_MECC').text) # normalizza a 5 cifre
    nome = r.find('DEN_160').text
    intermediari[abi] = (nome, {})
for r in root.findall('.//ROW'):
    # elimina gli intermediari chiusi o cessati. Attualmente ritorna 19029 filiali valide.
    if r.find('DATA_F_OPER').text != '9999-12-31': continue
    if r.find('DATA_F_VAL').text != '9999-12-31': continue
    abi = '%05d' % int(r.find('COD_MECC').text) # normalizza a 5 cifre
    cab = '%05d' % int(r.find('CAB_SEDE').text)
    if cab == '00000': continue
    comune = r.find('DES_COM_ITA').text
    via = r.find('INDIRIZZO').text
    intermediari[abi][1][cab] = (comune, via)

json.dump(banche, open('banche.json','w'))
print('Elenco delle banche con sportelli in Italia generato in banche.json')
