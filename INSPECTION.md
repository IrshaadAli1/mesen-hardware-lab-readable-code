# v14 additions

The five v13 visual presets are now standard by user request. Patch bytes and their sprite-hit caveat are unchanged. There is no experimental category in v14.

New rules:
- 19DDE7 and 19DE37: AND AL,7 -> AND AL,3. Original decrement followed by mask produces phase3,2,1,0, inside the existing eight-step table.
- 19DE9B: AND DL,31 -> AND DL,3. The original increment now traverses four samples. All outputs stay within the original 32-entry table.
- 19C972 and 19C90F: normal and short noise feedback constants ->2. Recurrence stays `(state>>1)|(((state^(state>>2))&1)<<14)`. Valid domain remains0..32767. Seed1 has period4599; other seeds need not.
- 19EEBC A report physical ID7 ->1 and 19EEFE Down report ID1 ->7 for A/Down exchange.
- 19EEBC A report ID7 ->0 and 19EEC6 B report ID6 ->1 for vertical-action coupling. Up/Down report bits remain unchanged; Start/Select untouched.

All changes use existing instruction sites, lengths and register operands. Conflict handling prevents two presets from requesting different values at one instruction. Effects remain game-dependent. Native bounds and restoration checks do not substitute for live gameplay/listening.

The following v13 section is historical; its experimental classification was removed in v14.

---

# v13 additions

Exact original DLL and source commit remain those documented below.

- F044B `sar r11d,15` -> 14; F044F `sar eax,14` -> 15. Background low/high samples remain masked to 1 and 2 before OR. These inputs also feed sprite-zero-hit evaluation. Explicit experimental classification; excluded from standard pools.
- 1932CD `ror al,4` -> 2; 1932D3 `ror bl,4` -> 2 or 6. Source-matched `LoadSprite` horizontal reversal, reached from LoadSpriteTileInfo at 19152D -> 192F10. Original in-range and mirror checks remain. Initial rotation followed by the original pair/bit swaps is a permutation of the eight row bits. Pattern reads have completed; coordinate stores and shifter scheduling remain unchanged. Only horizontally mirrored sprite rows change. Sprite-zero-hit behavior can change.
- Mutation walk changes one preset per tick, then explicitly resets at the walk deadline. Native transitions remove obsolete patches and add missing ones, retaining matching edits without writes. Original code restoration remains independent of gameplay state.

Five proposed stateful features remain unimplemented: input echoes, gradual channel drift, delayed palette writes, envelope cross-talk and moving scanline bands. Runtime hooks could implement them without rebuilding Mesen, but are not part of the verified patch backend.

Validation: 46 unit tests; 53 preset round trips and 231,658 compatible stack round trips against the mapped original DLL; original full-image hash recovered. Isolated Unicorn execution tests 24,576 bitplane cases and 9,216 sprite cases. No live Windows GUI or gameplay validation was available.

---

# v12 hardware-rule verification

## Exact target

Mesen CE 2.2.1, source commit `20ba206cef5ba207c21203176d02cb9f43dda9fb` as recorded in the uploaded EXE. Embedded MesenCore.dll SHA-256: `55a5f918c8ead04d4a401fc12f0ce9e4de69bebbc484f1ca3a7c018916b1fad1`.

Attachment verifies the loaded core's PE timestamp, image size, and entire `.text` SHA-256. This code section has no base relocations, so the mapped code can be compared directly. The per-instruction original bytes are checked again before writes, and patched bytes are verified afterward. Restoration rejects unrelated code changes. All offsets below are relative virtual addresses, not fixed process addresses.

## Sound-generation sites

### Triangle sequencer — 0x19DE9B

`AND DL,0x1F` becomes `AND DL,0x0F` or `AND DL,0x07`.

The site is in the inlined TriangleChannel::Run portion of NesApu::Run. Source order and disassembly agree on square1, square2, noise, triangle, and DMC execution. Immediately before this mask, DL holds the incremented sequence position. Immediately afterward it is stored to the sequence-position field and used to index the 32-sample triangle table.

The original sequence is 15 down to 0, then 0 up to 15. Mask 15 repeats only the descending 16 samples; mask 7 repeats the first eight. Neither can exceed the original table bounds. Timer progress, channel enable checks, length/linear counters, and audio-buffer indexing are unchanged.

The actual INC DL + AND DL instruction sequences were executed in isolated x64 emulation for all 256 input-byte values, for both replacement masks. Results matched the bounded sequence formula.

### Noise feedback — 0x19C972 and 0x19C90F

The low immediate byte in `MOV ECX,1` and `MOV R12D,6` becomes 5. These select the normal/short-mode tap in NoiseChannel::Run at 0x19C8F0, directly called by NesApu::Run.

The recurrence is:

`next = (state >> 1) | (((state ^ (state >> tap)) & 1) << 14)`

For seed 1, tap 1 has period 32767, tap 6 has period 93, and tap 5 has period 35. The entire nonzero 15-bit input-state space was checked to remain nonzero and below 32768 after one tap-5 update. The actual x64 recurrence was executed for both mode-flag states and representative registers, confirming the new tap is selected in both paths. Timer and sample-output logic were not patched.

## PPU sites

RTTI and the DefaultNesPpu vtable resolve Run at 0xEFC00. Its pixel path matches NesPpu::GetPixelColor and DefaultNesPpu::DrawPixel in the exact source. The relevant sprite-zero-hit checks and flag update occur before the following patch sites.

| RVA | Original | Replacement | Rule |
| --- | --- | --- | --- |
| 0xF0675 | JNE 0xF0689 | JE 0xF0689 | Reverse sprite BackgroundPriority condition when the background pixel is opaque |
| 0xF06A9 | TEST DIL,3 | TEST DIL,1 or TEST DIL,2 | Change which color bits permit the selected palette color rather than backdrop |
| 0xF069A | SETB AL | SETAE AL | Select the other of previous/current background tile palettes |

The priority patch changes only the condition opcode, not instruction length or branch displacement. The two existing paths still lead to sprite or background color selection. The background-empty shortcut remains unchanged. Palette-cutout variants choose either the already-bounded original palette index or zero. The palette-phase patch still selects only one of two existing palette bytes.

The actual modified x64 instructions were executed in isolation: both ZF outcomes for the priority branch, both CF outcomes for palette phase, and all 32 color-index values for each cutout variant. Results matched the intended decisions. No complete emulator execution was performed.

## Validation boundaries

The sixteen v6 presets were exercised against a mapped copy of the actual supplied core at a synthetic relocated base. The full mapped-image hash matched its starting value after every restore. Combined-effect failure recovery and repeated preset switching are covered by the included tests.

Instruction decoding and isolated execution establish the local patch semantics, not complete emulator stability. Source matching establishes the intended code role; it is not a substitute for live gameplay tests. Modified audio phase, queued samples, and any other runtime state are not reversed by restoring code.

## Exact source references

- https://github.com/nesdev-org/MesenCE/blob/20ba206cef5ba207c21203176d02cb9f43dda9fb/Core/NES/APU/TriangleChannel.h
- https://github.com/nesdev-org/MesenCE/blob/20ba206cef5ba207c21203176d02cb9f43dda9fb/Core/NES/APU/NoiseChannel.h
- https://github.com/nesdev-org/MesenCE/blob/20ba206cef5ba207c21203176d02cb9f43dda9fb/Core/NES/APU/NesApu.cpp
- https://github.com/nesdev-org/MesenCE/blob/20ba206cef5ba207c21203176d02cb9f43dda9fb/Core/NES/NesPpu.cpp
- https://github.com/nesdev-org/MesenCE/blob/20ba206cef5ba207c21203176d02cb9f43dda9fb/Core/NES/DefaultNesPpu.h

## v6 additions

- 0xF0675: `75 12` -> `75 00` for front sprites. Both taken and untaken routes reach 0xF0677, the existing sprite path. This changes only the displacement byte to a verified boundary.
- 0xF0675: `75 12` -> `EB 12` for behind sprites. Unconditional jump to existing background path 0xF0689. The transparent-background shortcut at 0xF0663 remains intact.
- 0xF06A9: mask 31 allows any nonzero palette index; output index is still 0..31.
- 0xF06BA: `48 0F 45 C8` -> `48 0F 44 C8` changes CMOVNE RCX,RAX to CMOVE RCX,RAX. Both options are the existing palette index or zero.
- Noise immediates at 0x19C972 and 0x19C90F can also become 3. Seed-1 period is 63, and all nonzero 15-bit states remain nonzero and in bounds.
- Three additional combination presets reuse these sites without overlap or conflicting mutations.

New branch instructions were executed for both ZF values, palette rules for all 32 indices, and tap-3 recurrence for both noise modes and representative register states. All matched expected local semantics. There was no full Windows emulator or GUI execution.

The scheduler operates only on preset IDs. It restores between bursts, never repeats immediately with multiple options, validates finite ordered timing ranges, and uses a generation counter to discard stale callbacks. Errors stop scheduling and attempt restoration; a failed restoration is explicitly reported. Thirteen unit tests pass, including 100 synthetic bursts and their clean gaps. This is callback testing, not a wall-clock accuracy guarantee.

## v7 instruction additions and combinations

| RVA | Original | v7 replacement | Bound |
| --- | --- | --- | --- |
| 0xF06A9 | TEST DIL,3 | TEST DIL,16 or TEST DIL,4 | Existing palette index or zero, always 0..31 |
| 0xF0697 | CMP ECX,8 | CMP ECX,4 or CMP ECX,12 | SETB/SETAE still produces 0 or 1 |
| 0xF0691 | AND ECX,7 | AND ECX,3 | Fine phase becomes 0..3; only influences palette choice |
| 0x19DE99 | INC DL | DEC DL | Rising-saw preset also installs AND DL,15 at 0x19DE9B |
| 0x19C972 / 0x19C90F | Noise tap constants 1/6 | Both become 9 | Nonzero 15-bit state remains in range; seed-1 period 93 |

These addresses and original instruction bytes were verified against the exact supplied DLL. Isolated native execution checked all 256 triangle input bytes, all 32 palette-color indices, palette compare inputs 0..15, phase inputs 0..255, and both noise modes with representative states. Tap 9's period and all 32,767 nonzero input-state bounds were checked separately.

The combination engine compares entire instruction ranges. Different edits to overlapping instructions are rejected, including edits to different bytes within the same instruction. Identical edits are deduplicated. Disjoint edits are allowed; all expected original instructions are checked before applying the first patch. Existing rollback records cover every unique patch. Group application is sequential, not an atomic transaction; each intermediate subset uses the same bounded instruction semantics.

Random enumeration excludes redundant presets, deduplicates equivalent resulting patch sets across counts, and chooses only verified compatible groups. With all 23 presets and requested count 2..4, there are 3,139 distinct groups. Every group was exercised in sparse-memory tests and against the mapped supplied DLL. The final whole-image hash matched after restoring all groups. Nineteen unit tests pass. No live Windows emulator or GUI testing was possible here.

## v8: pulse generator and sprite ink

The shared SquareChannel::UpdateOutput routine at 0x19BFA0 checks mute/envelope state, loads duty from object+0x6A and phase from object+0x6B, and uses the following lookup. The 32-byte table at RVA 0x5F0670 exactly matches SquareChannel.h's four eight-entry duty sequences. The manifest stores its original bytes and attachment verifies them.

| RVA | Original | New forms | Bound |
| --- | --- | --- | --- |
| 0x19BFF2 | LEA RDX,[RAX+RCX*8] | [RCX+RAX*4], [RAX+RAX*2], [RAX+RAX] | With phase RAX=0..7 and duty RCX=0..3, maxima 31,21,14 |
| 0x19DDE7 | AND AL,7 | AND AL,6 | Pulse 1 phases 0,2,4,6 |
| 0x19DE37 | AND AL,7 | AND AL,6 | Pulse 2 phases 0,2,4,6 |
| 0xF067F | ADD DIL,[RCX+RAX+0x1D4] | ADD DIL,[RCX+RAX+0x1D0] | Same sprite object; boolean priority replaces palette offset, yielding indices 1..4 |

These are explicit reviewed addressing changes, unlike earlier edits that retained every operand address. Pulse table indexing changes within the original 32 bytes; sprite selection reads an existing boolean within the same five-byte sprite record. The read of that priority field is corroborated by the CMP at 0xF066D. No new memory is allocated or addressed outside these existing objects. Sprite-zero-hit processing remains before the sprite color patch.

Actual x64 execution from 0x19BFF2 through 0x19C008 (exclusive) checked the complete index, table read and volume multiplication for all 4 duties x 8 phases x 16 volumes in each of the three lookup modes. Output stayed 0..15 and matched the expected table patterns. Both phase masks were executed for all 256 input bytes. The sprite instruction was executed for all 64 slots, both priority states and all three nontransparent color values.

All 29 presets and 12,604 distinct compatible stacks of 2..4 presets were applied and restored against the mapped supplied DLL. Its final whole-image hash matched the original. Twenty-three tests pass, including a new changed-duty-table refusal check. All checks are offline; no live Windows gameplay, perceptual audio comparison or GUI test was performed.

## v9: controller report source selection

NesController RTTI/vtable identifies RefreshStateBuffer at RVA 0x19ED50, which calls ToByte at 0x19EEA0 and stores AL at object offset 0x60. ReadRam at 0x19EF70 reads that same byte, shifts it and fills the high bit. The function's eight IsPressed calls and bit packing match the exact source's A,B,Select,Start,Up,Down,Left,Right sequence. IsPressed at 0xE3240 uses the input bit index to select a valid bit in the device state.

| RVA | Original | Role |
| --- | --- | --- |
| 0x19EEBC | MOV DL,7 | A report bit source |
| 0x19EEC6 | MOV DL,6 | B report bit source |
| 0x19EEFE | MOV DL,1 | Down report bit source |
| 0x19EF0B | MOV DL,2 | Left report bit source |
| 0x19EF18 | MOV DL,3 | Right report bit source |

v9 changes only these immediate argument bytes. Every replacement remains within valid button IDs 0..7. It does not patch the IsPressed implementation, locks, report-packing operations, strobe, serial-shift logic, Start/Select source calls, or CPU opcode handlers. The manifest records each report mapping explicitly.

Isolated x64 execution ran the actual ToByte body for the original and every compatible input-only configuration (13 configurations including original) across all 256 physical button combinations. IsPressed was replaced by a deterministic test stub; this is not full input-device emulation. All requested indices matched the mapping, every result matched expected report packing, and Start/Select stayed unchanged.

All 35 presets and 31,270 distinct compatible stacks of 2..4 presets were applied/restored against the mapped supplied DLL. Its final full-image hash matched the original. Twenty-six unit tests pass. Live Windows input, GUI behavior and game responses have not been tested.

Source reference: NesController.h and BaseControlDevice.h from the exact source commit recorded above.

## v10: DMC decoding rules

The exact source DeltaModulationChannel.cpp matches the native Run routine at RVA 0x40AB00, directly called by NesApu::Run. The selected interval handles bit direction and level updates, before decrementing the bit counter at 0x40ABBB and before buffer refill/DMA bookkeeping.

| RVA | Original | Replacement |
| --- | --- | --- |
| 0x40AB8E | CMOVE ECX,EAX | CMOVNE ECX,EAX |
| 0x40AB96 | CMOVE EAX,R12D | CMOVNE EAX,R12D |
| 0x40ABA4 | JE 0x40ABB0 | JNE 0x40ABB0 |
| 0x40ABAB | ADD CL,2 | ADD CL,1 or XOR CL,2 |
| 0x40ABB5 | SUB CL,2 | SUB CL,1 or XOR CL,2 |

The first pair swaps the shifter direction and bit mask relative to the existing configuration flag; both are patched together. The next instruction exchanges the meanings of zero and one bits. The last two sites alter the delta arithmetic. All instructions retain length, register operands and original memory operands; the conditional branch retains its destination.

The original level comparisons remain: upward operations run only at levels <=125, downward operations only at levels >=2. A +1/-1 replacement cannot escape 0..127 under those guards. XOR 2 preserves the high bits, so an input in 0..127 stays there. This remains true for mixed/intermediate subsets, avoiding dependence on atomic multi-instruction application. No DMC timing, sample addresses, bit counters, refill, DMA, or interrupt instructions are patched.

Actual x64 execution ran 0x40AB5D through 0x40ABBB (exclusive), using a synthetic object/configuration pointer chain. Thirty-five original/compatible DMC configurations were tested across every output level 0..127 and both input bits for each configuration flag. Every shifter byte 0..255 was also tested under both configuration flags at level 64, checking shifted state, selected bit mask and level update. Results matched the bounded decoder model.

All 41 individual presets and 67,655 distinct compatible stacks of 2..4 presets applied/restored against the mapped supplied DLL. Its final full-image hash matched. Thirty unit tests pass, including apply/restore-prefix bounds and simulated DMC write failures. No live Windows gameplay, GUI test or listening comparison was performed.

Source: https://github.com/nesdev-org/MesenCE/blob/20ba206cef5ba207c21203176d02cb9f43dda9fb/Core/NES/APU/DeltaModulationChannel.cpp

## v11: temporal composition

No new native instructions or preset definitions were introduced. The 41-effect manifest and exact core code hash are unchanged from v10. Build-up, Stutter and Rolling overlap use the same validated LabSession apply_many/restore operations.

Each scheduler instance retains one pending timer and a generation token. Stopping cancels the timer and invalidates queued stale callbacks. GUI stop/mode change additionally restores patches. Errors stop scheduling and attempt restoration; recovery failures are reported. Build-up applies nested subsets of a prevalidated group. Stutter uses a monotonic total-duration deadline. Rolling tracks independent monotonic deadlines per preset, checks instruction compatibility and patch budget before each addition, and keeps existing deadlines unchanged when the active set changes.

Active-set changes still restore/reapply byte patches sequentially; they are not atomic changes across native threads. Rolling's unexpired effects can therefore briefly pass through original code during an update. Scheduling is best effort, and queued audio can delay perceived transitions.

Thirty-seven tests pass. Seven new performance tests cover stage growth, stutter timing, independent rolling expiration, capacity/conflict checks, stale callback rejection, restart between modes, and failure recovery for every mode. They use a synthetic clock and LabSession backed by simulated memory. No live Windows GUI or gameplay timing verification was performed.

## v12: envelopes

NesApu::FrameCounterTick at RVA 0x19D6F0 matches the exact source's ordered pulse1, pulse2, triangle-linear-counter, noise envelope updates, followed by optional half-frame length/sweep work. ApuEnvelope.h matches the fields and branches: +0x21 volume, +0x22 start, +0x23 signed divider, +0x24 decay counter, and +0x3E length halt/loop flag.

| RVA | Original | Replacement |
| --- | --- | --- |
| 0x19D702, 0x19D749, 0x19D7AD | SUB [channel+0x23],1 | SUB [channel+0x23],4 |
| 0x19D73A, 0x19D778, 0x19D7DC | MOV [channel+0x24],15 | MOV [channel+0x24],7 |
| 0x19D71B, 0x19D75E, 0x19D7C2 | DEC AL | DEC AH |
| 0x19BFD7 | JE 0x19BFE0 | JNE 0x19BFE0 |
| 0x19C9EC | JE 0x19C9F4 | JNE 0x19C9F4 |

The divider input is 0..15. Subtracting 4 yields -4..11, and the existing JNS/reload logic immediately replaces negative values with the 0..15 volume. Counter decrement remains guarded above zero. Restart height 7 is also within range.

Frozen fades redirect the decrement from AL to AH, leaving the counter in AL unchanged for the existing store. This is an explicitly reviewed register-operand change. AH is dead along each subsequent path before any relevant EAX use: later channel operations reload EAX; the half-frame branch reloads EAX before its length operations; the remaining return is void. DEC flags are overwritten before use. The actual complete envelope block was executed to check the resulting channel states.

The volume-mode branches exchange the existing volume/counter fields after the original length/mute guards. Both sources remain in 0..15. Native selection tests check every volume/counter pair, both mode flags and both length-active states.

A model exhaustively checks valid volume, start, divider, counter and loop states across speed 1/4, restart 7/15 and frozen/normal variants. Actual x64 execution of 0x19D6F0..0x19D7E0 tested 31 valid configurations, all counter levels, representative volume/divider values (0,1,7,15 and 0,1,3,15), both start states and both loop states, checking all three channels together.

All 48 individual presets and 148,176 distinct compatible stacks of 2..4 presets were applied/restored against the mapped supplied DLL. Its final full-image hash matched the original. Forty unit tests pass, including the existing performance modes and new envelope bounds, sequences and failure rollback. No live Windows gameplay, GUI or listening test was performed.

Sources: retained ApuEnvelope.h, SquareChannel.h, NoiseChannel.h and NesApu.cpp at the exact source commit recorded above.
