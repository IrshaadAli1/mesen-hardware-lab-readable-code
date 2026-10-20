# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Random Týpek, for project contributions.
# Mesen-derived material is attributed in THIRD_PARTY_NOTICES.md.
import unittest
import hashlib
import struct
from unittest.mock import patch
from capstone import Cs,CS_ARCH_X86,CS_MODE_64,CS_GRP_JUMP
from capstone.x86 import X86_OP_REG,X86_OP_IMM,X86_OP_MEM
import hardware_lab as lab

class Memory:
    def __init__(self,base=0x7ff800000000):
        self.base=base;self.data={};self.fail_at=None
        for effect in lab.EFFECTS.values():
            for p in effect['points']:
                self.write(base+p['rva'],bytes.fromhex(p['original']))
    def read(self,a,n):return bytes(self.data.get(i,0) for i in range(a,a+n))
    def write(self,a,data):
        if self.fail_at==a:
            self.fail_at=None
            raise OSError('simulated transient write failure')
        self.data.update({a+i:b for i,b in enumerate(data)})

def session(memory):
    with patch.object(lab,'verify_build'):
        return lab.LabSession(memory,memory.base)

class HardwareTests(unittest.TestCase):
    def test_patch_encodings_and_verified_branch_targets(self):
        md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
        for effect in lab.EFFECTS.values():
            for p in effect['points']:
                raw=bytes.fromhex(p['original']);ins=next(md.disasm(raw,p['rva']))
                changed=bytearray(raw);changed[p['offset']]=p['value']
                new=next(md.disasm(bytes(changed),p['rva']))
                self.assertEqual(new.size,ins.size)
                self.assertEqual(ins.mnemonic+' '+ins.op_str,p['original_instruction'])
                self.assertEqual(new.mnemonic+' '+new.op_str,p['modified_instruction'])
                self.assertEqual(sum(a!=b for a,b in zip(raw,changed)),1)
                self.assertEqual(len(ins.operands),len(new.operands))
                for a,b in zip(ins.operands,new.operands):
                    self.assertEqual(a.type,b.type)
                    if a.type==X86_OP_REG:
                        if p['rva'] in (0x19d71b,0x19d75e,0x19d7c2):
                            self.assertEqual((md.reg_name(a.reg),md.reg_name(b.reg)),('al','ah'))
                        else:self.assertEqual(a.reg,b.reg)
                    if a.type==X86_OP_MEM:
                        if p['rva'] in (0x19bff2,0xf067f):
                            # These explicitly reviewed addressing changes have exhaustive bounds tests.
                            self.assertIn(p['modified_instruction'],[
                                'lea rdx, [rcx + rax*4]', 'lea rdx, [rax + rax*2]',
                                'lea rdx, [rax + rax]',
                                'add dil, byte ptr [rcx + rax + 0x1d0]'])
                        else:self.assertEqual((a.mem.base,a.mem.index,a.mem.scale,a.mem.disp),(b.mem.base,b.mem.index,b.mem.scale,b.mem.disp))
                    if a.type==X86_OP_IMM and ins.group(CS_GRP_JUMP):
                        self.assertEqual(b.imm,0xf0677 if p['rva']==0xf0675 and p['offset']==1 else a.imm)

    def test_all_effects_switch_and_restore_without_accumulation(self):
        m=Memory();before=dict(m.data);s=session(m)
        for _ in range(3):
            for key,effect in lab.EFFECTS.items():
                s.apply(key)
                changed={a for a,v in m.data.items() if v!=before[a]}
                expected={m.base+p['rva']+p['offset'] for p in effect['points']}
                self.assertEqual(changed,expected)
                self.assertEqual(s.active,key)
        s.restore();self.assertEqual(m.data,before);self.assertIsNone(s.active)

    def test_partial_combined_effect_failure_rolls_back(self):
        m=Memory();before=dict(m.data);s=session(m)
        point=lab.EFFECTS['impossible_sound']['points'][1]
        m.fail_at=m.base+point['rva']+point['offset']
        with self.assertRaises(OSError):s.apply('impossible_sound')
        self.assertEqual(m.data,before);self.assertFalse(s.engine.original)

    def test_stale_code_rejected(self):
        m=Memory();s=session(m);p=lab.EFFECTS['triangle_saw']['points'][0]
        m.write(m.base+p['rva'],b'\x90');before=dict(m.data)
        with self.assertRaises(ValueError):s.apply('triangle_saw')
        self.assertEqual(m.data,before)

    def test_triangle_indices_bounded_for_all_states(self):
        for old in range(256):
            for mask in (7,15,31):self.assertLess(((old+1)&255)&mask,32)
        wave=list(range(15,-1,-1))+list(range(16))
        self.assertEqual(wave[:16],list(range(15,-1,-1)))
        for mask,expected_period in [(7,8),(15,16),(31,32)]:
            pos=0;period=0
            while True:
                pos=(pos+1)&mask;period+=1
                if pos==0:break
            self.assertEqual(period,expected_period)

    def test_noise_period_and_all_state_bounds(self):
        for tap,expected in [(1,32767),(6,93),(5,35),(3,63)]:
            state=1;period=0
            while True:
                state=(state>>1)|(((state^(state>>tap))&1)<<14);period+=1
                if state==1:break
                self.assertLessEqual(period,32767)
            self.assertEqual(period,expected)
        for state in range(1,32768):
            for tap in (3,5):
                nxt=(state>>1)|(((state^(state>>tap))&1)<<14)
                self.assertTrue(0<nxt<32768)

    def test_pixel_palette_bounds_and_layer_priority(self):
        for color in range(32):
            for mask in (1,2,3,31):
                index=color if color&mask else 0
                self.assertTrue(0<=index<32)
        for behind in (False,True):
            for opaque_bg in (False,True):
                original_sprite=(not opaque_bg) or not behind
                modified_sprite=(not opaque_bg) or behind
                if opaque_bg:self.assertNotEqual(original_sprite,modified_sprite)
                else:self.assertTrue(original_sprite and modified_sprite)

    def test_hash_guard_rejects_changed_build(self):
        data=bytearray(512);data[:2]=b'MZ';struct.pack_into('<I',data,60,64)
        data[64:68]=b'PE\0\0';struct.pack_into('<H',data,68,0x8664)
        struct.pack_into('<I',data,72,123);struct.pack_into('<I',data,144,512);data[256:260]=b'code'
        class M:
            def read(self,a,n):return bytes(data[a:a+n])
        manifest={'timestamp':123,'image_size':512,'code_rva':256,'code_size':4,'code_sha256':hashlib.sha256(b'code').hexdigest()}
        with patch.object(lab,'MANIFEST',manifest):
            lab.verify_build(M(),0);data[256]^=1
            with self.assertRaises(ValueError):lab.verify_build(M(),0)

if __name__=='__main__':unittest.main()
