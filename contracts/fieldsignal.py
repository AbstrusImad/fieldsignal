# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from dataclasses import dataclass
from datetime import datetime, timezone
from genlayer import *
E="[EXPECTED]"; L="[LLM_ERROR]"
@allow_storage
@dataclass
class Station:
    id:str; name:str; region:str; operator:Address; sensor_count:u32; trust:u32
@allow_storage
@dataclass
class Sensor:
    id:str; station_id:str; metric:str; unit:str; baseline:str; calibration_url:str; status:str; trust:u32; signal_count:u32
@allow_storage
@dataclass
class Signal:
    id:str; sensor_id:str; value:str; observed_at:str; context:str; evidence_url:str; status:str; verdict:str; severity:u32; confidence:u32; analysis:str; response:str; incident_id:str
@allow_storage
@dataclass
class Incident:
    id:str; signal_id:str; station_id:str; title:str; severity:u32; status:str; response:str; inspection_id:str
@allow_storage
@dataclass
class Inspection:
    id:str; incident_id:str; assignee:Address; plan:str; findings:str; evidence_url:str; status:str; verdict:str; analysis:str
class FieldSignal(gl.Contract):
    stations:TreeMap[str,Station];sensors:TreeMap[str,Sensor];signals:TreeMap[str,Signal];incidents:TreeMap[str,Incident];inspections:TreeMap[str,Inspection]
    station_ids:DynArray[str];sensor_ids:DynArray[str];signal_ids:DynArray[str];incident_ids:DynArray[str];inspection_ids:DynArray[str]
    def __init__(self):
        self.station_ids=[];self.sensor_ids=[];self.signal_ids=[];self.incident_ids=[];self.inspection_ids=[]
        self._station("STA-001","Canal East Air Mast","Riverside industrial edge")
        self._station("STA-002","North Orchard Soil Array","Peri-urban food belt")
        self._station("STA-003","Harbor Inlet Buoy","Coastal freight corridor")
        self._station("STA-004","Central Heat Spine","Dense residential core")
        self._station("STA-005","Wetland Gate Monitor","Protected floodplain")
        self._station("STA-006","Hillcrest Wind Post","Upland residential ridge")
        specs=[("SEN-001","STA-001","PM2.5","µg/m³","8-18"),("SEN-002","STA-001","NO2","ppb","12-30"),("SEN-003","STA-002","Soil moisture","%","28-52"),("SEN-004","STA-003","Dissolved oxygen","mg/L","6.5-9.0"),("SEN-005","STA-004","Wet bulb temperature","°C","12-24"),("SEN-006","STA-005","Water level","m","0.4-1.8"),("SEN-007","STA-006","Wind speed","m/s","1-14"),("SEN-008","STA-003","Turbidity","NTU","1-12")]
        for x in specs:self._sensor(*x)
    def _now(self)->u64:return u64(int(datetime.now(timezone.utc).timestamp()))
    def _station(self,id,name,region):self.station_ids.append(id);self.stations[id]=Station(id,name,region,gl.message.sender_address,u32(0),u32(82))
    def _sensor(self,id,station,metric,unit,baseline):
        self.sensor_ids.append(id);self.sensors[id]=Sensor(id,station,metric,unit,baseline,"https://github.com/AbstrusImad/fieldsignal","ACTIVE",u32(80),u32(0));s=self.stations[station];s.sensor_count+=u32(1);self.stations[station]=s
    def _text(self,v,n,lo,hi):
        if len(v.strip())<lo or len(v.strip())>hi:raise gl.vm.UserError(f"{E} {n} must be {lo}-{hi} characters")
    @gl.public.write
    def enroll_sensor(self,station_id:str,metric:str,unit:str,baseline:str,calibration_url:str)->str:
        if station_id not in self.stations:raise gl.vm.UserError(f"{E} Station not found")
        self._text(metric,"Metric",2,60);self._text(baseline,"Baseline",2,100)
        if not calibration_url.startswith("https://"):raise gl.vm.UserError(f"{E} Calibration URL must use HTTPS")
        id=f"SEN-{len(self.sensor_ids)+1:03d}";self.sensor_ids.append(id);self.sensors[id]=Sensor(id,station_id,metric,unit,baseline,calibration_url,"ACTIVE",u32(60),u32(0));s=self.stations[station_id];s.sensor_count+=u32(1);self.stations[station_id]=s;return id
    @gl.public.write
    def submit_signal(self,sensor_id:str,value:str,observed_at:str,context:str,evidence_url:str)->str:
        if sensor_id not in self.sensors:raise gl.vm.UserError(f"{E} Sensor not found")
        self._text(value,"Value",1,40);self._text(observed_at,"Observed at",10,60);self._text(context,"Context",60,1200)
        if not evidence_url.startswith("https://"):raise gl.vm.UserError(f"{E} Evidence URL must use HTTPS")
        id=f"SIG-{len(self.signal_ids)+1:04d}";self.signal_ids.append(id);self.signals[id]=Signal(id,sensor_id,value,observed_at,context,evidence_url,"PENDING","",u32(0),u32(0),"","","");s=self.sensors[sensor_id];s.signal_count+=u32(1);self.sensors[sensor_id]=s;return id
    @gl.public.write
    def resolve_signal(self,signal_id:str)->None:
        if signal_id not in self.signals:raise gl.vm.UserError(f"{E} Signal not found")
        q=self.signals[signal_id]
        if q.status!="PENDING":raise gl.vm.UserError(f"{E} Signal not pending")
        s=self.sensors[q.sensor_id];st=self.stations[s.station_id]
        def assess()->dict:
            r=gl.nondet.exec_prompt(f"""Act as an environmental sensor integrity panel. Determine whether this reading is normal, requires watch, establishes an incident, or indicates sensor quarantine.
STATION {st.name}, {st.region}. SENSOR {s.metric} {s.unit}; baseline {s.baseline}; trust {s.trust}.
READING {q.value} at {q.observed_at}. CONTEXT {q.context}. EVIDENCE {q.evidence_url}. CALIBRATION {s.calibration_url}.
Use web context when relevant. Return JSON {{"verdict":"NORMAL"|"WATCH"|"INCIDENT"|"QUARANTINE","severity":0-100,"confidence":0-100,"analysis":"under 500 chars","response":"specific action under 500 chars"}}.""",response_format="json")
            if not isinstance(r,dict):raise gl.vm.UserError(f"{L} Invalid assessment")
            v=str(r.get("verdict","")).upper()
            if v not in ("NORMAL","WATCH","INCIDENT","QUARANTINE"):raise gl.vm.UserError(f"{L} Invalid verdict")
            return {"verdict":v,"severity":max(0,min(100,int(r.get("severity",0)))),"confidence":max(0,min(100,int(r.get("confidence",0)))),"analysis":str(r.get("analysis",""))[:500],"response":str(r.get("response",""))[:500]}
        def validate(x:gl.vm.Result)->bool:
            if not isinstance(x,gl.vm.Return):return False
            r=x.calldata;return isinstance(r,dict) and r.get("verdict") in ("NORMAL","WATCH","INCIDENT","QUARANTINE") and 0<=int(r.get("severity",-1))<=100 and 0<=int(r.get("confidence",-1))<=100
        r=gl.vm.run_nondet_unsafe(assess,validate);q.verdict=r["verdict"];q.severity=u32(r["severity"]);q.confidence=u32(r["confidence"]);q.analysis=r["analysis"];q.response=r["response"];q.status="RESOLVED"
        if q.verdict in ("INCIDENT","QUARANTINE"):
            id=f"INC-{len(self.incident_ids)+1:04d}";self.incident_ids.append(id);self.incidents[id]=Incident(id,q.id,st.id,f"{s.metric} anomaly at {st.name}",q.severity,"OPEN",q.response,"");q.incident_id=id
        if q.verdict=="QUARANTINE":s.status="QUARANTINED";s.trust=u32(max(0,int(s.trust)-20))
        elif q.verdict=="NORMAL":s.trust=u32(min(100,int(s.trust)+2))
        self.signals[q.id]=q;self.sensors[s.id]=s
    @gl.public.write
    def assign_inspection(self,incident_id:str,plan:str)->str:
        if incident_id not in self.incidents:raise gl.vm.UserError(f"{E} Incident not found")
        i=self.incidents[incident_id]
        if i.inspection_id!="":raise gl.vm.UserError(f"{E} Inspection already assigned")
        self._text(plan,"Plan",60,1200);id=f"INS-{len(self.inspection_ids)+1:04d}";self.inspection_ids.append(id);self.inspections[id]=Inspection(id,incident_id,gl.message.sender_address,plan,"","","ASSIGNED","","");i.inspection_id=id;i.status="INSPECTION";self.incidents[i.id]=i;return id
    @gl.public.write
    def submit_inspection(self,inspection_id:str,findings:str,evidence_url:str)->None:
        if inspection_id not in self.inspections:raise gl.vm.UserError(f"{E} Inspection not found")
        i=self.inspections[inspection_id]
        if i.status!="ASSIGNED":raise gl.vm.UserError(f"{E} Inspection not assigned")
        self._text(findings,"Findings",100,1800)
        if not evidence_url.startswith("https://"):raise gl.vm.UserError(f"{E} Evidence URL must use HTTPS")
        i.findings=findings;i.evidence_url=evidence_url;i.status="PENDING_REVIEW";self.inspections[i.id]=i
    @gl.public.write
    def resolve_inspection(self,inspection_id:str)->None:
        if inspection_id not in self.inspections:raise gl.vm.UserError(f"{E} Inspection not found")
        i=self.inspections[inspection_id]
        if i.status!="PENDING_REVIEW":raise gl.vm.UserError(f"{E} Inspection not ready")
        incident=self.incidents[i.incident_id];sig=self.signals[incident.signal_id];sensor=self.sensors[sig.sensor_id]
        def assess()->dict:
            r=gl.nondet.exec_prompt(f"""Review an environmental field inspection. INCIDENT {incident.title}. REQUIRED RESPONSE {incident.response}. FINDINGS {i.findings}. EVIDENCE {i.evidence_url}. Return JSON {{"verdict":"CONFIRMED"|"FALSE_ALARM"|"RECALIBRATE"|"ESCALATE","analysis":"under 500 chars"}}.""",response_format="json")
            if not isinstance(r,dict):raise gl.vm.UserError(f"{L} Invalid review")
            v=str(r.get("verdict","")).upper()
            if v not in ("CONFIRMED","FALSE_ALARM","RECALIBRATE","ESCALATE"):raise gl.vm.UserError(f"{L} Invalid verdict")
            return {"verdict":v,"analysis":str(r.get("analysis",""))[:500]}
        def validate(x:gl.vm.Result)->bool:return isinstance(x,gl.vm.Return) and isinstance(x.calldata,dict) and x.calldata.get("verdict") in ("CONFIRMED","FALSE_ALARM","RECALIBRATE","ESCALATE")
        r=gl.vm.run_nondet_unsafe(assess,validate);i.verdict=r["verdict"];i.analysis=r["analysis"];i.status="RESOLVED";incident.status="CLOSED" if i.verdict in ("CONFIRMED","FALSE_ALARM") else "ACTION_REQUIRED"
        if i.verdict=="FALSE_ALARM":sensor.status="ACTIVE";sensor.trust=u32(max(0,int(sensor.trust)-5))
        elif i.verdict=="RECALIBRATE":sensor.status="CALIBRATION_DUE"
        self.inspections[i.id]=i;self.incidents[incident.id]=incident;self.sensors[sensor.id]=sensor
    @gl.public.view
    def get_overview(self)->dict:return {"stations":len(self.station_ids),"sensors":len(self.sensor_ids),"active_sensors":sum(1 for i in self.sensor_ids if self.sensors[i].status=="ACTIVE"),"signals":len(self.signal_ids),"pending_signals":sum(1 for i in self.signal_ids if self.signals[i].status=="PENDING"),"incidents":len(self.incident_ids),"open_incidents":sum(1 for i in self.incident_ids if self.incidents[i].status!="CLOSED"),"inspections":len(self.inspection_ids)}
    @gl.public.view
    def get_stations(self)->list:return [self.stations[i] for i in self.station_ids]
    @gl.public.view
    def get_sensors(self)->list:return [self.sensors[i] for i in self.sensor_ids]
    @gl.public.view
    def get_signals(self)->list:return [self.signals[i] for i in self.signal_ids]
    @gl.public.view
    def get_incidents(self)->list:return [self.incidents[i] for i in self.incident_ids]
    @gl.public.view
    def get_inspections(self)->list:return [self.inspections[i] for i in self.inspection_ids]
