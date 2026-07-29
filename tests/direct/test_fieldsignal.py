import json
def deploy(vm,d,s):vm.sender=s;return d("contracts/fieldsignal.py")
def test_genesis(direct_vm,direct_deploy,direct_alice):
 c=deploy(direct_vm,direct_deploy,direct_alice);assert c.get_overview()["stations"]==6;assert len(c.get_sensors())==8
def test_enroll(direct_vm,direct_deploy,direct_alice):
 c=deploy(direct_vm,direct_deploy,direct_alice);assert c.enroll_sensor("STA-001","Black carbon","µg/m³","0.2-1.4","https://example.org/calibration")=="SEN-009"
def test_signal(direct_vm,direct_deploy,direct_alice):
 c=deploy(direct_vm,direct_deploy,direct_alice);i=c.submit_signal("SEN-001","86 µg/m³","2026-07-29T04:00:00Z","Three consecutive elevated readings occurred downwind of active freight loading while nearby sensors also rose above baseline.","https://example.org/signal");assert i=="SIG-0001"
def test_consensus_incident(direct_vm,direct_deploy,direct_alice):
 c=deploy(direct_vm,direct_deploy,direct_alice);i=c.submit_signal("SEN-001","86 µg/m³","2026-07-29T04:00:00Z","Three consecutive elevated readings occurred downwind of active freight loading while nearby sensors also rose above baseline.","https://example.org/signal")
 direct_vm.mock_llm(r".*environmental sensor integrity panel.*",json.dumps({"verdict":"INCIDENT","severity":78,"confidence":86,"analysis":"Corroborated excursion.","response":"Dispatch field verification and notify nearby operators."}));c.resolve_signal(i);assert c.get_overview()["incidents"]==1
def test_quarantine(direct_vm,direct_deploy,direct_alice):
 c=deploy(direct_vm,direct_deploy,direct_alice);i=c.submit_signal("SEN-001","999","2026-07-29T04:00:00Z","The reading jumped instantly without corroboration and the calibration certificate is beyond its expected maintenance interval.","https://example.org/signal")
 direct_vm.mock_llm(r".*environmental sensor integrity panel.*",json.dumps({"verdict":"QUARANTINE","severity":35,"confidence":90,"analysis":"Likely sensor fault.","response":"Remove sensor from incident aggregation and inspect calibration."}));c.resolve_signal(i);assert c.get_sensors()[0].status=="QUARANTINED"
