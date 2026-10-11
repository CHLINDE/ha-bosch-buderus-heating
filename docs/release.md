# Creating a release

Releases are built from a verified Git tag. The HACS archive contains the
integration directly at its root and is published together with a SHA-256
checksum file.

## 0.8.1-beta.1 verification

I prepared this beta on 2026-10-11 with PointT robustness and request use as
its main focus. It separates nonessential reads from functional discovery,
recovers pending metadata without a restart, preserves entity identities and
stops repeating successful reviewed metadata reads. The full policy, including
paths, deadlines, exception cases and measured savings, is in
[Request behavior and recovery](request-behavior.md).

This version is a pre-release; **0.8.0 remains Stable/Latest**. The combined
release branch is
`codex/release-v0.8.1-beta.1`. Other working checkouts are unaffected.

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
