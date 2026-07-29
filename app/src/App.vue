<script setup>
import { computed, onMounted, ref } from "vue";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Check,
  CircleDot,
  ExternalLink,
  FileCheck2,
  LocateFixed,
  LogOut,
  Radio,
  RefreshCw,
  Satellite,
  ScanLine,
  Sparkles,
  X,
} from "lucide-vue-next";
import {
  connectWallet,
  contractAddress,
  explorerUrl,
  formatError,
  readContract,
  writeContract,
} from "./services/genlayer";

const STORAGE_KEY = "fieldsignal:wallet-connected";
const modes = [
  { id: "field", label: "Decision field", index: "01" },
  { id: "signals", label: "Signal traces", index: "02" },
  { id: "response", label: "Response plan", index: "03" },
];

const ready = ref(false);
const wallet = ref(null);
const client = ref(null);
const connecting = ref(false);
const loading = ref(false);
const error = ref("");
const mode = ref("field");
const selected = ref("SEN-001");
const modal = ref(null);
const tx = ref({ open: false, stage: "", title: "", hash: "", error: "" });

const overview = ref({});
const stations = ref([]);
const sensors = ref([]);
const signals = ref([]);
const incidents = ref([]);
const inspections = ref([]);

const signalForm = ref({
  value: "42 ug/m3",
  observed_at: new Date().toISOString(),
  context:
    "A sustained anomaly appeared across consecutive intervals with supporting context from nearby activity and neighboring sensor behavior.",
  evidence_url: "https://github.com/AbstrusImad/fieldsignal",
});
const inspectionForm = ref({
  plan:
    "Verify physical condition and calibration, collect a co-located reference sample, document nearby activity, and publish time-aligned evidence.",
  findings:
    "Field inspection confirmed the device condition and compared its reading against a traceable reference instrument with timestamped context.",
  evidence_url: "https://github.com/AbstrusImad/fieldsignal",
});

const current = computed(
  () => sensors.value.find((item) => item.id === selected.value) || sensors.value[0],
);
const currentStation = computed(() => station(current.value?.station_id));
const hasData = computed(() => sensors.value.length > 0);
const pendingSignals = computed(() => signals.value.filter((item) => item.status === "PENDING"));
const txStep = computed(() => {
  if (tx.value.stage === "signature") return 1;
  if (["submitted", "consensus"].includes(tx.value.stage)) return 2;
  if (tx.value.stage === "accepted") return 3;
  return 0;
});
const marks = computed(() =>
  sensors.value.map((sensor, index) => {
    const stationData = station(sensor.station_id);
    const trust = Number(sensor.trust || 0);
    const signalCount = Number(sensor.signal_count || 0);
    return {
      ...sensor,
      x: clamp(trust + ((index % 3) - 1) * 7, 10, 92),
      y: clamp(
        22 + signalCount * 18 + Number(stationData?.sensor_count || 1) * 5 + ((index * 11) % 24),
        11,
        89,
      ),
    };
  }),
);

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}
function station(id) {
  return stations.value.find((item) => item.id === id);
}
function sensorFor(id) {
  return sensors.value.find((item) => item.id === id);
}
function short(value = "") {
  return value ? `${value.slice(0, 6)}...${value.slice(-4)}` : "";
}
function setMode(next) {
  mode.value = next;
  modal.value = null;
}
function selectSensor(id) {
  selected.value = id;
}
function openSignal(sensor) {
  if (sensor) selected.value = sensor.id;
  modal.value = { type: "signal" };
}
function openInspection(item) {
  modal.value = { type: "inspection", item };
}

async function restore() {
  try {
    if (localStorage.getItem(STORAGE_KEY) === "true") {
      const session = await connectWallet({ silent: true });
      if (session) enter(session);
      else await load({ quiet: true });
    } else {
      await load({ quiet: true });
    }
  } catch {
    localStorage.removeItem(STORAGE_KEY);
    await load({ quiet: true });
  } finally {
    ready.value = true;
  }
}
async function connect() {
  connecting.value = true;
  error.value = "";
  try {
    const session = await connectWallet();
    if (!session) throw new Error("Wallet not connected");
    localStorage.setItem(STORAGE_KEY, "true");
    enter(session);
  } catch (cause) {
    error.value = formatError(cause);
  } finally {
    connecting.value = false;
  }
}
function enter(session) {
  wallet.value = session.address;
  client.value = session.client;
  load();
}
function logout() {
  localStorage.removeItem(STORAGE_KEY);
  wallet.value = null;
  client.value = null;
  tx.value.open = false;
}
async function load({ quiet = false } = {}) {
  loading.value = true;
  error.value = "";
  try {
    const values = [];
    for (const name of [
      "get_overview",
      "get_stations",
      "get_sensors",
      "get_signals",
      "get_incidents",
      "get_inspections",
    ]) {
      values.push(await readContract(name));
    }
    [
      overview.value,
      stations.value,
      sensors.value,
      signals.value,
      incidents.value,
      inspections.value,
    ] = values;
    if (!sensors.value.some((item) => item.id === selected.value)) {
      selected.value = sensors.value[0]?.id || "";
    }
  } catch (cause) {
    if (!quiet) error.value = formatError(cause);
  } finally {
    loading.value = false;
  }
}
async function transact(title, functionName, args) {
  modal.value = null;
  tx.value = { open: true, stage: "signature", title, hash: "", error: "" };
  try {
    const result = await writeContract({
      client: client.value,
      functionName,
      args,
      onStage: (stage, hash) => {
        tx.value.stage = stage;
        if (hash) tx.value.hash = hash;
      },
    });
    tx.value.hash = result.hash;
    await load();
  } catch (cause) {
    tx.value.stage = "failed";
    tx.value.error = formatError(cause);
  }
}

const submitSignal = () =>
  transact("Transmit field signal", "submit_signal", [
    current.value.id,
    signalForm.value.value,
    signalForm.value.observed_at,
    signalForm.value.context,
    signalForm.value.evidence_url,
  ]);
const resolveSignal = (id) =>
  transact("Correlate environmental signal", "resolve_signal", [id]);
const assignInspection = (incident) =>
  transact("Dispatch field inspection", "assign_inspection", [
    incident.id,
    inspectionForm.value.plan,
  ]);
const submitInspection = (inspection) =>
  transact("Publish inspection findings", "submit_inspection", [
    inspection.id,
    inspectionForm.value.findings,
    inspectionForm.value.evidence_url,
  ]);
const reviewInspection = (id) =>
  transact("Resolve field inspection", "resolve_inspection", [id]);

onMounted(restore);
</script>

<template>
  <div v-if="!ready" class="boot-screen">
    <span>FS / STN</span>
    <div></div>
    <b>Plotting public field state</b>
  </div>

  <main v-else-if="!wallet" class="blueprint-gate">
    <div class="gate-register">
      <span>GENLAYER / STUDIONET</span>
      <span>PUBLIC ENVIRONMENTAL RECORD</span>
      <span>REV. 02 / LIVE</span>
    </div>

    <div class="gate-field" aria-hidden="true">
      <div class="axis axis-x"><span>CALIBRATION TRUST</span></div>
      <div class="axis axis-y"><span>CORROBORATION</span></div>
      <i v-for="n in 15" :key="n" :class="`gate-point point-${n}`"></i>
      <div class="gate-vector vector-a"></div>
      <div class="gate-vector vector-b"></div>
      <span class="quadrant-label q1">VERIFIED BASELINE</span>
      <span class="quadrant-label q2">CONTEXT WATCH</span>
      <span class="quadrant-label q3">FIELD INCIDENT</span>
      <span class="quadrant-label q4">CALIBRATION HOLD</span>
    </div>

    <section class="gate-title">
      <small>DECISION COORDINATES FOR PHYSICAL-WORLD EVIDENCE</small>
      <h1>Field<br />Signal</h1>
      <p>
        Environmental readings become accountable decisions through calibration history,
        public evidence, and GenLayer validator consensus.
      </p>
    </section>

    <section class="gate-origin">
      <div class="origin-cross"><LocateFixed /></div>
      <small>OPERATOR ORIGIN / WALLET GATE</small>
      <strong>{{ overview.sensors || "08" }} sensors plotted on StudioNet</strong>
      <button :disabled="connecting" @click="connect">
        <CircleDot />
        <span>{{ connecting ? "LOCATING WALLET..." : "PLACE OPERATOR ORIGIN" }}</span>
        <ArrowRight />
      </button>
      <p v-if="error">{{ error }}</p>
    </section>

    <div class="gate-index">
      <span><b>{{ overview.stations || "06" }}</b> stations</span>
      <span><b>{{ overview.signals || "03" }}</b> signals</span>
      <span><b>{{ overview.open_incidents || "02" }}</b> open incidents</span>
      <a :href="`${explorerUrl}/address/${contractAddress}`" target="_blank">
        Contract sheet <ExternalLink />
      </a>
    </div>
  </main>

  <div v-else class="field-system">
    <header class="drawing-header">
      <button class="wordmark" title="Decision field" @click="setMode('field')">
        <span>FS</span>
        <b>FieldSignal</b>
      </button>
      <nav>
        <button
          v-for="item in modes"
          :key="item.id"
          :class="{ active: mode === item.id }"
          @click="setMode(item.id)"
        >
          <small>{{ item.index }}</small>
          <span>{{ item.label }}</span>
        </button>
      </nav>
      <div class="header-tools">
        <span class="network"><i></i> StudioNet</span>
        <a
          :href="`${explorerUrl}/address/${contractAddress}`"
          target="_blank"
          title="Open contract in explorer"
        >
          <ExternalLink />
        </a>
        <button :class="{ spin: loading }" title="Refresh chain state" @click="load">
          <RefreshCw />
        </button>
        <button title="Disconnect wallet" @click="logout"><LogOut /></button>
      </div>
    </header>

    <main v-if="mode === 'field'" class="decision-workspace">
      <section class="decision-field">
        <header class="sheet-caption">
          <div>
            <small>SHEET 01 / LIVE DECISION FIELD</small>
            <h2>Environmental integrity map</h2>
          </div>
          <p>
            Coordinates combine on-chain sensor trust, signal history, and station
            corroboration.
          </p>
        </header>

        <div class="plot">
          <div class="plot-axis plot-x"><span>CALIBRATION TRUST</span></div>
          <div class="plot-axis plot-y"><span>CORROBORATION</span></div>
          <div class="quad quad-watch"><b>CONTEXT WATCH</b><small>Q-02</small></div>
          <div class="quad quad-verified"><b>VERIFIED BASELINE</b><small>Q-01</small></div>
          <div class="quad quad-hold"><b>CALIBRATION HOLD</b><small>Q-04</small></div>
          <div class="quad quad-incident"><b>FIELD INCIDENT</b><small>Q-03</small></div>

          <button
            v-for="mark in marks"
            :key="mark.id"
            class="sensor-mark"
            :class="{
              selected: current?.id === mark.id,
              attention: mark.status !== 'ACTIVE' || Number(mark.signal_count) > 0,
            }"
            :style="{ left: `${mark.x}%`, bottom: `${mark.y}%` }"
            :aria-label="`${mark.id} ${mark.metric}`"
            @click="selectSensor(mark.id)"
          >
            <i></i><span>{{ mark.id.replace("SEN-", "") }}</span>
          </button>
          <div v-if="current" class="selection-vector"></div>
        </div>

        <footer class="plot-legend">
          <span><i class="legend-active"></i> Active sensor</span>
          <span><i class="legend-alert"></i> Signal history</span>
          <span>Y / evidence corroboration</span>
          <span>X / protocol trust</span>
        </footer>
      </section>

      <aside v-if="current" class="sensor-annotation">
        <header>
          <span>ANNOTATION / {{ current.id }}</span>
          <b>{{ current.status }}</b>
        </header>
        <div class="annotation-title">
          <small>{{ currentStation?.id }} / {{ currentStation?.region }}</small>
          <h1>{{ current.metric }}</h1>
          <p>{{ currentStation?.name }}</p>
        </div>
        <div class="measurement">
          <span>REFERENCE BAND</span>
          <strong>{{ current.baseline }}</strong>
          <b>{{ current.unit }}</b>
        </div>
        <dl>
          <div><dt>Protocol trust</dt><dd>{{ current.trust }}%</dd></div>
          <div><dt>Signals filed</dt><dd>{{ current.signal_count }}</dd></div>
          <div><dt>Station sensors</dt><dd>{{ currentStation?.sensor_count }}</dd></div>
          <div><dt>Calibration</dt><dd><a :href="current.calibration_url" target="_blank">Source <ExternalLink /></a></dd></div>
        </dl>
        <button class="primary-action" @click="openSignal(current)">
          <Activity />
          <span>Transmit new reading</span>
          <ArrowRight />
        </button>
        <div class="sheet-number">
          <small>LIVE CONTRACT</small>
          <span>{{ short(contractAddress) }}</span>
          <b>FS-A1</b>
        </div>
      </aside>

      <section v-else class="empty-sheet">
        <ScanLine /><b>No sensor records returned</b><p>{{ error }}</p>
      </section>
    </main>

    <main v-else-if="mode === 'signals'" class="trace-workspace">
      <header class="workspace-heading">
        <div>
          <small>SHEET 02 / CONSENSUS TRACE REGISTER</small>
          <h1>Readings under examination</h1>
        </div>
        <span>{{ pendingSignals.length }} awaiting validator consensus</span>
      </header>

      <section class="trace-sheet">
        <div class="trace-scale">
          <span>INGEST</span><span>CONTEXT</span><span>VALIDATION</span><span>VERDICT</span>
        </div>
        <article v-for="(signal, index) in signals" :key="signal.id" class="signal-trace">
          <div class="trace-id">
            <small>{{ String(index + 1).padStart(2, "0") }}</small>
            <b>{{ signal.id }}</b>
            <span>{{ signal.sensor_id }}</span>
          </div>
          <div class="trace-reading">
            <small>{{ sensorFor(signal.sensor_id)?.metric }}</small>
            <strong>{{ signal.value }}</strong>
            <span>{{ signal.observed_at }}</span>
          </div>
          <div class="trace-line">
            <i v-for="n in 22" :key="n" :style="{ height: `${8 + ((n * (Number(signal.severity) || 13) + index * 7) % 38)}px` }"></i>
          </div>
          <div class="trace-context">
            <p>{{ signal.analysis || signal.context }}</p>
            <a :href="signal.evidence_url" target="_blank">Evidence <ExternalLink /></a>
          </div>
          <div class="trace-verdict">
            <span :class="signal.status.toLowerCase()">{{ signal.verdict || signal.status }}</span>
            <small v-if="signal.confidence">{{ signal.confidence }}% confidence</small>
            <button v-if="signal.status === 'PENDING'" @click="resolveSignal(signal.id)">
              <Sparkles /> Run consensus
            </button>
          </div>
        </article>
        <div v-if="!signals.length" class="empty-register">
          <Radio /><b>No signal records yet</b><p>Transmit a reading from the decision field.</p>
        </div>
      </section>
    </main>

    <main v-else class="response-workspace">
      <header class="workspace-heading">
        <div>
          <small>SHEET 03 / FIELD RESPONSE PLAN</small>
          <h1>From anomaly to accountable action</h1>
        </div>
        <span>{{ overview.open_incidents || 0 }} open incident routes</span>
      </header>

      <section class="response-plan">
        <div class="plan-rail" aria-hidden="true"></div>
        <article v-for="(incident, index) in incidents" :key="incident.id" class="incident-route">
          <div class="route-node"><span>{{ String(index + 1).padStart(2, "0") }}</span></div>
          <header>
            <small>{{ incident.id }} / {{ incident.station_id }}</small>
            <span>{{ incident.status }}</span>
          </header>
          <div class="route-body">
            <div>
              <h2>{{ incident.title }}</h2>
              <p>{{ incident.response }}</p>
            </div>
            <div class="severity-gauge">
              <strong>{{ incident.severity }}</strong>
              <span>SEVERITY / 100</span>
              <i><b :style="{ width: `${incident.severity}%` }"></b></i>
            </div>
          </div>
          <footer>
            <span>Source {{ incident.signal_id }}</span>
            <button v-if="!incident.inspection_id" @click="assignInspection(incident)">
              <LocateFixed /> Dispatch inspection
            </button>
            <span v-else>Linked {{ incident.inspection_id }}</span>
          </footer>
        </article>

        <article v-for="inspection in inspections" :key="inspection.id" class="inspection-route">
          <div class="route-node inspection-node"><FileCheck2 /></div>
          <header>
            <small>{{ inspection.id }} / {{ inspection.incident_id }}</small>
            <span>{{ inspection.status }}</span>
          </header>
          <div class="route-body">
            <div>
              <h2>{{ inspection.verdict || "Field inspection" }}</h2>
              <p>{{ inspection.analysis || inspection.findings || inspection.plan }}</p>
            </div>
            <div class="assignee">
              <small>ASSIGNEE</small>
              <span>{{ short(inspection.assignee) }}</span>
            </div>
          </div>
          <footer>
            <a v-if="inspection.evidence_url" :href="inspection.evidence_url" target="_blank">
              Inspection evidence <ExternalLink />
            </a>
            <button v-if="inspection.status === 'ASSIGNED'" @click="openInspection(inspection)">
              <FileCheck2 /> Submit findings
            </button>
            <button v-if="inspection.status === 'PENDING_REVIEW'" @click="reviewInspection(inspection.id)">
              <Sparkles /> Resolve with consensus
            </button>
          </footer>
        </article>

        <div v-if="!incidents.length && !inspections.length" class="empty-register">
          <Check /><b>No active response routes</b><p>Resolved readings have not opened an incident.</p>
        </div>
      </section>
    </main>

    <footer class="status-block">
      <div><small>NETWORK</small><b>StudioNet</b></div>
      <div><small>WALLET</small><b>{{ short(wallet) }}</b></div>
      <div><small>STATIONS</small><b>{{ overview.stations || 0 }}</b></div>
      <div><small>SENSORS</small><b>{{ overview.sensors || 0 }}</b></div>
      <div><small>OPEN ROUTES</small><b>{{ overview.open_incidents || 0 }}</b></div>
      <p v-if="error"><AlertTriangle /> {{ error }}</p>
    </footer>

    <div v-if="modal" class="input-overlay" @click.self="modal = null">
      <section class="input-sheet">
        <header>
          <div><small>FIELD INPUT / PUBLIC RECORD</small><b>FS-FORM / 01</b></div>
          <button title="Close" @click="modal = null"><X /></button>
        </header>
        <div class="input-intro">
          <span>{{ modal.type === "signal" ? current?.id : modal.item?.id }}</span>
          <h2>{{ modal.type === "signal" ? "Transmit a field reading" : "Publish inspection findings" }}</h2>
          <p>Every submitted field becomes part of the StudioNet contract record.</p>
        </div>
        <form v-if="modal.type === 'signal'" @submit.prevent="submitSignal">
          <label>
            <span>Observed value</span>
            <input v-model="signalForm.value" required maxlength="40" />
          </label>
          <label>
            <span>Observation timestamp</span>
            <input v-model="signalForm.observed_at" required />
          </label>
          <label class="wide">
            <span>Environmental context / 60 characters minimum</span>
            <textarea v-model="signalForm.context" required minlength="60" maxlength="1200"></textarea>
          </label>
          <label class="wide">
            <span>Public HTTPS evidence</span>
            <input v-model="signalForm.evidence_url" type="url" required />
          </label>
          <button class="form-submit" type="submit">
            <Satellite /><span>Transmit to StudioNet</span><ArrowRight />
          </button>
        </form>
        <form v-else @submit.prevent="submitInspection(modal.item)">
          <label class="wide">
            <span>Inspection findings / 100 characters minimum</span>
            <textarea v-model="inspectionForm.findings" required minlength="100" maxlength="1800"></textarea>
          </label>
          <label class="wide">
            <span>Public HTTPS evidence</span>
            <input v-model="inspectionForm.evidence_url" type="url" required />
          </label>
          <button class="form-submit" type="submit">
            <FileCheck2 /><span>Publish findings</span><ArrowRight />
          </button>
        </form>
      </section>
    </div>

    <aside v-if="tx.open" class="execution-strip" :class="tx.stage">
      <button class="tx-close" title="Close transaction status" @click="tx.open = false"><X /></button>
      <div class="tx-title">
        <small>GENLAYER EXECUTION TRACE</small>
        <b>{{ tx.title }}</b>
      </div>
      <div class="tx-progress">
        <div :class="{ active: txStep >= 1, failed: tx.stage === 'failed' }"><i>1</i><span>Wallet signature</span></div>
        <div :class="{ active: txStep >= 2, failed: tx.stage === 'failed' }"><i>2</i><span>Validator consensus</span></div>
        <div :class="{ active: txStep >= 3, failed: tx.stage === 'failed' }"><i>3</i><span>State accepted</span></div>
      </div>
      <div class="tx-result">
        <ScanLine v-if="!['accepted', 'failed'].includes(tx.stage)" />
        <Check v-else-if="tx.stage === 'accepted'" />
        <AlertTriangle v-else />
        <span v-if="tx.stage === 'signature'">Confirm the transaction in your wallet.</span>
        <span v-else-if="['submitted', 'consensus'].includes(tx.stage)">Validators are examining calibration, context, and evidence.</span>
        <span v-else-if="tx.stage === 'accepted'">The contract state has been updated.</span>
        <span v-else>{{ tx.error }}</span>
        <a v-if="tx.hash" :href="`${explorerUrl}/transactions/${tx.hash}`" target="_blank">Trace <ExternalLink /></a>
      </div>
    </aside>
  </div>
</template>
