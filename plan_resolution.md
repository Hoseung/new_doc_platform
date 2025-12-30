Below is a detailed, buildable plan for **Resolution v1**, plus a Python module skeleton you can paste into a fresh repo. I’m assuming you already have:

* canonical Pandoc AST model utilities (or at least a JSON-like structure)
* normalization stage producing wrapper `Div`s with IDs and metadata injected
* a registry snapshot conforming to `aarc-1.1` + spec pack

Detailed specs and contracts are in ./spec/Analysis Artifact Payload Sepcifcation.v1.md,
./spec/Analysis Artifact Registry Specification.v1.md, and ./spec/Resolution Spec v1.md.

---

# Tiny Spec: Resolution v1

## R1. What Resolution consumes

* **Input AST**: normalized, canonical Pandoc AST (semantic wrapper `Div`s exist; IDs on wrappers)
* **Analysis Artifact Registry**: `aarc-1.1` JSON snapshot + artifact_root
* **Build config**: target profile (`internal|external|dossier`) + strictness limits

## R2. What Resolution produces

* **Output AST**: same AST, but each computed block placeholder is replaced with computed payload nodes.

## R3. Wrapper invariants (non-negotiable)

* Computed content is injected **inside the semantic wrapper `Div`** (the one that carries `id`)
* The wrapper `Div` remains the stable identity boundary (attributes unchanged except optional provenance metadata)
* Authored prose inside wrapper remains untouched

## R4. Placeholder rules (v1 strict)

Inside each computed wrapper `Div`:

* exactly **one** placeholder token must exist (e.g., `[[COMPUTED:METRIC]]`)
* placeholder must be in a block that is “placeholder-only” (typically a `Para` whose inline text equals the token after trimming)
* 0 or >1 placeholders ⇒ build error

## R5. Metric injection canonical form (your decision)

For `metric.json@v1`, injection is a deterministic **2-column table**:

* Table has **1 row**:

  * col1: metric label (string)
  * col2: formatted value string:

    * if `format` exists: render it using `{value}` and `{unit}` (only those tokens; no eval)
    * else: `"{value} {unit}"` if unit present, otherwise `"{value}"`
* Caption is optional:

  * if wrapper contains authored description, do *not* duplicate it
  * if you want caption, use payload `label` as caption only if no prose exists (optional rule; pick one and stick to it)

Determinism:

* fixed table structure (same alignments/width defaults every time)
* stable string conversion for numbers (recommend: Python `Decimal` quantization only if you explicitly want; otherwise `repr(float)` vs `str(float)` ambiguity can bite—use a deterministic formatter)

## R6. Strictness by build target

* `dossier/external`: missing payload, hash mismatch, validation fail ⇒ **hard fail**
* `internal`: you may allow warnings if you want, but the resolver should still be capable of strict mode

---

# Development Plan: Resolution v1

## Phase 0 — Groundwork (½ day)

1. **Freeze the tiny spec** (above) in `docs/spec_resolution_v1.md`.
2. Create a `ResolutionConfig` dataclass (target profile, strictness, limits).
3. Implement structured error types (`ResolutionError`, `RegistryError`, `PayloadError`, `ValidationError`) with:

   * semantic_id
   * doc location/path
   * human-readable message

Deliverable: spec doc + error model.

---

## Phase 1 — Registry loader + model (½–1 day)

Goal: load `aarc-1.1` and provide lookup by semantic ID.

Tasks:

* `RegistrySnapshot.load(path)` parses JSON, validates top-level required fields
* `RegistrySnapshot.get(id)` returns `RegistryEntry` or error (strict)
* `resolve_uri(entry.uri)` → absolute path using `artifact_root`

Deliverable: unit tests for registry parsing and ID lookup.

---

## Phase 2 — ResolutionPlan builder (1 day)

Goal: “link” semantic IDs to registry entries and locate placeholder sites before touching artifacts.

Tasks:

* Walk AST and find semantic wrapper `Div`s for computed blocks.
* For each wrapper:

  * extract `semantic_id`
  * find placeholder blocks (by token match)
  * enforce placeholder rules (exactly one)
  * match registry entry and check compatibility:

    * wrapper kind (metric/table/figure) vs registry `artifact_type`/`spec`

Output:

* `ResolutionPlan(items=[ResolutionItem(...) ...])`

Deliverable: golden-ish tests:

* placeholder missing/duplicated errors
* registry entry missing
* kind mismatch

---

## Phase 3 — Metric pipeline end-to-end (2 days)

Implement the full chain for `metric.json@v1` first (your chosen first slice).

3.1 Payload load + hash verify

* Resolve path
* Verify sha256
* Parse JSON

3.2 Metric validation

* required: `label` non-empty string, `value` number
* optional: `unit` string, `format` string, etc.

3.3 Metric emission to Pandoc Table block

* Build Pandoc `Table` node deterministically
* Enforce stable defaults (alignment/widths)

3.4 Apply injection

* Replace placeholder block with the emitted Table block
* Preserve other blocks and wrapper attrs

Deliverable: golden tests:

* metric happy path (placeholder replaced)
* invalid metric payload fails
* hash mismatch fails

---

## Phase 4 — Extend to tables + figures (later, but scaffold now)

Even if you don’t implement them yet, stub the module interfaces so the architecture doesn’t shift later.

* `table.simple.json@v1` loader/validator/emitter
* `table.pandoc.json@v1` loader/validator (geometry/safety)/emitter (inject as-is)
* `figure.binary@v1` loader/validator/emitter (+ optional meta sidecar)

---

## Phase 5 — Integration points (after core passes)

* Add `resolve()` to your pipeline between normalization and validation
* Add caching (optional): memoize loaded payloads by `(uri, sha256)`
* Add profiling logs (optional): resolution plan size, payload bytes loaded

---

# Suggested Python module skeleton

## Proposed file tree

```
docplatform/
  __init__.py

  config.py
  errors.py

  registry/
    __init__.py
    model.py
    load.py
    resolve_paths.py

  resolver/
    __init__.py
    api.py
    plan.py
    apply.py
    placeholders.py

    loaders/
      __init__.py
      base.py
      metric_v1.py
      # table_simple_v1.py
      # table_pandoc_v1.py
      # figure_binary_v1.py
      # figure_meta_v1.py

    validators/
      __init__.py
      metric_v1.py
      # table_simple_v1.py
      # table_pandoc_v1.py

    emitters/
      __init__.py
      pandoc_builders.py
      metric_table_v1.py
      # table_simple_v1.py
      # figure_v1.py

  pandoc/
    __init__.py
    ast_types.py          # if you have typed wrappers
    walk.py               # AST traversal utilities
    patch.py              # replace node at path utilities

tests/
  test_registry_load.py
  test_resolution_plan.py
  test_resolve_metric_v1.py
  fixtures/
    registry_min.json
    metric_ok.json
    metric_bad.json
    doc_with_metric_wrapper.ast.json
```

---

## Core interfaces (skeleton)

### `config.py`

```python
from dataclasses import dataclass
from typing import Literal

BuildTarget = Literal["internal", "external", "dossier"]

@dataclass(frozen=True)
class ResolutionLimits:
    max_table_cells: int = 200_000
    max_text_len: int = 5_000_000
    max_image_bytes: int = 50_000_000

@dataclass(frozen=True)
class ResolutionConfig:
    target: BuildTarget = "internal"
    strict: bool = True
    allow_raw_pandoc: bool = False
    limits: ResolutionLimits = ResolutionLimits()
```

### `errors.py`

```python
class ResolutionError(Exception):
    def __init__(self, message: str, semantic_id: str | None = None, path: str | None = None):
        super().__init__(message)
        self.semantic_id = semantic_id
        self.path = path

class RegistryError(ResolutionError): ...
class PlaceholderError(ResolutionError): ...
class PayloadError(ResolutionError): ...
class ValidationError(ResolutionError): ...
```

---

## Registry model

### `registry/model.py`

```python
from dataclasses import dataclass
from typing import Any, Literal, Optional

ArtifactType = Literal["table", "metric", "figure"]

@dataclass(frozen=True)
class RegistryRun:
    run_id: str
    test_id: str
    pipeline_name: str
    pipeline_version: str
    code_commit: str
    code_dirty: bool
    dataset_fingerprint: str
    config_fingerprint: str

@dataclass(frozen=True)
class RegistryEntry:
    id: str
    artifact_type: ArtifactType
    format: str
    spec: str
    uri: str
    sha256: str
    origin_producer: str
    # optional extras
    meta_uri: Optional[str] = None
    meta_sha256: Optional[str] = None
    meta_spec: Optional[str] = None
    related: Optional[list[dict[str, Any]]] = None
    meta: Optional[dict[str, Any]] = None

@dataclass(frozen=True)
class RegistrySnapshot:
    registry_version: str
    generated_at: str
    artifact_root: str
    run: RegistryRun
    entries: dict[str, RegistryEntry]  # keyed by semantic id

    def get(self, semantic_id: str) -> RegistryEntry:
        return self.entries[semantic_id]
```

### `registry/load.py`

```python
import json
from .model import RegistrySnapshot, RegistryEntry, RegistryRun
from ..errors import RegistryError

def load_registry(path: str) -> RegistrySnapshot:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise RegistryError(f"Failed to read registry: {e}")

    if data.get("registry_version") != "aarc-1.1":
        raise RegistryError(f"Unsupported registry_version: {data.get('registry_version')}")

    run = data.get("run") or {}
    # validate required run fields (raise RegistryError with good message)
    rr = RegistryRun(
        run_id=run["run_id"],
        test_id=run["test_id"],
        pipeline_name=run["pipeline"]["name"],
        pipeline_version=run["pipeline"]["version"],
        code_commit=run["code"]["commit"],
        code_dirty=run["code"]["dirty"],
        dataset_fingerprint=run["inputs"]["dataset_fingerprint"],
        config_fingerprint=run["inputs"]["config_fingerprint"],
    )

    entries_map: dict[str, RegistryEntry] = {}
    for e in data.get("entries", []):
        origin = e.get("origin") or {}
        producer = origin.get("producer")
        if not producer:
            raise RegistryError(f"Entry {e.get('id')} missing origin.producer")

        entry = RegistryEntry(
            id=e["id"],
            artifact_type=e["artifact_type"],
            format=e["format"],
            spec=e["spec"],
            uri=e["uri"],
            sha256=e["sha256"],
            origin_producer=producer,
            meta_uri=e.get("meta_uri"),
            meta_sha256=e.get("meta_sha256"),
            meta_spec=e.get("meta_spec"),
            related=e.get("related"),
            meta=e.get("meta"),
        )
        if entry.id in entries_map:
            raise RegistryError(f"Duplicate entry id in registry: {entry.id}")
        entries_map[entry.id] = entry

    return RegistrySnapshot(
        registry_version=data["registry_version"],
        generated_at=data["generated_at"],
        artifact_root=data["artifact_root"],
        run=rr,
        entries=entries_map,
    )
```

---

## Resolution plan + placeholder detection

### `resolver/placeholders.py`

```python
from dataclasses import dataclass
from typing import Literal

PlaceholderKind = Literal["METRIC", "TABLE", "FIGURE"]

@dataclass(frozen=True)
class Placeholder:
    kind: PlaceholderKind
    token: str  # e.g. "[[COMPUTED:METRIC]]"

PLACEHOLDERS = {
    "[[COMPUTED:METRIC]]": Placeholder(kind="METRIC", token="[[COMPUTED:METRIC]]"),
    "[[COMPUTED:TABLE]]": Placeholder(kind="TABLE", token="[[COMPUTED:TABLE]]"),
    "[[COMPUTED:FIGURE]]": Placeholder(kind="FIGURE", token="[[COMPUTED:FIGURE]]"),
}
```

### `resolver/plan.py`

```python
from dataclasses import dataclass
from typing import Any, List
from ..errors import PlaceholderError, RegistryError
from ..registry.model import RegistrySnapshot, RegistryEntry
from .placeholders import PLACEHOLDERS, Placeholder

@dataclass(frozen=True)
class ResolutionItem:
    semantic_id: str
    entry: RegistryEntry
    wrapper_path: str            # your AST path representation
    placeholder_path: str        # points to placeholder block
    placeholder: Placeholder

@dataclass(frozen=True)
class ResolutionPlan:
    items: List[ResolutionItem]

def build_plan(ast: Any, registry: RegistrySnapshot, config) -> ResolutionPlan:
    items: list[ResolutionItem] = []

    # You’ll implement traversal based on your Pandoc AST representation.
    for wrapper_div, wrapper_path in iter_semantic_wrappers(ast):
        semantic_id = get_div_id(wrapper_div)
        if not semantic_id:
            continue

        # determine expected kind from wrapper metadata (kind=metric/table/figure)
        expected_artifact_type = get_wrapper_kind(wrapper_div)  # "metric" etc.

        # find placeholder blocks within wrapper
        matches = find_placeholders_in_div(wrapper_div)  # returns list[(Placeholder, path)]
        if len(matches) != 1:
            raise PlaceholderError(
                f"Expected exactly 1 placeholder in wrapper {semantic_id}, found {len(matches)}",
                semantic_id=semantic_id,
                path=str(wrapper_path),
            )
        placeholder, placeholder_path = matches[0]

        # registry lookup
        try:
            entry = registry.get(semantic_id)
        except KeyError:
            raise RegistryError(f"Missing registry entry for {semantic_id}", semantic_id=semantic_id)

        # compatibility check (strict)
        if entry.artifact_type != expected_artifact_type:
            raise RegistryError(
                f"Kind mismatch for {semantic_id}: wrapper expects {expected_artifact_type}, "
                f"registry has {entry.artifact_type}",
                semantic_id=semantic_id,
            )

        items.append(
            ResolutionItem(
                semantic_id=semantic_id,
                entry=entry,
                wrapper_path=str(wrapper_path),
                placeholder_path=str(placeholder_path),
                placeholder=placeholder,
            )
        )

    return ResolutionPlan(items=items)
```

(Where `iter_semantic_wrappers`, `get_div_id`, `get_wrapper_kind`, `find_placeholders_in_div` are thin wrappers around your AST traversal utilities.)

---

## Metric v1 end-to-end slice

### `resolver/loaders/metric_v1.py`

```python
import json, hashlib, os
from ...errors import PayloadError
from ...registry.model import RegistrySnapshot, RegistryEntry

def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()

def load_metric_v1(registry: RegistrySnapshot, entry: RegistryEntry) -> dict:
    path = os.path.join(registry.artifact_root, entry.uri)
    if not os.path.exists(path):
        raise PayloadError(f"Metric payload missing: {path}", semantic_id=entry.id)

    actual = _sha256_file(path)
    if entry.sha256 != actual:
        raise PayloadError(
            f"Metric hash mismatch for {entry.id}: expected {entry.sha256}, got {actual}",
            semantic_id=entry.id,
        )

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise PayloadError(f"Failed to parse metric json for {entry.id}: {e}", semantic_id=entry.id)
```

### `resolver/validators/metric_v1.py`

```python
from ...errors import ValidationError

def validate_metric_v1(payload: dict, semantic_id: str) -> None:
    if not isinstance(payload, dict):
        raise ValidationError("Metric payload must be an object", semantic_id=semantic_id)

    label = payload.get("label")
    value = payload.get("value")

    if not isinstance(label, str) or not label.strip():
        raise ValidationError("Metric.label must be a non-empty string", semantic_id=semantic_id)

    if not isinstance(value, (int, float)):
        raise ValidationError("Metric.value must be a number", semantic_id=semantic_id)

    unit = payload.get("unit")
    if unit is not None and (not isinstance(unit, str) or not unit.strip()):
        raise ValidationError("Metric.unit must be a non-empty string when present", semantic_id=semantic_id)

    fmt = payload.get("format")
    if fmt is not None and not isinstance(fmt, str):
        raise ValidationError("Metric.format must be a string when present", semantic_id=semantic_id)

    notes = payload.get("notes")
    if notes is not None:
        if not isinstance(notes, list) or not all(isinstance(x, str) for x in notes):
            raise ValidationError("Metric.notes must be an array of strings when present", semantic_id=semantic_id)
```

### `resolver/emitters/metric_table_v1.py`

```python
from typing import Any

def _format_metric_value(payload: dict) -> str:
    value = payload["value"]
    unit = payload.get("unit")
    fmt = payload.get("format")

    # Deterministic conversion:
    # - Use a controlled float formatting policy (choose one).
    # Here: if value is int -> str(int). if float -> use repr-like stable general format.
    if isinstance(value, int):
        value_s = str(value)
    else:
        value_s = format(value, ".15g")  # stable-ish, avoids scientific noise in most cases

    if fmt:
        # Only allow {value} and {unit} substitutions (no arbitrary formatting execution)
        return fmt.replace("{value}", value_s).replace("{unit}", unit or "").strip()

    if unit:
        return f"{value_s} {unit}"
    return value_s

def emit_metric_as_2col_table(payload: dict) -> Any:
    """
    Return a Pandoc Table block (JSON-like) with 1 row, 2 cols:
    [label] | [formatted value]
    """
    label = payload["label"]
    v = _format_metric_value(payload)

    # This depends on your Pandoc AST representation.
    # If you store raw Pandoc JSON, emit a Table block object deterministically.
    return build_pandoc_table_2col_single_row(left=label, right=v)

def build_pandoc_table_2col_single_row(left: str, right: str) -> Any:
    # Stub: implement using your internal Pandoc builders.
    # Keep defaults stable (alignments, widths, caption empty).
    raise NotImplementedError
```

### `resolver/apply.py`

```python
from typing import Any
from ..errors import ResolutionError
from .plan import ResolutionPlan
from .loaders.metric_v1 import load_metric_v1
from .validators.metric_v1 import validate_metric_v1
from .emitters.metric_table_v1 import emit_metric_as_2col_table

def apply_plan(ast: Any, plan: ResolutionPlan, registry, config) -> Any:
    out = ast  # copy if your AST is mutable; else operate immutably

    for item in plan.items:
        if item.entry.spec == "metric.json@v1":
            payload = load_metric_v1(registry, item.entry)
            validate_metric_v1(payload, item.semantic_id)
            injected_block = emit_metric_as_2col_table(payload)
            out = replace_block_at_path(out, item.placeholder_path, injected_block)
        else:
            raise ResolutionError(f"Unsupported spec in v1: {item.entry.spec}", semantic_id=item.semantic_id)

    return out
```

### `resolver/api.py`

```python
from typing import Any
from ..config import ResolutionConfig
from ..registry.load import load_registry
from .plan import build_plan
from .apply import apply_plan

def resolve(ast: Any, registry_path: str, config: ResolutionConfig) -> Any:
    registry = load_registry(registry_path)
    plan = build_plan(ast, registry, config)
    return apply_plan(ast, plan, registry, config)
```

---

# Test plan (metric slice)

## `test_resolve_metric_v1.py`

* Fixture AST: one wrapper `Div` with id `metric.face.yaw_mae.v1`, contains placeholder `[[COMPUTED:METRIC]]`
* Fixture registry: maps that ID to `metrics/yaw_mae.json`
* Fixture payload: metric.json with label/value/unit

Assertions:

* placeholder block is gone
* inside wrapper now exists exactly one Pandoc `Table` block
* label/value strings match formatting rules
* wrapper attributes unchanged (except optional provenance if you add it later)

Also add negative tests:

* missing placeholder
* two placeholders
* missing registry entry
* hash mismatch
* invalid metric payload (label missing, value not number)

---
