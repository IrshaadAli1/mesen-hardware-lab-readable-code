# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Random Týpek, for project contributions.
# Mesen-derived material is attributed in THIRD_PARTY_NOTICES.md.
import random
import unittest
from random_cycle import RandomCycle,MODES
from combinations import merge_points,compatible_groups
import hardware_lab as lab
from test_hardware_lab import Memory,session

class Clock:
    def __init__(self):self.now=0.;self.pending={};self.counter=0
    def after(self,ms,callback):
        self.counter+=1;self.pending[self.counter]=(self.now+ms/1000,callback);return self.counter
    def cancel(self,key):self.pending.pop(key,None)
    def tick(self):
        key=min(self.pending,key=lambda k:self.pending[k][0]);self.now,callback=self.pending.pop(key);callback()

class Performances(unittest.TestCase):
    def setUp(self):
        self.clock=Clock();self.events=[];self.errors=[]
        self.memory=Memory();self.before=dict(self.memory.data);self.session=session(self.memory)
        self.pool=['triangle_saw','sprite_depth','dmc_reverse','controls_ab']
        def apply(keys):
            self.session.apply_many(keys);self.events.append((self.clock.now,tuple(keys)))
        def restore():
            self.session.restore();self.assertEqual(self.memory.data,self.before);self.events.append((self.clock.now,()))
        self.runner=RandomCycle(self.clock.after,self.clock.cancel,apply,restore,lambda *a:None,self.errors.append,random.Random(13),lambda:self.clock.now)
    def compatible(self,keys):
        try:merge_points(lab.EFFECTS,keys);return True
        except ValueError:return False
    def start(self,mode,gap=(.2,.2),duration=(.6,1.2),count=3):
        groups=compatible_groups(lab.EFFECTS,self.pool,count,count)
        self.runner.start(self.pool,gap,duration,groups,mode,self.compatible)
    def test_build_up_grows_and_restores_whole_stack(self):
        self.start('Build-up',duration=(1,1))
        for _ in range(4):self.clock.tick()
        self.assertEqual([len(keys) for _,keys in self.events],[0,1,2,3,0])
        self.assertTrue(set(self.events[1][1])<set(self.events[2][1])<set(self.events[3][1]))
        self.assertAlmostEqual(self.events[-1][0],1.6,places=3)
        self.assertFalse(self.errors)
    def test_stutter_uses_same_stack_and_total_burst_deadline(self):
        self.start('Stutter',gap=(1,1),duration=(1.2,1.2))
        while self.clock.pending and min(x[0] for x in self.clock.pending.values())<2.3:self.clock.tick()
        modified=[keys for _,keys in self.events if keys]
        self.assertGreaterEqual(len(modified),2);self.assertTrue(all(keys==modified[0] for keys in modified))
        self.assertEqual(self.events[-1][1],());self.assertAlmostEqual(self.events[-1][0],2.2,delta=.002)
        self.assertTrue(all(bool(a[1])!=bool(b[1]) for a,b in zip(self.events[1:-1],self.events[2:-1])))
    def test_rolling_expires_independently_and_respects_limit(self):
        self.start('Rolling overlap',count=2)
        for _ in range(100):self.clock.tick()
        active=[keys for _,keys in self.events if keys]
        self.assertTrue(all(len(keys)<=2 for keys in active));self.assertTrue(any(len(keys)==2 for keys in active))
        self.assertTrue(any(set(a)&set(b) and set(a)!=set(b) for a,b in zip(active,active[1:])))
        self.assertFalse(self.errors);self.assertEqual(len(self.clock.pending),1)
        self.runner.stop();self.runner.restore();self.assertEqual(self.memory.data,self.before)
    def test_rolling_skips_conflicting_candidates(self):
        self.pool=['triangle_saw','triangle_short','sprite_depth'];self.start('Rolling overlap',count=2)
        for _ in range(100):self.clock.tick()
        for _,keys in self.events:self.assertFalse({'triangle_saw','triangle_short'}<=set(keys))
        self.assertFalse(self.errors)
    def test_stop_invalidates_pending_callbacks_in_every_mode(self):
        for mode in MODES:
            self.start(mode);self.clock.tick()
            stale=next(iter(self.clock.pending.values()))[1]
            self.runner.stop();self.runner.restore();before=list(self.events)
            stale();self.assertEqual(self.events,before);self.assertFalse(self.clock.pending)
    def test_application_failure_stops_every_mode_and_restores(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                original=self.runner.apply
                def broken(keys):
                    original(keys);raise OSError('simulated failure after applying')
                self.runner.apply=broken
                self.start(mode);self.clock.tick()
                self.assertFalse(self.runner.running);self.assertFalse(self.clock.pending)
                self.assertEqual(self.memory.data,self.before)
                self.runner.apply=original
        self.assertEqual(len(self.errors),len(MODES))
    def test_mode_restart_cancels_old_generation(self):
        self.start('Stutter');self.clock.tick();stale=next(iter(self.clock.pending.values()))[1]
        self.start('Rolling overlap');before=list(self.events);stale()
        self.assertEqual(self.events,before);self.assertEqual(len(self.clock.pending),1)
        self.clock.tick();self.assertTrue(self.session.active)

if __name__=='__main__':unittest.main()
