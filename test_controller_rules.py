# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Random Týpek, for project contributions.
# Mesen-derived material is attributed in THIRD_PARTY_NOTICES.md.
import unittest
from itertools import combinations
import hardware_lab as lab
from combinations import merge_points

ORDER=['A','B','Select','Start','Up','Down','Left','Right']
DEFAULT={'A':7,'B':6,'Select':5,'Start':4,'Up':0,'Down':1,'Left':2,'Right':3}
def report(state,mapping):
    return sum(((state>>mapping[name])&1)<<i for i,name in enumerate(ORDER))

class ControllerRules(unittest.TestCase):
    def test_reports_all_inputs_and_menu_buttons_unchanged(self):
        for effect in lab.EFFECTS.values():
            if effect['category']!='input':continue
            mapping=DEFAULT|effect['report_mapping']
            self.assertTrue(all(0<=v<=7 for v in mapping.values()))
            for state in range(256):
                output=report(state,mapping)
                self.assertTrue(0<=output<=255)
                self.assertEqual(output&12,report(state,DEFAULT)&12)
    def test_named_control_outcomes(self):
        def run(key,*pressed):
            state=sum(1<<DEFAULT[x] for x in pressed)
            value=report(state,DEFAULT|lab.EFFECTS[key]['report_mapping'])
            return {x for i,x in enumerate(ORDER) if value&(1<<i)}
        self.assertEqual(run('controls_a_down','A'),{'Down'})
        self.assertEqual(run('controls_a_down','Down'),{'A'})
        self.assertEqual(run('controls_vertical_actions','Up'),{'Up','A'})
        self.assertEqual(run('controls_vertical_actions','Down'),{'Down','B'})
        self.assertEqual(run('controls_vertical_actions','A'),set())
        self.assertEqual(run('controls_mirror','Left'),{'Right'})
        self.assertEqual(run('controls_ab','A'),{'B'})
        self.assertEqual(run('controls_a_right','A'),{'Right'})
        self.assertEqual(run('controls_b_left','Left'),{'B'})
        self.assertEqual(run('controls_b_down','B'),{'Down'})
        self.assertEqual(run('controls_diagonal','Up'),{'Up','Left'})
        self.assertEqual(run('controls_diagonal','Down'),{'Down','Right'})
        self.assertEqual(run('controls_diagonal','Left'),set())
    def test_combined_controls_keep_valid_inputs(self):
        inputs=[key for key,effect in lab.EFFECTS.items() if effect['category']=='input']
        for count in range(1,5):
            for keys in combinations(inputs,count):
                try:merge_points(lab.EFFECTS,keys)
                except ValueError:continue
                mapping=DEFAULT.copy()
                for key in keys:mapping.update(lab.EFFECTS[key]['report_mapping'])
                for state in range(256):
                    self.assertEqual(report(state,mapping)&12,report(state,DEFAULT)&12)

if __name__=='__main__':unittest.main()
