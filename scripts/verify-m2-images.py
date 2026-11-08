#!/usr/bin/env python3
"""Check the board DTB and trace the cpio into the final ARM zImage."""
import gzip
import struct
import sys
from pathlib import Path

output = Path(sys.argv[1])
kernel = output / f'build/linux-{sys.argv[2]}'
images = output / 'images'
blob = (images / 'imx6ull-alpha.dtb').read_bytes()
magic, total, structure, strings, _, version, _, _, strings_size, structure_size = (
    struct.unpack_from('>10I', blob)
)
assert magic == 0xd00dfeed and total == len(blob) and version >= 17, 'invalid FDT header'
string_table = blob[strings:strings + strings_size]
offset = structure
stack = []
properties = {}
while offset < structure + structure_size:
    token, = struct.unpack_from('>I', blob, offset)
    offset += 4
    if token == 1:  # FDT_BEGIN_NODE
        end = blob.index(0, offset)
        stack.append(blob[offset:end].decode())
        offset = (end + 4) & ~3
    elif token == 2:  # FDT_END_NODE
        stack.pop()
    elif token == 3:  # FDT_PROP
        size, name_offset = struct.unpack_from('>2I', blob, offset)
        offset += 8
        end = string_table.index(0, name_offset)
        name = string_table[name_offset:end].decode()
        path = '/'.join(stack) or '/'
        properties[path, name] = blob[offset:offset + size]
        offset = (offset + size + 3) & ~3
    elif token == 4:  # FDT_NOP
        continue
    elif token == 9:  # FDT_END
        break
    else:
        raise AssertionError(f'unknown FDT token: {token}')

def text_property(path, name):
    return properties[path, name].rstrip(b'\0').decode()

assert text_property('/', 'model') == 'ALPHA ATK-DL6Y2C i.MX6ULL'
assert properties['/', 'compatible'].split(b'\0')[:-1] == [
    b'alientek,atk-dl6y2c', b'fsl,imx6ull'
]
assert struct.unpack('>2I', properties['/memory@80000000', 'reg']) == (
    0x80000000, 0x20000000
), 'wrong DDR range'
uart = text_property('/aliases', 'serial0')
assert uart.endswith('/serial@2020000'), 'serial0 must be UART1'
assert text_property('/chosen', 'stdout-path') == uart, 'wrong stdout-path'
assert text_property(uart, 'status') == 'okay', 'UART1 is disabled'
assert (uart, 'pinctrl-0') in properties, 'UART1 has no pin configuration'
for (path, name), value in properties.items():
    if name == 'status' and any(part in path for part in (
        '/mmc@', '/ethernet@', '/lcdif@', '/usb@'
    )):
        assert value == b'disabled\0', f'peripheral unexpectedly enabled: {path}'
assert not any(path.startswith('/reserved-memory') for path, _ in properties), (
    'unexpected board reserved-memory'
)
print(f'dtb: 512 MiB DDR; UART1 {uart}; stdout and pinctrl verified')

cpio = (images / 'rootfs.cpio').read_bytes()
embedded = (kernel / 'usr/initramfs_inc_data').read_bytes()
assert gzip.decompress(embedded) == cpio, 'kernel embeds a different cpio'
image = (kernel / 'arch/arm/boot/Image').read_bytes()
assert embedded in image, 'initramfs not found in the uncompressed kernel'
assert f'Linux version {sys.argv[2]} '.encode() in image, 'unexpected kernel version'
compressed = (kernel / 'arch/arm/boot/compressed/piggy_data').read_bytes()
assert gzip.decompress(compressed) == image, 'compressed kernel differs from Image'
zimage = (images / 'zImage').read_bytes()
magic, start, end = struct.unpack_from('<3I', zimage, 0x24)
assert magic == 0x016f2818 and end - start == len(zimage), 'invalid ARM zImage header'
assert compressed in zimage, 'zImage does not contain the verified kernel'
print(f'zImage: {len(zimage)} bytes; Image: {len(image)} bytes; '
      f'built-in cpio: {len(cpio)} bytes; full image chain verified')

symbols = {}
for line in (kernel / 'System.map').read_text().splitlines():
    address, _, name = line.split()
    if name in ('_text', '_end'):
        symbols[name] = int(address, 16)
kernel_start = 0x80008000
kernel_end = kernel_start + symbols['_end'] - symbols['_text']
zimage_start = 0x84000000
zimage_end = zimage_start + len(zimage)
dtb_start = 0x88000000
dtb_end = dtb_start + len(blob)
assert kernel_end < zimage_start < zimage_end < dtb_start < dtb_end < 0x9e000000, (
    'M2 RAM layout overlaps kernel, zImage, DTB, or U-Boot area'
)
print(f'RAM: kernel [0x{kernel_start:08x}, 0x{kernel_end:08x}); '
      f'zImage [0x{zimage_start:08x}, 0x{zimage_end:08x}); '
      f'DTB [0x{dtb_start:08x}, 0x{dtb_end:08x}); no overlap')
