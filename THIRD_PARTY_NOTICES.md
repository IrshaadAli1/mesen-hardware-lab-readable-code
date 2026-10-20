# Third-party notices and provenance

## Project contributions

Copyright (C) 2026 Random Týpek, for project contributions.

This project is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. A copy is included in LICENSE.

## Mesen / Mesen Community Edition

Upstream: https://github.com/nesdev-org/MesenCE

Inspected source revision: https://github.com/nesdev-org/MesenCE/tree/20ba206cef5ba207c21203176d02cb9f43dda9fb

Copyright notice in the README at that revision:

> Copyright (C) 2014-2025 Sour, 2026 contributors

Upstream license: GNU GPL version 3 or, at your option, any later version. The upstream license text is reproduced unchanged in LICENSE.

The build manifest records original instruction fragments extracted from a locally inspected MesenCore.dll and modified instruction bytes used by this tool. It contains 39 distinct original instruction fragments totalling 125 bytes (each at most eight bytes), plus a 32-byte pulse-duty lookup table used for verification. These are not a complete emulator binary. Related constants, disassembly, descriptions and reference calculations also occur in tests and inspection notes. These counts describe the manifest, not every repeated occurrence in the package.

Source-informed reference models include the envelope, DMC, noise, pulse, triangle, controller-report and PPU behavior documented in INSPECTION.md. Our modifications introduce alternative patch constants, control mappings, waveform rules, combinations, scheduling, validation, and a standalone Python interface. Original upstream material retains its upstream attribution; a project-level copyright notice does not supersede it.

Relevant corresponding upstream sources at the inspected revision:

- [APU sources](https://github.com/nesdev-org/MesenCE/tree/20ba206cef5ba207c21203176d02cb9f43dda9fb/Core/NES/APU): ApuEnvelope.h, ApuTimer.h, NoiseChannel.h, SquareChannel.h, TriangleChannel.h, DeltaModulationChannel.cpp and NesApu.cpp.
- [NesPpu.cpp](https://github.com/nesdev-org/MesenCE/blob/20ba206cef5ba207c21203176d02cb9f43dda9fb/Core/NES/NesPpu.cpp) and [DefaultNesPpu.h](https://github.com/nesdev-org/MesenCE/blob/20ba206cef5ba207c21203176d02cb9f43dda9fb/Core/NES/DefaultNesPpu.h).
- Other source references and native locations are recorded in INSPECTION.md and build_manifest.json.

No Mesen executable, full core DLL, ROM, or upstream source tree is included. Mesen's name identifies compatibility; this project is not endorsed by or affiliated with its developers.

## Separately installed dependencies

The source ZIP does not vendor these projects. They retain their own licenses, independent of this project's license. If distributing bundled dependencies or a packaged executable later, preserve the applicable notices and review the exact versions being shipped.

| Component | Purpose | Upstream license / notice |
| --- | --- | --- |
| psutil | Process enumeration at runtime | BSD-3-Clause; Copyright (c) 2009 Jay Loden, Dave Daeschler, Giampaolo Rodola; [license](https://github.com/giampaolo/psutil/blob/master/LICENSE) |
| Capstone 5.x | Instruction-decoding tests | BSD-style 3-clause license; Copyright (c) 2013 COSEINC; [license](https://github.com/capstone-engine/capstone/blob/5.0.7/LICENSE.TXT) |
| Python / Tkinter / Tcl/Tk | Interpreter and GUI supplied by the user's Python installation | Respective upstream licenses; [Python licensing](https://docs.python.org/3/license.html) |

The optional native verification scripts that imported Unicorn and pefile are excluded from this public package. Neither library is required by the included application or unit tests. Historical validation reports mentioning those tools do not mean they are bundled, relicensed, or part of the public test suite.

Real Time Corruptor is referenced only for comparison. No RTC implementation is intentionally included. No affiliation or endorsement is claimed.
