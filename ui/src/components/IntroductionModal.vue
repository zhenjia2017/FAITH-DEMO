<template>
  <BModal
    v-model="modelValue"
    title="Introduction"
    size="lg"
    centered
    @hide="handleClose"
  >
    <div class="introduction-content">
      <h4 class="headline-text">FAITH method</h4>
      <p>
        Temporal question answering (QA) involves time constraints, with
        phrases such as ". . . in 2019" or ". . . before COVID". In the former,
        time is an explicit condition, in the latter it is implicit. State-of-the-
        art methods have limitations along three dimensions. First, with
        neural inference, time constraints are merely soft-matched, giving
        room to invalid or inexplicable answers. Second, questions with
        implicit time are poorly supported. Third, answers come from a
        single source: either a knowledge base (KB) or a text corpus. We
        propose <b>FAITH</b> (<u>FAI</u>ful <u>T</u>emporal Question Answering
        over <u>H</u>eterogeneous Sources) a temporal QA system that addresses
        these shortcomings.
        First, it enforces temporal constraints for faithful answering with
        tangible evidence. Second, it properly handles implicit questions.
        Third, it operates over heterogeneous sources, covering KB, text and
        web tables in a unified manner. The method has three stages: (i)
        understanding the question and its temporal conditions, (ii) retrieving evidence from all sources, and (iii) faithfully answering the
        question. As implicit questions are sparse in prior benchmarks, we
        introduce a principled method for generating diverse questions.
        Experiments show superior performance over a suite of baselines.
      </p>

      <div class="mt-4 text-center">
        <img 
          src="/images/overview-figure.png" 
          alt="FAITH System Overview" 
          class="img-fluid rounded"
          style="display: block; border: 1px solid #000; margin-left: auto; margin-right: auto;"
        >
        <i class="custom-caption">Overview of the FAITH pipeline. The figure illustrates the process of answering q<sub>3</sub> ("Queen's record company when recording Bohemian Rhapsody?" ) and q<sub>1</sub> ("Record company of Queen in 1975?" ). For answering q<sub>3</sub>, two intermediate questions q<sub>31</sub> and q<sub>32</sub> are generated, and run recursively through the entire FAITH pipeline.</i>
      </div>

      <hr class="separator">

      <h4 class="headline-text">Related Papers</h4>
      <p>
        <b>"Faithful Temporal Question Answering over Heterogeneous Sources"</b>, Zhen Jia, Philipp Christmann, and Gerhard Weikum. In
        <a href="https://www2024.thewebconf.org" target="_blank">WWW '24</a>, Singapore, 13 - 17 May 2024.
        <br>
        [<a href="https://dl.acm.org/doi/pdf/10.1145/3589334.3645547" target="_blank">Paper</a>]
        [<a href="https://github.com/zhenjia2017/FAITH" target="_blank">Code</a>]
        [<a href="https://qa.mpi-inf.mpg.de/faith/2024-www-poster-faith.pdf" target="_blank">Poster</a>]
      </p>
      <p>
        <b>"TIQ: A Benchmark for Temporal Question Answering with Implicit Time Constraints"</b>, Zhen Jia, Philipp Christmann, and Gerhard Weikum. In
        <a href="https://temporalweb.net" target="_blank">TempWeb@WWW '24</a>, Singapore, 14 May 2024.
        <br>
        [<a href="https://github.com/zhenjia2017/TIQ" target="_blank">Code</a>]
        [<a href="https://qa.mpi-inf.mpg.de/tiq/2024-www-tiq-slides.pdf" target="_blank">Slides</a>]
      </p>
      <p>
        <b>"Complex Temporal Question Answering on Knowledge Graphs"</b>, Zhen Jia, Soumajit Pramanik, Rishiraj Saha Roy, and Gerhard
        Weikum, in <a href="https://www.cikm2021.org/" target="_blank">CIKM' 21</a>, Virtual Event, 1 - 5 November
        2021.<br>
        [<a href="https://dl.acm.org/doi/pdf/10.1145/3459637.3482416" target="_blank" rel="noreferrer">Paper</a>] [<a
                href="https://github.com/zhenjia2017/EXAQT" target="_blank" rel="noreferrer">Code</a>] [<a
                href="https://qa.mpi-inf.mpg.de/exaqt/cikm21-slides-zjsprsrgw.pdf" target="_blank"
                rel="noreferrer">Slides</a>] [<a
                href="https://qa.mpi-inf.mpg.de/exaqt/cikm21-poster-zjsprsrgw.pdf" target="_blank"
                rel="noreferrer">Poster</a>] [<a
                href="https://qa.mpi-inf.mpg.de/exaqt/cikm21-video-zjsprsrgw.mp4" target="_blank"
                rel="noreferrer">Video</a>]
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
.introduction-content {
  font-size: 1rem;
  line-height: 1.6;
  text-align: justify;
}

h4 {
  color: #333;
  font-weight: bold;
  margin-top: 1.5rem;
  margin-bottom: 1rem;
}

ul, ol {
  padding-left: 1.5rem;
}

li {
  margin-bottom: 0.5rem;
}

img {
  max-width: 100%;
  height: auto;
  margin-top: 1rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.custom-caption {
  display: block;
  text-align: center;
  margin-top: 10px;
  font-style: italic;
  color: #6c757d;
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
</style> 