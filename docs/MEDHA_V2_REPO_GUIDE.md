# MEDHA V2 Repository Guide

This document explains the repository layout and establishes strict access policies for backend developers.

## `engine/v2/`
* **Purpose**: Contains the core canonical pipeline, inference definitions, priority triage logic, and V2 training scripts.
* **Backend Developers Should Touch**: `medha_v2_pipeline.py` (to import and invoke the pipeline).
* **Must Not Touch**: Any logic modifying feature definitions, missing-data handling, scaling rules, or tensor construction inside the pipeline.
* **Training-Only**: `train_v2_*.py` scripts are for reproducibility and should never be run in production.

## `engine/models/`
* **Purpose**: Contains the completely frozen serialized model artifacts (XGBoost JSONs, Ridge Pickles, PyTorch PTHs), preprocessors, feature configurations, and metadata JSON files.
* **Backend Developers Should Touch**: The directory path exclusively for loading models during pipeline initialization.
* **Must Not Touch**: Do not modify, overwrite, rename, or regenerate any file in this directory. Modifying these files breaks determinism and nullifies the mathematical verification.

## `engine/tests/`
* **Purpose**: Contains unit and integration tests for V2 components.
* **Backend Developers Should Touch**: Can be run to verify environment configuration (`pytest engine/tests/`).
* **Must Not Touch**: Do not disable failing tests or modify the test assertions to pass broken code.

## `engine/outputs/` & `outputs/`
* **Purpose**: Contains canonical test metrics, OOF predictions, and diagnostic test sets generated during model evaluations.
* **Status**: **Historical Reference**.
* **Backend Developers Should Touch**: Can read for metric verification.
* **Must Not Touch**: Do not use these outputs in the runtime pipeline.

## `docs/`
* **Purpose**: Official architectural decision records (ADRs), audits, ablation studies, and finalized documentation.
* **Status**: **Historical Reference & Active Documentation**.
* **Backend Developers Should Touch**: Read for integration guidance (`MEDHA_V2_API_HANDOFF.md`, `MEDHA_V2_DATA_CONTRACT.md`).
* **Must Not Touch**: Do not alter the historical step-by-step audit records (e.g., `MEDHA_V2_STEP17A_REPOSITORY_AUDIT.md`).

## `engine/fusion_engine/`
* **Purpose**: Experimental scripts and intermediate diagnostics used during Step 10 & 11 Fusion development.
* **Status**: **Archived / Historical Reference**.
* **Backend Developers Should Touch**: Nothing. Ignore this directory.

## `engine/gru-temporal-risk/` & `engine/legacy_v1/`
* **Purpose**: V1 models and inference APIs containing the legacy leaky 72-feature GRU architecture.
* **Status**: **Archived / Historical Reference**. Kept solely to document the migration path.
* **Backend Developers Should Touch**: Nothing. 
* **Must Not Touch**: Never invoke V1 models in production. They are conceptually deprecated and unsafe.

## `scratch/`
* **Purpose**: Temporary investigative scripts and scratchpads.
* **Status**: **Safe to Delete**.
* **Backend Developers Should Touch**: Nothing.
