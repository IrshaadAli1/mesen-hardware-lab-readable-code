from winmem import Target
from hardware_lab import LabSession, Patch
from typing import TypeAlias, Any, TypedDict, Callable


class Point(TypedDict):
    rva: int
    original: str
    offset: int
    value: int
    label: str

    original_instruction: str
    modified_instruction: str

    evidence: str


class Effect(TypedDict):
    id:             str
    title:          str
    description:    str
    points:         list[Point]
    category:       str


class State(TypedDict):
    target:     Target     | None
    session:    LabSession | None
    pids:       ProcessIDs
    ab:         Identifier | None
    pulse:      Identifier | None
    ab_running: bool



Key        : TypeAlias = str
EffectsDict: TypeAlias = dict[Key, Effect]
CVoidPtr:    TypeAlias = Any
NumberLike:  TypeAlias = int | float
Length:      TypeAlias = int
Keys:        TypeAlias = list[Key] | tuple[Key, ...] # Often keys of EffectsDict (can be tuple or list)
Patches:     TypeAlias = list[Patch]
PatchAddress:TypeAlias = int


# Random Cycle (and Tkinter) stuff I guess
Identifier: TypeAlias = str
After:      TypeAlias = Callable[[int, Callable[[...], object], ...], Identifier]
Cancel:     TypeAlias = Callable[[Identifier], None]


# Combinations stuff I guess
MergedPoints:      TypeAlias = list[Point]
PointSignature:    TypeAlias = tuple[int, str, int, int]
Fingerprint:       TypeAlias = frozenset[PointSignature]


CombChoice:        TypeAlias = tuple[str, ...]
CombChoices:       TypeAlias = list[CombChoice]
CompatibleGroups:  TypeAlias = dict[int, CombChoices]


# WinMem stuff I guess
OriginalPatches:   TypeAlias = dict[PatchAddress, tuple[Patch, bytes]]
PatchChanges:      TypeAlias = list[tuple[int, int, int, str]]
RestoreCount:      TypeAlias = int
ProcessID:         TypeAlias = int
ProcessHandle:     TypeAlias = int
ProcessName:       TypeAlias = str
ProcessIDs:        TypeAlias = list[tuple[ProcessID, ProcessName]]