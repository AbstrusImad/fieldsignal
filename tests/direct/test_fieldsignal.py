import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pytest

CONTRACT = "contracts/fieldsignal.py"
ROOT = Path(__file__).resolve().parents[2]


def deploy(vm, direct_deploy, sender):
    vm.sender = sender
    return direct_deploy(CONTRACT, False)


def migration_payload():
    data = json.loads((ROOT / "deployments/migration-payload.json").read_text())
    payload = json.dumps(data, separators=(",", ":"))
    return data, payload, hashlib.sha256(payload.encode()).hexdigest()


def plain(record):
    value = asdict(record)
    for key in ("operator", "assignee"):
        if key in value:
            value[key] = str(value[key]).lower()
    return value


def test_genesis(direct_vm, direct_deploy, direct_alice):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    assert contract.get_overview()["stations"] == 6
    assert len(contract.get_sensors()) == 8


def test_enroll_and_submit_signal(direct_vm, direct_deploy, direct_alice):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    assert (
        contract.enroll_sensor(
            "STA-001",
            "Black carbon",
            "ug/m3",
            "0.2-1.4",
            "https://example.org/calibration",
        )
        == "SEN-009"
    )
    signal_id = contract.submit_signal(
        "SEN-001",
        "86 ug/m3",
        "2026-07-29T04:00:00Z",
        "Three consecutive elevated readings occurred downwind of active freight loading while nearby sensors also rose above baseline.",
        "https://example.org/signal",
    )
    assert signal_id == "SIG-0001"


def test_consensus_incident(direct_vm, direct_deploy, direct_alice):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    signal_id = contract.submit_signal(
        "SEN-001",
        "86 ug/m3",
        "2026-07-29T04:00:00Z",
        "Three consecutive elevated readings occurred downwind of active freight loading while nearby sensors also rose above baseline.",
        "https://example.org/signal",
    )
    direct_vm.mock_llm(
        r".*environmental sensor integrity panel.*",
        json.dumps(
            {
                "verdict": "INCIDENT",
                "severity": 78,
                "confidence": 86,
                "analysis": "Corroborated excursion.",
                "response": "Dispatch field verification and notify nearby operators.",
            }
        ),
    )
    contract.resolve_signal(signal_id)
    assert contract.get_overview()["incidents"] == 1


def test_migration_preserves_every_record(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    contract = direct_deploy(CONTRACT, True)
    data, payload, snapshot_hash = migration_payload()
    contract.import_snapshot(payload, snapshot_hash)
    overview = contract.get_overview()

    assert overview["stations"] == 6
    assert overview["sensors"] == 8
    assert overview["signals"] == 5
    assert overview["incidents"] == 2
    assert overview["inspections"] == 1
    assert overview["migration_source_network"] == "StudioNet"
    assert overview["migration_source_transactions"] == 8
    assert overview["migration_snapshot_hash"] == snapshot_hash
    assert overview["migration_complete"] is True

    pairs = (
        (contract.get_stations(), data["stations"]),
        (contract.get_sensors(), data["sensors"]),
        (contract.get_signals(), data["signals"]),
        (contract.get_incidents(), data["incidents"]),
        (contract.get_inspections(), data["inspections"]),
    )
    for actual, expected in pairs:
        assert [plain(record) for record in actual] == expected


def test_migration_rejects_wrong_hash_and_second_import(
    direct_vm,
    direct_deploy,
    direct_alice,
):
    direct_vm.sender = direct_alice
    contract = direct_deploy(CONTRACT, True)
    _, payload, snapshot_hash = migration_payload()
    with pytest.raises(Exception):
        contract.import_snapshot(payload, "0" * 64)
    contract.import_snapshot(payload, snapshot_hash)
    with pytest.raises(Exception):
        contract.import_snapshot(payload, snapshot_hash)
