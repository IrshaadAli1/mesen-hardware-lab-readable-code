# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Random Týpek, for project contributions.
# Mesen-derived material is attributed in THIRD_PARTY_NOTICES.md.
import unittest,random
from itertools import combinations
import hardware_lab as lab
from combinations import merge_points,compatible_groups,signature
from test_hardware_lab import Memory,session
from random_cycle import RandomCycle

class CombinationTests(unittest.TestCase):
    def test_conflicting_instruction_edits_rejected_before_writes(self):
        m=Memory();s=session(m);s.apply('triangle_saw');before=dict(m.data)
        for keys in [('sprites_front','sprites_behind'),('triangle_saw','triangle_short'),('palette_early','palette_late')]:
            with self.assertRaisesRegex(ValueError,'Conflicting rules'):s.apply_many(keys)
            self.assertEqual(m.data,before)
        s.restore()
    def test_shared_patches_are_deduplicated(self):
        m=Memory();before=dict(m.data);s=session(m)
        self.assertEqual(s.apply_many(['triangle_saw','triangle_rising','impossible_sound']),4)
        self.assertEqual(len(s.engine.original),4)
        s.restore();self.assertEqual(m.data,before)
    def test_every_write_failure_in_stack_recovers(self):
        keys=['triangle_rising','noise_hollow','palette_early','sprite_spotlight']
        for p in merge_points(lab.EFFECTS,keys):
            m=Memory();before=dict(m.data);s=session(m)
            m.fail_at=m.base+p['rva']+p['offset']
            with self.assertRaises(OSError):s.apply_many(keys)
            self.assertEqual(m.data,before);self.assertFalse(s.engine.original)
    def test_all_available_groups_round_trip(self):
        groups=compatible_groups(lab.EFFECTS,lab.EFFECTS,2,4)
        self.assertEqual(set(groups),{2,3,4})
        m=Memory();before=dict(m.data);s=session(m)
        seen=set()
        for count,choices in groups.items():
            for keys in choices:
                self.assertEqual(len(keys),count)
                points=merge_points(lab.EFFECTS,keys)
                fingerprint=frozenset(signature(p) for p in points)
                self.assertNotIn(fingerprint,seen);seen.add(fingerprint)
                s.apply_many(keys)
                self.assertEqual(set(s.engine.original),{m.base+p['rva']+p['offset'] for p in points})
                s.restore();self.assertEqual(m.data,before)
    def test_impossible_pool_and_invalid_counts(self):
        for lo,hi in [(0,2),(3,2),(1,5),(2,2)]:
            with self.assertRaises(ValueError):compatible_groups(lab.EFFECTS,['cutout_1','cutout_2'],lo,hi)
    def test_random_groups_activate_together_and_restore_between(self):
        pending={};counter=0;events=[];errors=[];m=Memory();before=dict(m.data);s=session(m)
        def after(ms,callback):
            nonlocal counter
            counter+=1;pending[counter]=callback;return counter
        def apply(keys):s.apply_many(keys);events.append(keys)
        def restore():s.restore();self.assertEqual(m.data,before)
        groups=compatible_groups(lab.EFFECTS,lab.EFFECTS,2,4)
        r=RandomCycle(after,lambda key:pending.pop(key,None),apply,restore,lambda *a:None,errors.append,random.Random(8))
        r.start(list(lab.EFFECTS),(3,10),(2,6),groups)
        for _ in range(200):pending.pop(min(pending))()
        r.stop();restore()
        self.assertFalse(errors);self.assertFalse(pending)
        self.assertEqual(len(events),100);self.assertEqual({len(keys) for keys in events},{2,3,4})
        self.assertTrue(all(a!=b for a,b in zip(events,events[1:])))

if __name__=='__main__':unittest.main()
