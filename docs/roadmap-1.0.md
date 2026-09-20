# Pre-1.0 audit and release plan

Updated September 19, 2026 for the **0.10.0 candidate**. The source-level findings
from the 0.9.0 audit have been addressed and verified locally. **1.0.0 is still
blocked on remote CI and a release rehearsal**, not on reaching a feature count.
Task folders, alternative credentials and new scheduling features are outside
this stable-release scope.

The initial audit is preserved in the preceding Git commit. The
[support and scheduling contract](support.md) defines the behavior intended to
become stable, including deliberate limitations and compatibility changes.

## Completed implementation and evidence

| ID | Original finding | Resolution in 0.10.0 | Evidence |
| --- | --- | --- | --- |
| V1 | Booleans, fractional intervals/days and intervals over 365 were accepted. | Strict integer ranges, typed time values, whole seconds, no timezone/fold ambiguity. | Boundary/type tests across daily, weekly and monthly triggers. |
| V2 | A string argument container split into characters; flags/text were not validated. | Validate argument containers/elements, booleans and XML text. Preserve carriage returns through XML normalization. | Rejection-before-COM tests and native round-trip of spaces, quotes, empty arguments, CR/LF, tabs and Unicode. |
| C1 | A pre-existing COM STA failed with `RPC_E_CHANGED_MODE`. | Borrow STA initialization; balance only initialization owned by wintask; release interfaces before the COM guard. | Isolated STA/MTA processes verify apartment ownership after repeated success and failure. |
| E1 | Connection and operation errors had inconsistent translation. | Public `TaskSchedulerError` and `TaskPermissionError` retain unsigned HRESULT and operation, including connection failures. | Rust access-denied/unavailable-service mapping tests for every stage; real missing-task exceptions; Python exception compatibility/pickling tests. |
| T1 | No native execution or update coverage. | Add real create/update/run/exists/delete integration with bounded waits and cleanup. | A harmless marker script verifies arguments, working directory and interpreter; registered XML and enabled state are checked. |
| P1 | Claimed interpreter support exceeded the tested matrix. | Standard CPython 3.9-3.14 is explicit; PyPy/free-threading are not promised. Windows x64 jobs cover every version; x86/ARM64 have experimental 3.13 jobs. | All six CPython versions passed locally using independently built and installed Windows x64 wheels. Hosted OS/architecture results remain part of R1. |
| P2 | Missing distribution metadata and source-install verification. | Add summary, README, URLs, Apache-2.0 expression, typing files and source-content checks; rebuild wheels from sdist. | Twine strict checks, archive inspection, clean installation and source-distribution rebuild. |
| N1 | Task-name character/length policy was incomplete. | Document a conservative root-name policy of 1-200 UTF-16 units, reserved characters, controls, surrogates and edge whitespace/dots. | Valid/invalid names tested against every public operation before backend calls, including Unicode length boundaries. |
| S1 | Timezone, short-month, missed-run and session behavior was underspecified. | Publish an explicit scheduling contract and set `StartWhenAvailable=false`. | XML boundary/policy tests; document Windows calendar/DST delegation without promising catch-up or exactly-once behavior. |
| C2 | Native COM calls held the GIL. | Detach during COM calls while keeping all interfaces on their creating thread; document synchronous calling behavior. | Concurrent native lookups plus STA/MTA lifetime tests; advise worker threads for GUI/async callers. |
| R1 | Release gates and publisher paths were not rehearsed. | Add version/prerelease checks, immutable commit builds, wheel tests, source-install checks, serialized publication and manual `publish=false`. | Version/prerelease regression tests and actionlint pass locally. **External execution remains open.** |

## Local verification

- Windows x64 release wheels built, installed in clean environments and tested
  on CPython 3.9, 3.10, 3.11, 3.12, 3.13 and 3.14.
- 33 tests discovered on each interpreter: 32 pass and the non-Windows contract
  test skips on 3.11-3.14; 28 pass and five skip on 3.9-3.10 because release-tool
  tests additionally require Python 3.11+. All native integration tests run on
  every interpreter.
- Two Rust tests cover native absence/error classification and operation context.
  Minimum Rust 1.85 compilation succeeds with the locked dependencies.
- Release wheel and sdist metadata/content checks and `twine check --strict`
  pass. A wheel is rebuilt from the source distribution rather than assuming
  checkout builds prove sdist completeness.
- actionlint validates both workflows. Documentation builds with
  `mkdocs build --strict`.

The tests create uniquely named temporary tasks and remove them. Execution
writes only a local temporary marker. They do not stop the scheduler service or
change unrelated task ACLs. Access-denied and unavailable-service mappings use
synthetic native errors; actual service outages and another user's permissions
remain environmental scenarios, not falsely claimed live tests.

## Previous defects and lessons

| Defect | Evidence | Prevention |
| --- | --- | --- |
| Daily interval was not forwarded | Fix `f652ba4` | Keep forwarding and registered-XML checks. |
| Wrong HRESULT in `exists()` | `9bf62a9`, fixed in `c2bbe4f` | Use SDK constants and verify both absence and unrelated failures. |
| Nested existence test never ran | `tests/test_builder.py` before `c2bbe4f` | Review discovery and actual test names, not only a green result. |
| Invalid XML encoding/monthly element | Native reproduction and fix `c2bbe4f` | Run all schedules on Windows and test installed distributions. |
| CI built Windows wheels without testing them | Workflows before this audit | Install each selected wheel and run native integration before upload. |
| Publication skipped version/tests/docs checks | Original release workflow | Gate publication on the validated commit and all required test jobs. |
| Misplaced documentation and unordered changelog | Fix `c2bbe4f` | Combine strict builds with editorial review. |
| Repeated publisher configuration changes | `d28eb24`, `1a5cd51`, `9c3f04a`, `7869d06` | Separate build failures from publisher failures and retain a manual rehearsal path. |

The [manual 0.9.0 publication](https://github.com/ezer-mackenzie/wintask/actions/runs/35477016844)
and its [main CI](https://github.com/ezer-mackenzie/wintask/actions/runs/35476834740)
succeeded. Two PR runs failed building Windows x64
([first](https://github.com/ezer-mackenzie/wintask/actions/runs/35476920185),
[second](https://github.com/ezer-mackenzie/wintask/actions/runs/35321548422)); an
[older run](https://github.com/ezer-mackenzie/wintask/actions/runs/35316276136)
failed building Linux armv7. The first PR belongs to a Dependabot Rust-dependency
update. Its public annotation only reports maturin exit code 1, not a root cause.
The candidate retains the working locked dependency set; do not adopt a failing
update without inspecting its full log and rerunning the native matrix.

## Remaining stable-release gate

1. Push the reviewed candidate and obtain green CI for its exact commit,
   including Windows Server 2022/current hosted Windows, experimental architecture
   jobs, portable tests, Rust minimum, docs, and source-install checks. Local x64
   results do not stand in for these environments.
2. Run `Release` manually with the candidate tag and **`publish=false`**. Record
   the workflow URL and confirm the PyPI job is skipped while all gates run.
3. Publish a correctly versioned release candidate using the GitHub release
   path. Verify Trusted Publishing and install the resulting PyPI artifacts in
   clean environments. Record that workflow URL and the artifact version.
4. Review any failures and API compatibility changes. Only then freeze the
   contract and publish 1.0.0. Do not relabel the 0.10.0 candidate as stable.

These steps have not been executed in this session: no push, tag creation,
GitHub release or PyPI publication has been performed. The implementation work
originally proposed across 0.10-0.12 is consolidated into 0.10.0; additional
pre-1.0 versions should be driven by verification findings.

## Publication semantics

The workflow retains both `workflow_dispatch` and `release: types: [published]`.
A draft or tag push is not a published release. A GitHub prerelease also triggers
publication, so its flag must match a prerelease Cargo/tag version, for example
`1.0.0-rc.1` / `v1.0.0-rc.1`. Manual dispatch defaults to publishing after checks;
disable `publish` for a rehearsal. Never move or overwrite published tags.

All build jobs use the validated commit. The extra Windows 2022 compatibility
job does not upload a second copy of the same wheel filename. Publication waits
for all required jobs. Concurrent runs for the same version are serialized;
`uv publish --check-url` checks existing PyPI files without replacing them.
Historical tags missing the required validation tools/tests are rejected.

References: [GitHub release events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#release),
[DaysInterval](https://learn.microsoft.com/en-us/windows/win32/taskschd/taskschedulerschema-daysinterval-dailyscheduletype-element),
[CoInitializeEx](https://learn.microsoft.com/en-us/windows/win32/api/combaseapi/nf-combaseapi-coinitializeex).
