# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
import hashlib
import json
from dataclasses import dataclass
from genlayer import *

EXPECTED = "[EXPECTED]"
LLM_ERROR = "[LLM_ERROR]"
SOURCE_CONTRACT = "0x66127559067cb46da87e974fb598ba0a44fba75c"


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
    evidence_fingerprint: str
    status: str
    verdict: str
    severity: u32
    confidence: u32
    analysis: str
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
    response: str
    inspection_id: str


@allow_storage
@dataclass
class Inspection:
    id: str
    incident_id: str
    assignee: Address
    plan: str
    findings: str
    evidence_url: str
    evidence_fingerprint: str
    status: str
    verdict: str
    analysis: str
    response_assessment: str


class FieldSignal(gl.Contract):
    owner: Address
    stations: TreeMap[str, Station]
    sensors: TreeMap[str, Sensor]
    signals: TreeMap[str, Signal]
    incidents: TreeMap[str, Incident]
    inspections: TreeMap[str, Inspection]
    station_ids: DynArray[str]
    sensor_ids: DynArray[str]
    signal_ids: DynArray[str]
    incident_ids: DynArray[str]
    inspection_ids: DynArray[str]
    migration_source_network: str
    migration_source_contract: str
    migration_source_transactions: u32
    migration_snapshot_hash: str
    migration_enabled: bool
    migration_complete: bool

    def __init__(self, migration_mode: bool):
        self.owner = gl.message.sender_address
        self.station_ids = []
        self.sensor_ids = []
        self.signal_ids = []
        self.incident_ids = []
        self.inspection_ids = []
        self.migration_source_network = ""
        self.migration_source_contract = ""
        self.migration_source_transactions = u32(0)
        self.migration_snapshot_hash = ""
        self.migration_enabled = migration_mode
        self.migration_complete = False

        if migration_mode:
            return

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

    def _station(self, item_id: str, name: str, region: str):
        self.station_ids.append(item_id)
        self.stations[item_id] = Station(
            item_id,
            name,
            region,
            gl.message.sender_address,
            u32(0),
            u32(82),
        )

    def _sensor(
        self,
        item_id: str,
        station_id: str,
        metric: str,
        unit: str,
        baseline: str,
    ):
        self.sensor_ids.append(item_id)
        self.sensors[item_id] = Sensor(
            item_id,
            station_id,
            metric,
            unit,
            baseline,
            "https://github.com/AbstrusImad/fieldsignal",
            "ACTIVE",
            u32(80),
            u32(0),
        )
        station = self.stations[station_id]
        station.sensor_count += u32(1)
        self.stations[station_id] = station

    def _text(self, value: str, label: str, minimum: int, maximum: int):
        length = len(value.strip())
        if length < minimum or length > maximum:
            raise gl.vm.UserError(
                f"{EXPECTED} {label} must be {minimum}-{maximum} characters"
            )

    def _https(self, value: str):
        if not value.startswith("https://"):
            raise gl.vm.UserError(f"{EXPECTED} Public URL must use HTTPS")

    def _owner_only(self):
        if gl.message.sender_address != self.owner:
            raise gl.vm.UserError(f"{EXPECTED} Owner authorization required")

    def _authorized_station_operator(self, station_id: str):
        station = self.stations[station_id]
        if gl.message.sender_address != station.operator:
            raise gl.vm.UserError(
                f"{EXPECTED} Only station operator can perform this action"
            )

    def _fingerprint(self, value: str, label: str):
        if len(value) > 0 and (len(value) < 64 or len(value) > 128):
            raise gl.vm.UserError(
                f"{EXPECTED} {label} fingerprint must be 64-128 characters (SHA-256 hex)"
            )
        if len(value) > 0:
            for char in value.lower():
                if char not in "0123456789abcdef":
                    raise gl.vm.UserError(
                        f"{EXPECTED} {label} fingerprint must be hex encoded"
                    )

    def _migration_expect(self, condition: bool, message: str):
        if not condition:
            raise gl.vm.UserError(f"{EXPECTED} Migration {message}")

    @gl.public.write
    def import_snapshot(self, payload: str, expected_hash: str) -> None:
        self._owner_only()
        self._migration_expect(self.migration_enabled, "mode is disabled")
        self._migration_expect(not self.migration_complete, "is already complete")
        self._migration_expect(len(self.station_ids) == 0, "state is not empty")
        self._migration_expect(
            hashlib.sha256(payload.encode()).hexdigest() == expected_hash,
            "hash mismatch",
        )
        try:
            data = json.loads(payload)
            source = data["source"]
            overview = data["overview"]
        except Exception:
            raise gl.vm.UserError(f"{EXPECTED} Migration payload is invalid")

        self._migration_expect(source["network"] == "StudioNet", "network mismatch")
        self._migration_expect(
            source["contract"].lower() == SOURCE_CONTRACT,
            "source contract mismatch",
        )
        self._migration_expect(
            int(source["accepted_transactions"]) == 8,
            "source transaction count mismatch",
        )
        expected_counts = {
            "stations": 6,
            "sensors": 8,
            "signals": 5,
            "incidents": 2,
            "inspections": 1,
        }
        for key, count in expected_counts.items():
            self._migration_expect(len(data[key]) == count, f"{key} count mismatch")
            self._migration_expect(
                int(overview[key]) == count,
                f"{key} overview mismatch",
            )

        for record in data["stations"]:
            item = Station(
                record["id"],
                record["name"],
                record["region"],
                Address(record["operator"]),
                u32(record["sensor_count"]),
                u32(record["trust"]),
            )
            self.station_ids.append(item.id)
            self.stations[item.id] = item

        for record in data["sensors"]:
            item = Sensor(
                record["id"],
                record["station_id"],
                record["metric"],
                record["unit"],
                record["baseline"],
                record["calibration_url"],
                record["status"],
                u32(record["trust"]),
                u32(record["signal_count"]),
            )
            self.sensor_ids.append(item.id)
            self.sensors[item.id] = item

        for record in data["signals"]:
            reporter = record.get("reporter", record.get("sensor_id", ""))
            reporter_address = Address(reporter) if isinstance(reporter, str) and reporter.startswith("0x") else Address("0x0000000000000000000000000000000000000000")
            item = Signal(
                record["id"],
                record["sensor_id"],
                reporter_address,
                record["value"],
                record["observed_at"],
                record["context"],
                record["evidence_url"],
                record.get("evidence_fingerprint", ""),
                record["status"],
                record["verdict"],
                u32(record["severity"]),
                u32(record["confidence"]),
                record["analysis"],
                record["response"],
                record["incident_id"],
            )
            self.signal_ids.append(item.id)
            self.signals[item.id] = item

        for record in data["incidents"]:
            item = Incident(
                record["id"],
                record["signal_id"],
                record["station_id"],
                record["title"],
                u32(record["severity"]),
                record["status"],
                record["response"],
                record["inspection_id"],
            )
            self.incident_ids.append(item.id)
            self.incidents[item.id] = item

        for record in data["inspections"]:
            item = Inspection(
                record["id"],
                record["incident_id"],
                Address(record["assignee"]),
                record["plan"],
                record["findings"],
                record["evidence_url"],
                record.get("evidence_fingerprint", ""),
                record["status"],
                record["verdict"],
                record["analysis"],
                record.get("response_assessment", ""),
            )
            self.inspection_ids.append(item.id)
            self.inspections[item.id] = item

        self._migration_expect(
            sum(1 for item_id in self.sensor_ids if self.sensors[item_id].status == "ACTIVE")
            == int(overview["active_sensors"]),
            "active sensor count mismatch",
        )
        self._migration_expect(
            sum(1 for item_id in self.signal_ids if self.signals[item_id].status == "PENDING")
            == int(overview["pending_signals"]),
            "pending signal count mismatch",
        )
        self._migration_expect(
            sum(1 for item_id in self.incident_ids if self.incidents[item_id].status != "CLOSED")
            == int(overview["open_incidents"]),
            "open incident count mismatch",
        )
        self.migration_source_network = source["network"]
        self.migration_source_contract = source["contract"]
        self.migration_source_transactions = u32(source["accepted_transactions"])
        self.migration_snapshot_hash = expected_hash
        self.migration_complete = True

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
        self._authorized_station_operator(station_id)
        self._text(metric, "Metric", 2, 60)
        self._text(baseline, "Baseline", 2, 100)
        self._https(calibration_url)
        item_id = f"SEN-{len(self.sensor_ids)+1:03d}"
        self.sensor_ids.append(item_id)
        self.sensors[item_id] = Sensor(
            item_id,
            station_id,
            metric,
            unit,
            baseline,
            calibration_url,
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
        evidence_fingerprint: str = "",
    ) -> str:
        if sensor_id not in self.sensors:
            raise gl.vm.UserError(f"{EXPECTED} Sensor not found")
        sensor = self.sensors[sensor_id]
        self._authorized_station_operator(sensor.station_id)
        self._text(value, "Value", 1, 40)
        self._text(observed_at, "Observed at", 10, 60)
        self._text(context, "Context", 60, 1200)
        self._https(evidence_url)
        self._fingerprint(evidence_fingerprint, "Evidence")
        item_id = f"SIG-{len(self.signal_ids)+1:04d}"
        self.signal_ids.append(item_id)
        self.signals[item_id] = Signal(
            item_id,
            sensor_id,
            gl.message.sender_address,
            value,
            observed_at,
            context,
            evidence_url,
            evidence_fingerprint,
            "PENDING",
            "",
            u32(0),
            u32(0),
            "",
            "",
            "",
        )
        sensor = self.sensors[sensor_id]
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

        fingerprint_instruction = (
            f" EVIDENCE FINGERPRINT {signal.evidence_fingerprint}."
            if signal.evidence_fingerprint
            else ""
        )

        def assess() -> dict:
            result = gl.nondet.exec_prompt(
                f"""Act as an environmental sensor integrity panel. Determine whether this reading is normal, requires watch, establishes an incident, or indicates sensor quarantine.
STATION {station.name}, {station.region}. SENSOR {sensor.metric} {sensor.unit}; baseline {sensor.baseline}; trust {sensor.trust}. REPORTER {signal.reporter}.
READING {signal.value} at {signal.observed_at}. CONTEXT {signal.context}. EVIDENCE {signal.evidence_url}. CALIBRATION {sensor.calibration_url}.{fingerprint_instruction}
{"Verify that the evidence at the URL matches the provided fingerprint. If fingerprint is provided but evidence cannot be verified, note this in your analysis." if signal.evidence_fingerprint else ""}
Use web context when relevant. Return JSON {{"verdict":"NORMAL"|"WATCH"|"INCIDENT"|"QUARANTINE","severity":0-100,"confidence":0-100,"analysis":"under 500 chars","response":"specific action under 500 chars"}}.""",
                response_format="json",
            )
            if not isinstance(result, dict):
                raise gl.vm.UserError(f"{LLM_ERROR} Invalid assessment")
            verdict = str(result.get("verdict", "")).upper()
            if verdict not in ("NORMAL", "WATCH", "INCIDENT", "QUARANTINE"):
                raise gl.vm.UserError(f"{LLM_ERROR} Invalid verdict")
            return {
                "verdict": verdict,
                "severity": max(0, min(100, int(result.get("severity", 0)))),
                "confidence": max(0, min(100, int(result.get("confidence", 0)))),
                "analysis": str(result.get("analysis", ""))[:500],
                "response": str(result.get("response", ""))[:500],
            }

        def validate(result: gl.vm.Result) -> bool:
            if not isinstance(result, gl.vm.Return) or not isinstance(result.calldata, dict):
                return False
            try:
                independent = assess()
                leader = result.calldata
                return (
                    leader.get("verdict") == independent["verdict"]
                    and abs(int(leader.get("severity", -1)) - independent["severity"]) <= 20
                    and abs(int(leader.get("confidence", -1)) - independent["confidence"]) <= 25
                )
            except Exception:
                return False

        decision = gl.vm.run_nondet_unsafe(assess, validate)
        signal.verdict = decision["verdict"]
        signal.severity = u32(decision["severity"])
        signal.confidence = u32(decision["confidence"])
        signal.analysis = decision["analysis"]
        signal.response = decision["response"]
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
                signal.response,
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
    def assign_inspection(self, incident_id: str, plan: str) -> str:
        if incident_id not in self.incidents:
            raise gl.vm.UserError(f"{EXPECTED} Incident not found")
        incident = self.incidents[incident_id]
        if incident.inspection_id != "":
            raise gl.vm.UserError(f"{EXPECTED} Inspection already assigned")
        self._text(plan, "Plan", 60, 1200)
        item_id = f"INS-{len(self.inspection_ids)+1:04d}"
        self.inspection_ids.append(item_id)
        self.inspections[item_id] = Inspection(
            item_id,
            incident_id,
            gl.message.sender_address,
            plan,
            "",
            "",
            "ASSIGNED",
            "",
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
        evidence_fingerprint: str = "",
    ) -> None:
        if inspection_id not in self.inspections:
            raise gl.vm.UserError(f"{EXPECTED} Inspection not found")
        inspection = self.inspections[inspection_id]
        if inspection.status != "ASSIGNED":
            raise gl.vm.UserError(f"{EXPECTED} Inspection not assigned")
        if gl.message.sender_address != inspection.assignee:
            raise gl.vm.UserError(
                f"{EXPECTED} Only assigned inspector can submit findings"
            )
        self._text(findings, "Findings", 100, 1800)
        self._https(evidence_url)
        self._fingerprint(evidence_fingerprint, "Evidence")
        inspection.findings = findings
        inspection.evidence_url = evidence_url
        inspection.evidence_fingerprint = evidence_fingerprint
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

        fingerprint_instruction = (
            f" EVIDENCE FINGERPRINT {inspection.evidence_fingerprint}."
            if inspection.evidence_fingerprint
            else ""
        )

        def assess() -> dict:
            result = gl.nondet.exec_prompt(
                f"""Review an environmental field inspection. INCIDENT {incident.title}. REQUIRED RESPONSE {incident.response}. INSPECTOR {inspection.assignee}. FINDINGS {inspection.findings}. EVIDENCE {inspection.evidence_url}.{fingerprint_instruction}
{"Verify that the evidence at the URL matches the provided fingerprint. If fingerprint is provided but evidence cannot be verified, note this in your analysis." if inspection.evidence_fingerprint else ""}
Evaluate whether the findings adequately address the required response. Return JSON {{"verdict":"CONFIRMED"|"FALSE_ALARM"|"RECALIBRATE"|"ESCALATE","analysis":"under 500 chars","response_assessment":"under 200 chars explaining if findings address the required response"}}.""",
                response_format="json",
            )
            if not isinstance(result, dict):
                raise gl.vm.UserError(f"{LLM_ERROR} Invalid review")
            verdict = str(result.get("verdict", "")).upper()
            if verdict not in ("CONFIRMED", "FALSE_ALARM", "RECALIBRATE", "ESCALATE"):
                raise gl.vm.UserError(f"{LLM_ERROR} Invalid verdict")
            return {
                "verdict": verdict,
                "analysis": str(result.get("analysis", ""))[:500],
                "response_assessment": str(result.get("response_assessment", ""))[:200],
            }

        def validate(result: gl.vm.Result) -> bool:
            if not isinstance(result, gl.vm.Return) or not isinstance(result.calldata, dict):
                return False
            try:
                independent = assess()
                leader = result.calldata
                return (
                    leader.get("verdict") == independent["verdict"]
                    and len(independent.get("response_assessment", "")) >= 20
                )
            except Exception:
                return False

        decision = gl.vm.run_nondet_unsafe(assess, validate)
        inspection.verdict = decision["verdict"]
        inspection.analysis = decision["analysis"]
        inspection.response_assessment = decision["response_assessment"]
        inspection.status = "RESOLVED"
        incident.status = (
            "CLOSED"
            if inspection.verdict in ("CONFIRMED", "FALSE_ALARM")
            else "ACTION_REQUIRED"
        )
        if inspection.verdict == "FALSE_ALARM":
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
                1
                for item_id in self.sensor_ids
                if self.sensors[item_id].status == "ACTIVE"
            ),
            "signals": len(self.signal_ids),
            "pending_signals": sum(
                1
                for item_id in self.signal_ids
                if self.signals[item_id].status == "PENDING"
            ),
            "incidents": len(self.incident_ids),
            "open_incidents": sum(
                1
                for item_id in self.incident_ids
                if self.incidents[item_id].status != "CLOSED"
            ),
            "inspections": len(self.inspection_ids),
            "migration_source_network": self.migration_source_network,
            "migration_source_contract": self.migration_source_contract,
            "migration_source_transactions": self.migration_source_transactions,
            "migration_snapshot_hash": self.migration_snapshot_hash,
            "migration_complete": self.migration_complete,
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
