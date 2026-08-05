import hashlib
import json

import pytest


CONTRACT = "contracts/fieldsignal.py"
SIGNAL_URL = "https://evidence.example/signal-001"
INSPECTION_URL = "https://evidence.example/inspection-001"
SIGNAL_BODY = "Timestamped PM2.5 readings: 84, 86, and 87 ug/m3. Co-located reference: 85 ug/m3. Freight loading active upwind."
INSPECTION_BODY = "Authorized inspector dispatched. Reference reading collected. Sensor inlet clear. Source conditions photographed and sampling cadence increased."


def account(value):
    return "0x" + bytes(value).hex()


def deploy(vm, direct_deploy, sender):
    vm.sender = sender
    return direct_deploy(CONTRACT)


def submit_incident(contract, vm, sender):
    vm.sender = sender
    signal_id = contract.submit_signal(
        "SEN-001",
        "86 ug/m3",
        "2026-08-05T12:00:00Z",
        "Three consecutive elevated readings were corroborated by a co-located reference instrument while freight loading remained active upwind.",
        SIGNAL_URL,
    )
    vm.mock_web(r".*evidence\.example/signal-001.*", {"status": 200, "body": SIGNAL_BODY})
    vm.mock_llm(
        r".*environmental sensor integrity panel.*",
        json.dumps(
            {
                "verdict": "INCIDENT",
                "severity": 78,
                "confidence": 91,
                "analysis": "Retrieved evidence corroborates a sustained PM2.5 excursion.",
                "response_code": "DISPATCH_INSPECTION",
            }
        ),
    )
    contract.resolve_signal(signal_id)
    return signal_id, "INC-0001"


def test_genesis_registers_owner_roles(direct_vm, direct_deploy, direct_alice):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    overview = contract.get_overview()
    roles = contract.get_roles(account(direct_alice))

    assert overview["stations"] == 6
    assert overview["sensors"] == 8
    assert overview["operators"] == 1
    assert overview["inspectors"] == 1
    assert roles == {
        "account": str(account(direct_alice)).lower(),
        "operator": True,
        "inspector": True,
        "owner": True,
    }


def test_only_owner_manages_roles(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    direct_vm.sender = direct_bob

    with direct_vm.expect_revert("Owner authorization required"):
        contract.set_operator(account(direct_bob), True)
    with direct_vm.expect_revert("Owner authorization required"):
        contract.set_inspector(account(direct_bob), True)


def test_readings_require_authorized_operator(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    direct_vm.sender = direct_bob

    with direct_vm.expect_revert("Authorized station operator required"):
        contract.submit_signal(
            "SEN-001",
            "86 ug/m3",
            "2026-08-05T12:00:00Z",
            "This unauthorized submission contains enough text to satisfy ordinary field context validation but must still be rejected.",
            SIGNAL_URL,
        )

    direct_vm.sender = direct_alice
    contract.set_operator(account(direct_bob), True)
    direct_vm.sender = direct_bob
    assert contract.submit_signal(
        "SEN-001",
        "86 ug/m3",
        "2026-08-05T12:00:00Z",
        "This authorized submission contains a corroborated reading and enough operational context for the protocol record.",
        SIGNAL_URL,
    ) == "SIG-0001"
    assert str(contract.get_signals()[0].reporter).lower() == account(direct_bob)


def test_contract_retrieves_and_hashes_signal_evidence(
    direct_vm, direct_deploy, direct_alice
):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    signal_id, incident_id = submit_incident(contract, direct_vm, direct_alice)
    signal = contract.get_signals()[0]
    incident = contract.get_incidents()[0]

    assert signal.id == signal_id
    assert signal.evidence_verified is True
    assert signal.evidence_digest == hashlib.sha256(SIGNAL_BODY.encode()).hexdigest()
    assert signal.response_code == "DISPATCH_INSPECTION"
    assert incident.id == incident_id
    assert incident.response_code == "DISPATCH_INSPECTION"
    assert "authorized inspector" in incident.response.lower()


def test_unreachable_signal_evidence_cannot_open_incident(
    direct_vm, direct_deploy, direct_alice
):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    signal_id = contract.submit_signal(
        "SEN-001",
        "86 ug/m3",
        "2026-08-05T12:00:00Z",
        "A claimed anomaly has context but its linked source is deliberately unavailable to the validator network for this test.",
        "https://unreachable.example/evidence",
    )
    contract.resolve_signal(signal_id)
    signal = contract.get_signals()[0]

    assert signal.verdict == "INVALID_EVIDENCE"
    assert signal.evidence_verified is False
    assert signal.incident_id == ""
    assert contract.get_overview()["incidents"] == 0


def test_inspection_assignment_requires_operator_and_registered_inspector(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    _, incident_id = submit_incident(contract, direct_vm, direct_alice)

    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("Authorized station operator required"):
        contract.assign_inspection(
            incident_id,
            account(direct_charlie),
            "A malicious self-assignment plan with enough text must not bypass the station operator authorization boundary.",
        )

    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("Authorized inspector role required"):
        contract.assign_inspection(
            incident_id,
            account(direct_bob),
            "Inspect the sensor and collect a co-located reference reading with timestamped evidence and source photographs.",
        )

    contract.set_inspector(account(direct_bob), True)
    assert contract.assign_inspection(
        incident_id,
        account(direct_bob),
        "Inspect the sensor and collect a co-located reference reading with timestamped evidence and source photographs.",
    ) == "INS-0001"
    inspection = contract.get_inspections()[0]
    assert str(inspection.assigned_by).lower() == account(direct_alice)
    assert inspection.assignee == account(direct_bob)


def test_recorded_inspector_role_is_enforced_at_submission(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    _, incident_id = submit_incident(contract, direct_vm, direct_alice)
    contract.set_inspector(account(direct_bob), True)
    inspection_id = contract.assign_inspection(
        incident_id,
        account(direct_bob),
        "Inspect the sensor and collect a co-located reference reading with timestamped evidence and source photographs.",
    )

    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("Only recorded assignee may submit"):
        contract.submit_inspection(
            inspection_id,
            "Another wallet cannot file findings for this inspection even if it has access to the public evidence and knows the incident details.",
            INSPECTION_URL,
        )

    direct_vm.sender = direct_alice
    contract.set_inspector(account(direct_bob), False)
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("Inspector role is not active"):
        contract.submit_inspection(
            inspection_id,
            "The recorded inspector cannot submit after the owner has revoked the inspector role from the on-chain authorization registry.",
            INSPECTION_URL,
        )


def test_validators_persist_required_response_result_in_incident(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    _, incident_id = submit_incident(contract, direct_vm, direct_alice)
    contract.set_inspector(account(direct_bob), True)
    inspection_id = contract.assign_inspection(
        incident_id,
        account(direct_bob),
        "Inspect the sensor and collect a co-located reference reading with timestamped evidence and source photographs.",
    )
    direct_vm.sender = direct_bob
    contract.submit_inspection(
        inspection_id,
        "The authorized inspector collected a co-located reference reading, documented source conditions, confirmed the sensor inlet was clear, and increased sampling cadence.",
        INSPECTION_URL,
    )
    direct_vm.mock_web(
        r".*evidence\.example/inspection-001.*",
        {"status": 200, "body": INSPECTION_BODY},
    )
    direct_vm.mock_llm(
        r".*Review an authorized environmental inspection.*",
        json.dumps(
            {
                "verdict": "CONFIRMED",
                "required_response_met": True,
                "analysis": "The retrieved evidence confirms the reported excursion.",
                "response_assessment": "Dispatch, reference measurement, source documentation, and increased sampling are all directly evidenced.",
            }
        ),
    )
    contract.resolve_inspection(inspection_id)

    inspection = contract.get_inspections()[0]
    incident = contract.get_incidents()[0]
    assert inspection.evidence_verified is True
    assert inspection.evidence_digest == hashlib.sha256(INSPECTION_BODY.encode()).hexdigest()
    assert inspection.required_response_met is True
    assert incident.required_response_met is True
    assert incident.response_assessment == inspection.response_assessment
    assert incident.status == "CLOSED"


def test_response_remains_action_required_when_not_proven(
    direct_vm, direct_deploy, direct_alice
):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    _, incident_id = submit_incident(contract, direct_vm, direct_alice)
    inspection_id = contract.assign_inspection(
        incident_id,
        account(direct_alice),
        "Inspect the sensor and collect a co-located reference reading with timestamped evidence and source photographs.",
    )
    contract.submit_inspection(
        inspection_id,
        "The inspector viewed the sensor enclosure but did not collect the required co-located reading or document all source conditions.",
        INSPECTION_URL,
    )
    direct_vm.mock_web(
        r".*evidence\.example/inspection-001.*",
        {"status": 200, "body": "A visual enclosure check was completed."},
    )
    direct_vm.mock_llm(
        r".*Review an authorized environmental inspection.*",
        json.dumps(
            {
                "verdict": "ESCALATE",
                "required_response_met": False,
                "analysis": "Material required actions remain undocumented.",
                "response_assessment": "No co-located reference reading or complete source-condition record is present in the retrieved evidence.",
            }
        ),
    )
    contract.resolve_inspection(inspection_id)

    incident = contract.get_incidents()[0]
    assert incident.required_response_met is False
    assert incident.status == "ACTION_REQUIRED"
