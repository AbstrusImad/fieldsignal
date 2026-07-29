# FieldSignal

**Environmental observation becomes trusted action only after correlation.**

[Live application](https://abstrusimad.github.io/fieldsignal/) | [StudioNet contract](https://explorer-studio.genlayer.com/address/0x66127559067cB46dA87E974fb598ba0a44fBA75C)

FieldSignal is a GenLayer-native environmental sensor integrity and incident-response network. Operators enroll calibrated instruments, transmit contextual readings, and ask validators to distinguish a credible anomaly from normal conditions or sensor failure. Consensus changes operational state: it can watch a signal, open an incident, quarantine an instrument, dispatch an inspection, and resolve field evidence into a confirmed event, false alarm, recalibration order, or escalation.

## Live StudioNet state

| Resource | Value |
| --- | --- |
| Contract | `0x66127559067cB46dA87E974fb598ba0a44fBA75C` |
| Deployment transaction | `0xf9b20fdbba84dbf783c4b396c14ebfd5636ab113f7fb866eb7ef7ee26728381c` |
| Stations / sensors | 6 / 8 |
| Signals / incidents | 3 / 2 |
| Inspections | 1 |
| Accepted activity transactions | 8 |

The frontend reads these records from StudioNet and contains no mocked protocol dataset.

## Intelligence pipeline

```text
Calibrated sensor + reading + time + context + evidence
                           |
                           v
            validator environmental correlation
                           |
           NORMAL / WATCH / INCIDENT / QUARANTINE
                           |
                 field inspection assignment
                           |
                           v
   CONFIRMED / FALSE_ALARM / RECALIBRATE / ESCALATE
```

Validator output persists severity, confidence, reasoning, response instructions, sensor trust, quarantine state, incident status, and inspection outcome. Deterministic guards protect identifiers, lifecycle transitions, input bounds, and HTTPS evidence.

## Interface

FieldSignal uses a technical blueprint language built around a two-axis decision field. The landing places the connected wallet as an operator origin; the application then plots every live sensor by protocol trust and corroboration history across four operational quadrants. Signal traces use a horizontal examination register, incidents and inspections follow a connected response plan, and every write exposes signature, consensus, acceptance, or failure in a stable execution title block.

The design is responsive without changing its information model: the field becomes a square mobile chart and its active sensor annotation moves below it. Wallet sessions persist across refresh.

## Design reservation

| Property | Reserved value |
| --- | --- |
| Primary style | `blueprint-style` |
| Layout skeleton | `quadrant-decision-field` |
| Reservation | `design-fieldsignal-redesign-002` |

## Verify

```bash
genvm-lint check contracts/fieldsignal.py
python -m pytest tests/direct -q
cd app && pnpm install && pnpm build
```

Private keys are loaded only by ignored local deployment scripts. The browser bundle contains public addresses only.

## License

MIT
