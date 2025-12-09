<template>
  <BModal
    v-model="modelValue"
    title="Benchmarks"
    size="lg"
    centered
    @hide="handleClose"
  >
    <div class="benchmarks-content">
      <h5 class="headline-text">TIQ</h5>
      <p>
        <b>TIQ</b> (<u>T</u>emporal <u>I</u>mplicit <u>Q</u>uestions), is for temporal QA with 10,000 implicit questions. Questions are derived from heterogeneous sources: Wikipedia text, Wikipedia tables and the Wikidata KB.
        You can download it below:
      </p>
      <a
        class="btn btn-outline-secondary btn-block"
        href="https://faith.mpi-inf.mpg.de/benchmark/tiq/train.json"
        target="_blank"
        role="button"
      >
        <span
          class="oi oi-data-transfer-download download-icon"
          title="data-transfer-download"
          aria-hidden="true"
        ></span>
        Train Set (6000 Questions)
      </a>
      <a
        class="btn btn-outline-secondary btn-block"
        href="https://faith.mpi-inf.mpg.de/benchmark/tiq/dev.json"
        target="_blank"
        role="button"
      >
        <span
          class="oi oi-data-transfer-download download-icon"
          title="data-transfer-download"
          aria-hidden="true"
        ></span>
        Dev Set (2000 Questions)
      </a>
      <a
        class="btn btn-outline-secondary btn-block"
        href="https://faith.mpi-inf.mpg.de/benchmark/tiq/test.json"
        target="_blank"
        role="button"
      >
        <span
          class="oi oi-data-transfer-download download-icon"
          title="data-transfer-download"
          aria-hidden="true"
        ></span>
        Test Set (2000 Questions)
      </a>

      <!-- Division line -->
      <hr class="separator">

      <h5 class="headline-text">TimeQuestions</h5>
      <p>
        <b>TimeQuestions</b> were collected from eight
        KG-QA datasets for time-related questions.
        Each question is associated with its temporal category, and the answers are linked to Wikidata and Wikipedia.
      </p>
      <a
        class="btn btn-outline-secondary btn-block"
        href="https://exaqt.mpi-inf.mpg.de/static/data/TimeQuestions/train.json"
        target="_blank"
        role="button"
      >
        <span
          class="oi oi-data-transfer-download download-icon"
          title="data-transfer-download"
          aria-hidden="true"
        ></span>
        Training Set (9708 Questions)
      </a>
      <a
        class="btn btn-outline-secondary btn-block"
        href="https://exaqt.mpi-inf.mpg.de/static/data/TimeQuestions/dev.json"
        target="_blank"
        role="button"
      >
        <span
          class="oi oi-data-transfer-download download-icon"
          title="data-transfer-download"
          aria-hidden="true"
        ></span>
        Dev Set (3236 Questions)
      </a>
      <a
        class="btn btn-outline-secondary btn-block"
        href=" https://exaqt.mpi-inf.mpg.de/static/data/TimeQuestions/test.json"
        target="_blank"
        role="button"
      >
        <span
          class="oi oi-data-transfer-download download-icon"
          title="data-transfer-download"
          aria-hidden="true"
        ></span>
        Test Set (3237 Questions)
      </a>

      <p>
        TimeQuestions is licensed under a
        <a rel="license" href="https://creativecommons.org/licenses/by/4.0/" target="_blank">
          Creative Commons Attribution 4.0 International License
        </a>.
      </p>
    </div>

    <template #footer>
      <BButton variant="secondary" @click="handleClose">Close</BButton>
    </template>
  </BModal>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { BModal, BButton } from 'bootstrap-vue-3';

const props = defineProps<{
  modelValue: boolean
}>();

const emit = defineEmits(['update:modelValue', 'close']);

const modelValue = computed({
  get: () => props.modelValue,
  set: (value) => {
    emit('update:modelValue', value);
    if (!value) {
      emit('close');
    }
  }
});

const handleClose = () => {
  emit('update:modelValue', false);
  emit('close');
};
</script>

<style scoped>
.benchmarks-content {
  font-size: 1rem;
  line-height: 1.6;
  text-align: justify;
}

h4, h5 {
  color: #333;
  font-weight: bold;
  margin-top: 1.5rem;
  margin-bottom: 1rem;
}

.separator {
  border: none;
  border-top: 1px solid #e9ecef;
  margin: 30px 0;
}

.headline-text {
  color: #333;
  font-weight: bold;
  margin-bottom: 10px;
}

.btn.btn-outline-secondary.btn-block {
  margin-bottom: 10px;
  transition: background-color 0.3s ease;
}

.btn.btn-outline-secondary.btn-block:hover {
  background-color: #f8f9fa;
}
</style> 