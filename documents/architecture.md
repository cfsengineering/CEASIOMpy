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
