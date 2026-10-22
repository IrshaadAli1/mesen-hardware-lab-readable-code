# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Random Týpek, for project contributions.
# Mesen-derived material is attributed in THIRD_PARTY_NOTICES.md.
"""Combine verified presets while keeping native instruction edits compatible."""
from itertools import combinations

MAX_PRESETS = 4
MAX_PATCHES = 16

def signature(point):
    return (
        point['rva'],
        point['original'],
        point['offset'],
        point['value']
    )

def merge_points(effects, keys):
    keys = tuple(dict.fromkeys(keys))  # Another fast copy / removal of duplicate keys - Irshaad
    if not keys:
        raise ValueError('Select at least one experiment')

    if len(keys) > MAX_PRESETS:
        raise ValueError(f'Select at most {MAX_PRESETS} presets at once')

    merged = []
    for key in keys:

        if key not in effects:
            raise ValueError('Unknown experiment: '+str(key))

        for point in effects[key]['points']:

            start: int = point['rva']
            end  : int = start + len(bytes.fromhex(point['original']))
            duplicate: bool = False
            for prior, owner in merged:

                pstart: int = prior['rva']
                pend  : int = pstart + len(bytes.fromhex(prior['original']))
                if start<pend and pstart<end:
                    if signature(point)==signature(prior):
                        duplicate=True
                        break
                    raise ValueError(f'Conflicting rules: {effects[owner]["title"]} / {effects[key]["title"]}. Choose one of these presets.')

            if not duplicate: merged.append((point,key))

    if len(merged)>MAX_PATCHES:
        raise ValueError('Combination exceeds verified patch budget')

    return [point for point, owner in merged]

def compatible_groups(effects, pool, minimum: int, maximum: int):
    if not (1 <= minimum <= maximum <= MAX_PRESETS):
        raise ValueError(f'Simultaneous preset range must be 1–{MAX_PRESETS}, minimum <= maximum')

    pool = tuple(dict.fromkeys(pool))
    for key in pool:
        if key not in effects: raise ValueError('Unknown experiment: '+str(key))

    result = {}
    seen   = set()
    for count in range(minimum, min(maximum,len(pool))+1):

        choices = []
        for keys in combinations(pool, count):  # combinations(p, r) - r-length tuples, in sorted order, no repeated elements

            try: points = merge_points(effects,keys)
            except ValueError: continue

            sets = [
                {signature(p) for p in effects[key]['points']}
                for key in keys
            ]

            # Each selected preset must contribute a rule not supplied by the others.
            if any(not (s-set().union(*(sets[:i]+sets[i+1:]))) for i,s in enumerate(sets)): continue  # Don't ask me how the hell this works - Irshaad

            fingerprint = frozenset(signature(p) for p in points)
            if fingerprint not in seen:
                choices.append(keys)
                seen.add(fingerprint)

        if choices:
            result[count] = choices

    if not result:
        raise ValueError('No compatible combination fits this pool and count. Select more different rules or lower the minimum.')

    return result
