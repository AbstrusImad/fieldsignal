# FieldSignal

> **Field note 01:** a sensor reading is a claim about the physical world.
> FieldSignal makes that claim survive calibration checks, public evidence, validator reasoning, and accountable response before it becomes an incident.

[Open the live decision field](https://abstrusimad.github.io/fieldsignal/) | [Inspect the Bradbury contract](https://explorer-bradbury.genlayer.com/address/0x42a6982fA6bAD35b3FE4A0E21c162a07195D18Cb) | [Review the deployment transaction](https://explorer-bradbury.genlayer.com/tx/0xea062a0b11bb9532b6f30e2f6b0344608400aeaefd2b8f116953563b911e5356)

## 00 / The observation problem

Environmental operations often fail at the boundary between measurement and interpretation. A reading can be numerically unusual while still being harmless, or look ordinary while neighboring activity, maintenance history, and field evidence indicate a real event. Conventional alert systems usually separate those facts and leave a human operator to reconcile them after the alarm has already propagated.

FieldSignal is a GenLayer-native integrity and response protocol for that boundary. It keeps stations, instruments, contextual readings, validator conclusions, incidents, and inspections in one durable lifecycle. GenLayer intelligence is not used as a detached answer service: validator output changes sensor trust, opens incidents, quarantines instruments, assigns response work, and determines how inspection evidence affects protocol state.

## 01 / Live plate

The public deployment is populated with the verified records from the original StudioNet protocol. The frontend reads Bradbury directly and does not ship a mocked protocol dataset.

| Coordinate | Live value |
| --- | ---: |
| Network | GenLayer Bradbury Testnet |
| Contract | `0x42a6982fA6bAD35b3FE4A0E21c162a07195D18Cb` |
| Deployment transaction | `0xea062a0b11bb9532b6f30e2f6b0344608400aeaefd2b8f116953563b911e5356` |
| Migration transaction | `0x94fbf701cbd7f4f6932c00c33783663efd663a555a89fdf5ecc01c103b95d6f5` |
| Snapshot SHA-256 | `e4ac9c7255e9773df4929b7bacebdb6ea086430af2959f3c16753fd87db2f28f` |
| Monitoring stations | 6 |
| Registered sensors | 8 |
| Submitted signals | 5 |
| Durable incidents | 2 |
| Field inspections | 1 |
| Migrated records | 22 |
| Accepted source transactions | 8 |

The deployed field covers air quality, soil moisture, dissolved oxygen, wet-bulb temperature, water level, wind speed, and turbidity across industrial, agricultural, coastal, residential, wetland, and upland contexts.

## 02 / How a claim moves

```text
PHYSICAL OBSERVATION
  value + timestamp + context + HTTPS evidence
                |
                v
SIGNAL RECORD  [PENDING]
                |
                v
GENLAYER VALIDATOR CORRELATION
  station + region + metric + baseline + sensor trust
  + calibration source + observation + public evidence
                |
      +---------+----------+-----------+
      |         |          |           |
    NORMAL    WATCH     INCIDENT   QUARANTINE
      |         |          |           |
 trust +2    durable    open route   trust -20
                         |            sensor held
                         v
                 FIELD INSPECTION
            plan -> findings -> evidence
                         |
                         v
             SECOND VALIDATOR DECISION
       CONFIRMED / FALSE_ALARM / RECALIBRATE / ESCALATE
```

The first consensus decides what the observation means. The second decides what the physical inspection proves. Both decisions are normalized to bounded enums before any storage mutation occurs. On Bradbury, validators independently repeat the assessment and compare verdicts, severity, and confidence against the leader instead of accepting a well-shaped leader response on structure alone.

## 03 / Intelligence under constraint

### Signal correlation

Validators receive the station identity and region, the sensor metric and unit, its baseline band and trust score, the submitted value and timestamp, environmental context, calibration source, and public evidence URL.

The accepted output is restricted to:

| Verdict | Durable effect |
| --- | --- |
| `NORMAL` | Resolves the signal and increases sensor trust, capped at 100 |
| `WATCH` | Resolves and preserves the observation for continued monitoring |
| `INCIDENT` | Opens a durable response record with severity and instructions |
| `QUARANTINE` | Opens an incident, reduces trust, and removes the sensor from active status |

Each result also persists bounded severity, bounded confidence, analysis, and a specific response instruction. Invalid shapes, unsupported verdicts, and out-of-range values fail validation instead of entering storage.

### Inspection review

After an incident receives a field plan, the assignee publishes findings and an HTTPS evidence source. A second validator task compares those findings with the original incident and required response.

| Verdict | Durable effect |
| --- | --- |
| `CONFIRMED` | Resolves the inspection and closes the incident |
| `FALSE_ALARM` | Closes the incident and adjusts the sensor trust record |
| `RECALIBRATE` | Marks the sensor as calibration due and keeps action visible |
| `ESCALATE` | Leaves the incident in an action-required state |

This two-decision design prevents a plausible initial anomaly from becoming an unquestioned final truth.

## 04 / Contract field catalogue

The Intelligent Contract is implemented in [`contracts/fieldsignal.py`](contracts/fieldsignal.py) and stores five linked record families.

| Record | Important state |
| --- | --- |
| `Station` | region, operator, sensor count, station trust |
| `Sensor` | metric, unit, baseline, calibration source, status, trust, signal count |
| `Signal` | observation, context, evidence, verdict, severity, confidence, response |
| `Incident` | source signal, station, severity, lifecycle status, inspection link |
| `Inspection` | assignee, plan, findings, evidence, verdict, analysis |

### Public writes

| Method | Purpose | Important boundary |
| --- | --- | --- |
| `enroll_sensor` | Register a calibrated instrument at an existing station | Existing station, bounded fields, HTTPS calibration URL |
| `submit_signal` | Persist a contextual physical-world observation | Existing sensor, 60-1200 character context, HTTPS evidence |
| `resolve_signal` | Run validator correlation and mutate operational state | Signal must still be `PENDING` |
| `assign_inspection` | Attach a field plan and assignee to an incident | Incident exists and has no inspection |
| `submit_inspection` | Publish field findings and evidence | Assigned inspection, 100-1800 character findings |
| `resolve_inspection` | Run validator review of the field evidence | Inspection must be ready for review |
| `import_snapshot` | Reconstruct the verified source state once | Owner-only, migration-mode, exact hash and count guards |

### Public views

`get_overview`, `get_stations`, `get_sensors`, `get_signals`, `get_incidents`, and `get_inspections` expose JSON-safe records used by the live interface.

## 05 / Operator field kit

The interface behaves like physical environmental equipment rather than a dashboard.

- **Wallet latch:** the disconnected landing is a closed weatherproof case. Wallet authorization rotates the central latch and opens the kit; a previous connection is restored silently after refresh when the wallet still exposes the authorized account.
- **Survey file:** sensors live behind staggered index tabs. The active instrument file combines an analog trust gauge, reference tape, station punches, calibration source, report count, and a spring-loaded reading control.
- **Trace dossier:** submitted observations become stacked evidence folders containing sample labels, ink traces, validator analysis, source tape, confidence, and rubber verdict stamps.
- **Response clipboard:** incidents and inspections share one clipped field sheet with severity instruments, handwritten instructions, route thread, assignee label, and pull-tab actions.
- **Observation sheets:** writes use ruled reports and a guarded mechanical lever while enforcing the same input boundaries as the contract.
- **Execution receipt:** every write feeds a perforated receipt through signature, validator review, acceptance, or a human-readable failure.

On mobile, the case becomes a handheld vertical kit: fabric tabs move to the thumb edge, sensor folders scroll as a compact index, reports remain full-width artifacts, and the receipt reel stays attached to the active action.

## 06 / Transaction trace

```mermaid
sequenceDiagram
    actor Operator
    participant Wallet
    participant App as FieldSignal UI
    participant Contract as Intelligent Contract
    participant Validators as GenLayer Validators

    Operator->>App: Submit observation or inspection evidence
    App->>Wallet: Request signature
    Wallet-->>App: Signed Bradbury transaction
    App->>Contract: Persist pending action
    Contract->>Validators: Execute bounded reasoning task
    Validators-->>Contract: Normalized verdict and analysis
    Contract->>Contract: Apply lifecycle and trust effects
    Contract-->>App: Accepted receipt or readable rejection
    App->>App: Reload live contract state
```

The client retries transient Bradbury saturation responses with bounded backoff. Contract rejections are decoded from GenVM receipts, retain their transaction hash, and link to the canonical `/tx/<hash>` explorer route instead of collapsing failures into `[object Object]`.

## 07 / Run the instrument

### Requirements

- Node.js 20 or newer
- pnpm 9
- A browser wallet compatible with GenLayer Bradbury
- Python and GenLayer tooling for contract verification

### Frontend

```bash
cd app
pnpm install
pnpm run dev
```

Production build:

```bash
cd app
pnpm run build
```

### Environment reference

No secret belongs in the browser bundle.

| Variable | Scope | Secret |
| --- | --- | --- |
| `VITE_CONTRACT_ADDRESS` | Frontend public deployment address | No |
| `VITE_EXPLORER_URL` | Frontend public explorer base URL | No |
| `GENLAYER_PRIVATE_KEY_0` | Local deployment and seeding only | **Yes** |

Deployment scripts read `GENLAYER_PRIVATE_KEY_0` from the ignored Season 3 `.env`. Never place it in `app/.env`, committed JSON, screenshots, logs, or GitHub Actions output.

## 08 / Verify before trusting

Contract lint:

```bash
genvm-lint check contracts/fieldsignal.py
```

Focused direct tests:

```bash
python -m pytest tests/direct -q
```

Frontend production build:

```bash
cd app
pnpm run build
```

Exact network-state verification:

```bash
pnpm run snapshot:build
pnpm run verify:live
```

The browser verification pass covers the disconnected wallet gate, persistent re-entry, all six Bradbury reads, the three operational views, write forms, transaction lifecycle placement, full-width desktop rendering, and mobile overflow.

## 09 / Deploy and migrate

From the repository root:

```bash
pnpm install
pnpm run snapshot:build
pnpm run deploy
pnpm run snapshot:import
pnpm run verify:live
```

The source audit first captured all six read surfaces from StudioNet. `snapshot:build` converts that capture into one canonical 8,688-byte payload and SHA-256 manifest. The Bradbury contract starts empty in migration mode; an owner-only transaction imports exactly 6 stations, 8 sensors, 5 signals, 2 incidents, and 1 inspection. The method rejects altered hashes, unexpected source coordinates, incorrect counts, non-empty state, and repeated imports. `verify:live` then reads every collection from Bradbury and compares every field with the canonical payload.

Deployment metadata is written to `deployments/bradbury.json`; public frontend values go to the ignored `app/.env.production`. Neither file contains the private key.

## 10 / Repository bearings

```text
fieldsignal/
|-- app/                       Vue interface and Bradbury client
|   |-- src/App.vue            Wallet gate and operational surfaces
|   |-- src/services/          GenLayer reads, writes, retries, receipt errors
|   `-- .env.production        Public contract and explorer values
|-- contracts/fieldsignal.py   Intelligent Contract
|-- deployments/               Public deployment and activity receipts
|-- scripts/                   Source audit, migration, deployment, verification
|-- tests/direct/              Direct-mode contract tests
`-- README.md                  This field notebook
```

## 11 / Security perimeter

- Private keys remain outside the repository and are consumed only by local scripts.
- User input is bounded before validator execution.
- Calibration and evidence sources must use HTTPS.
- Lifecycle guards prevent duplicate resolution and duplicate inspection assignment.
- Validator results are schema-checked, enum-restricted, and independently compared before state mutation.
- Migration is owner-only, one-use, hash-locked, source-bound, and count-checked.
- Trust and score updates are clamped to valid ranges.
- The frontend displays public addresses and transaction hashes only.

## 12 / Public coordinates

- **Live application:** https://abstrusimad.github.io/fieldsignal/
- **Repository:** https://github.com/AbstrusImad/fieldsignal
- **Publishing account:** [@AbstrusImad](https://github.com/AbstrusImad)
- **Bradbury explorer:** https://explorer-bradbury.genlayer.com
- **Contract:** `0x42a6982fA6bAD35b3FE4A0E21c162a07195D18Cb`
- **Deployment:** https://explorer-bradbury.genlayer.com/tx/0xea062a0b11bb9532b6f30e2f6b0344608400aeaefd2b8f116953563b911e5356
- **State import:** https://explorer-bradbury.genlayer.com/tx/0x94fbf701cbd7f4f6932c00c33783663efd663a555a89fdf5ecc01c103b95d6f5
- **Archived source:** https://explorer-studio.genlayer.com/address/0x66127559067cB46dA87E974fb598ba0a44fBA75C

---

FieldSignal is released under the MIT License. The contract is public, the evidence trail is inspectable, and the final authority remains the state transition accepted by GenLayer validators.
