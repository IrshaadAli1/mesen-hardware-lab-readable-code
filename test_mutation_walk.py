# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Random Týpek, for project contributions.
# Mesen-derived material is attributed in THIRD_PARTY_NOTICES.md.
import random
import unittest
import test_performances as performance
from test_hardware_lab import Memory, session
import hardware_lab as lab

class MutationWalk(unittest.TestCase):
    setUp=performance.Performances.setUp
    start=performance.Performances.start
    compatible=performance.Performances.compatible
    def test_walk_changes_one_preset_and_respects_conflicts(self):
        self.pool=['triangle_saw','triangle_short','sprite_depth','dmc_reverse']
        self.start('Mutation walk',gap=(.1,.3),duration=(100,100),count=3)
        for _ in range(100):self.clock.tick()
        for (_,a),(_,b) in zip(self.events,self.events[1:]):
            self.assertEqual(len(set(a)^set(b)),1)
            self.assertLessEqual(len(b),3)
            self.assertFalse({'triangle_saw','triangle_short'}<=set(b))
        self.assertTrue(any(len(keys)>1 for _,keys in self.events))
        self.assertFalse(self.errors)

    def test_walk_deadline_restores(self):
        self.start('Mutation walk',gap=(.2,.2),duration=(1,1))
        for _ in range(6):self.clock.tick()
        self.assertEqual(self.events[-1][1],())
        self.assertAlmostEqual(self.events[-1][0],1.2)

class Transitions(unittest.TestCase):
    def test_retained_bytes_are_never_rewritten(self):
        m=Memory();s=session(m);s.apply('triangle_saw')
        writes=[];write=m.write
        def record(a,b):writes.append(a);write(a,b)
        m.write=record
        s.apply_many(('triangle_saw','sprite_depth'))
        s.apply_many(('triangle_saw',))
        tri=lab.EFFECTS['triangle_saw']['points'][0]
        self.assertNotIn(m.base+tri['rva']+tri['offset'],writes)
        self.assertEqual(len(writes),2)

    def test_same_stack_is_noop_and_still_checks_for_tampering(self):
        m=Memory();s=session(m);s.apply('triangle_saw')
        m.write=lambda *args:self.fail('Unnecessary write')
        s.apply('triangle_saw')
        pt=lab.EFFECTS['triangle_saw']['points'][0]
        m.data[m.base+pt['rva']]=0x90
        with self.assertRaises(ValueError):s.apply('triangle_saw')

    def test_replacement_at_different_instruction_offset(self):
        m=Memory();before=dict(m.data);s=session(m)
        s.apply('sprites_front');s.apply('sprites_behind');s.restore()
        self.assertEqual(m.data,before)

    def test_failed_addition_restores_retained_rules(self):
        m=Memory();before=dict(m.data);s=session(m);s.apply('triangle_saw')
        pt=lab.EFFECTS['sprite_depth']['points'][0]
        m.fail_at=m.base+pt['rva']+pt['offset']
        with self.assertRaises(OSError):s.apply_many(('triangle_saw','sprite_depth'))
        self.assertEqual(m.data,before);self.assertIsNone(s.active)

if __name__=='__main__':unittest.main()
