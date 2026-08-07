<script setup>
import { computed } from "vue";
import { Radio, Satellite } from "lucide-vue-next";

const props = defineProps({ section: { type: String, required: true } });

const labels = {
  survey: {
    title: "Synchronizing field instruments",
    detail: "Reading registered stations, sensors, trust values, and operator roles from StudioNet.",
  },
  traces: {
    title: "Recovering validator traces",
    detail: "Loading observations, evidence digests, consensus verdicts, and response codes from StudioNet.",
  },
  response: {
    title: "Assembling response files",
    detail: "Loading incidents, assigned inspectors, findings, and required-response assessments from StudioNet.",
  },
  access: {
    title: "Verifying field credentials",
    detail: "Reading active operators, inspectors, and recorded station assignments directly from StudioNet.",
  },
};

const copy = computed(() => labels[props.section] || labels.survey);
</script>

<template>
  <article class="active-file chain-loader" aria-live="polite" aria-busy="true">
    <div class="file-tab"><span>{{ section.toUpperCase() }} / LIVE READ</span></div>
    <div class="chain-instrument">
      <div class="radar-scope">
        <i class="radar-ring ring-one"></i>
        <i class="radar-ring ring-two"></i>
        <i class="radar-ring ring-three"></i>
        <span class="radar-sweep"></span>
        <Satellite />
      </div>
      <div class="chain-copy">
        <small>GENLAYER STUDIONET / CONTRACT STATE</small>
        <h2>{{ copy.title }}</h2>
        <p>{{ copy.detail }}</p>
        <div class="signal-pulses">
          <i v-for="n in 12" :key="n" :style="{ '--delay': `${n * 70}ms` }"></i>
        </div>
        <span class="chain-status"><Radio /> Waiting for blockchain response</span>
      </div>
    </div>
  </article>
</template>
