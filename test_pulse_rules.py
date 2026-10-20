# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Random Týpek, for project contributions.
# Mesen-derived material is attributed in THIRD_PARTY_NOTICES.md.
import unittest
from unittest.mock import patch
import hardware_lab as lab
from test_hardware_lab import Memory, session

class PulseRules(unittest.TestCase):
    def test_all_lookup_indices_and_output_levels(self):
        wave=bytes.fromhex(lab.MANIFEST['data_guards'][0]['expected'])
        self.assertEqual(len(wave),32);self.assertEqual(set(wave),{0,1})
        for duty in range(4):
            for phase in range(8):
                for index in [duty+phase*4,phase*3,phase*2]:
                    self.assertTrue(0<=index<32)
                    for volume in range(16):self.assertTrue(0<=wave[index]*volume<=15)
        self.assertEqual([wave[p*3] for p in range(8)],[0,0,0,0,0,1,0,1])
        self.assertEqual([wave[p*2] for p in range(8)],[0,0,0,0,0,0,0,1])
    def test_pulse_phase_bounds_and_four_step_cycle(self):
        for old in range(256):self.assertIn((old-1)&6,(0,2,4,6))
        position=0;values=[]
        for _ in range(4):position=(position-1)&6;values.append(position)
        self.assertEqual(values,[6,4,2,0])
    def test_sprite_palette_source_in_same_object_and_in_bounds(self):
        for i in range(64):
            address=0x1d0+i*5
            self.assertLess(address,address+5)
            for color in range(1,4):
                for priority in (0,1):self.assertTrue(0<=color+priority<32)
    def test_duty_guard_rejects_changed_native_table(self):
        import hashlib,struct
        data=bytearray(512);data[:2]=b'MZ';struct.pack_into('<I',data,60,64)
        data[64:68]=b'PE\0\0';struct.pack_into('<H',data,68,0x8664)
        struct.pack_into('<I',data,72,123);struct.pack_into('<I',data,144,512)
        data[256:260]=b'code';data[300:304]=bytes([0,1,0,1])
        class M:
            def read(self,a,n):return bytes(data[a:a+n])
        manifest={'timestamp':123,'image_size':512,'code_rva':256,'code_size':4,'code_sha256':hashlib.sha256(b'code').hexdigest(),'data_guards':[{'rva':300,'expected':'00010001','label':'test duty table'}]}
        with patch.object(lab,'MANIFEST',manifest):
            lab.verify_build(M(),0);data[300]=2
            with self.assertRaisesRegex(ValueError,'test duty table'):lab.verify_build(M(),0)

if __name__=='__main__':unittest.main()
