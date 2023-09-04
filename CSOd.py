# A simple CSO to ISO decompressor for the PPSSPP Playstation Portable emulator
import zlib, sys, struct

if len(sys.argv) < 2:
    print('ERROR: a compressed CSO input image MUST be specified!')
    sys.exit(1)

cso = open(sys.argv[1], 'rb')

if b'CISO' != cso.read(4):
    print('ERROR: not a CSO compressed ISO image!')
    sys.exit(1)

cso.read(4) # header size (ignored)

iso_size = struct.unpack('<Q', cso.read(8))[0] # uncompressed ISO size
frame_size = struct.unpack('<L', cso.read(4))[0] # sector size (0x0800 = 2048)
compressor = struct.unpack('<L', cso.read(4))[0] # compression (0=none,1=zip,2=bzip2,3=lzma)

if compressor != 1:
    print('ERROR: only ZIP compression is supported, unknown method %d!'%compressor)
    sys.exit(1)
if frame_size<2048 or frame_size>32768:
    print('ERROR: only ZIP compression is supported, bad frame size %d!'%frame_size)
    sys.exit(1)

if len(sys.argv) > 2:
    outname = sys.argv[2]
else:
    outname = sys.argv[1][:-3] + 'iso'

print('Decompressing CSO image (with a %d bytes frame) to "%s"' % (frame_size,outname))

out = open(outname, 'wb')
i = 0
for block in range(iso_size//frame_size):
    cso.seek(24 + block*4)
    DW1 = struct.unpack('<L', cso.read(4))[0] # offset of compressed block
    DW2 = struct.unpack('<L', cso.read(4))[0] # offset of next compressed block
    begin = DW1 & 0x7FFFFFFF
    end = DW2 & 0x7FFFFFFF
    cso.seek(begin)
    z = cso.read(end-begin) # current block
    if not (DW1 & 0x80000000):
        try:
            s = zlib.decompress(z, -15)
            out.write(s)
        except:
            print('\nBad compressed block %d detected!' % i)
    else: # was stored uncompressed
        out.write(z)
    sys.stdout.write('Written block %d\r'%i)
    i+=1
    if out.tell() >= iso_size: break

out.close()
size = cso.tell()
gain = float(iso_size)/size*100

print('\nOK. Size expanded by %.02f%% from %d to %d bytes.' % (gain, size, iso_size))
