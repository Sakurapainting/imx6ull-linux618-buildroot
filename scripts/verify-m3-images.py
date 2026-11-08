#!/usr/bin/env python3
"""Verify storage DT wiring, the ordinary kernel, and diagnostic initramfs."""
import gzip
import struct
import sys
import zlib
from pathlib import Path

output = Path(sys.argv[1])
kernel = output / f'build/linux-{sys.argv[2]}'
images = output / 'images'
config = (kernel / '.config').read_text().splitlines()
for name in (
    'BLK_DEV_INITRD', 'RD_GZIP', 'KERNEL_GZIP', 'DEVTMPFS', 'DEVTMPFS_MOUNT',
    'SERIAL_IMX', 'SERIAL_IMX_CONSOLE', 'MMC', 'MMC_BLOCK', 'MMC_SDHCI',
    'MMC_SDHCI_PLTFM', 'MMC_SDHCI_ESDHC_IMX', 'MSDOS_PARTITION', 'EXT4_FS',
    'REGULATOR', 'REGULATOR_FIXED_VOLTAGE', 'GPIO_MXC', 'VFAT_FS',
    'CMDLINE_FROM_BOOTLOADER', 'AUTO_ZRELADDR',
):
    assert f'CONFIG_{name}=y' in config, f'{name} must be built in'
assert 'CONFIG_INITRAMFS_SOURCE=""' in config, 'kernel must not embed Buildroot rootfs'
assert 'CONFIG_CMDLINE="console=ttymxc0,115200"' in config
br_config = (output / '.config').read_text().splitlines()
assert '# BR2_TARGET_ROOTFS_INITRAMFS is not set' in br_config

blob = (images / 'imx6ull-alpha-m3.dtb').read_bytes()
magic, total, structure, strings, _, version, _, _, strings_size, structure_size = (
    struct.unpack_from('>10I', blob)
)
assert magic == 0xd00dfeed and total == len(blob) and version >= 17
string_table = blob[strings:strings + strings_size]
offset, stack, properties = structure, [], {}
while offset < structure + structure_size:
    token, = struct.unpack_from('>I', blob, offset)
    offset += 4
    if token == 1:
        end = blob.index(0, offset)
        stack.append(blob[offset:end].decode())
        offset = (end + 4) & ~3
    elif token == 2:
        stack.pop()
    elif token == 3:
        size, name_offset = struct.unpack_from('>2I', blob, offset)
        offset += 8
        end = string_table.index(0, name_offset)
        name = string_table[name_offset:end].decode()
        properties['/'.join(stack) or '/', name] = blob[offset:offset + size]
        offset = (offset + size + 3) & ~3
    elif token == 4:
        continue
    elif token == 9:
        break
    else:
        raise AssertionError(f'invalid FDT token {token}')

def text(path, name):
    return properties[path, name].rstrip(b'\0').decode()

def cells(path, name):
    data = properties[path, name]
    return struct.unpack(f'>{len(data) // 4}I', data)

def phandle_node(phandle):
    return next(path for (path, name), value in properties.items()
                if name == 'phandle' and value == struct.pack('>I', phandle))

assert text('/', 'model') == 'ALPHA ATK-DL6Y2C i.MX6ULL'
assert cells('/memory@80000000', 'reg') == (0x80000000, 0x20000000)
uart = text('/aliases', 'serial0')
assert uart.endswith('/serial@2020000') and text(uart, 'status') == 'okay'
assert text('/chosen', 'stdout-path') == uart
for number, address, width, pin_count in (
    (0, '2190000', 4, 7), (1, '2194000', 8, 10)
):
    path = text('/aliases', f'mmc{number}')
    assert path.endswith(f'/mmc@{address}'), f'wrong mmc{number} alias'
    assert text(path, 'status') == 'okay'
    assert cells(path, 'bus-width') == (width,)
    assert cells(path, 'max-frequency') == (50000000,)
    assert (path, 'no-1-8-v') in properties
    pins = phandle_node(cells(path, 'pinctrl-0')[0])
    assert len(cells(pins, 'fsl,pins')) == pin_count * 6
    if number == 0:
        gpio, pin, flags = cells(path, 'cd-gpios')
        assert phandle_node(gpio).endswith('/gpio@209c000')
        assert (pin, flags) == (19, 1), 'wrong active-low SD detect GPIO'
        regulator = phandle_node(cells(path, 'vmmc-supply')[0])
        assert cells(regulator, 'regulator-min-microvolt') == (3300000,)
        assert cells(regulator, 'regulator-max-microvolt') == (3300000,)
    else:
        assert (path, 'non-removable') in properties
for (path, name), value in properties.items():
    if name == 'status' and any(part in path for part in ('/ethernet@', '/usb@', '/lcdif@')):
        assert value == b'disabled\0', f'unexpected enabled peripheral: {path}'
print('DTB: 512 MiB, UART1, SD 4-bit/CD GPIO1_IO19, eMMC 8-bit, 50 MHz verified')

image = (kernel / 'arch/arm/boot/Image').read_bytes()
compressed = (kernel / 'arch/arm/boot/compressed/piggy_data').read_bytes()
zimage = (images / 'zImage').read_bytes()
assert f'Linux version {sys.argv[2]} '.encode() in image
assert gzip.decompress(compressed) == image
magic, start, end = struct.unpack_from('<3I', zimage, 0x24)
assert magic == 0x016f2818 and end - start == len(zimage)
assert compressed in zimage
cpio = (images / 'rootfs.cpio').read_bytes()
assert cpio not in image, 'full Buildroot cpio unexpectedly embedded'
ramdisk = (images / 'rootfs.cpio.uboot').read_bytes()
header, payload = bytearray(ramdisk[:64]), ramdisk[64:]
magic, header_crc, _, size, _, _, data_crc = struct.unpack_from('>7I', header)
assert magic == 0x27051956 and size == len(payload)
struct.pack_into('>I', header, 4, 0)
assert zlib.crc32(header) == header_crc and zlib.crc32(payload) == data_crc
assert tuple(header[28:32]) == (5, 2, 3, 0), 'expected Linux ARM ramdisk header'
assert payload == (images / 'rootfs.cpio.gz').read_bytes()
assert gzip.decompress(payload) == cpio
print(f'zImage: {len(zimage)} bytes, no embedded Buildroot cpio; '
      f'diagnostic ramdisk: {len(ramdisk)} bytes, U-Boot header/CRC/gzip verified')

symbols = {}
for line in (kernel / 'System.map').read_text().splitlines():
    address, _, name = line.split()
    if name in ('_text', '_end'):
        symbols[name] = int(address, 16)
ranges = [
    ('kernel', 0x80008000, 0x80008000 + symbols['_end'] - symbols['_text']),
    ('zImage', 0x84000000, 0x84000000 + len(zimage)),
    ('DTB', 0x88000000, 0x88000000 + len(blob)),
    ('ramdisk', 0x89000000, 0x89000000 + len(ramdisk)),
]
assert all(0x80000000 <= start < end < 0x9e000000 for _, start, end in ranges)
assert all(left[2] < right[1] for left, right in zip(ranges, ranges[1:]))
for name, start, end in ranges:
    print(f'RAM {name}: [0x{start:08x}, 0x{end:08x})')

ext4 = (images / 'rootfs.ext4').read_bytes()[1024:2048]
assert struct.unpack_from('<H', ext4, 56)[0] == 0xef53
assert ext4[120:136].rstrip(b'\0') == b'imx6ull-m3'
compat = struct.unpack_from('<I', ext4, 92)[0]
incompat = struct.unpack_from('<I', ext4, 96)[0]
assert compat & 4, 'ext4 journal missing'
assert not incompat & 0x80, '64bit ext4 is incompatible with the original U-Boot'
assert (images / 'rootfs.ext4').stat().st_size == 128 * 1024 * 1024
print('ext4: 128 MiB, label imx6ull-m3, journal enabled, 64bit feature disabled')
