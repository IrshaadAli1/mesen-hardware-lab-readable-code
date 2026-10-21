from typing import TypeAlias, Any, TypedDict, Iterable, Callable


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
    id: str
    title: str
    description: str
    points: list[Point]
    category: str


EffectsDict: TypeAlias = dict[str, Effect]
CVoidPtr:    TypeAlias = Any
NumberLike:  TypeAlias = int | float
Length:      TypeAlias = int
Keys:        TypeAlias = Iterable[str]  # Often keys of EffectsDict (can be tuple or list)