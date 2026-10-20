# Creating a release

Releases are built from a verified Git tag. The HACS archive contains the
integration directly at its root and is published together with a SHA-256
checksum file.

## 0.8.2-beta.2 verification

I prepared this beta on 2026-10-21 with the start-counter changes from PR #72.
Thank you, CHLINDE, for the initial implementation and for confirming that the
missing counter became visible. I keep general and per-source counters
independent, validate their readings and restore existing entities through
normal polling. The [implementation report](start-counters.md) and its
[German version](start-counters.de.md) explain the previous weaknesses and
the changes in detail.

The release is a pre-release. **0.8.1 remains Stable/Latest.**

- Home Assistant 2026.10.1, Python 3.14.2: **1,460 tests passed**, with
  **96.64% combined statement and branch coverage**. Counts include
  parametrized variants; the counter-assessment module has 100% coverage.
- Ruff formatting and lint and strict Mypy passed.
- The follow-up review found inconsistent source-ID handling during recovery.
  Five cases failed before the correction. I added twelve cases covering
  identity restoration, rejected paths and actual discovery/polling after
  403, 404 and 406 responses. Forbidden-resource pauses remain effective.
- Tests also exercise Home Assistant registration and reload with two
  synthetic gateways, recorder statistics, bounded request batches, malformed
  readings, cloud failures, deterministic packaging and isolated ZIP imports.

The Linux archive contains **56 files** and **230,306 bytes**, with
`manifest.json` at its root and version `0.8.2-beta.2`. Every archived file
matches the prepared component source. ZIP SHA-256:
`02919378b6036bf537ebef1899f1d943bf4c84aa676c99f194b765f0ca97fa50`.

Publication requires the protected main branch and successful checks on the
final PR commit. The tag-triggered workflow repeats source checks, tests, the
isolated dependency audit, Hassfest and HACS before publishing. The published
ZIP, checksum and release notes must match the locally verified package and
the matching CHANGELOG section.

CHLINDE's feedback confirms visibility with the initial implementation.
The revised recovery and multi-source behavior still need field confirmation.
I performed no physical appliance writes for this beta. Select the beta
explicitly in HACS and restart Home Assistant after updating.

## 0.8.2-beta.1 verification

I prepared this beta on 2026-10-20 with the pool-heating start counter from
PR #70 and the manual-setpoint recovery from PR #71. I extended CHLINDE's
original recovery implementation and tests with bounded outage handling,
normal polling for late values, error pauses and cancellation checks.
Thank you, CHLINDE, for the initial contribution.

The release is a pre-release. **0.8.1 remains Stable/Latest.**

- Home Assistant 2026.10.1, Python 3.14.7: **1,350 tests passed**, with
  **96.55% combined statement and branch coverage**. Counts include parametrized
  variants.
- Ruff 0.17.0 formatting and lint and strict Mypy 2.4.0 passed.
- An isolated runtime dependency audit found no known vulnerabilities.
- Tests cover at most one 3/10/20-second recovery sequence per outage,
  continued regular polling, independent circuits and gateways, authentication
  and rate-limit errors, forbidden-resource pauses, mode changes, unloading,
  stable entity identities and late pool-counter values.
- The release tests built two identical component-rooted archives and imported
  the integration from an isolated extracted installation.

I independently built the Linux archive twice. It contains **55 files** and
**226,828 bytes**, with `manifest.json` at its root and version
`0.8.2-beta.1`. Every archived file matches the prepared component source.
ZIP SHA-256:
`6234bb5ea0f87166a18b699f7d3c5bf17889bc7f0133b20182516b922b34db4b`.

The protected main branch requires successful combined checks before merging.
The tag-triggered workflow repeats verification, including the dependency
audit, Hassfest and HACS, before publication. Published notes, archive and
checksum must match the verified local artifacts.

I performed no physical appliance writes for this beta. The static APK
comparison does not establish the recovery delay on a real installation.
Field confirmation remains open. Select the beta explicitly in HACS and
restart Home Assistant after updating.

## 0.8.1 verification

I prepared the full stable release on 2026-10-20 from main, including the HACS
timezone corrections, holiday dialog and write changes, the earlier startup
recovery and season-switching betas, and the compatible dependency updates.

- Home Assistant 2026.10.1, Python 3.14.2: **1,287 tests passed**, with
  **96.45% combined statement and branch coverage**.
- Home Assistant 2026.9.4: **366 targeted compatibility cases passed** for
  configuration, holiday dialogs, timezone preparation, writing and coordination.
- Ruff 0.17.0 formatting and lint, strict Mypy 2.4.0 and the isolated runtime
  dependency audit passed. The audit found no known vulnerabilities.
- Local browser component checks passed at 390 and 1280 pixels: adjacent date
  and time, minute-only clocks, empty required dates, editable 08:00 defaults,
  saved times, keyboard deletion, repeated-click protection, invalid drafts,
  failed-request recovery and confirmation routing. The test used simulated
  flow responses and performed no appliance writes.
- Regression tests cover asynchronous timezone preparation before publishing
  successful, adjusted and duplicate write results. The existing cold-cache
  tests check that named-zone disk access occurs outside the event loop.

The earlier installation evidence in [Holiday periods](holiday-periods.md)
covers the dialog layout and a midnight edit of one existing test holiday.
Creation and deletion were not repeated on the appliance for this release.
The broader recovery and installation checks below remain open.

The locally built Linux archive contains **55 files**, **224,569 bytes**, with
`manifest.json` at the root and both the timezone module and new dialog assets.
Two independent test builds produced identical archives, and import from an
isolated extracted installation passed. ZIP SHA-256:
`d39b236bb724a284b6a1fbf715f0c57666763bad977e338b0b2d0fd35e4bf13a`.

The release uses the protected main branch and its required checks. The
tag-triggered workflow repeats source checks, tests, the dependency audit,
Hassfest and HACS validation before publication. Published notes, the archive
and its checksum must match the locally verified release artifacts.

## 0.8.1-beta.2 verification

I prepared this beta on 2026-10-11 to expose central season switching in Home
Assistant. The new select uses the gateway's offered options and write
permission, with the existing validated write and read-back service.
[Season switching](season-switching.md) documents the setting, its separate
actual-status sensor and the available local appliance evidence.

- Python 3.14.2 with the pinned development environment (HA 2026.10.0b4):
  **1,125 tests passed**, **96.26% combined statement and branch coverage**.
  This includes **24 new parametrized season-control test cases**.
- With released HA 2026.10.0, **185 targeted control, sensor and diagnostic
  tests passed**.
- Ruff 0.16.10 formatting/lint, strict Mypy 2.4.0 and development dependency
  consistency passed. An isolated runtime dependency audit found no known
  vulnerabilities.
- The Linux package contains **52 files**, **213,834 bytes**, with
  `manifest.json` at its root. Tests verify reproducible construction and
  import from an isolated extracted installation. Every archived file matches
  the prepared component source.
- ZIP SHA-256:
  `eef26ab8ccf75096aa4efc6455d639b339d53fcffd68c6f082bade7881b3a30a`.

The package was built and tested from an isolated Linux copy of the staged
source to avoid Windows worktree metadata being interpreted as Linux paths.
No application credentials or raw installation exports are included.
The new HA select still needs a physical test after installation. Existing
local appliance records confirm the underlying setting, not this new UI.

Publication uses the protected main branch, required PR checks and the existing
tag-triggered release workflow. The release is a pre-release;
**0.8.0 remains Stable/Latest**. Published assets and notes must be compared with
this package and the matching CHANGELOG section after the workflow finishes.

## 0.8.1-beta.1 verification

I prepared this beta on 2026-10-11 with PointT robustness and request use as
its main focus. It separates nonessential reads from functional discovery,
recovers pending metadata without a restart, preserves entity identities and
stops repeating successful reviewed metadata reads. The full policy, including
paths, deadlines, exception cases and measured savings, is in
[Request behavior and recovery](request-behavior.md).

This version is a pre-release; **0.8.0 remains Stable/Latest**. The combined
release branch is
`release/v0.8.1-beta.1`. Other working checkouts are unaffected.

### Included changes

| Source | Included in the beta |
| --- | --- |
| Startup recovery work | Separate reader service and encapsulated state; license omission; reviewed successful-once metadata; bounded automatic recovery; stable entities; diagnostics schema 14; documentation and tests. |
| PR #55, `5070ff21ba915a970940fe8fd1f02f9b4a176818` | Ruff pre-commit 0.16.10. |
| PR #56, `a4f650cad750d50f4ebe73593ede36b3b690ed36` | Hypothesis 6.168.5, Mypy 2.4.0, HA test package 0.13.370 and Ruff 0.16.10. Pytest stays at 9.0.3, the exact version required by that HA test package. The proposed 9.1.1 pin is incompatible. |
| PR #57, `9b95fc107ab24cf0cc5ab106ec9a7c3abf14bc02` | Both pinned CodeQL actions at 4.38.3. |
| Compatibility found during combined validation | Form schemas use the backend selected by the installed HA. Suggested values and required markers remain consistent across Voluptuous and Probatio. Binary-sensor typing uses the newer defining module while preserving the older runtime import. |
| Current main through PR #54 | Existing 0.8.0 features and the already documented local notification testing. This is prior evidence, not a new field test of the startup changes. |

The maintenance commits were incorporated into the combined release change
with their provenance, superseding the separate changes in #55, #56 and #57.
PR #56's original quality check failed during dependency
installation because its two Pytest requirements conflict. The combined beta
corrects that conflict without relaxing validation or suppressing type errors.

### Verification scope

Python 3.14.2 is used throughout. The new pinned test package supplies HA
2026.10.0b4, so I also check a released HA version separately. The additional
environment deliberately overrides only the test package's HA pin to 2026.10.0;
it is a compatibility check, not the default dependency resolution used by CI.
The default development environment passes `pip check`.

- Full test suite with the pinned development environment: **1,101 passed**,
  **96.23% combined statement and branch coverage**.
- Full test suite with released **HA 2026.10.0**: **1,101 passed**, with the
  same **96.23% combined coverage**. Strict Mypy passed in this environment too.
- On HA 2026.9.4, **167 targeted form, notification-options and holiday-write
  tests passed**, including choosing the correct schema backend when both
  validator packages are installed.
- Ruff 0.16.10 lint and formatting checks and strict Mypy 2.4.0 passed.
- A fresh audit environment containing the integration runtime dependencies
  and audit tools found **no known vulnerabilities**. Test-only HA dependencies
  are not presented as integration runtime requirements.
- The tests include deterministic component-rooted package construction and
  an import from an isolated extracted installation.

These counts include parametrized test variants. They do not represent 1,101
different physical installations. No appliance writes or new field tests were
performed for this beta. Long-term cloud stability and recovery on affected
installations still require observation.

### Prepared package

- Version: `0.8.1-beta.1` in both manifest and project metadata.
- Code/package verification commit: `30f307d79cd086a53e193eaec5f100a6112c4073`.
- Archive: `dist/bosch_buderus_heating.zip`, **213,574 bytes**, **52 files**,
  with `manifest.json` at the root and all three new runtime modules included.
- SHA-256: `f30fb2da203987fcc256474e62ddb4a536244c5f7d2c455b0475dd4b0200b389`.
- Two Linux builds produced byte-identical archives. Every archived file was
  compared with its committed Git blob; archive integrity and the matching
  checksum file were verified. Generated notes match the exact 0.8.1-beta.1
  CHANGELOG section. No untracked files, caches or credentials are packaged.

The checksum identifies the local prepared artifact. Verification of a future
published download remains a separate publication step. Later changes to
release documentation alone do not change the component archive.

### Publication gates

Before publication, the combined change must go through a PR with all required
checks and resolved review conversations. HACS, hassfest and CodeQL must pass
on that combined change. Successful checks on individual maintenance PRs do
not substitute for those combined checks. The tag-triggered release workflow
repeats its validation before publishing the archive.

After explicit release approval, publish an annotated beta tag only from the
verified merged result. The release must be marked as a pre-release and must
not replace 0.8.0 as Latest. Compare the published ZIP and checksum with the
locally verified Linux build and compare the release body with the matching
CHANGELOG section. Overlapping maintenance PRs must be reconciled with the
combined change rather than applying their changes twice.

## Local release checks

Run the following commands from the repository root:

```bash
ruff format --check .
ruff check .
mypy
pytest
python -m venv .audit-venv
.audit-venv/bin/python -m pip install -e ".[security]"
.audit-venv/bin/python -m pip freeze --exclude-editable > .audit-venv/requirements.txt
.audit-venv/bin/python -m pip_audit --strict --requirement .audit-venv/requirements.txt
python scripts/build_release.py --expected-version <version>
```

Use `.audit-venv\Scripts\python.exe` instead on Windows. Keeping the audit in a
clean environment prevents Home Assistant's test-only dependency set from
being mistaken for the integration's runtime dependencies.

The official HACS and hassfest validation requires Docker. If Docker is not
available locally, publication remains gated: the tag-triggered GitHub
workflow runs both checks before creating a release.

After the build, `dist/bosch_buderus_heating.zip` and
`dist/bosch_buderus_heating.zip.sha256` must exist. For an additional check,
extract the ZIP into an empty directory. `manifest.json` must be located at the
archive root.

## Publication

1. Ensure that the version in `manifest.json`, `pyproject.toml`, and the
   heading in `CHANGELOG.md` match.
2. Require a clean working tree and successful local checks.
3. Push the verified state to GitHub only after explicit release approval.
4. Create and push the signed or annotated version tag.

The tag starts the release workflow. It repeats tests, type checks, formatting,
linting, dependency auditing, hassfest, and HACS validation. Only then does it
create the GitHub release with the ZIP and checksum.

## Field validation before 0.8.1

I released 0.8.0 as stable after an initial local check in which beta.3
appeared to work. Apart from the version number, the integration code and
packaged assets match beta.3. The release includes all changes from the
three 0.8.0 betas, including the maintenance updates.

I have tested the notification feature extensively on my own installation
and closed #36 as implemented and tested locally.

A 48-hour connection test and preservation of the expected solar entities
after restart and reload on the affected installation still need specific
confirmation.
The original cause of the connection loss in #49 has not been established.
Issues #48 and #49 remain open for that feedback.

I tested beta.1 on my installation: notifications appeared when faults
occurred and changed to resolved when they cleared. Retained details are
kept only for the visible message and are cleared on dismissal, disabling
notifications, unloading or restart. Solar entities belong to the gateway
device. These checks do not require appliance writes or deliberately
triggering a fault.

Existing field feedback includes a Buderus installation
with a K40 gateway and an installation with two heating circuits whose reporter
confirmed the expected controls and changes appearing in MyBuderus. That report
does not enumerate every tested control or confirm restoration of every value.
Bosch systems, additional gateway and multi-source configurations, and long-term
operation still need broader field evidence. A stable release does not imply
that every supported function has been tested on every installation.
The holiday-input corrections in 0.7.2 still need confirmation on a physical
installation after an update and restart.
