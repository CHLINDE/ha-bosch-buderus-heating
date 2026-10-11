# Season switching

The **Season switching** select controls the central season setting of one
gateway, using `/system/seasonOptimizer/mode`. It appears only when that exact
resource is discovered with string options and write permission. It does not
create a separate setting for each heating circuit.

| Offered code | English label | German label |
| --- | --- | --- |
| `off` | Heating/cooling off | Heizen/Kühlen aus |
| `automatic` | Automatic | Automatisch |
| `forcedHeat` | Heating only | Nur Heizbetrieb |
| `forcedCool` | Cooling only | Nur Kühlbetrieb |

Only options offered by the gateway appear. An installation offering only
`off`, `automatic` and `forcedHeat` does not receive a cooling option.
As with existing enum controls, additional advertised codes remain available
under their own text. Unoffered options are rejected, and options refresh with
the resource's metadata during normal polling.

Heating only enables the heating season. The heating circuit's operation mode,
schedule, target temperature and other operating conditions still determine
heat demand. It does not command continuous compressor operation. Automatic
returns season selection to the controller. This select does not write the
domestic-hot-water settings or change heating/cooling thresholds.

The existing **Current heating/cooling status** sensor reads
`/system/globalSeasonOptimizer/currentMode`. It displays the actual
`off`, `heating` or `cooling` status separately from the requested season
setting. Existing legacy status codes and entity identities are preserved.
This diagnostic sensor remains disabled by default; enable it in the entity
settings if desired. Existing user choices about entity activation are kept.

The setting retains its normal five-minute polling interval, or ten minutes
with the cloud-friendly profile. A change uses the shared validated write
service: at most one PUT, followed by read-back of the same setting. The select
updates only after that confirmation. Actual operating status changes on its
normal poll, without being inferred from the chosen setting. No additional
background cloud requests are introduced.

An unavailable resource, revoked write permission or cloud rate-limit pause
prevents a write. A missing read-back confirmation reports an error rather
than claiming success. Diagnostics show the control's eligibility, known
offered options and the count of other options, without exporting current
settings or unknown option text.

## Evidence and limits

Local records from 2026-10-11 show a writable season setting with the options
`off`, `automatic` and `forcedHeat`. The earlier record contains
`off` and heating-circuit status `summer_idle`; the later read-back contains
`forcedHeat`, actual season status `heating` and circuit status
`heating_manual_on`. These records establish the underlying setting on that
installation. They are not a physical test of this new Home Assistant select.
Cooling and other installations require their own offered capabilities and
field validation. No raw installation exports are included in the repository.
