# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Random Týpek, for project contributions.
# Mesen-derived material is attributed in THIRD_PARTY_NOTICES.md.
import unittest
from itertools import combinations
import hardware_lab as lab
from combinations import merge_points
from test_hardware_lab import Memory,session

DMC=[key for key,effect in lab.EFFECTS.items() if effect.get('subsystem')=='dmc']

def decoded_level(level,bit,points):
    up=[0x80,0xc1,2];down=[0x80,0xe9,2];invert=False
    for p in points:
        if p['rva']==0x40abab:up[p['offset']]=p['value']
        if p['rva']==0x40abb5:down[p['offset']]=p['value']
        if p['rva']==0x40aba4:invert=p['value']==0x75
    if invert:bit=not bit
    if bit:
        if level>125:return level
        return (level^up[2]) if up[1]==0xf1 else level+up[2]
    if level<2:return level
    return (level^down[2]) if down[1]==0xf1 else level-down[2]

class DmcRules(unittest.TestCase):
    def test_all_valid_levels_during_apply_and_restore_prefixes(self):
        for count in range(1,5):
            for keys in combinations(DMC,count):
                try:points=merge_points(lab.EFFECTS,keys)
                except ValueError:continue
                states=[points[:i] for i in range(len(points)+1)]
                # Engine restores in insertion order, so all remaining suffixes must be safe too.
                states += [points[i:] for i in range(len(points)+1)]
                for partial in states:
                    for level in range(128):
                        for bit in (0,1):self.assertTrue(0<=decoded_level(level,bit,partial)<=127)
    def test_known_decoder_steps(self):
        def run(key,level,bit):return decoded_level(level,bit,lab.EFFECTS[key]['points'])
        self.assertEqual(run('dmc_soft',64,1),65)
        self.assertEqual(run('dmc_soft',64,0),63)
        self.assertEqual(run('dmc_rise',64,1),66)
        self.assertEqual(run('dmc_rise',64,0),63)
        self.assertEqual(run('dmc_fall',64,1),65)
        self.assertEqual(run('dmc_fall',64,0),62)
        self.assertEqual(run('dmc_invert',64,1),62)
        self.assertEqual(run('dmc_buzz',64,1),66)
        self.assertEqual(run('dmc_buzz',66,0),64)
    def test_xor_and_step_immediate_same_instruction_conflict(self):
        for key in ['dmc_soft','dmc_rise','dmc_fall']:
            with self.assertRaisesRegex(ValueError,'Conflicting rules'):merge_points(lab.EFFECTS,[key,'dmc_buzz'])
    def test_decoder_write_failures_restore(self):
        keys=['dmc_soft','dmc_reverse','dmc_invert']
        for p in merge_points(lab.EFFECTS,keys):
            m=Memory();s=session(m);before=dict(m.data)
            m.fail_at=m.base+p['rva']+p['offset']
            with self.assertRaises(OSError):s.apply_many(keys)
            self.assertEqual(m.data,before)

if __name__=='__main__':unittest.main()
