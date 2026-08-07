<script setup>
import {
  ArrowLeft,
  BookOpenCheck,
  CheckCircle2,
  CircleDot,
  ExternalLink,
  FileCheck2,
  Fingerprint,
  Radio,
  Satellite,
  ShieldCheck,
  TriangleAlert,
  Wallet,
} from "lucide-vue-next";

defineProps({
  appUrl: { type: String, required: true },
  contractAddress: { type: String, required: true },
  explorerUrl: { type: String, required: true },
});
</script>

<template>
  <main class="guide-page">
    <header class="guide-topbar">
      <a :href="appUrl" class="guide-back"><ArrowLeft /> FIELD SIGNAL</a>
      <span><i></i> STUDIONET LIVE</span>
      <a :href="`${explorerUrl}/address/${contractAddress}`" target="_blank">
        CONTRACT <ExternalLink />
      </a>
    </header>

    <section class="guide-intro">
      <div class="manual-mark"><BookOpenCheck /><span>FS-06</span></div>
      <div>
        <small>FIELD OPERATIONS MANUAL / REVIEWER EDITION</small>
        <h1>Operate FieldSignal from reading to verified response.</h1>
        <p>
          This guide follows the exact live StudioNet workflow. It explains who may act,
          what evidence validators retrieve, which state changes are recorded, and how to
          interpret every transaction result.
        </p>
      </div>
    </section>

    <div class="guide-layout">
      <nav class="chapter-index" aria-label="Guide chapters">
        <span>CHAPTER INDEX</span>
        <a href="#before">01 Before you begin</a>
        <a href="#connect">02 Connect safely</a>
        <a href="#reading">03 Submit a reading</a>
        <a href="#consensus">04 Run consensus</a>
        <a href="#incident">05 Work an incident</a>
        <a href="#inspection">06 File inspection evidence</a>
        <a href="#roles">07 Roles and permissions</a>
        <a href="#receipts">08 Receipts and errors</a>
      </nav>

      <article class="manual-body">
        <section id="before" class="guide-chapter">
          <div class="chapter-number">01</div>
          <div class="chapter-copy">
            <small>PRE-FLIGHT</small>
            <h2>Before you begin</h2>
            <p>
              FieldSignal is role-gated. The deployed reviewer wallet
              <code>0x95803126315A05E642D8E46CE1d77eA2199a2A6E</code> is seeded as owner,
              operator, and inspector so the complete lifecycle can be tested. Other wallets
              can read every public record but protected controls remain unavailable until the
              owner grants the required role from the app's <b>Access</b> file.
            </p>
            <div class="chapter-checks">
              <span><CheckCircle2 /> Use a browser wallet that exposes standard EIP-1193 accounts.</span>
              <span><CheckCircle2 /> Keep public evidence reachable over HTTPS.</span>
              <span><CheckCircle2 /> Use the seeded owner wallet or onboard a separate operator and inspector in Access.</span>
            </div>
          </div>
        </section>

        <section id="connect" class="guide-chapter">
          <div class="chapter-number">02</div>
          <div class="chapter-copy">
            <small>WALLET ENTRY</small>
            <h2>Connect without MetaMask Snaps</h2>
            <p>
              Return to the app and press <b>Unlock with wallet</b>. The frontend requests the
              selected account through <code>eth_requestAccounts</code>. It never invokes
              <code>wallet_getSnaps</code>, <code>wallet_requestSnaps</code>, or a GenLayer
              client connection helper that probes unsupported Snap methods.
            </p>
            <div class="flow-strip">
              <span><Wallet /> UNLOCK</span><i></i><span><Fingerprint /> EIP-1193</span><i></i><span><ShieldCheck /> ROLE READ</span>
            </div>
            <p class="note"><b>Persistent entry:</b> after a successful connection, refreshing the page silently restores the wallet when the provider still exposes the authorized account.</p>
          </div>
        </section>

        <section id="reading" class="guide-chapter">
          <div class="chapter-number">03</div>
          <div class="chapter-copy">
            <small>SURVEY FILE</small>
            <h2>Submit an authenticated sensor reading</h2>
            <ol>
              <li>Select a registered sensor in <b>Survey</b>. Each sensor belongs to a station with a recorded operator.</li>
              <li>Press <b>Log reading</b> and provide the observed value, UTC timestamp, field context, and a public HTTPS evidence URL.</li>
              <li>Confirm the wallet transaction and keep the animated receipt open until StudioNet reaches a terminal state.</li>
            </ol>
            <p>
              The contract rejects unknown sensors and unauthorized senders. A reading may be
              filed only by that station's operator or an account in the active operator
              registry; the sender is permanently stored as the reading's typed reporter address.
              That authorization is checked again when consensus starts, so a revoked reporter
              cannot turn a pending reading into incident state.
            </p>
            <a class="sample-link" href="https://raw.githubusercontent.com/AbstrusImad/fieldsignal/main/docs/evidence/signal-pm25.md" target="_blank">
              OPEN SAMPLE SENSOR EVIDENCE <ExternalLink />
            </a>
          </div>
        </section>

        <section id="consensus" class="guide-chapter">
          <div class="chapter-number">04</div>
          <div class="chapter-copy">
            <small>TRACES FILE</small>
            <h2>Retrieve evidence and run validator consensus</h2>
            <ol>
              <li>Open <b>Traces</b> and select a reading with status <b>Pending</b>.</li>
              <li>Press <b>Run consensus</b>. The intelligent contract retrieves the submitted URL through <code>gl.nondet.web.render</code>.</li>
              <li>Validators independently compare the verdict, severity, confidence, evidence digest, and required response code.</li>
            </ol>
            <div class="validator-grid">
              <span><Radio /><b>VERDICT</b> routine, anomaly, invalid evidence</span>
              <span><Satellite /><b>EVIDENCE</b> retrieved text and SHA-256 digest</span>
              <span><CircleDot /><b>RESPONSE</b> bounded canonical response code</span>
            </div>
            <p>
              Material readings open an incident. The contract maps the agreed response code to
              canonical response text, so unchecked free-form output cannot become operational
              incident state.
            </p>
          </div>
        </section>

        <section id="incident" class="guide-chapter">
          <div class="chapter-number">05</div>
          <div class="chapter-copy">
            <small>RESPONSE FILE</small>
            <h2>Dispatch the recorded inspector</h2>
            <ol>
              <li>Open <b>Response</b> and select an incident without an inspection.</li>
              <li>Select a wallet from the live <b>Authorized inspector</b> registry, then press <b>Dispatch inspection</b>. The station operator records that exact address and the field plan.</li>
              <li>The resulting inspection stores the exact assignee. Another wallet cannot claim or submit that inspection.</li>
            </ol>
            <p class="note"><b>Enforced throughout:</b> inspector status is checked at assignment, findings submission, and consensus resolution. Revoking the role blocks the stored assignee before validator output can alter the incident.</p>
          </div>
        </section>

        <section id="inspection" class="guide-chapter">
          <div class="chapter-number">06</div>
          <div class="chapter-copy">
            <small>FIELD FINDINGS</small>
            <h2>Prove the required response was completed</h2>
            <ol>
              <li>Connect as the inspection's recorded assignee and press <b>File findings</b>.</li>
              <li>Describe the field result and attach public HTTPS evidence that directly proves each required action.</li>
              <li>Press <b>Review evidence</b>. Validators retrieve the source and independently decide <code>required_response_met</code>.</li>
            </ol>
            <p>
              The inspection verdict, evidence digest, response assessment, and completion
              boolean are written to both the inspection and its incident. Closure occurs only
              when the evidence is verified and every material response action is proven.
              If validators return <code>ACTION_REQUIRED</code>, the recorded inspector uses
              <b>File correction</b> to replace the findings and evidence. Each attempt is counted,
              re-fetched, re-hashed, and reviewed before the incident can close.
            </p>
            <a class="sample-link" href="https://raw.githubusercontent.com/AbstrusImad/fieldsignal/main/docs/evidence/inspection-pm25.md" target="_blank">
              OPEN SAMPLE INSPECTION EVIDENCE <ExternalLink />
            </a>
          </div>
        </section>

        <section id="roles" class="guide-chapter">
          <div class="chapter-number">07</div>
          <div class="chapter-copy">
            <small>ACCESS CONTROL</small>
            <h2>Roles and permissions</h2>
            <ol>
              <li>Connect the contract owner and open <b>Access</b>.</li>
              <li>Enter a wallet, enable Operator and/or Inspector, and choose a station when assigning operator authority.</li>
              <li>Confirm <b>Apply authorization</b>. One contract call updates both role records and the optional station assignment.</li>
              <li>To revoke access, submit the wallet again with the corresponding role disabled. Pending consensus rechecks the recorded actor.</li>
            </ol>
            <div class="role-table">
              <div><b>OWNER</b><span>Atomically activate or revoke operators and inspectors, and bind a station to its recorded operator.</span></div>
              <div><b>OPERATOR</b><span>Enroll sensors, submit readings, and dispatch inspections.</span></div>
              <div><b>INSPECTOR</b><span>Submit findings only for the inspection assigned to that wallet.</span></div>
              <div><b>VALIDATORS</b><span>Retrieve evidence and agree on bounded state transitions.</span></div>
            </div>
          </div>
        </section>

        <section id="receipts" class="guide-chapter">
          <div class="chapter-number">08</div>
          <div class="chapter-copy">
            <small>TRANSACTION CONTROL</small>
            <h2>Read waiting states, receipts, and failures</h2>
            <p>
              Every write opens a receipt immediately. It progresses through wallet signature,
              validator review, and contract state. The animation stops only when the public
              StudioNet client reports a terminal status.
            </p>
            <div class="receipt-guide">
              <span><i class="amber"></i><b>SIGNATURE</b> confirm in wallet</span>
              <span><i class="cyan"></i><b>CONSENSUS</b> validators evaluating</span>
              <span><i class="green"></i><b>ACCEPTED</b> state applied and refreshed</span>
              <span><i class="red"></i><b>ROLLBACK</b> state unchanged; read the decoded reason</span>
            </div>
            <div class="troubleshooting">
              <TriangleAlert />
              <p><b>Common expected rejection:</b> "Authorized station operator required" means the connected wallet lacks active authority. "Only recorded assignee may submit" means the wallet is not the stored inspector. "Recorded inspector role is not active" means authorization was revoked before consensus. These are contract protections, not wallet failures.</p>
            </div>
          </div>
        </section>

        <footer class="guide-finish">
          <FileCheck2 />
          <div><b>Ready for field operation</b><span>Return to the live kit and follow the chapters in order.</span></div>
          <a :href="appUrl">OPEN FIELD SIGNAL</a>
        </footer>
      </article>
    </div>
  </main>
</template>

<style scoped>
.guide-page { min-height: 100vh; color: #242a23; background: #d8d1b9; font-family: Arial, Helvetica, sans-serif; }
.guide-topbar { position: sticky; z-index: 20; top: 0; min-height: 64px; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 20px; padding: 0 5vw; color: #edf0db; background: #29362e; border-bottom: 5px solid #f06436; }
.guide-topbar a { display: inline-flex; align-items: center; gap: 8px; color: inherit; font-size: 14px; font-weight: 700; text-decoration: none; }
.guide-topbar a:last-child { justify-self: end; }
.guide-topbar span { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 700; }
.guide-topbar span i { width: 9px; height: 9px; border-radius: 50%; background: #43c1bd; box-shadow: 0 0 0 5px rgba(67,193,189,.14); }
.guide-topbar svg { width: 17px; }
.guide-intro { display: grid; grid-template-columns: 150px minmax(0, 800px); gap: 34px; align-items: start; padding: 80px max(6vw, calc((100vw - 1180px) / 2)); background: linear-gradient(120deg, #536548 0 32%, #3b4a3e 32% 100%); color: #f2f0dc; }
.manual-mark { width: 130px; height: 150px; display: grid; place-content: center; justify-items: center; gap: 10px; border: 3px solid #d2c95e; transform: rotate(-2deg); }
.manual-mark svg { width: 42px; height: 42px; color: #43c1bd; }
.manual-mark span { font: 800 27px "Barlow Condensed", Arial, sans-serif; }
.guide-intro small, .chapter-copy > small { color: #d7ca5a; font-size: 13px; font-weight: 800; }
.guide-intro h1 { max-width: 800px; margin: 12px 0 18px; font: 800 clamp(42px, 6vw, 72px)/.98 "Barlow Condensed", Arial, sans-serif; }
.guide-intro p { max-width: 760px; margin: 0; font-size: 18px; line-height: 1.65; }
.guide-layout { width: min(1180px, calc(100% - 48px)); display: grid; grid-template-columns: 230px minmax(0, 1fr); gap: 42px; margin: 0 auto; padding: 58px 0 100px; }
.chapter-index { position: sticky; top: 96px; align-self: start; display: grid; border-left: 4px solid #3d584b; }
.chapter-index span { padding: 0 18px 14px; color: #a53d27; font-size: 13px; font-weight: 800; }
.chapter-index a { padding: 10px 18px; color: #3a4038; font-size: 14px; font-weight: 700; line-height: 1.35; text-decoration: none; }
.chapter-index a:hover { color: #a53d27; background: rgba(255,255,255,.25); }
.manual-body { min-width: 0; }
.guide-chapter { scroll-margin-top: 90px; display: grid; grid-template-columns: 64px minmax(0, 1fr); gap: 26px; padding: 0 0 58px; margin-bottom: 52px; border-bottom: 2px dashed #99937d; }
.chapter-number { width: 58px; height: 58px; display: grid; place-items: center; border: 4px solid #3d584b; border-radius: 50%; color: #3d584b; font: 800 18px "Barlow Condensed", Arial, sans-serif; }
.chapter-copy h2 { margin: 6px 0 16px; font: 800 38px/1 "Barlow Condensed", Arial, sans-serif; }
.chapter-copy p, .chapter-copy li { font-size: 16px; line-height: 1.7; }
.chapter-copy code { overflow-wrap: anywhere; padding: 2px 5px; color: #294f4b; background: rgba(255,255,255,.45); font: 600 14px "IBM Plex Mono", monospace; }
.chapter-copy ol { display: grid; gap: 12px; margin: 18px 0; padding-left: 24px; }
.chapter-checks { display: grid; gap: 10px; margin-top: 20px; }
.chapter-checks span { display: flex; align-items: flex-start; gap: 9px; font-size: 15px; line-height: 1.45; }
.chapter-checks svg { width: 19px; min-width: 19px; color: #347e79; }
.flow-strip { display: grid; grid-template-columns: 1fr 40px 1fr 40px 1fr; align-items: center; gap: 8px; margin: 25px 0; }
.flow-strip span { min-height: 64px; display: flex; align-items: center; justify-content: center; gap: 8px; border: 2px solid #526256; font-size: 13px; font-weight: 800; }
.flow-strip i { border-top: 2px dashed #6e705e; }
.flow-strip svg { width: 18px; color: #a53d27; }
.note { padding: 15px 17px; border-left: 6px solid #f06436; background: rgba(255,255,255,.36); }
.sample-link { display: inline-flex; align-items: center; gap: 8px; margin-top: 8px; padding: 12px 15px; border: 2px solid #35574e; color: #27473f; font-size: 13px; font-weight: 800; text-decoration: none; }
.sample-link svg { width: 15px; }
.validator-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 9px; margin: 24px 0; }
.validator-grid span { min-height: 115px; display: grid; align-content: start; gap: 7px; padding: 16px; border: 2px solid #777764; font-size: 14px; line-height: 1.45; }
.validator-grid svg { color: #a53d27; }
.role-table { margin-top: 20px; border-top: 2px solid #686b5d; }
.role-table div { display: grid; grid-template-columns: 150px 1fr; gap: 18px; padding: 16px 4px; border-bottom: 1px solid #92917c; }
.role-table b { font: 800 19px "Barlow Condensed", Arial, sans-serif; }
.role-table span { font-size: 15px; line-height: 1.5; }
.receipt-guide { display: grid; grid-template-columns: repeat(2, 1fr); gap: 9px; margin: 22px 0; }
.receipt-guide span { display: grid; grid-template-columns: 14px 100px 1fr; align-items: center; gap: 8px; padding: 13px; border: 1px solid #7f806f; font-size: 14px; }
.receipt-guide i { width: 11px; height: 11px; border-radius: 50%; }
.amber { background: #d5a53a; }.cyan { background: #43c1bd; }.green { background: #40845e; }.red { background: #b53d2c; }
.troubleshooting { display: grid; grid-template-columns: 25px 1fr; gap: 12px; padding: 18px; color: #422b24; background: #e4cbb0; }
.troubleshooting svg { color: #a53d27; }
.troubleshooting p { margin: 0; font-size: 15px; }
.guide-finish { display: grid; grid-template-columns: 48px 1fr auto; align-items: center; gap: 16px; padding: 24px; color: #eff0df; background: #34463b; }
.guide-finish svg { width: 36px; height: 36px; color: #43c1bd; }
.guide-finish div { display: grid; gap: 4px; }
.guide-finish b { font: 800 23px "Barlow Condensed", Arial, sans-serif; }
.guide-finish span { font-size: 14px; }
.guide-finish a { padding: 13px 16px; color: #1f2c25; background: #d7ca5a; font-size: 13px; font-weight: 800; text-decoration: none; }
@media (max-width: 820px) {
  .guide-topbar { grid-template-columns: 1fr auto; padding: 0 16px; }.guide-topbar > span { display: none; }
  .guide-intro { grid-template-columns: 1fr; gap: 22px; padding: 50px 24px; }.manual-mark { width: 92px; height: 105px; }
  .guide-intro h1 { font-size: 46px; }.guide-intro p { font-size: 16px; }
  .guide-layout { width: calc(100% - 32px); display: block; padding-top: 30px; }.chapter-index { position: relative; top: auto; display: none; }
  .guide-chapter { grid-template-columns: 45px minmax(0, 1fr); gap: 13px; padding-bottom: 40px; margin-bottom: 38px; }
  .chapter-number { width: 42px; height: 42px; border-width: 3px; font-size: 15px; }.chapter-copy h2 { font-size: 32px; }
  .flow-strip { grid-template-columns: 1fr; }.flow-strip i { width: 2px; height: 22px; justify-self: center; border: 0; border-left: 2px dashed #6e705e; }
  .validator-grid, .receipt-guide { grid-template-columns: 1fr; }.validator-grid span { min-height: 0; }
  .role-table div { grid-template-columns: 1fr; gap: 4px; }.guide-finish { grid-template-columns: 40px 1fr; }.guide-finish a { grid-column: 1 / -1; text-align: center; }
}
</style>
