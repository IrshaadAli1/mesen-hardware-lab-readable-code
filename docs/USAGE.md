# Mesen Hardware Lab v14 — Impossible NES

59 named hardware-rule presets for the supported Mesen CE 2.2.1 x64 core, with five scheduling modes and up to four compatible presets active together. No Mesen source changes, rebuild, DLL replacement or ROM edits are required.

## New in v14

All five formerly experimental bitplane and sprite-pixel presets now belong to the standard pool: selected on startup, included by Standard pool and Visual only, and available to random performances. The Experimental button and title prefixes are removed. Their behavior is unchanged: they can still alter sprite-zero-hit timing and disrupt games that use it. Promotion does not imply additional live stability testing.

Six new presets are also included by default:

| Preset | Change |
| --- | --- |
| Pulse 1 four-step melody | Cycle pulse 1 through phases 3,2,1,0 |
| Pulse 2 four-step melody | Independently shorten pulse 2 the same way |
| Four-step triangle bass | Repeat the first four triangle samples |
| Long repeating percussion | Feedback tap 2 in both noise modes; seed-1 period 4599 |
| A and Down exchange | Physical A reports Down; physical Down reports A |
| Vertical movement also presses A/B | Up reports Up+A; Down reports Down+B; physical A/B no longer drive their action bits |

These work with random intervals, Mutation walk and simultaneous compatible effects. The pulse/triangle presets shorten sequence periods without changing game tempo or channel timers. Some waveform combinations become quiet, constant or silent. Noise differences depend on the passage being played; no live listening test was available.

## v13: implemented scope

| Requested idea | Status |
| --- | --- |
| Mutation walks | Implemented: add or remove one preset per random step, retaining other patches continuously |
| Split bitplanes | Implemented: independent low/high background-plane sample offsets, or both in opposing directions |
| Scrambled sprite pixels | Implemented for horizontally mirrored sprite rows: common or different permutations of the two planes; coordinates remain unchanged |
| Controller echoes | Not implemented; needs retained input history and a poll-time hook |
| Gradual audio clock drift | Not implemented; needs per-channel evolving parameters and verified timer integration |
| Delayed palette changes | Not implemented; needs palette-write history and controlled replay |
| Channel cross-talk | Not implemented; needs cross-channel state access at the right update point |
| Moving scanline bands | Not implemented; needs scanline-aware gating rather than an external wall-clock timer |

The five remaining ideas could potentially use injected runtime hooks without changing Mesen's source. They are outside this release's verified single-byte patch system. This release implements three of the eight ideas; it does not claim the other five require source changes.

Choose **Mutation walk** to evolve the selected pool at random 0.5–2 second intervals. Maximum simultaneous count applies; minimum count is ignored. Each step adds or removes exactly one preset, avoiding immediate backtracking when alternatives exist. The walk lasts a random 10–20 seconds by default, then restores and starts another after a gap. A reset at that deadline may remove multiple presets together. A bundled preset can alter multiple native rules. Hold/lifetime sets the walk duration, not an individual effect lifetime.

Shared and retained patches stay in place during Mutation walk, Rolling overlap and Build-up transitions. Reapplying the same stack performs validation without rewriting its bytes. Conflicts are checked before writes; write failures attempt to restore all owned patches.

The bitplane and sprite-pixel presets are now included by **Standard pool**, **Visual only**, and the initial selection. They can combine with existing audio and controller effects. Sprite permutations only affect the horizontal-mirror path. These five visual presets can change sprite-zero-hit timing; restoring code does not rewind gameplay.


## Run

1. Extract this ZIP into a new folder. Use 64-bit Python on Windows.
2. Install dependencies: `py -3 -m pip install -r requirements.txt`
3. Close earlier corruptors and restart Mesen to clear their patches.
4. Load an NES game in your supported Mesen CE 2.2.1 build. For visual effects, use the standard renderer without HD packs.
5. Run `Start.bat`. The title should say **Mesen Hardware Lab v14**.
6. Select Mesen and click **Attach and verify build**. The core DLL is found automatically in the running process.
7. Click **Start random mode**.

Default **Classic bursts** behavior: clean gap of 3–10 seconds, then **2–4 compatible presets together for 2–6 seconds**, then restore and repeat. Both timing ranges and simultaneous preset count are editable. The first phase is a clean gap.

The public package excludes the two optional Unicorn verification scripts. Native validation results below describe earlier development checks, not scripts shipped in this release.

This package contains no Mesen executable, core DLL, or ROM. Other core builds fail the exact code-hash check.

## Earlier additions from v12: envelopes and articulation

| Preset | What changes |
| --- | --- |
| Pulse 1 fast fades | First pulse envelope divider advances by four per tick instead of one |
| Pulse 2 fast fades | Same change for the second pulse channel, independently selectable |
| Noise fast fades | Faster decay/loop cycles for noise percussion |
| Pulse volume modes exchange | Swap fixed-volume and decay-counter output for pulse channels |
| Noise volume modes exchange | Swap those two volume sources for noise percussion |
| Short envelope cycles | Pulse/noise envelope resets and loops start at 7 instead of 15 |
| Frozen fades | Hold the current pulse/noise envelope level between resets |

Click **Envelopes only** to fill the random pool with these presets. All five performance modes support them. For a useful manual combination, click None and select **Pulse volume modes exchange + Pulse 1 fast fades + Pulse 2 fast fades + Short envelope cycles**, then Apply selected together.

Automatic envelope changes can be inaudible when a game uses fixed volume. The volume-mode presets exchange those sources, so they can make previously steady notes fade while making previously envelope-driven notes steady. Effects depend on the song. The shared pulse volume-source routine may also affect expansion-audio callers using SquareChannel.

Fast fades change divider progress, not frame-clock or game tempo. Frozen fades preserve the envelope level but do not override channel mute/length checks, and notes can still stop. A frozen zero level remains silent until a reset or another state change. Short cycles take full effect on the next envelope reset/loop; they do not immediately clamp an existing level.

All counter and output values stay within 0..15. Restoring native code does not restore an old envelope phase or level; normal ticking and subsequent note resets determine recovery. Most presets can be combined, though speed changes have no audible effect while the same decay counter is frozen.

## Performance modes

Choose a mode from the dropdown above the timing controls, then click **Start random mode**. Changing modes stops and restores the previous performance and loads useful timing defaults. Edit those values afterward if desired.

| Mode | Behavior | Defaults |
| --- | --- | --- |
| Classic bursts | Whole compatible group on, then clean gap | Gap 3–10 s, hold 2–6 s |
| Build-up | Add one preset per stage, hold the completed stack, then restore all | Stage/clean gap 0.5–1.5 s, final hold 3–6 s |
| Stutter | Toggle the chosen stack between original and modified rules every 150–400 ms within the burst | Clean gap 3–8 s, total burst 2–5 s |
| Rolling overlap | Introduce one effect at random gaps; each expires independently while others continue | Addition gap 0.5–1.5 s, per-effect lifetime 4–8 s |

**Build-up** starts at one preset even when the minimum count is higher; the count range selects the final stack size. It uses the gap range both for the initial clean interval and spacing between additions. The hold range applies once the full stack has been reached.

**Stutter** uses the hold range for total burst length, not the length of each flash. Its internal 150–400 ms on/off timing is randomized. Short bursts may end before more than one toggle. Audio already queued by Mesen can blur these transitions; this mode deliberately causes rapid picture/audio changes.

**Rolling overlap** uses only the maximum count; the minimum is ignored. Actual active count varies from zero to that limit. If the limit is reached or no compatible candidate fits, it waits for later events rather than forcing a conflicting addition. There is no guaranteed clean gap between additions. An effect's deadline is unchanged when another joins. Shared patches remain until the last active preset using them expires.

For a recording, try **Build-up** with audio and visual effects, or **Rolling overlap** with the full pool. **Stutter** is most obvious with a few clearly visible presets such as palette cutouts. These modes provide different sequences using the same selected presets.

Stop random and restore, Esc while this window has focus, and closing behave as before. Stale callbacks are invalidated when a performance is stopped or replaced. Effects remain stateful: restoring code does not rewind gameplay, audio phase or the DMC accumulator.

## Simultaneous effects

The list under **Random performances / combine presets** serves two purposes:

- **Random pool:** select all the presets you want available, then Start random mode. The tool chooses compatible combinations from that pool. Restart random mode after changing the pool, timings or counts.
- **Manual combination:** click **None**, select up to four presets, then **Apply selected together**. They remain active until restored. Conflicts are reported by name; they are never resolved by silently overwriting another effect.

For example, select **Rising sawtooth bass + Hollow repeating percussion + Sprites always in front + Early tile palette handoff** for concurrent audio, depth and palette changes.

Two presets cannot request different edits to the same instruction. For example, front sprites and behind sprites conflict; so do two different triangle wrap masks. Identical shared patches are applied only once. Classic, Build-up and Stutter choose nonredundant groups and avoid repeating the same chosen configuration immediately when another is available. Rolling chooses one compatible addition at a time and avoids immediately reselecting its last addition when alternatives are available. A preset can itself be a bundled effect, so four selected presets may change more than four hardware rules.

The requested count is sampled among feasible counts within your range. If the pool supports only two compatible presets and you ask for 2–4, it uses two and logs the available count. If none fit the minimum, it explains the problem instead of starting. Counts are limited to 1–4, with at most 16 unique patched bytes. Classic/Stutter groups share a burst window. Build-up introduces presets in stages; Rolling overlap gives them separate lifetimes.

## Earlier additions from v10: DMC sample decoding

| Preset | Decoder change |
| --- | --- |
| DMC smaller decoding steps | Use +1/-1 rather than +2/-2 per bit |
| DMC upward-biased samples | Keep +2 but reduce downward steps to -1 |
| DMC downward-biased samples | Reduce upward steps to +1 but keep -2 |
| DMC inverted bit meaning | Reverse whether a decoded bit requests an upward or downward step |
| DMC reversed bit order | Reverse bit order within each byte relative to the emulator's ReverseDpcmBitOrder setting |
| DMC two-level buzz | Use XOR 2 under the original guards, usually toggling between nearby output levels |

These effects need a game passage using **DMC sampled audio**, such as sampled percussion or speech. They do nothing audible during passages with no DMC activity, and do not directly change pulse/triangle/noise synthesis. Bit reversal changes neither byte order nor playback duration; it is not backward sample playback. Inverted bit meaning can sound similar to the original in some passages. Two-level buzz may be quiet because it has a small level excursion.

Click **Samples only** and **Start random mode** to test them in isolation. The existing 2–4 count range automatically uses counts that are feasible for this pool. For a specific combination, click **None**, choose **DMC smaller decoding steps + DMC reversed bit order + DMC inverted bit meaning**, and Apply selected together. Add an effect from another subsystem if desired.

Output remains in the original 0..127 range, including intermediate subsets while patches are being applied or restored. Sample addresses, buffer refill, bit count, DMA, interrupts and playback timers are unchanged. The XOR mode conflicts with the step-size modes; conflicts are rejected by the same instruction-overlap checks as other presets.

Restoring code does not rewind the DMC output accumulator. Bias or other accumulated decoder state can persist until further decoding, a game write or a reset changes it. This is another reason live listening/gameplay remains necessary even after bounds checks.

## Earlier additions from v9: temporary controller rules

| Preset | What the game receives |
| --- | --- |
| Left and right reverse | Physical Left becomes Right; Right becomes Left |
| A and B reverse | Physical A becomes B; B becomes A |
| A and Right exchange | Physical A becomes Right; Right becomes A |
| B and Left exchange | Physical B becomes Left; Left becomes B |
| B and Down exchange | Physical B becomes Down; Down becomes B |
| Vertical input becomes diagonal | Up produces Up+Left; Down produces Down+Right; physical Left/Right stop driving those two report bits |

Use **Controls only** to fill the random pool with controller effects. Set the count to **1–2** to concentrate on changes to controls, or leave **Standard pool / 2–4** for sound, picture and controls together. For a manual combination, click **None** and choose **Left and right reverse + A and B reverse + Crosswired pulse waves + Early tile palette handoff**, then Apply selected together.

These presets alter the native standard NES controller report routine. Your Windows keyboard bindings and host hotkeys are unchanged. Start and Select report bits remain unchanged. Both players can be affected because their standard controllers share this routine; unusual peripherals are outside its tested scope. The input HUD may still show the physical buttons rather than the altered report.

Input rules apply when Mesen builds a fresh controller report. Restoring original code returns normal behavior on subsequent polls, but does not undo walking, jumping, deaths or other gameplay events. Physical input filtering happens before these edits, so some button combinations can yield opposing directions or other unusual reports; game reactions vary. Native memory checks do not guarantee every game will handle every altered input sensibly.

Each control preset remains compatible with disjoint audio/visual rules. Two control presets requesting different sources for the same report bit conflict and are rejected. Ordinary button remapping can reproduce individual swaps; this edition's value is their timed, verified integration with the other emulator-rule changes.

## Earlier additions from v8

| Preset | Rule change |
| --- | --- |
| Crosswired pulse waves | Transpose duty/phase lookup to produce new pulse patterns on both melody channels |
| Double-pulse melody | Replace duty selection with the eight-step pattern 00000101 |
| Needle-thin melody | Force the narrow eight-step pattern 00000001 |
| Pulse 1 skips alternate steps | First pulse channel cycles through 6,4,2,0 rather than all eight phase positions |
| Pulse 2 skips alternate steps | Same change for the second pulse channel, independently selectable |
| Sprites borrow background ink | Replace the sprite palette-bank offset with its boolean priority field; output colors come from background palette entries |

For a strong audio experiment, click **None** and select **Crosswired pulse waves**, **Pulse 1 skips alternate steps**, **Pulse 2 skips alternate steps**, and **Rising sawtooth bass**, then **Apply selected together**. The first three pulse-lookup presets conflict with each other, but either pulse-step effect can combine with any one of them.

The pulse-step effects halve sequence length and can change pitch and timbre. With the original narrow duty, skipping odd positions removes its only high sample, so that channel can become silent. The waveform presets require active pulse channels; they do not guarantee a dramatic difference in every song. They affect the shared SquareChannel output routine and may also affect expansion-audio callers using that routine.

All new waveform lookups stay within the original 32-byte 0/1 duty table. The tool verifies that table on attachment as well as the core code hash. It modifies only machine-code instructions; it does not rewrite the table itself. The sprite color change happens after sprite-zero-hit checks, and its new palette indices stay in 1..4.

## Earlier additions from v7

| Preset | Rule change |
| --- | --- |
| Sprite spotlight | Sprite-palette pixels keep their colors; background-palette pixels become backdrop |
| Alternating palette banks | Keep colors only from banks with palette-index bit 2 set |
| Early tile palette handoff | Move the previous/current tile palette threshold from 8 to 4 |
| Late tile palette handoff | Move that threshold from 8 to 12 |
| Half-tile palette cadence | Fold fine horizontal palette-selection phase to four steps instead of eight |
| Rising sawtooth bass | Reverse the triangle sequencer and wrap at 16 samples |
| Hollow repeating percussion | Set both noise feedback modes to tap 9 (seed-1 period 93) |

Palette timing changes affect which palette is chosen, not PPU clock timing. Their visibility depends on scrolling, fine scroll and neighboring tile palettes. Rising sawtooth can sound similar to descending sawtooth in some passages. Noise and triangle changes require those channels to be active.

Previous presets remain: descending sawtooth, short triangle steps, metallic noise, robotic noise, Impossible sound chip, reversed sprite depth, sprites in front/behind, low/high-bit cutouts, swapped tile palette timing, revealed palette-zero entries, backdrop silhouettes, Paper cutout world, Inside-out scenery and Robot console. Backdrop silhouettes may deliberately blank much of the image; deselect it if unwanted.

## Other controls

- **Apply modified rules:** apply the single preset in the top dropdown.
- **Restore original / Esc:** stop all scheduled effects and restore code. Esc requires this app to have focus.
- **Pulse for 3 seconds / A/B:** use the top dropdown's single preset, as in v6.
- Changing that dropdown, manual application, attaching, or closing stops random scheduling. Closing attempts to restore all patches.
- The status and log show all presets active together.

Timers are best effort. Patches within a group are written sequentially with validation and rollback, not as an atomic multi-instruction transaction. Short transition states can occur. All use bounded data calculations or existing instruction paths, but this does not guarantee crash-free gameplay.

“Original” means original native code bytes. It does not rewind the game, oscillator phase or queued audio. If the tool is force-closed, its cleanup cannot run; restart Mesen to reset. A failed restore is reported, and recovery records are retained. Do not run another memory patcher on the same core concurrently.

## Verification and limits

`py -3 -m pip install -r requirements-dev.txt
py -3 -m unittest discover -v`

46 tests pass, covering exact instruction decoding, hash/build rejection, switching, shared-patch deduplication, instruction-overlap conflicts, every simulated write failure in a representative stack, all generated random-stack round trips, timer cancellation and 100 simulated random multi-effect bursts.

The previous v13 validation covered 53 individual presets and 231,658 distinct compatible combinations of 2–4 presets offline against a mapped copy of the supplied DLL. See the v14 validation note below for the expanded pool. The final full-image hash matched the original. Isolated x64 execution verified new instruction semantics and bounded results, including the full pulse table-read and volume-multiply sequence for every duty, phase and volume combination. Controller report packing was executed for 13 original/modified configurations and all 256 button states, with the IsPressed dependency stubbed to deterministic inputs. The DMC decoder was executed for 35 original/modified configurations, checking every valid level/bit and both bit-order settings, plus all shifter bytes at a representative level. Performance tests exercise staged growth, stutter deadlines, independent expiry, conflicts, cancellation, mode replacement and injected failures using a synthetic clock and the actual patch session with simulated memory. Envelope arithmetic was checked over every valid counter/divider state, and native envelope ticks were executed in 31 configurations. v13 additionally checks one-preset walk steps, reset deadlines, no writes to retained patches, same-stack validation, cross-offset replacement and rollback after a failed addition. Native tests cover 24,576 background sampling cases and 9,216 sprite permutation cases, including unchanged unmirrored rows and unchanged surrounding object memory. These are offline checks, not live Windows/Mesen gameplay or GUI testing; live stability and perceived effect strength remain unmeasured.

The app targets the exact supplied core: SHA-256 `55a5f918c8ead04d4a401fc12f0ce9e4de69bebbc484f1ca3a7c018916b1fad1`, source commit `20ba206cef5ba207c21203176d02cb9f43dda9fb`. See INSPECTION.md and build_manifest.json for individual instruction evidence.

RTC is extensible and can target host memory too. This tool's specialty is source-matched hardware experiments, compatible combinations and scheduling for this specific build, rather than a capability that RTC could never reproduce.




## v14 validation

46 unit tests pass, plus the updated named-controller assertions. All 59 presets and 354,946 compatible stacks were applied/restored against the mapped exact DLL; the full-image hash returned to the original. Native controller tests covered 23 configurations times 256 button states. The three triangle wrap masks and four pulse phase-mask presets were executed for all 256 input bytes each. Tap2 noise was checked over all 32,768 states in both modes (65,536 native cases), and its seed-1 period is 4599. The unchanged visual patches retain v13's native validation. These remain offline checks; live Windows GUI, gameplay stability and listening are untested.
