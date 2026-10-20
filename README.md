# Mesen Hardware Lab

A Windows tool that corrupts **Mesen's native emulator code in memory**, changing emulated hardware rules instead of editing the ROM.

Created by **Random Týpek**. Unofficial and unaffiliated with Mesen, Mesen Community Edition, or Real Time Corruptor.

## Features

- 59 presets affecting sound synthesis, envelopes, DMC decoding, graphics, and controller reports.
- Up to four compatible presets active together, with shared patches applied once.
- Random timing and five modes: Classic bursts, Build-up, Stutter, Rolling overlap, and Mutation walk.
- Exact-build verification, instruction checks, conflict rejection, and restoration of owned patches.
- No Mesen rebuild, DLL replacement, or ROM modification required.

Effects depend on the game and its active hardware channels. This is an experimental corruption tool: it can break gameplay, blank the picture, or crash the emulator. Native bounds checks do not guarantee stability.

## Supported build

**Windows x64, NES games, one exact Mesen CE 2.2.1 core.** This is not general support for every build labelled 2.2.1 or for Mesen's other consoles.

| Identifier | Expected value |
| --- | --- |
| Core | `MesenCore.dll` |
| Original DLL SHA-256 | `55a5f918c8ead04d4a401fc12f0ce9e4de69bebbc484f1ca3a7c018916b1fad1` |
| Source commit recorded in the inspected build | `20ba206cef5ba207c21203176d02cb9f43dda9fb` |

The tool locates the core in the running process and verifies its executable section and selected data. A matching version string or rebuilding the same commit is not enough to guarantee a match. Unsupported builds are rejected; do not disable the checks to force attachment.

Mesen CE is available from its [upstream repository](https://github.com/nesdev-org/MesenCE). Its current release may not match this tool. No emulator download is bundled or asserted to match the required hash.

## Run

1. Install **64-bit Python 3.10 or newer** on Windows, with Tkinter and the Python launcher.
2. Download this repository and extract it into a folder.
3. Open a terminal in that folder and install dependencies:

   ```powershell
   py -3 -m pip install -r requirements.txt
   ```

4. Restart the supported Mesen build, load an NES game, and use its standard renderer without HD packs.
5. Run `Start.bat`, select the Mesen process, and click **Attach and verify build**.
6. Click **Start random mode**, or choose a preset and apply it manually.

Default random behavior: wait 3–10 seconds, activate 2–4 compatible presets for 2–6 seconds, restore, and repeat. All 59 presets are in the standard pool, including the bitplane and sprite-pixel effects that can alter sprite-zero-hit timing.

Use **Restore original**, press **Esc while this tool has focus**, or close the tool to attempt restoration. A forced close cannot run cleanup; restart Mesen. Restoring code does not rewind gameplay or reset accumulated emulation state. Patch groups are written sequentially, not atomically.

For modes, preset descriptions, and combinations, see [the usage guide](docs/USAGE.md).

## Tests and validation

Install the additional test dependency and run from the repository root:

```powershell
py -3 -m pip install -r requirements-dev.txt
py -3 -m unittest discover -v
```

The included 46-test suite covers instruction decoding, simulated patching and restoration, compatibility, scheduler behavior, and bounded calculations. It does not require an emulator or ROM. Some exhaustive tests take time.

During v14 development, all 59 presets and 354,946 compatible stacks were applied and restored against an offline mapped copy of the inspected DLL. Isolated native instruction checks were also performed. **Live Windows GUI behavior, gameplay stability, and audible effect quality have not been validated.**

The two optional Unicorn-based native verification scripts from the private development package are omitted from this public package pending a separate licensing review. Those historical native checks are not reproduced by the included unit suite. See [inspection notes](INSPECTION.md) for patch evidence.

## Reporting issues

Include your Windows and Python versions, Mesen build and core hash if available, the exact error, selected presets, and performance mode. For gameplay issues, include the game title and reproduction steps. Do not attach ROMs, emulator binaries, or memory dumps. Exact-build rejection is expected for unsupported cores.

## License and attribution

This project is distributed under **GNU GPL version 3 or, at your option, any later version**, without warranty. See [LICENSE](LICENSE).

Copyright (C) 2026 Random Týpek, for project contributions. Mesen-derived instruction fragments, hardware reference data, and source-informed test models are attributed separately; this project does not claim ownership of upstream material. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Mesen executables, core DLLs, ROMs, and third-party dependency binaries are not included. This project was developed with AI assistance. License selection and attribution are not a guarantee of legal clearance or runtime safety.
