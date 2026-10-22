# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Random Týpek, for project contributions.
# Mesen-derived material is attributed in THIRD_PARTY_NOTICES.md.
"""Timed hardware performances; independent of Tk and process memory."""
import math
import random
import time

MODES=('Classic bursts','Build-up','Stutter','Rolling overlap','Mutation walk')

class RandomCycle:
    def __init__(self, after, cancel, apply, restore, notify, error, rng=None, clock=None):
        self.after   = after
        self.cancel  = cancel
        self.apply   = apply
        self.restore = restore
        self.notify  = notify
        self.error   = error

        self.rng   = rng or random.Random()
        self.clock = clock or time.monotonic

        self.running       = False
        self.timer         = None
        self.generation    = 0
        self.last          = None

    def stop(self):
        self.running = False
        self.generation += 1

        if self.timer is not None:
            self.cancel(self.timer)
            self.timer = None

    def start(self, pool, gap, duration, groups=None, mode='Classic bursts', compatible=None):
        pool = tuple(dict.fromkeys(pool))
        if not pool:
            raise ValueError('Select at least one random experiment')

        if mode not in MODES:
            raise ValueError('Unknown performance mode')

        if mode!='Classic bursts' and not groups:
            raise ValueError('This mode needs compatible preset groups')

        if mode in ('Rolling overlap','Mutation walk') and compatible is None:
            raise ValueError('This mode needs a compatibility check')

        gap, duration = tuple(map(float,gap)), tuple(map(float,duration))
        for lo,hi in (gap,duration):
            if not (math.isfinite(lo) and math.isfinite(hi) and .1<=lo<=hi<=3600):
                raise ValueError('Timing ranges must be 0.1–3600 seconds, with minimum <= maximum')

        self.stop()

        self.pool = pool
        self.gap = gap
        self.duration = duration
        self.groups = groups
        self.mode = mode
        self.compatible = compatible
        self.limit = max(groups) if groups else 1
        self.last = None
        self.running = True
        self.expires = {}

        self._clean()

    def _schedule(self, bounds, callback, phase):
        self._later(self.rng.uniform(*bounds), callback, phase)

    def _later(self,delay,callback,phase):
        generation = self.generation
        self.notify(phase,delay)

        def tick():
            if not self.running or generation!=self.generation: return
            self.timer = None
            callback()

        self.timer = self.after(max(1,round(delay*1000)),tick)

    def _failed(self, exc):
        self.stop()
        try:self.restore()
        except Exception as recovery:
            exc = RuntimeError(f'{exc}; restore failed: {recovery}. Restart Mesen.')
        self.error(exc)

    def _clean(self):
        try:
            self.restore()

            if self.mode=='Mutation walk':
                self.walk = ()
                self.walk_end = None
                self.walk_previous = None
                self._schedule(self.gap,self._walk_tick,'Original rules; start mutation walk')

            elif self.mode=='Rolling overlap':
                self.expires = {}
                self.next_add = self.clock()
                self._schedule(self.gap,self._roll_tick,'Original rules; first rolling effect')

            else:
                self._schedule(self.gap,self._burst,'Original rules; next burst')

        except Exception as exc: self._failed(exc)

    def _choose(self):
        if self.groups is None:
            choices = [x for x in self.pool if x!=self.last] or list(self.pool)
            return self.rng.choice(choices)
        available = {
            n: [
                g for g in options
                if g!=self.last
            ]
            for n, options in self.groups.items()
        }
        available = {
                        n: options
                        for n,options in available.items()
                        if options
        } or self.groups

        return self.rng.choice(
            available[
                self.rng.choice(list(available))
            ]
        )

    def _burst(self):
        try:
            key = self._choose()
            self.last = key

            if self.mode=='Build-up':
                self.ramp = list(key)
                self.rng.shuffle(self.ramp)
                self.ramp_count = 0
                self._ramp_tick()
                return

            self.apply(key)
            if self.mode=='Stutter':
                self.stutter_keys = key
                self.stutter_on = True
                self.stutter_end = self.clock()+self.rng.uniform(*self.duration)
                self._stutter_later()
            else: self._schedule(self.duration,self._clean,'Modified rules; restore')
        except Exception as exc: self._failed(exc)

    def _ramp_tick(self):
        try:
            self.ramp_count += 1
            self.apply(tuple(self.ramp[:self.ramp_count]))

            if self.ramp_count<len(self.ramp):
                self._schedule(self.gap,self._ramp_tick,f'Build-up {self.ramp_count}/{len(self.ramp)}; add next')
            else: self._schedule(self.duration,self._clean,'Full stack; restore')

        except Exception as exc: self._failed(exc)

    def _stutter_later(self):
        remaining=max(0,self.stutter_end-self.clock())
        self._later(min(self.rng.uniform(.15,.4),remaining),self._stutter_tick,
                    'Stutter: '+('modified' if self.stutter_on else 'original')+'; switch')

    def _stutter_tick(self):
        try:
            if self.clock()>=self.stutter_end:self._clean();return
            if self.stutter_on:self.restore()
            else:self.apply(self.stutter_keys)
            self.stutter_on=not self.stutter_on
            self._stutter_later()
        except Exception as exc:self._failed(exc)

    def _roll_tick(self):
        try:
            now = self.clock()
            before = tuple(self.expires)
            self.expires = {
                key:deadline
                for key,deadline in self.expires.items()
                if deadline > now
            }
            if now >= self.next_add:
                if len(self.expires) < self.limit:
                    candidates = [
                        key
                        for key in self.pool
                        if (key not in self.expires and self.compatible(tuple(self.expires)+(key,)))
                    ]

                    choices = [
                                  key for key in candidates
                                  if key != self.last
                              ] or candidates

                    if choices:
                        key = self.rng.choice(choices)
                        self.last = key
                        self.expires[key] = now + self.rng.uniform(*self.duration)

                self.next_add = now + self.rng.uniform(*self.gap)

            active = tuple(self.expires)
            if active != before:
                if active: self.apply(active)
                else:      self.restore()

            deadline = min([self.next_add,*self.expires.values()])
            self._later(
                max(.001,deadline-self.clock()),
                self._roll_tick,
                f'Rolling: {len(active)} active; next event'
            )

        except Exception as exc: self._failed(exc)

    def _walk_tick(self):
        try:
            now = self.clock()
            if self.walk_end is None:
                self.walk_end = now + self.rng.uniform(*self.duration)
            elif now >= self.walk_end:
                self._clean()
                return

            candidates = []
            if len(self.walk) < self.limit:
                candidates.extend(
                    self.walk+(key,)
                    for key in self.pool
                    if key not in self.walk and self.compatible(self.walk+(key,))
                )

            if len(self.walk) > 1 or not candidates:
                candidates.extend(
                    self.walk[:i]+self.walk[i+1:]
                    for i in range(len(self.walk))
                )

            choices = [
                          keys
                          for keys in candidates
                          if frozenset(keys)!=self.walk_previous
                      ] or candidates

            if choices:
                next_keys = self.rng.choice(choices)
                self.walk_previous = frozenset(self.walk)
                self.walk = next_keys

                if self.walk: self.apply(self.walk)
                else:         self.restore()

            delay = min(
                self.rng.uniform(*self.gap),
                max(.001,self.walk_end-self.clock())
            )

            self._later(delay, self._walk_tick,f'Mutation walk: {len(self.walk)} active; next step/reset')

        except Exception as exc: self._failed(exc)
