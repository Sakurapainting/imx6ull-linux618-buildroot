#!/usr/bin/env python3
"""Inspect the generated newc archive without extracting device nodes."""
import gzip
import posixpath
import stat
import sys
from pathlib import Path

raw = Path(sys.argv[1]).read_bytes()
assert gzip.decompress(Path(sys.argv[2]).read_bytes()) == raw, 'gzip content mismatch'
entries = {}
owners = {}
offset = 0
while True:
    header = raw[offset:offset + 110]
    assert header[:6] == b'070701', 'expected newc archive'
    fields = [int(header[i:i + 8], 16) for i in range(6, 110, 8)]
    _, mode, uid, gid, _, _, size, _, _, rmajor, rminor, namesize, _ = fields
    start = offset + 110
    name = raw[start:start + namesize - 1].decode()
    start = (start + namesize + 3) & ~3
    data = raw[start:start + size]
    offset = (start + size + 3) & ~3
    if name == 'TRAILER!!!':
        break
    name = posixpath.normpath('/' + name)
    entries[name] = (mode, rmajor, rminor, data)
    owners[name] = (uid, gid)

def resolve(name):
    for _ in range(20):
        mode, major, minor, data = entries[name]
        if not stat.S_ISLNK(mode):
            return mode, major, minor, data
        name = posixpath.normpath(posixpath.join(posixpath.dirname(name), data.decode()))
    raise AssertionError('symlink loop')

for name in ('/init', '/bin/sh', '/sbin/init', '/sbin/getty', '/bin/mount', '/bin/ps', '/bin/uname'):
    mode, _, _, data = resolve(name)
    assert stat.S_ISREG(mode) and mode & 0o111 and data, f'missing executable: {name}'
    assert owners[name] == (0, 0), f'wrong startup file ownership: {name}'
user_ids = {int(line.split(':')[2]) for line in resolve('/etc/passwd')[3].decode().splitlines()}
group_ids = {int(line.split(':')[2]) for line in resolve('/etc/group')[3].decode().splitlines()}
for name, (uid, gid) in owners.items():
    assert uid in user_ids and gid in group_ids, f'undeclared archive owner: {name}: {uid}:{gid}'
init_script = resolve('/init')[3]
assert b'/bin/mount -t devtmpfs devtmpfs /dev' in init_script
assert b'exec /sbin/init' in init_script
mode, major, minor, _ = entries['/dev/console']
assert stat.S_ISCHR(mode) and (major, minor) == (5, 1), 'missing initial console device'
inittab = [line.split(b'#', 1)[0].split() for line in resolve('/etc/inittab')[3].splitlines()]
assert [b'ttymxc0::respawn:/sbin/getty', b'-L', b'ttymxc0', b'115200', b'vt100'] in inittab
assert resolve('/lib/ld-musl-armhf.so.1')[3][:4] == b'\x7fELF', 'missing dynamic loader'
assert resolve('/bin/busybox')[3][:4] == b'\x7fELF', 'missing BusyBox ELF'
for name in ('/proc', '/sys', '/dev', '/tmp', '/etc/init.d/rcS'):
    assert name in entries, f'missing startup path: {name}'
assert f'VERSION={sys.argv[3]}' in resolve('/usr/lib/os-release')[3].decode().splitlines()
print(f'rootfs: {len(entries)} entries; gzip matches; system ownership, init, console, getty, loader and shell verified')
