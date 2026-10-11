# Architecture

Bosch/Buderus Heating contains a Home Assistant-independent PointT client in
`custom_components/bosch_buderus_heating/pointt`. That internal package owns
OAuth/PKCE, transport, PointT parsing, batch behavior, and error normalization.
The integration layer owns Home Assistant lifecycle, config flows,
coordinators, devices, entities, translations, repairs, and diagnostics.

```text
Config Flow
    -> TokenManager
    -> PointTClient
    -> DiscoveryService
    -> CapabilitySnapshot
    -> PollPlanner / ResourceStore
    -> Coordinators
    -> EntityFactory
```

## Boundaries

- Home Assistant injects its HTTP session; entity code performs no HTTP calls.
- PointT modules have no Home Assistant imports and can be tested in isolation.
- An account and brand form one config entry that may contain multiple gateways.
- Discovery follows bounded, cycle-safe references and runs only on explicit or
  infrequent events.
- For advertised heating circuits, a small catalog of core child paths is read
  even if their parent directory fails. References precede catalog paths, which
  precede other optional probes. Failed probes do not invent capabilities.
- Only curated capabilities become entities; unknown resources stay diagnostic.
- Batch item failures do not discard successful items or last good values.
- A discovered resource returning 404 becomes unavailable until its next valid
  response, with a new attempt at the next regular group poll.
- A rate limit opens a global brake and never triggers an individual-request
  storm.
- `assess_control` derives each discovered resource's current write contract;
  UI options, write validation, and diagnostics use the same assessment.
- Control platforms listen for newly eligible resources without replacing
  entity identities or registry preferences.
- Writes validate current metadata and become successful only after read-back.
- Diagnostics never expose credentials, stable personal identifiers, names, or
  raw usage profiles.

The observed resource inventory, user-facing naming rules, dynamic circuit
model, and write-release classification are maintained in
[`resource-catalog.md`](resource-catalog.md).

## Nonessential startup reads

The exact paths, lifecycle events, error policy, timing and comparison with
0.8.0 are documented in [Request behavior and recovery](request-behavior.md).

Functional discovery runs for every selected gateway before supplementary
reads receive one shared 30-second entry budget. Only the exact unused license
endpoint is omitted. Reviewed informational leaves are deferred, never whole
directories. Device product names and installed refrigerant-circuit counts
become static only after a valid read-only scalar response. Writable or
structural surprises retain normal catalog handling; references remain bounded.

`StartupSession` owns memory-only values and pending reads per entry and gateway.
Its state module, `startup_data.py`, owns retry deadlines, path reservations,
gateway fairness and cache lifetime. Consumers use explicit state transitions;
read statuses are immutable and the queue is exposed through a read-only view.
`startup_reader.py` owns supplementary batch requests, deadlines, reply
validation and bounded reference expansion. Both modules are independent of
Home Assistant. The coordinator translates authentication errors, applies the
account brake, records outcomes and merges confirmed snapshots. Sensor code
only retains existing identities and adds recovered entities.

Automatic setup retries retain this state and the account brake. A completed
load followed by reload, a restart, changed options/gateway selection or changed
credentials starts fresh metadata state; ordinary token refresh does not.
No startup cache file is written. Existing fault storage is unaffected.
The account brake is retained separately in Home Assistant memory across
explicit reloads as well, so clearing metadata does not bypass a rate limit.
Deleting the entry clears its brake; restarting Home Assistant clears memory.

Recovery runs after a gateway's normal polling work, never after a failed
functional cycle. One entry can claim at most one batch per minute, with a
30-second deadline and at most 30 paths. Gateways rotate, pending paths use
increasing per-path retry delays, and successful reads stop repeating. The
512-path discovery limit and depth-eight limit also constrain supplementary
reads and their references. No immediate GET fallback or automatic network
retry is used for these reads. Authentication refresh and account backoff
remain shared with the regular client.

Metadata timestamps record actual reads. Supplementary success neither
refreshes unrelated measurements nor confirms fault resolution. Sensor
listeners add recovered supported resources once and preserve registered IDs,
names and user enable/disable choices. Diagnostic-only values get no entities.

The local HTTP test models an already initialized gateway with 30 fast values
and two reviewed metadata leaves. It advances one hour of polling and counts
actual requests to a local server, including the 30-path batch boundary:

| Profile | Previous hourly HTTP requests | New hourly HTTP requests | Previous metadata path reads | New metadata path reads |
| --- | ---: | ---: | ---: | ---: |
| Standard | 64 | 60 | 8 | 0 |
| Cloud-friendly | 32 | 30 | 4 | 0 |

This measures steady polling after successful startup, not startup cost or
a physical installation. Smaller batches can carry metadata without needing
an extra HTTP request; in that case only requested paths and response size
decrease. Read-only product and circuit-count values no longer repeat 96 times
per day in the standard profile or 48 times in the cloud-friendly profile.

## Stable identities

Config entry: `{brand}:{stable_account_subject}`

Gateway device: `(domain, gateway_id)`

Logical entity group: `{kind}:{logical_id}` inside the stable entity key

Entity: `{gateway_id}:{logical_device}:{semantic_key}`

All entities of one gateway share its Home Assistant device. Dynamic logical
groups remain part of stable entity keys and are rendered as name prefixes.
Localized labels, model names, and live API values never participate in unique
IDs. Any future schema change requires an explicit migration and migration test.
