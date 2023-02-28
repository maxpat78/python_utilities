# -*- coding: windows-1252 -*-
from ctypes import *
from datetime import *
import struct, getopt, sys, glob, os


class SYSTEMTIME(Structure):
    _fields_ = [("wYear", c_short), ("wMonth", c_short), ("wDayOfWeek", c_short), ("wDay", c_short), ("wHour", c_short), ("wMinute", c_short), ("wSecond", c_short), ("wMillisecond", c_short) ]

class FILETIME(Structure):
	_fields_ = [("dwLowDateTime", c_uint), ("dwHighDateTime", c_uint)]

def dt2FILETIME(dt, UTC=1):
	"Converte un oggetto Python datetime in una struttura FILETIME di Win32"
	delta = datetime.utcnow() - datetime.now()
	if UTC: dt += delta
	st, ft = SYSTEMTIME(), FILETIME()
	st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond = dt.timetuple()[:6]
	windll.kernel32.SystemTimeToFileTime(byref(st), byref(ft))
	return ft

def arg2dt(arg):
	"Crea un oggetto datetime da un timestamp Unix o da vari formati stringa"
	parsed=None
	try:
		parsed = datetime.utcfromtimestamp(int(arg))
	except:
		pass
	if not parsed:
		for fmt in ('%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y%m%dT%H%M%S', ):
			try:
				parsed = datetime.strptime(arg, fmt)
			except:
				continue
	return parsed



def touch(name, ctime, atime, wtime):
	"Imposta date e ora di creazione, accesso e modifica di un file"
	hFile = windll.kernel32.CreateFileA(bytes(name,'ascii'), 0x0100, 0, c_void_p(0), 3, 0x02000000, c_void_p(0))
	if hFile == -1:
		return hFile
	if not windll.kernel32.SetFileTime(hFile, byref(ctime), byref(atime), byref(wtime)):
		return -2
	windll.kernel32.CloseHandle(hFile)
	return 0


def stat_save(objname, txtfile):
	"Salva in un file di testo i timestamp Unix con date e ore di tutti i file in un ramo di directory"
	# ATTENZIONE: os.stat ritorna il localtime, non UTC che serve a dt2FILETIME!
	out = open(txtfile,'w')
	print("; ctime mtime atime pathname", file=out)
	for root, dirs, files in os.walk(objname):
		for f in files:
			pn = os.path.join(root, f)
			print("%d %d %d %s" % (os.stat(pn).st_ctime, os.stat(pn).st_mtime, os.stat(pn).st_atime, pn), file=out)
	out.close()


def stat_restore(txtfile):
	"Ripristina date e ore salvate con stat_save"
	for line in open(txtfile):
		if line[0] == ';': continue
		x = line.split()
		# grazie ad arg2dt, il file può essere editato a mano usando il formato ISO AAAAMMGGTOOMMSS
		ctime, atime, wtime = arg2dt(x[0]), arg2dt(x[2]), arg2dt(x[1])
		ctime, atime, wtime = map(lambda x:dt2FILETIME(x,0), [ctime, atime, wtime])
		touch(' '.join(x[3:]), ctime, atime, wtime)



if __name__ == '__main__':
	ATime = CTime = WTime = datetime.now()

	opts, args = getopt.getopt(sys.argv[1:], "a:c:w:h", ["all="])
	if opts and opts[0][0] == '-h':
			print ('Usa: wintouch.py [-a | -c | -w "DD/MM/YYYY HH:MM" | UNIX_TIMESTAMP]')
			print ("\nImposta data e ora di accesso, creazione, modifica dei file al valore indicato o a quello corrente.")
			sys.exit(1)
	if not args:
		print("Occorre specificare uno o più file o cartelle dei quali modificare data e ora!")
		sys.exit(1)
	for o, a in opts:
		if o == '-a':
			ATime = arg2dt(a)
		if o == '-c':
			CTime = arg2dt(a)
		if o == '-w':
			WTime = arg2dt(a)
		if o == '--all':
			ATime = CTime = WTime = arg2dt(a)
	ATime, CTime, WTime = map(lambda x:dt2FILETIME(x), [ATime, CTime, WTime])
	for g in args:
		for f in glob.glob(g):
			ret = touch(f, CTime, ATime, WTime)
			if ret == -1:
				print ("Attenzione: non è stato possibile accedere a '%s'" % f)
				continue
			if ret == -2:
				print ("Attenzione: non è stato possibile modificare gli attributi di '%s'" % f)
				continue
			else:
				print ("Aggiornate data e ora per '%s'" % f)
