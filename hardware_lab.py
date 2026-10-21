# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Random Týpek, for project contributions.
# Mesen-derived material is attributed in THIRD_PARTY_NOTICES.md.
"""Mesen Hardware Lab v14: deterministic, verified NES hardware-rule experiments."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import struct
from random_cycle import RandomCycle, MODES
from combinations import merge_points, compatible_groups, MAX_PATCHES
from winmem import Windows, Target, Engine, ALLOWED

from typings_and_alias import EffectsDict, Length, CVoidPtr, NumberLike, Keys


MANIFEST:   dict                     = json.loads(Path(__file__).with_name('build_manifest.json').read_text())
EFFECTS :   EffectsDict              = {item['id']:item for item in MANIFEST['effects']}

@dataclass(frozen=True)
class Patch:
    address:    int
    code:       bytes
    offset:     int
    label:      str
    values:     tuple
    bits:       int         = 0

    @property
    def patch_address(self) -> int: return self.address + self.offset


def verify_build(target: Target, base: CVoidPtr):
    dos: bytes = target.read(base,64)
    if dos[:2] != b'MZ':
        raise ValueError('Invalid module header')

    off: NumberLike = struct.unpack_from('<I',dos,60)[0]
    if not 64<=off<=1024*1024:
        raise ValueError('Invalid PE offset')

    header: bytes = target.read(base+off,88)
    if header[:4] != b'PE\0\0' or struct.unpack_from('<H',header,4)[0] != 0x8664:
        raise ValueError('Expected the supported x64 MesenCore.dll')

    if (struct.unpack_from('<I',header,8)[0]!=MANIFEST['timestamp'] or
        struct.unpack_from('<I',header,80)[0]!=MANIFEST['image_size']):
        raise ValueError('Build mismatch: this lab targets the exact supported Mesen CE 2.2.1 build only')

    code: bytes = target.read(base+MANIFEST['code_rva'],MANIFEST['code_size'])
    if hashlib.sha256(code).hexdigest()!=MANIFEST['code_sha256']:
        raise ValueError('Code hash mismatch. Restart Mesen to clear other patches. A different build is unsupported.')

    for guard in MANIFEST.get('data_guards',[]):
        expected = bytes.fromhex(guard['expected'])
        if target.read(base+guard['rva'], len(expected))!=expected:
            raise ValueError(guard['label']+' differs from the verified build. Restart Mesen.')


class LabSession:
    def __init__(self, target: Target, base: CVoidPtr):
        verify_build(target,base)
        self.target:        Target         = target
        self.base  :        CVoidPtr       = base
        self.engine:        Engine         = Engine(target)
        self.active                        = None

    def restore(self) -> int:
        count = self.engine.undo()
        self.active = None
        return count

    def apply(self,effect_id) -> Length:
        return self.apply_many((effect_id,))

    def apply_many(self, effect_ids) -> Length:
        keys: Keys = tuple(dict.fromkeys(effect_ids))
        points = merge_points(EFFECTS, keys)  # Validate before touching the current state.
        patches: list[Patch] = []

        for point in points:
            original = bytes.fromhex(point['original'])
            patches.append(Patch(self.base+point['rva'],original,point['offset'],point['label'],(point['value'],)))

        desired: dict[int, Patch] ={p.patch_address: p for p in patches}
        if len(desired) != len(patches):
            raise ValueError('Duplicate patch site in experiment')

        # Validate all managed and requested instructions before any transition write.
        for item,expected in self.engine.original.values():
            if self.target.read(item.address,len(item.code))!=expected:
                raise ValueError('Active instruction changed externally. Restart Mesen.')

        for item in patches:
            prior = next((record for record in self.engine.original.values()
                        if record[0].address==item.address and record[0].code==item.code),None)
            expected = prior[1] if prior else item.code
            if self.target.read(item.address,len(item.code))!=expected:
                raise ValueError('Instruction mismatch. Restart Mesen before applying this experiment.')

        def unchanged(item,expected,wanted) -> bool:
            return (wanted is not None and item.address==wanted.address and item.code==wanted.code
                    and item.offset==wanted.offset and expected[item.offset]==wanted.values[0])

        try:
            # Retained patches never toggle off. Remove obsolete edits before adding new ones.
            for address,(item,expected) in list(self.engine.original.items()):
                if not unchanged(item,expected,desired.get(address)):self.engine.restore(address)

            for patch in patches:
                if patch.patch_address not in self.engine.original:
                    self.engine.blast([patch],1,MAX_PATCHES,'Balanced')

        except Exception:
            try: self.restore()
            except Exception: pass  # Keep outstanding recovery entries.
            raise

        self.active=keys[0] if len(keys)==1 else keys
        return len(patches)


def main():
    import tkinter as tk
    from tkinter import ttk, messagebox
    import psutil

    api: Windows = Windows()

    root: tk.Tk = tk.Tk()
    root.title('Mesen Hardware Lab v14 — Impossible NES')
    root.geometry('960x920');root.minsize(860,820)

    frame: ttk.Frame = ttk.Frame(root,padding=20);frame.pack(fill='both',expand=True)

    ttk.Label(
        frame,
        text='IMPOSSIBLE NES',
        font=('Segoe UI',22,'bold')
    ).pack(anchor='w')

    ttk.Label(
        frame,
        text='Mesen Hardware Lab v14 • named changes to sound, picture and controller rules'
    ).pack(anchor='w',pady=(4,12))

    process: ttk.Combobox = ttk.Combobox(frame, state='readonly')
    process.pack(fill='x')

    row: ttk.Frame = ttk.Frame(frame)
    row.pack(fill='x',pady=8)

    ttk.Label(
        frame,
        text='Experiment'
    ).pack(anchor='w',pady=(10,2))

    picker: ttk.Combobox = ttk.Combobox(frame, state='readonly', values=[e['title'] for e in EFFECTS.values()])
    picker.pack(fill='x')
    picker.current(list(EFFECTS).index('impossible_sound'))

    description: tk.StringVar = tk.StringVar()
    ttk.Label(
        frame,
        textvariable=description,
        wraplength=750,justify='left'
    ).pack(anchor='w',fill='x',pady=10)

    status: tk.StringVar = tk.StringVar(value='Not attached — load an NES game in the supported Mesen build')
    ttk.Label(
        frame,
        textvariable=status,
        font=('Segoe UI',11,'bold'),
        wraplength=840
    ).pack(anchor='w',pady=8)

    actions: ttk.Frame = ttk.Frame(frame)
    actions.pack(fill='x',pady=6)

    timings: ttk.Frame = ttk.Frame(frame)
    timings.pack(fill='x',pady=6)

    ttk.Label(
        frame,
        text='A/B changes the emulator rules, not the save state. Gameplay continues during both phases.',
        wraplength=750
    ).pack(anchor='w',pady=6)

    random_box: ttk.LabelFrame = ttk.LabelFrame(frame, text='Random performances / combine presets', padding=8)
    random_box.pack(fill='x',pady=8)

    mode:           tk.StringVar = tk.StringVar(value='Classic bursts')
    mode_picker:    ttk.Combobox = ttk.Combobox(random_box, state='readonly', values=MODES, textvariable=mode)
    mode_picker.pack(fill='x',pady=(0,5))

    mode_help: tk.StringVar = tk.StringVar(value='Whole groups alternate with clean gaps.')
    ttk.Label(
        random_box,
        textvariable=mode_help,
        wraplength=820
    ).pack(anchor='w')

    ranges: ttk.Frame = ttk.Frame(random_box)
    ranges.pack(fill='x')

    gap_min:        tk.StringVar = tk.StringVar(value='3')
    gap_max:        tk.StringVar = tk.StringVar(value='10')

    duration_min:   tk.StringVar = tk.StringVar(value='2')
    duration_max:   tk.StringVar = tk.StringVar(value='6')

    for label,var in [
        ('Gap / step min',gap_min),
        ('max',gap_max),
        ('Hold / lifetime min',duration_min),
        ('max',duration_max)
    ]:
        ttk.Label(
            ranges,
            text=label
        ).pack(side='left',padx=(5,2))

        ttk.Entry(
            ranges,
            textvariable=var,
            width=6
        ).pack(side='left')


    ttk.Label(
        ranges,
        text='seconds'
    ).pack(side='left',padx=5)

    counts: ttk.Frame = ttk.Frame(random_box)
    counts.pack(fill='x',pady=4)

    count_min: tk.StringVar = tk.StringVar(value='2')
    count_max=tk.StringVar(value='4')

    ttk.Label(
        counts,
        text='Simultaneous presets: minimum'
    ).pack(side='left')

    ttk.Spinbox(
        counts,
        from_=1,
        to=4,
        textvariable=count_min,
        width=4
    ).pack(side='left',padx=5)

    ttk.Label(
        counts,
        text='maximum'
    ).pack(side='left')

    ttk.Spinbox(
        counts,
        from_=1,
        to=4,
        textvariable=count_max,
        width=4
    ).pack(side='left',padx=5)

    ttk.Label(
        counts,
        text='Compatible rules only; shared patches applied once.'
    ).pack(side='left',padx=8)


    pool_frame: ttk.Frame = ttk.Frame(random_box)
    pool_frame.pack(fill='x',pady=5)

    pool: tk.Listbox = tk.Listbox(pool_frame,selectmode='multiple',exportselection=False,height=5)
    pool.pack(side='left',fill='x',expand=True)

    for effect in EFFECTS.values():
        pool.insert('end',effect['title'])

    pool.selection_set(0,'end')

    pool_scroll: ttk.Scrollbar = ttk.Scrollbar(pool_frame,orient='vertical',command=pool.yview)
    pool_scroll.pack(side='left',fill='y')
    pool.configure(yscrollcommand=pool_scroll.set)

    pool_actions: ttk.Frame = ttk.Frame(pool_frame)
    pool_actions.pack(side='left',padx=6)

    def select_pool(category):
        pool.selection_clear(0,'end')
        for i,effect in enumerate(EFFECTS.values()):
            if (
                    category=='all'
                    or effect['category']==category
                    or (
                        category=='samples'
                        and effect.get('subsystem')=='dmc'
                    )
                    or (
                        category=='envelopes'
                        and effect.get('subsystem')=='envelope'
                    )
            ):
                pool.selection_set(i)

    for label,category in [
        ('Standard pool','all'),
        ('None','none'),
        ('Audio only','audio'),
        ('Visual only','visual'),
        ('Controls only','input'),
        ('Samples only','samples'),
        ('Envelopes only','envelopes')
    ]:
        ttk.Button(
            pool_actions,
            text=label,
            command=lambda c=category:select_pool(c)
        ).pack(fill='x')

    random_status: tk.StringVar = tk.StringVar(value='Select presets above. Pool and timing changes take effect on next Start.')

    ttk.Label(
        random_box,
        textvariable=random_status
    ).pack(anchor='w')

    log: tk.Text = tk.Text(frame,height=8,state='disabled',font=('Consolas',10))
    log.pack(fill='both',expand=True)

    state: dict = {
        'target':       None,
        'session':      None,
        'pids':         [],
        'ab':           None,
        'pulse':        None,
        'ab_running':   False
    }

    def note(text) -> None:
        log.configure(state='normal')
        log.insert('end',text+'\n')

        if int(log.index('end-1c').split('.')[0])>600:
            log.delete('1.0','200.0')

        log.see('end')
        log.configure(state='disabled')

    def chosen(): return list(EFFECTS)[picker.current()]

    def cancel_timers() -> None:
        for key in ('ab','pulse'):
            if state[key] is not None:
                root.after_cancel(state[key])
                state[key]=None

        state['ab_running'] = False
        ab_button.configure(text='Start A/B • 2 seconds')

        random_cycle.stop()

        random_button.configure(text='Start random mode')
        random_status.set('Random mode stopped')

    def fail(exc) -> None:
        cancel_timers()
        status.set('Stopped — '+str(exc))
        note('ERROR: '+str(exc))

    def live_session():
        if not state['target'] or not state['target'].alive():
            raise ValueError('Attach to a running Mesen process first')

        if not state['session']:
            raise ValueError('No verified core attached')

        if ('mesencore.dll',state['session'].base) not in [(n.lower(),b) for n,b in state['target'].modules()]:
            raise ValueError('Core module changed; restart and attach again')

        return state['session']

    def original(cancel=True):
        if cancel: cancel_timers()
        try:
            if state['session']:
                session = live_session()
                n       = session.restore()

                status.set('ORIGINAL hardware rules')
                note(f'Restored {n} code byte(s).')
            return True
        except Exception as exc:
            fail(exc)
            return False

    def modified(cancel=True):
        if cancel: cancel_timers()

        try:
            session = live_session()
            key     = chosen()
            n       = session.apply(key)

            status.set('MODIFIED • '+EFFECTS[key]['title'])
            note(f'Applied {EFFECTS[key]["title"]}: {n} verified byte patch(es).')
            return True
        except Exception as exc:
            fail(exc)
            return False

    def pulse():
        if modified():
            state['pulse'] = root.after(3000,original)

    def ab_tick():
        state['ab'] = None
        if not state['ab_running']: return

        if state['session'] and state['session'].active:
            success = original(False)
        else:
            success = modified(False)

        if success and state['ab_running']:
            state['ab'] = root.after(2000,ab_tick)

    def toggle_ab():
        if state['ab_running']:
            original()
            return

        cancel_timers()
        state['ab_running'] = True
        ab_button.configure(text='Stop A/B and restore')
        ab_tick()

    def random_apply(keys):
        session = live_session()
        n       = session.apply_many(keys)

        titles=' + '.join(EFFECTS[key]['title'] for key in keys)
        status.set('MODIFIED • '+titles)
        note(f'Applied together: {titles} ({n} unique verified byte patches).')

    def apply_selected():
        if not original(): return
        try: random_apply(tuple(list(EFFECTS)[i] for i in pool.curselection()))
        except Exception as exc: fail(exc)

    def random_restore():
        live_session().restore()
        status.set('ORIGINAL hardware rules')

    def random_notice(phase,delay):
        random_status.set(f'{phase} in {delay:.1f}s')

    random_cycle: RandomCycle = RandomCycle(
        root.after,
        root.after_cancel,
        random_apply,
        random_restore,
        random_notice,
        fail
    )

    def can_combine(keys) -> bool:
        try:
            points = merge_points(EFFECTS,keys)
            return len(keys)==1 or len(points)>len(merge_points(EFFECTS,keys[:-1]))
        except ValueError: return False

    def mode_changed(event=None):
        original()
        settings={
            'Classic bursts':  (
                '3',
                '10',
                '2',
                '6',
                'Whole groups alternate with clean gaps.'
            ),

            'Build-up':        (
                '0.5',
                '1.5',
                '3',
                '6',
                'Add one preset each gap until the chosen stack is complete; hold, then restore.'
            ),

            'Stutter':         (
                '3',
                '8',
                '2',
                '5',
                'Switch the chosen group on/off every 150–400 ms during each burst.'
            ),

            'Mutation walk':   (
                '0.5',
                '2',
                '10',
                '20',
                'Add or remove one preset per random step; retained patches stay active. Hold/lifetime sets walk length before a clean reset; minimum count is ignored.'
            ),

            'Rolling overlap': (
                '0.5',
                '1.5',
                '4',
                '8',
                'Add effects at random gaps; each has its own lifetime. Maximum count applies; minimum is ignored.'
            )
        }

        a, b, c, d, help_text = settings[mode.get()]
        for var, value in zip(
                (gap_min,gap_max,duration_min,duration_max),
                (a,b,c,d)
        ):
            var.set(value)

        mode_help.set(help_text)

    def toggle_random():
        if random_cycle.running:
            original()
            return

        if not original(): return

        try:
            live_session()
            keys: list[str] = [list(EFFECTS)[i] for i in pool.curselection()]
            minimum = 1 if mode.get() in ('Rolling overlap','Mutation walk') else int(count_min.get())

            random_status.set('Preparing compatible groups…')
            root.update_idletasks()

            groups = compatible_groups(EFFECTS, keys, minimum, int(count_max.get()))
            random_cycle.start(
                keys,
                (gap_min.get(), gap_max.get()),
                (duration_min.get(), duration_max.get()),
                groups=groups,
                mode=mode.get(),
                compatible=can_combine
            )

            note('Available simultaneous counts: '+', '.join(map(str,groups)))
            if random_cycle.running:
                random_button.configure(text='Stop random and restore')
                note(f'{mode.get()} started: {len(keys)} presets, gap/step {gap_min.get()}–{gap_max.get()}s, hold/lifetime {duration_min.get()}–{duration_max.get()}s.')
        except Exception as exc: fail(exc)

    def refresh():
        found=[]
        for proc in psutil.process_iter(['pid','name']):
            if (proc.info['name'] or '').lower() in ALLOWED:
                found.append((
                    proc.info['pid'],
                    proc.info['name']
                ))

        state['pids'] = found
        process['values'] = [f'{name} — PID {pid}' for pid,name in found]
        process.set('')

        if found: process.current(0)
        note(f'Found {len(found)} Mesen process(es).')

    def attach():
        cancel_timers()
        target = None
        try:
            index = process.current()
            if index<0:
                raise ValueError('Start Mesen, load an NES game, then refresh')

            if state['session'] and state['target'].alive():
                state['session'].restore()

            if state['target']:
                state['target'].close()

            state['target'] = state['session'] = None
            target = Target(api,state['pids'][index][0])
            cores = [base for name, base in target.modules() if name.lower() == 'mesencore.dll']  # This is some kinda C voidptr I think

            if len(cores)!=1:
                raise ValueError('Load a game first: exactly one MesenCore.dll must be loaded')

            session = LabSession(target, cores[0])
            state['target']  = target
            state['session'] = session

            status.set('ORIGINAL • exact Mesen CE 2.2.1 core verified')
            note('Full loaded code hash matched. NES audio experiments are ready.')
            note('Visual experiments target the standard NES PPU; disable HD packs for those.')
        except Exception as exc:
            if target:
                target.close()
            fail(exc)

    def selection(event=None):
        original()
        description.set(EFFECTS[chosen()]['description'])

    def close():
        cancel_timers()

        try:
            if state['session'] and state['target'].alive():
                state['session'].restore()
        except Exception as exc:
            messagebox.showwarning('Restart Mesen',f'Could not restore all code: {exc}\nRestart Mesen for a clean reset.')

        if state['target']:
            state['target'].close()
        root.destroy()

    ttk.Button(row,text='Refresh processes',command=refresh)            .pack(side='left')
    ttk.Button(row,text='Attach and verify build',command=attach)       .pack(side='left',padx=8)
    ttk.Button(actions,text='Apply modified rules',command=modified)    .pack(side='left')
    ttk.Button(actions,text='Restore original • Esc',command=original)  .pack(side='left',padx=8)
    ttk.Button(timings,text='Pulse for 3 seconds',command=pulse)        .pack(side='left')

    ab_button: ttk.Button = ttk.Button(timings,text='Start A/B • 2 seconds',command=toggle_ab)
    ab_button.pack(side='left',padx=8)

    random_button: ttk.Button = ttk.Button(random_box,text='Start random mode',command=toggle_random)
    random_button.pack(anchor='w',pady=5)

    ttk.Button(
        random_box,
        text='Apply selected together (up to 4)',
        command=apply_selected
    ).pack(anchor='w')

    mode_picker.bind('<<ComboboxSelected>>',mode_changed)
    picker.bind('<<ComboboxSelected>>',selection)

    root.bind('<Escape>',lambda event:original())
    root.protocol('WM_DELETE_WINDOW',close)

    description.set(EFFECTS[chosen()]['description'])
    refresh()
    root.mainloop()

if __name__=='__main__':
    try: main()
    except ImportError as exc: raise SystemExit(f'{exc}\nInstall dependencies: py -3 -m pip install -r requirements.txt')
