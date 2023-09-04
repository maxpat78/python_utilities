# A simple ISO to CSO v1 compressor for the PPSSPP Playstation Portable emulator
import zlib, sys, struct
#from zopfli import ZopfliCompressor

def b2mb(n): return n / (1<<20)

if len(sys.argv) < 2:
    print('ERROR: a source ISO input image MUST be specified!')
    print('Use: CSOc.py <ISO file> [[CSO file] level]\n')
    print('Defaults: CSO goes to same path of input, with best compression.')
    sys.exit(1)

# Default unit compression size is 2K (like an ISO block)
# Incrementing up to the maximum of 32K slightly improves compression:
# this is supported by PPSSPP emulator
frame_size = 8<<10

if len(sys.argv) > 3:
    level = int(sys.argv[3])
else:
    level = 9

iso = open(sys.argv[1], 'rb')
iso.seek(0, 2)
iso_size = iso.tell()
iso.seek(0)

if len(sys.argv) > 2:
    outname = sys.argv[2]
else:
    outname = sys.argv[1][:-3] + 'cso'

print('Compressing a %.02f MB ISO (with a %d bytes frame) to "%s"' % (b2mb(iso_size),frame_size,outname))

out = open(outname, 'w+b')
out.seek(0)

out.write(b'CISO') # magic tag
out.write(struct.pack('<l',24)) # header size (ignored by decompressor)
out.write(struct.pack('<q',iso_size)) # ISO size
out.write(struct.pack('<l',frame_size)) # sector size (min 2048 bytes, max 32768)
out.write(struct.pack('<l',1)) # compression type (only 1=ZIP is supported!)

out.seek(24 + 4*(1+iso_size//frame_size)-1) # offset of first compressed block
out.write(b'\x00')

buf = 1
CHUNK_SIZE = 64
i = 0
beg = 0
while buf:
    buf = iso.read(frame_size*CHUNK_SIZE)
    if not buf: break
    chunks = b''
    sizes=[]
    for chunk in range(len(buf)//frame_size):
        sub = buf[chunk*frame_size : chunk*frame_size+frame_size]
        cobj = zlib.compressobj(level, zlib.DEFLATED, -15)
        z = cobj.compress(sub) + cobj.flush(zlib.Z_FINISH)
        # cobj = ZopfliCompressor(iterations=3)
        # z = cobj.compress(sub) + cobj.flush()
        if len(z) < frame_size:
            chunks += z
            sizes += [len(z)]
        else:
            chunks += sub
            sizes += [frame_size]
    out.seek(0,2)
    beg = out.tell()
    out.write(chunks) # writes out sectors array
    out.seek(24+i*4)
    for size in sizes:
        n=beg
        if size == frame_size:
            n = beg|0x80000000 # uncompressed flag
        out.write(struct.pack('<L',n)) # stores sector offset
        beg += size
    i += len(sizes)
    sys.stdout.write('Written sector %d\r'%i)

out.write(struct.pack('<L',beg)) # stores next sector offset (virtual)
out.seek(0,2)
size = out.tell()
out.close()
gain = 100.0 - size/float(iso_size)*100

print('\nOK. Size reduced by %.02f%% to %.02f MB.' % (gain, b2mb(size)))
