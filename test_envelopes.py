# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Random Týpek, for project contributions.
# Mesen-derived material is attributed in THIRD_PARTY_NOTICES.md.
import unittest
from itertools import product
import hardware_lab as lab
from test_hardware_lab import Memory,session
from combinations import merge_points

def tick(volume,start,divider,counter,loop,speed=1,height=15,freeze=False):
    if start:return 0,volume,height
    divider-=speed
    if divider<0:
        divider=volume
        if counter>0:
            if not freeze:counter-=1
        elif loop:counter=height
    return start,divider,counter

class Envelopes(unittest.TestCase):
    def test_all_valid_states_remain_bounded(self):
        for volume,start,divider,counter,loop,speed,height,freeze in product(range(16),(0,1),range(16),range(16),(0,1),(1,4),(7,15),(False,True)):
            a,b,c=tick(volume,start,divider,counter,loop,speed,height,freeze)
            self.assertIn(a,(0,1));self.assertTrue(0<=b<=15);self.assertTrue(0<=c<=15)
    def test_fast_fade_loop_and_freeze_sequences(self):
        def levels(speed=1,height=15,freeze=False):
            start,divider,counter=1,0,0;out=[]
            for _ in range(20):
                start,divider,counter=tick(3,start,divider,counter,True,speed,height,freeze);out.append(counter)
            return out
        self.assertEqual(levels(4)[:5],[15,14,13,12,11])
        self.assertEqual(levels(1)[:5],[15,15,15,15,14])
        self.assertEqual(levels(4,7)[:9],[7,6,5,4,3,2,1,0,7])
        self.assertEqual(levels(4,7,True),[7]*20)
    def test_each_write_failure_in_envelope_stack_restores(self):
        keys=['env_freeze','env_short','env_pulse_mode','env_noise_fast']
        for point in merge_points(lab.EFFECTS,keys):
            m=Memory();s=session(m);before=dict(m.data)
            m.fail_at=m.base+point['rva']+point['offset']
            with self.assertRaises(OSError):s.apply_many(keys)
            self.assertEqual(m.data,before)

if __name__=='__main__':unittest.main()
