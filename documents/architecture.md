# Architecture (WIP)

## Core ideas

- **CPACS as the source of truth**: modules read inputs from CPACS and write results back to CPACS.
- **Workflows**: a workflow is an ordered list of modules applied to an input CPACS file.
- **Working directory**: execution typically happens inside a `WKDIR/Workflow_XXX/` folder.

## Layers

CEASIOMpy currently blends two concerns:

1. **Computation modules** under `src/ceasiompy/` (meshing, solvers, post-processing).
2. **Streamlit UI** under `src/app/` (workflow builder and settings UI).

The long-term goal is to keep computational modules runnable in headless mode without importing
Streamlit, and keep Streamlit-specific code in the UI layer.

## Configuration flow

Most modules expose GUI settings via a `__specs__.py` file. In the UI, those settings are written
into CPACS under the `CEASIOMpy` branch, and later read by the module at runtime to configure
external tools and internal algorithms.

# CEASIOMpy Documentation (WIP)

This folder is the start of a deeper, repo-wide documentation set for CEASIOMpy.

## What CEASIOMpy is

CEASIOMpy is a conceptual aircraft design environment built around the CPACS format. It lets you
assemble workflows (geometry → mesh → solver → post-processing) by chaining CEASIOMpy modules.

## Module deep dives

Module-level deep documentation now lives directly in each module’s `readme.md` under
`src/ceasiompy/<Module>/readme.md` (see the “Settings reference” section).

## Contributing docs

When documenting a module, prefer describing:

1. **What the module does** (inputs/outputs).
2. **What the GUI controls change** (CPACS XPaths + defaults).
3. **How those CPACS values map to external tools** (e.g., SU2 config keys).
4. **Limitations & troubleshooting** (common failure modes, validation hints).
