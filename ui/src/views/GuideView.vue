<template>
  <div class="app-shell d-flex flex-column min-vh-100">
    <div class="academic-header">
      <h1 class="main-title">
        <router-link
          :to="{ name: 'Guide' }"
          class="title-abbr"
          style="text-decoration: none; color: inherit;"
        >
          FAITH Demo
        </router-link>
      </h1>
      <h3 class="sub-title">
        <span class="title-full">Faithful Temporal Question Answering over Heterogeneous Sources</span>
      </h3>
      <div class="subtitle-wrapper">
        <div class="academic-meta">
          <span class="meta-divider">·</span>
          <span class="meta-item" @click="handleIntroductionClick">
            <i class="bi bi-journal-bookmark"></i>
            Introduction
          </span>
          <span class="meta-divider">·</span>
          <span class="meta-item" @click="handleBenchmarksClick">
            <i class="bi bi-download"></i>
            Benchmarks
          </span>
          <span class="meta-divider">·</span>
          <span class="meta-item" @click="handleLeaderboardClick">
            <i class="bi bi-trophy"></i>
            Leaderboard
          </span>
          <span class="meta-divider">·</span>
          <span class="meta-item" @click="handleContactClick">
            <i class="bi bi-envelope"></i>
            Contact
          </span>
        </div>
      </div>
    </div>
    <main class="flex-grow-1">
      <BContainer>

        <!-- Answer Component -->
        <div class="answer-component">
          <AnswerComponent 
            :initial-question="selectedExample" 
            @question-submitted="handleQuestionSubmitted" />
        </div>

        <!-- Configuration Card -->
        <!-- <BCard class="mt-4 mb-4 no-hover">
          <Configuration 
            @example-selected="onExampleSelected" 
            @config-changed="handleConfigChanged" />
        </BCard> -->

        <!-- Start Button -->
        <!-- <div class="text-center mb-4">
          <BButton variant="primary" size="lg" @click="startAnalysis" :disabled="!canStart">
            <i class="bi bi-play-fill me-2"></i>
            Start Analysis
          </BButton>
        </div> -->

        <!-- 引入模态框组件 -->
        <IntroductionModal
          v-model="showIntroductionModal"
          @close="handleModalClose('introduction')"
        />

        <BenchmarksModal
          v-model="showBenchmarksModal"
          @close="handleModalClose('benchmarks')"
        />

        <LeaderboardModal
          v-model="showLeaderboardModal"
          @close="handleModalClose('leaderboard')"
        />

        <ContactModal
          v-model="showContactModal"
          @close="handleModalClose('contact')"
        />
      </BContainer>
    </main>

    <footer class="site-footer mt-auto">
      <div class="footer-inner">
        <span>FAITH · Temporal QA System</span>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import Configuration from '../components/Configuration.vue';
import AnswerComponent from '../components/AnswerComponent.vue';
import IntroductionModal from '../components/IntroductionModal.vue';
import BenchmarksModal from '../components/BenchmarksModal.vue';
import LeaderboardModal from '../components/LeaderboardModal.vue';
import ContactModal from '../components/ContactModal.vue';
import {
  BContainer,
  BButton,
  BCard
} from 'bootstrap-vue-3';

const router = useRouter();
const route = useRoute();
const question = ref('');
const configData = ref({
  selectedCheckboxTypes: ['text', 'kb', 'table', 'info'],
  selectedRadioType1: 'classifier',
  selectedRadioType2: 'gnn',
  selectedRadioType3: 'timequestions'
});

// 控制模态框显示与隐藏的变量
const showIntroductionModal = ref(false);
const showBenchmarksModal = ref(false);
const showLeaderboardModal = ref(false);
const showContactModal = ref(false);

// 处理模态框点击事件
const handleIntroductionClick = () => {
  showIntroductionModal.value = true;
};

const handleBenchmarksClick = () => {
  showBenchmarksModal.value = true;
};

const handleLeaderboardClick = () => {
  showLeaderboardModal.value = true;
};

const handleContactClick = () => {
  showContactModal.value = true;
};

const selectedExample = ref('')
// Configuration.vue 发出的 event 会被上层捕获
function onExampleSelected(q: string) {
  selectedExample.value = q
}
onMounted(() => {
  if (route.query.APPquestion) {
    selectedExample.value = route.query.APPquestion as string
  }
})

// 处理模态框关闭事件
const handleModalClose = (modalName: string) => {
  switch (modalName) {
    case 'introduction':
      showIntroductionModal.value = false;
      break;
    case 'benchmarks':
      showBenchmarksModal.value = false;
      break;
    case 'leaderboard':
      showLeaderboardModal.value = false;
      break;
    case 'contact':
      showContactModal.value = false;
      break;
  }
};

// 处理问题提交
const handleQuestionSubmitted = (submittedQuestion: string) => {
  question.value = submittedQuestion;
};

// 处理配置变更
const handleConfigChanged = (newConfig: any) => {
  configData.value = newConfig;
};

// 计算是否可以开始分析
const canStart = computed(() => {
  return question.value.trim() !== '' && 
         configData.value.selectedCheckboxTypes.length > 0;
});

// 开始分析
const startAnalysis = () => {
  if (canStart.value) {
    // 将问题和配置数据编码为URL参数
    const questionParam = encodeURIComponent(question.value);
    router.push({
      name: 'Faith',
      query: {
        question: questionParam,
        config: JSON.stringify(configData.value)
      }
    });
  }
};
</script>

<style>
html, body, #app {
  height: 100%;
}
body {
  margin: 0 !important;
  padding: 0 !important;
  background-color: #dedede !important;
}
</style>

<style scoped>
.no-hover {
  transition: none !important;
  box-shadow: none !important;
}
.no-hover:hover {
  box-shadow: none !important;
  transform: none !important;
}
.academic-header {
  background: linear-gradient(to bottom, #b0d48c, #f1f0f0);
  background-size: 170% 170%;
  padding: 30px;
  border-bottom: 1px solid #e9ecef;
  text-align: center;
  margin-bottom: 2rem;
}

.main-title {
  padding: 50px 0 20px 0;
  font-size: 4rem;
  color: #283c64;
  margin-bottom: 0;
}

.sub-title {
  margin-bottom: 15px;
}

.title-abbr {
  font-weight: bold;
  color: #283c64;
  margin-right: 20px;
  font-size: 90px;
}

.title-full {
  color: #283c64;
  font-weight: bold;
  font-size: 35px;
}

.subtitle-wrapper {
  margin-top: 10px;
}

.academic-meta {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  padding-bottom: 20px;
}

.meta-item {
  display: flex;
  align-items: center;
  font-size: 1rem;
  color: #007bff;
  margin: 5px 10px;
  cursor: pointer;
  transition: color 0.3s ease;
  font-weight: bold;
}

.meta-item:hover {
  color: #0056b3;
}

.meta-item i {
  margin-right: 5px;
}

.meta-divider {
  color: #6c757d;
  margin: 0 10px;
}

.answer-component {
  margin-bottom: 2rem;
}

@media (max-width: 768px) {
  .main-title {
    font-size: 2rem;
  }

  .title-full {
    display: block;
    font-size: 1.5rem;
  }

  .academic-meta {
    flex-direction: column;
  }

  .meta-item {
    margin: 5px 0;
  }

  .meta-divider {
    display: none;
  }
}
.site-footer {
  background: #424242;
  color: #fff;
  padding: 14px 0;
  margin-top: 24px;
}

.footer-inner {
  max-width: 1140px;  /* 和 BContainer 宽度接近 */
  margin: 0 auto;
  padding: 0 12px;
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.dot {
  opacity: .6;
}

.site-footer a {
  color: #fff;
  text-decoration: none;
  border-bottom: 1px dashed rgba(255,255,255,.4);
}

.site-footer a:hover {
  border-bottom-color: #fff;
}
</style> 