# CEASIOMpy Documentation (WIP)

This folder is the start of a deeper, repo-wide documentation set for CEASIOMpy.

## What CEASIOMpy is

CEASIOMpy is a conceptual aircraft design environment built around the CPACS format. It lets you
assemble workflows (geometry → mesh → solver → post-processing) by chaining CEASIOMpy modules.

## Module deep dives

Module-level deep documentation now lives directly in each module’s `README.md` under
`src/ceasiompy/<Module>/README.md` (see the “Settings reference” section).

## Contributing docs

When documenting a module, prefer describing:

1. **What the module does** (inputs/outputs).
2. **What the GUI controls change** (CPACS XPaths + defaults).
3. **How those CPACS values map to external tools** (e.g., SU2 config keys).
4. **Limitations & troubleshooting** (common failure modes, validation hints).
