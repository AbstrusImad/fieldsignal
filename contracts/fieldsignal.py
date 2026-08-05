# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
import hashlib
from dataclasses import dataclass
from genlayer import *


EXPECTED = "[EXPECTED]"
LLM_ERROR = "[LLM_ERROR]"


@allow_storage
@dataclass
class Station:
    id: str
    name: str
    region: str
    operator: Address
    sensor_count: u32
    trust: u32


@allow_storage
@dataclass
class Sensor:
    id: str
    station_id: str
    metric: str
    unit: str
    baseline: str
    calibration_url: str
    status: str
    trust: u32
    signal_count: u32


@allow_storage
@dataclass
class Signal:
    id: str
    sensor_id: str
    reporter: Address
    value: str
    observed_at: str
    context: str
    evidence_url: str
    evidence_digest: str
    evidence_verified: bool
    status: str
    verdict: str
    severity: u32
    confidence: u32
    analysis: str
    response_code: str
    response: str
    incident_id: str


@allow_storage
@dataclass
class Incident:
    id: str
    signal_id: str
    station_id: str
    title: str
    severity: u32
    status: str
    response_code: str
    response: str
    required_response_met: bool
    response_assessment: str
    inspection_id: str


@allow_storage
@dataclass
class Inspection:
    id: str
    incident_id: str
    assigned_by: Address
    assignee: str
    plan: str
    findings: str
    evidence_url: str
    evidence_digest: str
    evidence_verified: bool
    status: str
    verdict: str
    analysis: str
    required_response_met: bool
    response_assessment: str


class FieldSignal(gl.Contract):
    owner: Address
    stations: TreeMap[str, Station]
    sensors: TreeMap[str, Sensor]
    signals: TreeMap[str, Signal]
    incidents: TreeMap[str, Incident]
    inspections: TreeMap[str, Inspection]
    operators: TreeMap[str, bool]
    inspectors: TreeMap[str, bool]
    station_ids: DynArray[str]
    sensor_ids: DynArray[str]
    signal_ids: DynArray[str]
    incident_ids: DynArray[str]
    inspection_ids: DynArray[str]
    operator_accounts: DynArray[str]
    inspector_accounts: DynArray[str]

    def __init__(self):
        self.owner = gl.message.sender_address
        self.station_ids = []
        self.sensor_ids = []
        self.signal_ids = []
        self.incident_ids = []
        self.inspection_ids = []
        self.operator_accounts = []
        self.inspector_accounts = []

        owner_key = self._account_key(self.owner)
        self.operators[owner_key] = True
        self.inspectors[owner_key] = True
        self.operator_accounts.append(owner_key)
        self.inspector_accounts.append(owner_key)

        self._station("STA-001", "Canal East Air Mast", "Riverside industrial edge")
        self._station("STA-002", "North Orchard Soil Array", "Peri-urban food belt")
        self._station("STA-003", "Harbor Inlet Buoy", "Coastal freight corridor")
        self._station("STA-004", "Central Heat Spine", "Dense residential core")
        self._station("STA-005", "Wetland Gate Monitor", "Protected floodplain")
        self._station("STA-006", "Hillcrest Wind Post", "Upland residential ridge")
        specs = [
            ("SEN-001", "STA-001", "PM2.5", "ug/m3", "8-18"),
            ("SEN-002", "STA-001", "NO2", "ppb", "12-30"),
            ("SEN-003", "STA-002", "Soil moisture", "%", "28-52"),
            ("SEN-004", "STA-003", "Dissolved oxygen", "mg/L", "6.5-9.0"),
            ("SEN-005", "STA-004", "Wet bulb temperature", "C", "12-24"),
            ("SEN-006", "STA-005", "Water level", "m", "0.4-1.8"),
            ("SEN-007", "STA-006", "Wind speed", "m/s", "1-14"),
            ("SEN-008", "STA-003", "Turbidity", "NTU", "1-12"),
        ]
        for spec in specs:
            self._sensor(*spec)

    def _account_key(self, account) -> str:
        if isinstance(account, str):
            return account.lower()
        return str(account).lower()

    def _station(self, item_id: str, name: str, region: str) -> None:
        self.station_ids.append(item_id)
        self.stations[item_id] = Station(
            item_id, name, region, self.owner, u32(0), u32(82)
        )

    def _sensor(
        self,
        item_id: str,
        station_id: str,
        metric: str,
        unit: str,
        baseline: str,
    ) -> None:
        self.sensor_ids.append(item_id)
        self.sensors[item_id] = Sensor(
            item_id,
            station_id,
            metric,
            unit,
            baseline,
            "https://raw.githubusercontent.com/AbstrusImad/fieldsignal/main/docs/evidence/calibration-registry.md",
            "ACTIVE",
            u32(80),
            u32(0),
        )
        station = self.stations[station_id]
        station.sensor_count += u32(1)
        self.stations[station_id] = station

    def _text(self, value: str, label: str, minimum: int, maximum: int) -> None:
        length = len(value.strip())
        if length < minimum or length > maximum:
            raise gl.vm.UserError(
                f"{EXPECTED} {label} must be {minimum}-{maximum} characters"
            )

    def _https(self, value: str) -> None:
        if not value.startswith("https://"):
            raise gl.vm.UserError(f"{EXPECTED} Public URL must use HTTPS")

    def _owner_only(self) -> None:
        if gl.message.sender_address != self.owner:
            raise gl.vm.UserError(f"{EXPECTED} Owner authorization required")

    def _is_operator(self, account: Address) -> bool:
        key = self._account_key(account)
        return key in self.operators and self.operators[key]

    def _is_inspector(self, account: Address) -> bool:
        key = self._account_key(account)
        return key in self.inspectors and self.inspectors[key]

    def _require_station_operator(self, station_id: str) -> None:
        station = self.stations[station_id]
        sender = gl.message.sender_address
        if sender != station.operator and not self._is_operator(sender):
            raise gl.vm.UserError(
                f"{EXPECTED} Authorized station operator required"
            )

    def _canonical_response(self, response_code: str) -> str:
        responses = {
            "LOG_ONLY": "Record the verified reading and retain routine sampling cadence.",
            "INCREASE_MONITORING": "Increase sampling cadence, compare neighboring sensors, and publish a four-hour follow-up record.",
            "DISPATCH_INSPECTION": "Dispatch an authorized inspector, collect a co-located reference reading, and document the source conditions.",
            "ISOLATE_SENSOR": "Quarantine the sensor, suspend automated actions from its readings, and require verified recalibration before restoration.",
            "EVIDENCE_REQUIRED": "Replace the evidence source with a publicly retrievable record before operational action.",
        }
        return responses[response_code]

    def _response_matches(self, verdict: str, response_code: str) -> bool:
        if verdict == "NORMAL":
            return response_code in ("LOG_ONLY", "INCREASE_MONITORING")
        if verdict == "WATCH":
            return response_code in ("INCREASE_MONITORING", "DISPATCH_INSPECTION")
        if verdict == "INCIDENT":
            return response_code in ("DISPATCH_INSPECTION", "ISOLATE_SENSOR")
        if verdict == "QUARANTINE":
            return response_code == "ISOLATE_SENSOR"
        return verdict == "INVALID_EVIDENCE" and response_code == "EVIDENCE_REQUIRED"

    @gl.public.write
    def set_operator(self, account: str, enabled: bool) -> None:
        self._owner_only()
        key = self._account_key(account)
        if key not in self.operators:
            self.operator_accounts.append(key)
        self.operators[key] = enabled

    @gl.public.write
    def set_inspector(self, account: str, enabled: bool) -> None:
        self._owner_only()
        key = self._account_key(account)
        if key not in self.inspectors:
            self.inspector_accounts.append(key)
        self.inspectors[key] = enabled

    @gl.public.write
    def set_station_operator(self, station_id: str, operator: Address) -> None:
        self._owner_only()
        if station_id not in self.stations:
            raise gl.vm.UserError(f"{EXPECTED} Station not found")
        if not self._is_operator(operator):
            raise gl.vm.UserError(f"{EXPECTED} Operator role is not active")
        station = self.stations[station_id]
        station.operator = operator
        self.stations[station_id] = station

    @gl.public.write
    def enroll_sensor(
        self,
        station_id: str,
        metric: str,
        unit: str,
        baseline: str,
        calibration_url: str,
    ) -> str:
        if station_id not in self.stations:
            raise gl.vm.UserError(f"{EXPECTED} Station not found")
        self._require_station_operator(station_id)
        self._text(metric, "Metric", 2, 60)
        self._text(unit, "Unit", 1, 20)
        self._text(baseline, "Baseline", 2, 100)
        self._https(calibration_url)
        item_id = f"SEN-{len(self.sensor_ids)+1:03d}"
        self.sensor_ids.append(item_id)
        self.sensors[item_id] = Sensor(
            item_id,
            station_id,
            metric.strip(),
            unit.strip(),
            baseline.strip(),
            calibration_url.strip(),
            "ACTIVE",
            u32(60),
            u32(0),
        )
        station = self.stations[station_id]
        station.sensor_count += u32(1)
        self.stations[station_id] = station
        return item_id

    @gl.public.write
    def submit_signal(
        self,
        sensor_id: str,
        value: str,
        observed_at: str,
        context: str,
        evidence_url: str,
    ) -> str:
        if sensor_id not in self.sensors:
            raise gl.vm.UserError(f"{EXPECTED} Sensor not found")
        sensor = self.sensors[sensor_id]
        self._require_station_operator(sensor.station_id)
        if sensor.status not in ("ACTIVE", "CALIBRATION_DUE"):
            raise gl.vm.UserError(f"{EXPECTED} Sensor cannot submit readings")
        self._text(value, "Value", 1, 40)
        self._text(observed_at, "Observed at", 20, 40)
        self._text(context, "Context", 60, 1200)
        self._https(evidence_url)
        item_id = f"SIG-{len(self.signal_ids)+1:04d}"
        self.signal_ids.append(item_id)
        self.signals[item_id] = Signal(
            item_id,
            sensor_id,
            gl.message.sender_address,
            value.strip(),
            observed_at.strip(),
            context.strip(),
            evidence_url.strip(),
            "",
            False,
            "PENDING",
            "",
            u32(0),
            u32(0),
            "",
            "",
            "",
            "",
        )
        sensor.signal_count += u32(1)
        self.sensors[sensor_id] = sensor
        return item_id

    @gl.public.write
    def resolve_signal(self, signal_id: str) -> None:
        if signal_id not in self.signals:
            raise gl.vm.UserError(f"{EXPECTED} Signal not found")
        signal = self.signals[signal_id]
        if signal.status != "PENDING":
            raise gl.vm.UserError(f"{EXPECTED} Signal not pending")
        sensor = self.sensors[signal.sensor_id]
        station = self.stations[sensor.station_id]

        def assess() -> dict:
            try:
                page = gl.nondet.web.render(
                    signal.evidence_url, mode="text", wait_after_loaded="2s"
                )
            except Exception:
                return {
                    "verdict": "INVALID_EVIDENCE",
                    "severity": 0,
                    "confidence": 100,
                    "analysis": "The linked public evidence could not be retrieved by validators.",
                    "response_code": "EVIDENCE_REQUIRED",
                    "evidence_digest": "",
                }
            page_text = str(page)
            digest = hashlib.sha256(page_text.encode()).hexdigest()
            result = gl.nondet.exec_prompt(
                f"""Act as an environmental sensor integrity panel. Use only the retrieved evidence and the authenticated on-chain record.
STATION: {station.name}, {station.region}. SENSOR: {sensor.metric} {sensor.unit}; baseline {sensor.baseline}; trust {sensor.trust}.
AUTHORIZED REPORTER: {signal.reporter}. READING: {signal.value} at {signal.observed_at}. CONTEXT: {signal.context}.
RETRIEVED EVIDENCE SHA256: {digest}. EVIDENCE CONTENT: <evidence>{page_text[:16000]}</evidence>
Return JSON {{"verdict":"NORMAL|WATCH|INCIDENT|QUARANTINE","severity":0-100,"confidence":0-100,"analysis":"under 500 chars","response_code":"LOG_ONLY|INCREASE_MONITORING|DISPATCH_INSPECTION|ISOLATE_SENSOR"}}.
The verdict and response code must be supported by concrete facts in the retrieved evidence. INCIDENT requires operational intervention. QUARANTINE requires evidence of sensor integrity failure.""",
                response_format="json",
            )
            if not isinstance(result, dict):
                raise gl.vm.UserError(f"{LLM_ERROR} Invalid assessment")
            verdict = str(result.get("verdict", "")).upper()
            response_code = str(result.get("response_code", "")).upper()
            if verdict not in ("NORMAL", "WATCH", "INCIDENT", "QUARANTINE"):
                raise gl.vm.UserError(f"{LLM_ERROR} Invalid verdict")
            if not self._response_matches(verdict, response_code):
                raise gl.vm.UserError(f"{LLM_ERROR} Response does not match verdict")
            return {
                "verdict": verdict,
                "severity": max(0, min(100, int(result.get("severity", 0)))),
                "confidence": max(0, min(100, int(result.get("confidence", 0)))),
                "analysis": str(result.get("analysis", ""))[:500],
                "response_code": response_code,
                "evidence_digest": digest,
            }

        def validate(leader_result: gl.vm.Result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                independent = assess()
                leader = leader_result.calldata
                return (
                    leader["verdict"] == independent["verdict"]
                    and leader["response_code"] == independent["response_code"]
                    and leader["evidence_digest"] == independent["evidence_digest"]
                    and abs(int(leader["severity"]) - independent["severity"]) <= 15
                    and abs(int(leader["confidence"]) - independent["confidence"]) <= 20
                )
            except Exception:
                return False

        decision = gl.vm.run_nondet_unsafe(assess, validate)
        signal.verdict = decision["verdict"]
        signal.severity = u32(decision["severity"])
        signal.confidence = u32(decision["confidence"])
        signal.analysis = decision["analysis"]
        signal.response_code = decision["response_code"]
        signal.response = self._canonical_response(signal.response_code)
        signal.evidence_digest = decision["evidence_digest"]
        signal.evidence_verified = len(signal.evidence_digest) == 64
        signal.status = "RESOLVED"

        if signal.verdict in ("INCIDENT", "QUARANTINE"):
            incident_id = f"INC-{len(self.incident_ids)+1:04d}"
            self.incident_ids.append(incident_id)
            self.incidents[incident_id] = Incident(
                incident_id,
                signal.id,
                station.id,
                f"{sensor.metric} anomaly at {station.name}",
                signal.severity,
                "OPEN",
                signal.response_code,
                signal.response,
                False,
                "",
                "",
            )
            signal.incident_id = incident_id
        if signal.verdict == "QUARANTINE":
            sensor.status = "QUARANTINED"
            sensor.trust = u32(max(0, int(sensor.trust) - 20))
        elif signal.verdict == "NORMAL":
            sensor.trust = u32(min(100, int(sensor.trust) + 2))
        self.signals[signal.id] = signal
        self.sensors[sensor.id] = sensor

    @gl.public.write
    def assign_inspection(
        self, incident_id: str, assignee: str, plan: str
    ) -> str:
        if incident_id not in self.incidents:
            raise gl.vm.UserError(f"{EXPECTED} Incident not found")
        incident = self.incidents[incident_id]
        self._require_station_operator(incident.station_id)
        if incident.inspection_id != "":
            raise gl.vm.UserError(f"{EXPECTED} Inspection already assigned")
        if not self._is_inspector(assignee):
            raise gl.vm.UserError(f"{EXPECTED} Authorized inspector role required")
        self._text(plan, "Plan", 60, 1200)
        item_id = f"INS-{len(self.inspection_ids)+1:04d}"
        self.inspection_ids.append(item_id)
        self.inspections[item_id] = Inspection(
            item_id,
            incident_id,
            gl.message.sender_address,
            self._account_key(assignee),
            plan.strip(),
            "",
            "",
            "",
            False,
            "ASSIGNED",
            "",
            "",
            False,
            "",
        )
        incident.inspection_id = item_id
        incident.status = "INSPECTION"
        self.incidents[incident.id] = incident
        return item_id

    @gl.public.write
    def submit_inspection(
        self,
        inspection_id: str,
        findings: str,
        evidence_url: str,
    ) -> None:
        if inspection_id not in self.inspections:
            raise gl.vm.UserError(f"{EXPECTED} Inspection not found")
        inspection = self.inspections[inspection_id]
        if inspection.status != "ASSIGNED":
            raise gl.vm.UserError(f"{EXPECTED} Inspection not assigned")
        if self._account_key(gl.message.sender_address) != inspection.assignee:
            raise gl.vm.UserError(f"{EXPECTED} Only recorded assignee may submit")
        if not self._is_inspector(gl.message.sender_address):
            raise gl.vm.UserError(f"{EXPECTED} Inspector role is not active")
        self._text(findings, "Findings", 100, 1800)
        self._https(evidence_url)
        inspection.findings = findings.strip()
        inspection.evidence_url = evidence_url.strip()
        inspection.status = "PENDING_REVIEW"
        self.inspections[inspection.id] = inspection

    @gl.public.write
    def resolve_inspection(self, inspection_id: str) -> None:
        if inspection_id not in self.inspections:
            raise gl.vm.UserError(f"{EXPECTED} Inspection not found")
        inspection = self.inspections[inspection_id]
        if inspection.status != "PENDING_REVIEW":
            raise gl.vm.UserError(f"{EXPECTED} Inspection not ready")
        incident = self.incidents[inspection.incident_id]
        signal = self.signals[incident.signal_id]
        sensor = self.sensors[signal.sensor_id]

        def assess() -> dict:
            try:
                page = gl.nondet.web.render(
                    inspection.evidence_url, mode="text", wait_after_loaded="2s"
                )
            except Exception:
                return {
                    "verdict": "INVALID_EVIDENCE",
                    "required_response_met": False,
                    "analysis": "The inspection evidence could not be retrieved by validators.",
                    "response_assessment": "Required response remains unverified because the linked evidence is unavailable.",
                    "evidence_digest": "",
                }
            page_text = str(page)
            digest = hashlib.sha256(page_text.encode()).hexdigest()
            result = gl.nondet.exec_prompt(
                f"""Review an authorized environmental inspection using only the retrieved evidence.
INCIDENT: {incident.title}. REQUIRED RESPONSE CODE: {incident.response_code}. REQUIRED RESPONSE: {incident.response}.
RECORDED INSPECTOR: {inspection.assignee}. PLAN: {inspection.plan}. FINDINGS: {inspection.findings}.
RETRIEVED EVIDENCE SHA256: {digest}. EVIDENCE CONTENT: <evidence>{page_text[:16000]}</evidence>
Return JSON {{"verdict":"CONFIRMED|FALSE_ALARM|RECALIBRATE|ESCALATE","required_response_met":true|false,"analysis":"under 500 chars","response_assessment":"under 300 chars citing which required actions are or are not evidenced"}}.
Set required_response_met true only when the evidence directly proves every material action in the required response. ESCALATE when a real incident remains insufficiently addressed.""",
                response_format="json",
            )
            if not isinstance(result, dict):
                raise gl.vm.UserError(f"{LLM_ERROR} Invalid review")
            verdict = str(result.get("verdict", "")).upper()
            if verdict not in ("CONFIRMED", "FALSE_ALARM", "RECALIBRATE", "ESCALATE"):
                raise gl.vm.UserError(f"{LLM_ERROR} Invalid verdict")
            met = bool(result.get("required_response_met", False))
            assessment = str(result.get("response_assessment", ""))[:300]
            if len(assessment.strip()) < 30:
                raise gl.vm.UserError(f"{LLM_ERROR} Response assessment is incomplete")
            return {
                "verdict": verdict,
                "required_response_met": met,
                "analysis": str(result.get("analysis", ""))[:500],
                "response_assessment": assessment,
                "evidence_digest": digest,
            }

        def validate(leader_result: gl.vm.Result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                independent = assess()
                leader = leader_result.calldata
                return (
                    leader["verdict"] == independent["verdict"]
                    and bool(leader["required_response_met"])
                    == independent["required_response_met"]
                    and leader["evidence_digest"] == independent["evidence_digest"]
                )
            except Exception:
                return False

        decision = gl.vm.run_nondet_unsafe(assess, validate)
        inspection.verdict = decision["verdict"]
        inspection.analysis = decision["analysis"]
        inspection.required_response_met = decision["required_response_met"]
        inspection.response_assessment = decision["response_assessment"]
        inspection.evidence_digest = decision["evidence_digest"]
        inspection.evidence_verified = len(inspection.evidence_digest) == 64
        inspection.status = "RESOLVED"

        incident.required_response_met = inspection.required_response_met
        incident.response_assessment = inspection.response_assessment
        incident.status = (
            "CLOSED"
            if inspection.evidence_verified
            and inspection.required_response_met
            and inspection.verdict in ("CONFIRMED", "FALSE_ALARM")
            else "ACTION_REQUIRED"
        )
        if inspection.verdict == "FALSE_ALARM" and inspection.evidence_verified:
            sensor.status = "ACTIVE"
            sensor.trust = u32(max(0, int(sensor.trust) - 5))
        elif inspection.verdict == "RECALIBRATE":
            sensor.status = "CALIBRATION_DUE"
        self.inspections[inspection.id] = inspection
        self.incidents[incident.id] = incident
        self.sensors[sensor.id] = sensor

    @gl.public.view
    def get_overview(self) -> dict:
        return {
            "stations": len(self.station_ids),
            "sensors": len(self.sensor_ids),
            "active_sensors": sum(
                1 for item_id in self.sensor_ids if self.sensors[item_id].status == "ACTIVE"
            ),
            "signals": len(self.signal_ids),
            "pending_signals": sum(
                1 for item_id in self.signal_ids if self.signals[item_id].status == "PENDING"
            ),
            "incidents": len(self.incident_ids),
            "open_incidents": sum(
                1 for item_id in self.incident_ids if self.incidents[item_id].status != "CLOSED"
            ),
            "inspections": len(self.inspection_ids),
            "operators": sum(
                1 for key in self.operator_accounts if self.operators[key]
            ),
            "inspectors": sum(
                1 for key in self.inspector_accounts if self.inspectors[key]
            ),
        }

    @gl.public.view
    def get_roles(self, account: str) -> dict:
        key = self._account_key(account)
        return {
            "account": key,
            "operator": key in self.operators and self.operators[key],
            "inspector": key in self.inspectors and self.inspectors[key],
            "owner": key == self._account_key(self.owner),
        }

    @gl.public.view
    def get_stations(self) -> list:
        return [self.stations[item_id] for item_id in self.station_ids]

    @gl.public.view
    def get_sensors(self) -> list:
        return [self.sensors[item_id] for item_id in self.sensor_ids]

    @gl.public.view
    def get_signals(self) -> list:
        return [self.signals[item_id] for item_id in self.signal_ids]

    @gl.public.view
    def get_incidents(self) -> list:
        return [self.incidents[item_id] for item_id in self.incident_ids]

    @gl.public.view
    def get_inspections(self) -> list:
        return [self.inspections[item_id] for item_id in self.inspection_ids]
