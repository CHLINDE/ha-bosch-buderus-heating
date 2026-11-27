# ADR 0001: Project identity and license

- Status: Accepted, amended by ADR 0005 and the display-name amendment below
- Date: 2026-08-16

## Decision

Use repository `ha-bosch-buderus-heating`, Home Assistant domain
`bosch_buderus_heating`, display name “Bosch/Buderus Heating”, internal PointT
module `custom_components.bosch_buderus_heating.pointt`, and the term “PointT
Cloud API” in technical documentation. License original work under MIT.

The project is explicitly unofficial and uses vendor marks only to describe
compatibility. Foreign code requires provenance and preserved license notices.

## Consequences

These identifiers are stable public contracts. Changes require migrations.
The internal PointT client and integration share one repository and release.

## Display-name amendment, 2026-10-25

I changed the display name to **Bosch/Buderus Home Comfort** to reflect the
broader device scope. GitHub's description now covers heating, cooling, hot
water, air treatment, water softeners and read-only wallbox monitoring.
The integration remains explicitly unofficial.

The repository stays `ha-bosch-buderus-heating`. The Home Assistant domain and
component folder remain `bosch_buderus_heating`, the archive remains
`bosch_buderus_heating.zip`, and existing URLs and technical identifiers remain
unchanged. The earlier migration requirement applies to those identifiers;
this amendment changes presentation and requires no domain migration.

Manifest, HACS metadata, translation titles, messages, README and future release
titles use the new display name. New entries receive the appropriate brand's
Home Comfort title. Existing entry titles are retained, including on
reconfiguration; user-defined device and entity names are not rewritten.
Published releases and historical release records keep their original names.

The display-name change ships with 0.8.2-beta.7. The older 0.8.1 and
0.8.2-beta.6 packages retain the former name.
