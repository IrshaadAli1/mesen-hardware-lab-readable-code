# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Random Týpek, for project contributions.
# Mesen-derived material is attributed in THIRD_PARTY_NOTICES.md.
"""Win32 memory backend and reversible byte-patch engine for the hardware lab."""
import ctypes as C
from ctypes import wintypes as W
import os
import random
import struct
import sys

from hardware_lab import Patch
from typings_and_alias import Patches, OriginalPatches, PatchChanges, RestoreCount, ProcessID, ProcessHandle


def code_sections(read, base):
    """Return only executable PE sections, bounded by SizeOfImage."""
    dos = read(base, 64)
    if dos[:2] != b'MZ':
        raise ValueError('Module has no DOS header')

    offset = struct.unpack_from('<I', dos, 60)[0]
    if not 64 <= offset <= 1024 * 1024:
        raise ValueError('Invalid PE offset')

    nt = read(base + offset, 24)
    if nt[:4] != b'PE\0\0':
        raise ValueError('Invalid PE signature')

    count = struct.unpack_from('<H', nt, 6)[0]
    optional_size = struct.unpack_from('<H', nt, 20)[0]
    if not 1 <= count <= 96 or not 64 <= optional_size <= 4096:
        raise ValueError('Invalid section table')

    optional = read(base + offset + 24, optional_size)
    if struct.unpack_from('<H', optional)[0] not in (0x10b, 0x20b):
        raise ValueError('Unsupported PE format')

    image_size = struct.unpack_from('<I', optional, 56)[0]
    table = read(base + offset + 24 + optional_size, count * 40)
    sections = []
    for i in range(count):
        entry = table[i*40:(i+1)*40]
        size, rva = struct.unpack_from('<II', entry, 8)
        flags = struct.unpack_from('<I', entry, 36)[0]
        if flags & 0x20000000 and size and rva < image_size:
            sections.append((base + rva, min(size, image_size-rva)))

    if not sections:
        raise ValueError('No executable sections in this module')
    return sections


# I'm not even going to BOTHER touching this.. you got it bro you got it - Irshaad
# Ok i lied im sorry - Irshaad later
# Moved Windows to Windows.py
class Windows:
    def __init__(self):
        if os.name != 'nt' or C.sizeof(C.c_void_p) != 8:
            raise RuntimeError('Use 64-bit Python on Windows.')

        self.k = C.WinDLL('kernel32', use_last_error=True)
        self.p = C.WinDLL('psapi', use_last_error=True)

        P, S, D, H = C.c_void_p, C.c_size_t, W.DWORD, W.HANDLE

        signatures = {
            'OpenProcess': ([D, W.BOOL, D], H),
            'CloseHandle': ([H], W.BOOL),
            'QueryFullProcessImageNameW': ([H, D, W.LPWSTR, C.POINTER(D)], W.BOOL),
            'ReadProcessMemory': ([H, P, P, S, C.POINTER(S)], W.BOOL),
            'WriteProcessMemory': ([H, P, P, S, C.POINTER(S)], W.BOOL),
            'VirtualProtectEx': ([H, P, S, D, C.POINTER(D)], W.BOOL),
            'FlushInstructionCache': ([H, P, S], W.BOOL),
            'WaitForSingleObject': ([H, D], D),
        }

        for name, (args, result) in signatures.items():
            fn = getattr(self.k, name)
            fn.argtypes, fn.restype = args, result

        self.p.EnumProcessModulesEx.argtypes = [H, C.POINTER(P), D, C.POINTER(D), D]
        self.p.EnumProcessModulesEx.restype  = W.BOOL
        self.p.GetModuleFileNameExW.argtypes = [H, P, W.LPWSTR, D]
        self.p.GetModuleFileNameExW.restype  = D

    @staticmethod
    def check(ok: int) -> None:  # I think this thing just checks whether the value returned is 0
        if not ok:
            raise C.WinError(C.get_last_error())


ALLOWED: set[str] = {
    'mesen.exe',
    'mesen2.exe',
    'mesence.exe',
    'mesen-s.exe'
}

MODULES: set[str] = (
    ALLOWED | {
    'mesencore.dll',
    'meseninterop.dll'
})


class Target:
    def __init__(self, api: Windows, pid: ProcessID):
        self.api   : Windows        = api
        self.handle: ProcessHandle  = api.k.OpenProcess(0x100000 | 0x0400 | 0x0038, False, pid)
        api.check(self.handle)

        try:
            path, n = C.create_unicode_buffer(32768), W.DWORD(32768)
            api.check(api.k.QueryFullProcessImageNameW(self.handle, 0, path, C.byref(n)))

            if os.path.basename(path.value).lower() not in ALLOWED:
                raise ValueError('Selected process is not a supported Mesen executable')

        except Exception:
            self.close()
            raise

    def close(self):
        if self.handle:
            self.api.k.CloseHandle(self.handle)
            self.handle = None

    def alive(self) -> bool:
        return self.handle and self.api.k.WaitForSingleObject(self.handle, 0) == 258

    def read(self, address, size) -> bytes:
        buf, done = C.create_string_buffer(size), C.c_size_t()
        self.api.check(self.api.k.ReadProcessMemory(self.handle, address, buf, size, C.byref(done)))

        if done.value != size:
            raise OSError('Incomplete memory read')

        return buf.raw

    def write(self, address, data):
        # All callers write exactly one byte, never crossing a protection boundary.
        if len(data) != 1:
            raise ValueError('Only single-byte writes are supported')

        old, dummy, done = W.DWORD(), W.DWORD(), C.c_size_t()
        k, h = self.api.k, self.handle
        self.api.check(k.VirtualProtectEx(h, address, 1, 0x40, C.byref(old)))

        try:
            buf = C.create_string_buffer(data)
            self.api.check(k.WriteProcessMemory(h, address, buf, 1, C.byref(done)))

            if done.value != 1:
                raise OSError('Incomplete memory write')

            self.api.check(k.FlushInstructionCache(h, address, 1))
        finally:
            self.api.check(k.VirtualProtectEx(h, address, 1, old.value, C.byref(dummy)))

    def modules(self):
        count = 256
        while True:
            array, needed = (C.c_void_p * count)(), W.DWORD()
            self.api.check(self.api.p.EnumProcessModulesEx(self.handle, array, C.sizeof(array), C.byref(needed), 3))

            if needed.value <= C.sizeof(array):
                break

            count = needed.value // C.sizeof(C.c_void_p) + 16


        result = []
        for base in array[:needed.value // C.sizeof(C.c_void_p)]:
            path = C.create_unicode_buffer(32768)

            if self.api.p.GetModuleFileNameExW(self.handle, base, path, len(path)):
                name = os.path.basename(path.value)
                if name.lower() in MODULES:
                    result.append((name, base))

        return sorted(result, key=lambda m: (m[0].lower() != 'mesencore.dll', m[0]))


class Engine:
    def __init__(self, target: Target):
        self.target  : Target           = target
        self.original: OriginalPatches  = {}
        self.rng     : random.Random    = random.Random()
        self.cache                      = {}  # I can't find a usage for it what is this var for - Irshaad

    def blast(self, candidates: Patches, count=1, active_limit=1, profile='Conservative') -> PatchChanges:
        if not 1 <= count <= active_limit <= 24:
            raise ValueError('Require 1 <= patches per blast <= active limit <= 24')

        if profile == 'Conservative' and (count != 1 or active_limit != 1):
            raise ValueError('Conservative mode allows exactly one active patch')

        if not candidates:
            raise ValueError('No eligible SIMD instructions. No corruption applied.')

        changes: PatchChanges = []
        try:
            for _ in range(min(count, len(candidates))):
                while len(self.original) >= active_limit:
                    self.restore(next(iter(self.original)))

                available: Patches = [c for c in candidates if c.patch_address not in self.original]
                if not available:
                    self.restore(next(iter(self.original)))
                    available = [c for c in candidates if c.patch_address not in self.original]

                item: Patch = self.rng.choice(available)
                before: bytes = self.target.read(item.address, len(item.code))
                if before != item.code:
                    raise ValueError('Instruction changed since scan; restart Mesen and reattach')

                changed = bytearray(before)
                if item.values:
                    changed[item.offset] = self.rng.choice(item.values)
                elif profile == 'Conservative':
                    changed[item.offset] ^= 1 << self.rng.randrange(item.bits)
                else:
                    mask                 = (1 << item.bits)-1
                    old                  = before[item.offset] & mask
                    new                  = self.rng.choice([v for v in range(mask+1) if v != old])
                    changed[item.offset] = (before[item.offset] & ~mask) | new

                expected = bytes(changed)
                self.original[item.patch_address] = (item, expected)
                self.target.write(item.patch_address, expected[item.offset:item.offset+1])

                if self.target.read(item.address, len(expected)) != expected:
                    raise OSError('Patch verification failed')

                changes.append((item.patch_address,before[item.offset],expected[item.offset],item.label))
        except Exception:
            try:
                self.undo()
            except Exception:
                pass  # Recovery records remain when restoration fails.
            raise

        return changes

    def restore(self, address: int) -> None:
        item, expected = self.original[address]
        current = self.target.read(item.address, len(item.code))
        if current not in (item.code, expected):
            raise ValueError('Code changed externally; refusing to overwrite it. Restart Mesen.')

        self.target.write(address, item.code[item.offset : item.offset+1])
        if self.target.read(item.address, len(item.code)) != item.code:
            raise OSError('Restore verification failed')  # wuh oh

        del self.original[address]

    def undo(self) -> RestoreCount:
        restored: RestoreCount = 0
        for address in list(self.original):
            self.restore(address)
            restored += 1

        return restored

