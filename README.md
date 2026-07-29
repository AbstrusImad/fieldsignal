# FieldSignal

**Environmental observation becomes trusted action only after correlation.**

[Live observatory](https://abstrusimad.github.io/fieldsignal/) · [StudioNet contract](https://explorer-studio.genlayer.com/address/0x66127559067cB46dA87E974fb598ba0a44fBA75C)

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

FieldSignal is designed as an instrument, not a dashboard. Wallet entry is a calibration scope; the connected app uses a radial sensor observatory, waveform correlation queue, response array, and animated consensus telemetry. Wallet sessions persist across refresh.

## Verify

```bash
genvm-lint check contracts/fieldsignal.py
python -m pytest tests/direct -q
cd app && pnpm install && pnpm build
```

Private keys are loaded only by ignored local deployment scripts. The browser bundle contains public addresses only.

## License

MIT
