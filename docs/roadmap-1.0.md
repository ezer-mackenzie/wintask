# Pre-1.0 audit and release plan

Audit dated September 19, 2026, covering `c2bbe4f` (0.9.0) and the subsequent
workflow changes. **The library is not ready to be declared stable yet.**
The exit criterion is a tested, documented contract rather than a feature count.
Task folders and additional credentials are not required for 1.0 if the current
scope remains explicit.

## Scope and limitations

Reviewed Python/Rust code, tests, Git history, workflows, documentation, a release
CPython 3.14 x64 wheel installed in a clean environment, and recent public Actions
runs. Reproduced incomplete validation and a COM apartment conflict. The full
GitHub matrix, permission/service scenarios, private PyPI publisher settings and
repository protections were not verified. This audit does not certify the
absence of other defects.

## Local verification

- Built and installed a release CPython 3.14 x64 wheel in a clean environment;
  confirmed imports from `site-packages`, without an editable installation.
- All 17 tests passed, including daily, weekly and monthly registration,
  existence and deletion. Test tasks were removed; no scripts were executed.
- Checked workflow YAML, job dependencies, triggers, validated commit selection
  and Windows integration settings.
- Exercised seven release validation cases: valid version, malformed tag,
  mismatched version, shell metacharacters, mismatched lock, missing changelog
  and missing integration tests.
- Built documentation with `mkdocs build --strict` and checked the diff.
- Modified workflows have not run on GitHub yet. Local checks do not replace that.

## Previous defects and why they escaped

| Defect | Evidence | Status and prevention |
| --- | --- | --- |
| Daily interval was not forwarded correctly | Fix `f652ba4` | Fixed; retain forwarding tests and inspect registered XML. |
| `exists()` treated an account-information HRESULT as absence | `9bf62a9`, fixed in `c2bbe4f` | Fixed; use SDK constants and native absence/presence tests. |
| Existence test was nested inside another test | `tests/test_builder.py` before `c2bbe4f` | Fixed; review test discovery as well as the green result. |
| Windows rejected the BSTR encoding declaration and the monthly XML element | Native reproduction and fix `c2bbe4f` | Fixed; exercise all three schedules on real Windows. |
| Windows CI built wheels without running them | `.github/workflows/ci.yml` | Added installation and integration tests; remote runner confirmation pending. |
| Publication required builds but not version checks or tests | `.github/workflows/publish.yml` | Added version, changelog, test and documentation gates; all builds use the validated commit. |
| Documentation was inserted into wrong sections and the changelog was unordered | Fix `c2bbe4f` | Fixed; documentation builds still need editorial review. |
| Repeated publication configuration changes | `d28eb24`, `1a5cd51`, `9c3f04a`, `7869d06` | Latest manual publication succeeded; do not attribute every failure to credentials without examining logs. |

The [manual 0.9.0 publication](https://github.com/ezer-mackenzie/wintask/actions/runs/35477016844)
and its [main CI](https://github.com/ezer-mackenzie/wintask/actions/runs/35476834740)
succeeded. Two PR runs failed in **Windows x64 Build wheels**
([first](https://github.com/ezer-mackenzie/wintask/actions/runs/35476920185),
[second](https://github.com/ezer-mackenzie/wintask/actions/runs/35321548422)). An
[earlier run](https://github.com/ezer-mackenzie/wintask/actions/runs/35316276136)
failed building Linux armv7. The Actions API confirmed the failing steps, not
the internal cause. Inspect logs before adopting those dependency updates;
these build failures do not demonstrate PyPI authentication failures.

## Stable-release blockers

P1 requires a fix and verification before 1.0. P2 requires a documented support
or behavior decision with tests appropriate to the chosen contract.

| ID | Priority | Finding / evidence | Acceptance criterion |
| --- | --- | --- | --- |
| V1 | P1 | Daily intervals `True`, `1.5` and `366`, and monthly days `True`/`1.5`, are accepted. | Reject booleans and non-integers; daily interval 1-365 and day 1-31. Test types, boundaries and rejection before COM. |
| V2 | P1 | `arguments="ab"` becomes `a b`; flags use `str(value).lower()` without type validation. | Reject string/bytes argument containers, non-string/NUL elements and non-boolean flags; test quoting, Unicode and spaces. |
| C1 | P1 | Calling `exists()` after `CoInitializeEx(None, 2)` returns `RPC_E_CHANGED_MODE` (`0x80010106`). | Support STA/MTA without changing or uninitializing the caller's apartment; isolated process/thread success and error tests. |
| E1 | P1 | Connection errors always become `RuntimeError`, while operations distinguish access denied. | Consistent connection/operation mapping, inspectable HRESULT, tests for denied access, absence and unavailable service without hiding errors as `False`. |
| T1 | P1 | Integration creates/queries/deletes but does not execute scripts or verify updates. | Run a harmless marker script; verify arguments, directory and interpreter with timeout/cleanup. Test updates, missing run/delete and denied access. |
| P1 | P1 | Python >=3.9 and PyPy are advertised without a matching matrix; Windows selects only 3.13. | Define supported versions/interpreters/architectures; test each promised combination or narrow the promise. |
| P2 | P1 | Wheel lacks summary, long description, project URLs and license expression (LICENSE.md is included). | Complete distribution metadata, validate packaging and install wheel/sdist from scratch. |
| R1 | P1 | New release gates have only been checked locally. | Green remote CI; test both triggers with a test version and reject invalid tags; verify Trusted Publishing without repository secrets. |
| N1 | P2 | Name validation accepts `/` and DEL (`\x7f`) without a length limit despite the documented control-character restriction. | Check Windows name rules, define and test characters/length, and update docs. Python acceptance alone does not establish Windows acceptance. |
| S1 | P2 | DST, short months, missed schedules and signed-out sessions lack a detailed contract; logon uses an interactive token. | Document delegation to Windows and explicit limitations; boundary tests without promising automatic recovery. |
| C2 | P2 | Synchronous COM calls retain the GIL; only short calls have been tested. | Document blocking behavior or safely release the GIL and test concurrency. |

The interval limit follows the [DaysInterval schema](https://learn.microsoft.com/en-us/windows/win32/taskschd/taskschedulerschema-daysinterval-dailyscheduletype-element).
COM ownership must follow the [CoInitializeEx contract](https://learn.microsoft.com/en-us/windows/win32/api/combaseapi/nf-combaseapi-coinitializeex).

## Proposed milestones

1. **0.10.0 - Validation and errors:** V1, V2, N1 and E1; test public inputs and
   define exceptions before freezing the API.
2. **0.11.0 - Native Windows:** C1 and T1; STA/MTA, execution, updates, permissions
   and cleanup. Complete S1/C2 decisions.
3. **0.12.0 - Distribution:** support matrix P1, metadata P2, wheel/sdist
   installation and review failed dependency-update builds.
4. **1.0.0-rc.1 - Rehearsal:** exercise both publication paths, install published
   artifacts in clean environments and close R1. A GitHub prerelease also
   triggers PyPI publication: Cargo/tag must carry the prerelease version;
   checking the GitHub prerelease box alone does not change package metadata.
5. **1.0.0:** all P1 items closed, P2 decisions documented, frozen API/support
   contract, coherent documentation/changelog and green CI for the exact commit.

These are proposed milestones. No tags or releases were created by this audit.

## Manual and release-triggered publication

`Release` retains `workflow_dispatch` with an explicit tag and
`release: types: [published]`. Drafting a release or pushing a tag is not
publication. Publishing a stable release or prerelease triggers the
[GitHub event](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#release).
Events created using `GITHUB_TOKEN` have workflow-trigger restrictions; account
for this if release creation is automated later.

The workflow checks the tag, Cargo.toml, Cargo.lock and changelog, runs tests and
builds the validated SHA. Windows jobs install the wheel from `dist` compatible
with the selected interpreter; other interpreter versions still need matrix
coverage. Publication requires every dependency to pass. Runs for the same
version are serialized; `uv publish --check-url` skips existing PyPI files but
does not replace published artifacts. No publication happens without a GitHub
workflow trigger.

Merge these controls before creating the next tag. Do not move published tags.
Historical tags without integration tests are explicitly rejected; rebuilding
historical distributions requires a separate procedure without changing their
published contents.
