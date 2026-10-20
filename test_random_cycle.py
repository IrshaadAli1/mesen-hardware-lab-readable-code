# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Random Týpek, for project contributions.
# Mesen-derived material is attributed in THIRD_PARTY_NOTICES.md.
import random
import unittest
from random_cycle import RandomCycle

class RandomTests(unittest.TestCase):
    def setUp(self):
        self.pending={};self.delays=[];self.events=[];self.errors=[];self.counter=0
        def after(ms,callback):
            self.counter+=1;self.pending[self.counter]=callback;self.delays.append(ms);return self.counter
        self.runner=RandomCycle(after,lambda key:self.pending.pop(key,None),
            lambda key:self.events.append(('apply',key)),lambda:self.events.append(('restore',None)),
            lambda phase,delay:None,self.errors.append,random.Random(123))
    def tick(self):
        key=min(self.pending);self.pending.pop(key)()
    def test_repeated_random_bursts_always_have_clean_gaps(self):
        self.runner.start(['a','b','c'],(3,10),(2,6))
        for _ in range(200):self.tick()
        self.assertEqual(len(self.pending),1)
        self.assertFalse(self.errors)
        self.assertEqual([x[0] for x in self.events],['restore','apply']*100+['restore'])
        selected=[x[1] for x in self.events if x[0]=='apply']
        self.assertTrue(all(a!=b for a,b in zip(selected,selected[1:])))
        for i,delay in enumerate(self.delays):self.assertTrue((3000<=delay<=10000) if i%2==0 else (2000<=delay<=6000))
        self.assertGreater(len(set(self.delays)),20)
    def test_cancel_ignores_stale_callbacks_and_restart(self):
        self.runner.start(['a'],(1,1),(1,1));stale=next(iter(self.pending.values()))
        self.runner.stop();self.assertFalse(self.pending);old=list(self.events)
        stale();self.assertEqual(self.events,old)
        self.runner.start(['b'],(1,1),(1,1));stale();self.tick()
        self.assertEqual(self.events[-1],('apply','b'))
    def test_apply_failure_restores_and_stops(self):
        def broken(key):raise OSError('write failed')
        self.runner.apply=broken
        self.runner.start(['a'],(1,1),(1,1));self.tick()
        self.assertFalse(self.pending);self.assertFalse(self.runner.running)
        self.assertEqual(self.events[-1],('restore',None));self.assertEqual(len(self.errors),1)
    def test_restore_failure_is_reported(self):
        def broken():raise OSError('restore failed')
        self.runner.restore=broken
        self.runner.start(['a'],(1,1),(1,1))
        self.assertFalse(self.pending);self.assertIn('Restart Mesen',str(self.errors[0]))
    def test_invalid_ranges_and_empty_pool(self):
        for gap in [(0,1),(2,1),(1,float('inf')),(float('nan'),2),(1,3601)]:
            with self.assertRaises(ValueError):self.runner.start(['a'],gap,(1,2))
        with self.assertRaises(ValueError):self.runner.start([],(1,2),(1,2))
        self.assertFalse(self.events)

if __name__=='__main__':unittest.main()
