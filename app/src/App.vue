<script setup>
import { computed, onMounted, ref } from "vue";
import {
  Activity,
  AlertTriangle,
  Check,
  CircleDot,
  ExternalLink,
  FileCheck2,
  Gauge,
  LogOut,
  MapPin,
  Radio,
  RefreshCw,
  Satellite,
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
const ready = ref(false);
const wallet = ref(null);
const client = ref(null);
const connecting = ref(false);
const loading = ref(false);
const error = ref("");
const section = ref("survey");
const selectedSensor = ref("SEN-001");
const selectedSignal = ref("");
const selectedResponse = ref("");
const sheet = ref(null);
const tx = ref({ open: false, stage: "", title: "", hash: "", error: "" });

const overview = ref({});
const stations = ref([]);
const sensors = ref([]);
const signals = ref([]);
const incidents = ref([]);
const inspections = ref([]);
const roles = ref({ operator: false, inspector: false, owner: false });

const signalForm = ref({
  value: "42 ug/m3",
  observed_at: new Date().toISOString(),
  context:
    "A sustained anomaly appeared across consecutive intervals with supporting context from nearby activity and neighboring sensor behavior.",
  evidence_url:
    "https://raw.githubusercontent.com/AbstrusImad/fieldsignal/main/docs/evidence/signal-pm25.md",
});
const inspectionForm = ref({
  plan:
    "Verify physical condition and calibration, collect a co-located reference sample, document nearby activity, and publish time-aligned evidence.",
  findings:
    "Field inspection confirmed the device condition and compared its reading against a traceable reference instrument with timestamped context.",
  evidence_url:
    "https://raw.githubusercontent.com/AbstrusImad/fieldsignal/main/docs/evidence/inspection-pm25.md",
});

const currentSensor = computed(
  () =>
    sensors.value.find((item) => item.id === selectedSensor.value) ||
    sensors.value[0],
);
const currentStation = computed(() =>
  stations.value.find((item) => item.id === currentSensor.value?.station_id),
);
const currentSignal = computed(
  () =>
    signals.value.find((item) => item.id === selectedSignal.value) ||
    signals.value[0],
);
const responseFiles = computed(() => [
  ...incidents.value.map((item) => ({ ...item, kind: "incident" })),
  ...inspections.value.map((item) => ({ ...item, kind: "inspection" })),
]);
const currentResponse = computed(
  () =>
    responseFiles.value.find((item) => item.id === selectedResponse.value) ||
    responseFiles.value[0],
);
const txIndex = computed(() => {
  if (tx.value.stage === "signature") return 1;
  if (["submitted", "consensus"].includes(tx.value.stage)) return 2;
  if (tx.value.stage === "accepted") return 3;
  return 0;
});
const gaugeAngle = computed(() => {
  const trust = Number(currentSensor.value?.trust || 0);
  return -118 + (trust / 100) * 236;
});

function short(value = "") {
  return value ? `${value.slice(0, 6)}...${value.slice(-4)}` : "";
}
function sensorFor(id) {
  return sensors.value.find((item) => item.id === id);
}
function stationFor(id) {
  return stations.value.find((item) => item.id === id);
}
function switchSection(next) {
  section.value = next;
  sheet.value = null;
}
function pickSensor(id) {
  selectedSensor.value = id;
}
function pickSignal(id) {
  selectedSignal.value = id;
}
function pickResponse(id) {
  selectedResponse.value = id;
}
function openReading() {
  sheet.value = { type: "signal" };
}
function openInspection(item) {
  sheet.value = { type: "inspection", item };
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
  if (!quiet) error.value = "";
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
    roles.value = wallet.value
      ? await readContract("get_roles", [wallet.value])
      : { operator: false, inspector: false, owner: false };
    selectedSensor.value ||= sensors.value[0]?.id || "";
    selectedSignal.value ||= signals.value[0]?.id || "";
    selectedResponse.value ||= responseFiles.value[0]?.id || "";
  } catch (cause) {
    if (!quiet) error.value = formatError(cause);
  } finally {
    loading.value = false;
  }
}
async function transact(title, functionName, args) {
  sheet.value = null;
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
    if (cause?.hash) tx.value.hash = cause.hash;
    tx.value.stage = "failed";
    tx.value.error = formatError(cause);
  }
}

const submitSignal = () =>
  transact("Field reading", "submit_signal", [
    currentSensor.value.id,
    signalForm.value.value,
    signalForm.value.observed_at,
    signalForm.value.context,
    signalForm.value.evidence_url,
  ]);
const resolveSignal = (id) =>
  transact("Signal correlation", "resolve_signal", [id]);
const assignInspection = (incident) =>
  transact("Inspection dispatch", "assign_inspection", [
    incident.id,
    wallet.value,
    inspectionForm.value.plan,
  ]);
const submitInspection = (inspection) =>
  transact("Inspection evidence", "submit_inspection", [
    inspection.id,
    inspectionForm.value.findings,
    inspectionForm.value.evidence_url,
  ]);
const reviewInspection = (id) =>
  transact("Inspection review", "resolve_inspection", [id]);

onMounted(restore);
</script>

<template>
  <div v-if="!ready" class="packing-screen">
    <div class="packing-case"><i></i><b>FIELD SIGNAL</b><span>Preparing field kit</span></div>
  </div>

  <main v-else-if="!wallet" class="case-landing">
    <div class="bench-grain"></div>
    <section class="closed-case">
      <div class="case-handle"><span></span></div>
      <i v-for="n in 8" :key="n" :class="`case-bolt bolt-${n}`"></i>
      <div class="case-stripe"></div>
      <div class="case-brand">
        <small>ENVIRONMENTAL EVIDENCE KIT</small>
        <h1>FIELD<br />SIGNAL</h1>
        <p>STUDIONET / UNIT FS-06</p>
      </div>
      <div class="condition-dial">
        <span>FIELD STATE</span>
        <div><i></i><b>LIVE</b></div>
      </div>
      <div class="case-manifest">
        <span><b>{{ overview.stations || "06" }}</b> STATIONS</span>
        <span><b>{{ overview.sensors || "08" }}</b> SENSORS</span>
        <span><b>{{ overview.signals || "05" }}</b> REPORTS</span>
      </div>
      <div class="case-sticker">
        <MapPin />
        <span>CORRELATE<br />BEFORE ACTION</span>
      </div>
      <button class="unlock-latch" :disabled="connecting" @click="connect">
        <span class="latch-ring"><i></i></span>
        <b>{{ connecting ? "RELEASING" : "UNLOCK" }}</b>
        <small>WITH WALLET</small>
      </button>
      <div class="catch catch-left"></div>
      <div class="catch catch-right"></div>
      <p v-if="error" class="landing-error">{{ error }}</p>
      <a
        class="case-serial"
        :href="`${explorerUrl}/address/${contractAddress}`"
        target="_blank"
      >
        CONTRACT {{ short(contractAddress) }} <ExternalLink />
      </a>
    </section>
    <p class="landing-caption">Physical claims / public evidence / validator response</p>
  </main>

  <main v-else class="field-bench">
    <div class="bench-grain"></div>
    <section class="open-kit">
      <div class="kit-lid">
        <div class="lid-pocket">
          <span>FIELD SIGNAL</span>
          <small>Environmental integrity kit / Bradbury</small>
        </div>
        <div class="lid-map">
          <i v-for="n in 6" :key="n" :class="`map-pin pin-${n}`"></i>
          <svg viewBox="0 0 500 110" preserveAspectRatio="none" aria-hidden="true">
            <path d="M5 80 C80 20 125 100 190 48 S310 12 360 66 S430 100 495 28" />
          </svg>
        </div>
        <div class="kit-utilities">
          <span class="wallet-tag"><i></i>{{ short(wallet) }}</span>
          <a :href="`${explorerUrl}/address/${contractAddress}`" target="_blank" title="Contract">
            <ExternalLink />
          </a>
          <button :class="{ spinning: loading }" title="Reload field state" @click="load()">
            <RefreshCw />
          </button>
          <button title="Pack and disconnect" @click="logout"><LogOut /></button>
        </div>
      </div>

      <div class="case-tray">
        <nav class="fabric-tabs" aria-label="Field files">
          <button :class="{ active: section === 'survey' }" @click="switchSection('survey')">
            <Gauge /><span>SURVEY</span><small>01</small>
          </button>
          <button :class="{ active: section === 'traces' }" @click="switchSection('traces')">
            <Radio /><span>TRACES</span><small>02</small>
          </button>
          <button :class="{ active: section === 'response' }" @click="switchSection('response')">
            <FileCheck2 /><span>RESPONSE</span><small>03</small>
          </button>
        </nav>

        <div class="file-stack">
          <i class="folder-back back-one"></i>
          <i class="folder-back back-two"></i>

          <article v-if="section === 'survey' && currentSensor" class="active-file survey-file">
            <div class="file-tab"><span>{{ currentSensor.id }}</span></div>
            <div class="sensor-index">
              <button
                v-for="sensor in sensors"
                :key="sensor.id"
                :class="{ active: sensor.id === currentSensor.id, flagged: sensor.status !== 'ACTIVE' || Number(sensor.signal_count) > 0 }"
                @click="pickSensor(sensor.id)"
              >
                <span>{{ sensor.id.slice(-2) }}</span>
                <small>{{ sensor.metric }}</small>
              </button>
            </div>

            <section class="field-report">
              <header class="report-heading">
                <div>
                  <small>INSTRUMENT FIELD RECORD</small>
                  <h2>{{ currentSensor.metric }}</h2>
                  <p><MapPin /> {{ currentStation?.name }} / {{ currentStation?.region }}</p>
                </div>
                <span class="status-lamp" :class="currentSensor.status.toLowerCase()">
                  <i></i>{{ currentSensor.status }}
                </span>
              </header>

              <div class="instrument-cluster">
                <div class="analog-gauge">
                  <div class="gauge-face">
                    <i v-for="n in 17" :key="n" :style="{ transform: `rotate(${-120 + n * 15}deg)` }"></i>
                    <span class="needle" :style="{ transform: `rotate(${gaugeAngle}deg)` }"></span>
                    <b>{{ currentSensor.trust }}</b>
                    <small>TRUST</small>
                  </div>
                </div>
                <div class="baseline-tape">
                  <small>REFERENCE BAND</small>
                  <strong>{{ currentSensor.baseline }}</strong>
                  <span>{{ currentSensor.unit }}</span>
                  <p>Calibration source attached / {{ currentSensor.signal_count }} reports filed</p>
                  <a :href="currentSensor.calibration_url" target="_blank">OPEN SOURCE <ExternalLink /></a>
                </div>
                <div class="station-punches">
                  <span v-for="station in stations" :key="station.id" :class="{ active: station.id === currentStation?.id }">
                    <i></i>{{ station.id.slice(-2) }}
                  </span>
                </div>
              </div>

              <div class="field-note">
                <b>Operator note</b>
                <p>
                  Compare a new reading with the instrument band, local context,
                  neighboring behavior, and public evidence before requesting a
                  validator conclusion.
                </p>
              </div>

              <button class="push-control" :disabled="!roles.operator" @click="openReading">
                <span><Activity /></span>
                <b>LOG READING</b>
                <small>press to prepare field sheet</small>
              </button>
            </section>
          </article>

          <article v-else-if="section === 'traces'" class="active-file trace-file">
            <div class="file-tab orange-tab"><span>SIGNAL TRACES</span></div>
            <div class="dossier-tabs">
              <button
                v-for="(signal, index) in signals"
                :key="signal.id"
                :class="{ active: currentSignal?.id === signal.id }"
                @click="pickSignal(signal.id)"
              >
                <b>{{ String(index + 1).padStart(2, "0") }}</b>
                <span>{{ signal.id }}</span>
                <i :class="signal.status.toLowerCase()"></i>
              </button>
            </div>

            <section v-if="currentSignal" class="signal-dossier">
              <div class="dossier-head">
                <span>PUBLIC OBSERVATION / {{ currentSignal.id }}</span>
                <small>{{ currentSignal.observed_at }}</small>
              </div>
              <div class="sample-label">
                <small>{{ currentSignal.sensor_id }} / {{ sensorFor(currentSignal.sensor_id)?.metric }}</small>
                <strong>{{ currentSignal.value }}</strong>
                <p>{{ stationFor(sensorFor(currentSignal.sensor_id)?.station_id)?.name }}</p>
              </div>
              <div class="trace-paper">
                <div class="trace-ink">
                  <i
                    v-for="n in 38"
                    :key="n"
                    :style="{ height: `${8 + ((n * (Number(currentSignal.severity) || 17)) % 48)}px` }"
                  ></i>
                </div>
                <p>{{ currentSignal.analysis || currentSignal.context }}</p>
              </div>
              <div class="evidence-tape">
                <span>{{ currentSignal.evidence_verified ? "EVIDENCE VERIFIED" : "EVIDENCE" }}</span>
                <a :href="currentSignal.evidence_url" target="_blank">
                  public source <ExternalLink />
                </a>
                <small v-if="currentSignal.evidence_digest">SHA256 {{ short(currentSignal.evidence_digest) }}</small>
              </div>
              <div class="verdict-stamp" :class="currentSignal.status.toLowerCase()">
                <b>{{ currentSignal.verdict || currentSignal.status }}</b>
                <small v-if="currentSignal.confidence">{{ currentSignal.confidence }}% CONFIDENCE</small>
              </div>
              <button
                v-if="currentSignal.status === 'PENDING'"
                class="stamp-control"
                @click="resolveSignal(currentSignal.id)"
              >
                <span><Sparkles /></span>
                <b>RUN CONSENSUS</b>
              </button>
            </section>
            <div v-else class="empty-file"><Radio /><b>No reports filed</b><span>Use the Survey file to log a reading.</span></div>
          </article>

          <article v-else class="active-file response-file">
            <div class="file-tab cyan-tab"><span>FIELD RESPONSE</span></div>
            <div class="response-tabs">
              <button
                v-for="item in responseFiles"
                :key="item.id"
                :class="{ active: currentResponse?.id === item.id, inspection: item.kind === 'inspection' }"
                @click="pickResponse(item.id)"
              >
                <span>{{ item.id }}</span>
                <small>{{ item.status }}</small>
              </button>
            </div>

            <section v-if="currentResponse" class="response-sheet">
              <div class="clip"><i></i></div>
              <template v-if="currentResponse.kind === 'incident'">
                <div class="response-number">{{ currentResponse.id }}</div>
                <small>INCIDENT / {{ currentResponse.station_id }}</small>
                <h2>{{ currentResponse.title }}</h2>
                <div class="severity-meter">
                  <span>SEVERITY</span><b>{{ currentResponse.severity }}</b>
                  <i><u :style="{ width: `${currentResponse.severity}%` }"></u></i>
                </div>
                <div class="hand-note">
                  <span>Required field response / {{ currentResponse.response_code }}</span>
                  <p>{{ currentResponse.response }}</p>
                </div>
                <div v-if="currentResponse.response_assessment" class="hand-note response-check">
                  <span>{{ currentResponse.required_response_met ? "RESPONSE VERIFIED" : "RESPONSE STILL REQUIRED" }}</span>
                  <p>{{ currentResponse.response_assessment }}</p>
                </div>
                <div class="route-thread">
                  <i class="done"></i><span>Signal {{ currentResponse.signal_id }}</span>
                  <b></b>
                  <i :class="{ done: currentResponse.inspection_id }"></i>
                  <span>{{ currentResponse.inspection_id || "Inspection unassigned" }}</span>
                </div>
                <button
                  v-if="!currentResponse.inspection_id && roles.operator && roles.inspector"
                  class="pull-action"
                  @click="assignInspection(currentResponse)"
                >
                  <span>DISPATCH INSPECTION</span><i></i>
                </button>
              </template>
              <template v-else>
                <div class="response-number">{{ currentResponse.id }}</div>
                <small>INSPECTION / {{ currentResponse.incident_id }}</small>
                <h2>{{ currentResponse.verdict || "Field inspection" }}</h2>
                <div class="assignee-tag">
                  <span>ASSIGNED TO</span><b>{{ short(currentResponse.assignee) }}</b>
                </div>
                <div class="hand-note">
                  <span>{{ currentResponse.response_assessment ? "Required response assessment" : currentResponse.findings ? "Published findings" : "Field plan" }}</span>
                  <p>{{ currentResponse.response_assessment || currentResponse.analysis || currentResponse.findings || currentResponse.plan }}</p>
                </div>
                <a
                  v-if="currentResponse.evidence_url"
                  class="evidence-label"
                  :href="currentResponse.evidence_url"
                  target="_blank"
                >
                  {{ currentResponse.evidence_verified ? "EVIDENCE VERIFIED" : "EVIDENCE ATTACHED" }} <ExternalLink />
                </a>
                <button
                  v-if="currentResponse.status === 'ASSIGNED' && roles.inspector && currentResponse.assignee?.toLowerCase() === wallet?.toLowerCase()"
                  class="pull-action"
                  @click="openInspection(currentResponse)"
                >
                  <span>FILE FINDINGS</span><i></i>
                </button>
                <button
                  v-if="currentResponse.status === 'PENDING_REVIEW'"
                  class="pull-action review-pull"
                  @click="reviewInspection(currentResponse.id)"
                >
                  <span>REVIEW EVIDENCE</span><i></i>
                </button>
                <div v-if="currentResponse.verdict" class="final-stamp">{{ currentResponse.verdict }}</div>
              </template>
            </section>
            <div v-else class="empty-file"><Check /><b>No response files</b><span>No signal has opened a field incident.</span></div>
          </article>
        </div>

        <div class="tray-counter">
          <span><i></i> STUDIONET</span>
          <b>{{ overview.stations || 0 }}</b><small>stations</small>
          <b>{{ overview.sensors || 0 }}</b><small>sensors</small>
          <b>{{ overview.open_incidents || 0 }}</b><small>open</small>
        </div>
        <p v-if="error" class="pinned-error"><AlertTriangle /> {{ error }}</p>
      </div>
    </section>

    <section v-if="sheet" class="report-layer">
      <div class="clipboard">
        <div class="board-clip"></div>
        <button class="clip-close" title="Close report" @click="sheet = null"><X /></button>
        <header>
          <small>FIELD SIGNAL / PUBLIC RECORD</small>
          <span>{{ sheet.type === "signal" ? currentSensor?.id : sheet.item?.id }}</span>
          <h2>{{ sheet.type === "signal" ? "Observation sheet" : "Inspection findings" }}</h2>
        </header>
        <form v-if="sheet.type === 'signal'" @submit.prevent="submitSignal">
          <label><span>OBSERVED VALUE</span><input v-model="signalForm.value" required maxlength="40" /></label>
          <label><span>UTC TIMESTAMP</span><input v-model="signalForm.observed_at" required /></label>
          <label class="long-line">
            <span>FIELD CONTEXT / MINIMUM 60 CHARACTERS</span>
            <textarea v-model="signalForm.context" required minlength="60" maxlength="1200"></textarea>
          </label>
          <label class="long-line">
            <span>PUBLIC HTTPS EVIDENCE</span>
            <input v-model="signalForm.evidence_url" type="url" required />
          </label>
          <button class="guarded-lever" type="submit">
            <i><Satellite /></i><span>PULL TO TRANSMIT</span><b></b>
          </button>
        </form>
        <form v-else @submit.prevent="submitInspection(sheet.item)">
          <label class="long-line">
            <span>FIELD FINDINGS / MINIMUM 100 CHARACTERS</span>
            <textarea v-model="inspectionForm.findings" required minlength="100" maxlength="1800"></textarea>
          </label>
          <label class="long-line">
            <span>PUBLIC HTTPS EVIDENCE</span>
            <input v-model="inspectionForm.evidence_url" type="url" required />
          </label>
          <button class="guarded-lever" type="submit">
            <i><FileCheck2 /></i><span>PULL TO FILE</span><b></b>
          </button>
        </form>
        <footer><span>Operator {{ short(wallet) }}</span><b>FS / ORIGINAL</b></footer>
      </div>
    </section>

    <aside v-if="tx.open" class="receipt-reel" :class="tx.stage">
      <div class="printer-mouth"><i></i><i></i><i></i></div>
      <section>
        <button title="Tear off receipt" @click="tx.open = false"><X /></button>
        <small>GENLAYER / EXECUTION RECEIPT</small>
        <h3>{{ tx.title }}</h3>
        <div class="receipt-stage" :class="{ done: txIndex >= 1, failed: tx.stage === 'failed' }">
          <i></i><span>WALLET SIGNATURE</span><b>{{ txIndex >= 1 ? "MARKED" : "WAIT" }}</b>
        </div>
        <div class="receipt-stage" :class="{ done: txIndex >= 2, failed: tx.stage === 'failed' }">
          <i></i><span>VALIDATOR REVIEW</span><b>{{ txIndex >= 2 ? "RUNNING" : "WAIT" }}</b>
        </div>
        <div class="receipt-stage" :class="{ done: txIndex >= 3, failed: tx.stage === 'failed' }">
          <i></i><span>CONTRACT STATE</span><b>{{ txIndex >= 3 ? "ACCEPTED" : "WAIT" }}</b>
        </div>
        <p v-if="tx.stage === 'signature'">Confirm this field action in the connected wallet.</p>
        <p v-else-if="['submitted', 'consensus'].includes(tx.stage)">Validators are correlating the record and its evidence.</p>
        <p v-else-if="tx.stage === 'accepted'">Receipt accepted. Live files have been refreshed.</p>
        <p v-else>{{ tx.error }}</p>
        <a v-if="tx.hash" :href="`${explorerUrl}/tx/${tx.hash}`" target="_blank">
          TRACE {{ short(tx.hash) }} <ExternalLink />
        </a>
        <div class="receipt-teeth"></div>
      </section>
    </aside>
  </main>
</template>
