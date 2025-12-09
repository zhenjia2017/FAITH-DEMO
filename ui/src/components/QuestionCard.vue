<template>
  <div class="card mt-4">
    <div class="card-header bg-light d-flex justify-content-between align-items-center">
      <h5 class="mb-0 fw-bold">Question Understanding</h5>
    </div>

    <div class="card-body">
      <div class="row">
        <!-- Top level -->
        <div class="col-12">
          <h6 class="text-muted fw-bold section-title">Current Question</h6>
          <p id="currentQuestion" class="border-bottom pb-2">
            {{ question || 'No question' }}
          </p>
        </div>

        <div class="col-12">
          <h6 class="fw-bold section-title text-dark">Time-aware Structured Frame</h6>
          <div class="border-bottom pb-2 mb-3">
            <div class="row g-3">
              <div class="col-md-6 detail">
                <small class="text-muted fw-bold section-title">Entity:</small>
                <p class="mb-2">{{ temporalInfo.entity || 'No information' }}</p>
              </div>
              <div class="col-md-6 detail">
                <small class="text-muted fw-bold section-title">Temporal Category:</small>
                <p class="mb-2">{{ temporalInfo.category === 'implicit' ? 'implicit' : 'non-implicit' }}</p>
              </div>
              <div class="col-12 detail">
                <small class="text-muted fw-bold section-title">Relation:</small>
                <p class="mb-2">{{ temporalInfo.relation || 'No information' }}</p>
              </div>
              <div class="col-md-6 detail">
                <small class="text-muted fw-bold section-title">Answer type:</small>
                <p class="mb-2">
                  {{ overrideAnswerType || temporalInfo.answerType || 'No information' }}
                </p>
              </div>
              <div class="col-md-6 detail">
                <small class="text-muted fw-bold section-title">Temporal signal:</small>
                <p class="mb-2">{{ temporalInfo.temporalSignal || 'No information' }}</p>
              </div>
              <div class="col-12">
                <small class="text-muted fw-bold section-title">Temporal value:</small>
                <div class="list-group list-group-flush">
                  <div
                    v-for="(timeRange, index) in temporalInfo.temporalValues"
                    :key="index"
                    class="temporal-value-item"
                  >
                    <small class="text-muted fw-bold">Time range {{ index + 1 }}：</small>
                    <div class="d-flex align-items-center">
                      <span>{{ formatDate(timeRange[0]) }}</span>
                      <i class="bi bi-arrow-right mx-2"></i>
                      <span>{{ formatDate(timeRange[1]) }}</span>
                    </div>
                  </div>
                  <div v-if="!temporalInfo.temporalValues?.length" class="list-group-item text-muted">
                    No time value information
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 单卡模式：一个折叠，内部依次为 Answers -> Evidences -> Question Understanding -> Evidences Retrieval -> Graphs -->
        <div
          class="col-12 mt-3"
          v-if="!isDual && (intermediateQuestionText || hasIntermediateInfo)"
        >
          <h6 class="text-muted fw-bold section-title">Implicit Question Resolver</h6>

          <div class="intermediate-question-section">
            <p
              @click="toggleOuter()"
              class="clickable-text"
              :class="{ 'text-primary': !outerOpen }"
            >
              {{ intermediateQuestionText || 'Intermediate details' }}
              <i :class="['bi', outerOpen ? 'bi-chevron-up' : 'bi-chevron-down']"></i>
            </p>

            <transition name="slide-fade">
              <div v-if="outerOpen" class="intermediate-details">
                <div class="intermediate-details-content">
                  <b-card class="AR-SE no-hover">
                    <!-- Ranked Answers -->
                    <div :class="['AR-SE-card', 'section', 'mt-4', 'no-hover', 'intermediate-section', { collapsed: !answersOpenSingle }]">
                      <h6 class="section-title header-toggle d-flex justify-content-between align-items-center" @click="toggleAnswersSingle">
                        <span>Ranked Answers</span>
                        <i :class="answersOpenSingle ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
                      </h6>
                      <transition name="slide-fade">             
                        <div v-show="answersOpenSingle">
                          <div class="row g-3">
                            <template v-if="answers && answers.length">
                              <div
                                v-for="(answer, index) in answers.slice(0, 5)"
                                :key="answer.id || index"
                                class="col-md-6 col-lg-4"
                              >
                                <div class="card h-100 intermediate-card shadow-sm">
                                  <div class="card-body">
                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                      <span class="badge rounded-pill bg-secondary">TOP {{ index + 1 }}</span>
                                      <span class="badge bg-light text-dark">{{ Number(answer.score ?? 0).toFixed(3) }}</span>
                                    </div>
                                    <h6 class="card-title text-truncate fw-bold" :title="answer.label">
                                      {{ answer.label }}
                                    </h6>
                                    <p class="card-text small text-muted mb-0 fw-bold">
                                      ID:
                                      <template v-if="answer.id && answer.id.startsWith('Q')">
                                        <a
                                          :href="`https://www.wikidata.org/wiki/${answer.id}`"
                                          target="_blank"
                                          rel="noopener noreferrer"
                                        >
                                          {{ answer.id }}
                                        </a>
                                      </template>
                                      <template v-else>{{ answer.id }}</template>
                                    </p>
                                  </div>
                                </div>
                              </div>
                            </template>
                            <div v-else class="col-12">
                              <div class="alert alert-info mb-0">No answer ranking information</div>
                            </div>
                          </div>
                        </div>
                      </transition>
                    </div>

                    <!-- Supporting Evidences -->
                    <div :class="['AR-SE-card', 'section', 'mt-4', 'no-hover', 'intermediate-section', { collapsed: !evidencesOpenSingle }]">
                      <h6 class="section-title header-toggle d-flex justify-content-between align-items-center" @click="toggleEvidencesSingle">
                        <span>Supporting Evidences</span>
                        <i :class="evidencesOpenSingle ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
                      </h6>
                      <transition name="slide-fade">
                        <div v-show="evidencesOpenSingle">
                          <div class="row g-3">
                            <template v-if="evidences && evidences.length">
                              <div v-for="(evidence, index) in evidences.slice(0, 5)" :key="index" class="col-12">
                                <div
                                  class="card h-100 intermediate-card shadow-sm"
                                  v-if="selectedTypes.includes(evidence.source)"
                                >
                                  <div class="card-body">
                                    <div class="d-flex justify-content-between align-items-start mb-2">
                                      <div class="d-flex align-items-center">
                                        <span class="badge bg-secondary rounded-pill me-2">
                                          <a
                                            v-if="evidence.url"
                                            :href="evidence.url"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            class="evidence-link"
                                          >
                                            Evidence {{ index + 1 }}
                                          </a>
                                          <template v-else>Evidence {{ index + 1 }}</template>
                                        </span>
                                      </div>
                                      <div class="d-flex align-items-center">
                                        <span class="badge bg-light text-dark me-2">
                                          {{ Number(evidence.score ?? 0).toFixed(3) }}
                                        </span>
                                        <span class="badge bg-light text-dark" :title="'Source'">
                                          <i :class="getSourceIcon(evidence.source)"></i>
                                          {{ getSourceName(evidence.source) }}
                                        </span>
                                      </div>
                                    </div>
                                    <p class="card-text mb-0 evidence-text fw-bold" v-html="evidence.text"></p>
                                  </div>
                                </div>
                              </div>
                            </template>
                            <div v-else class="col-12">
                              <div class="alert alert-info mb-0">No evidence information</div>
                            </div>
                          </div>
                        </div>
                      </transition>
                    </div>
                  </b-card>

                  <b-card class="QU-ER-HA no-hover">
                    <!-- 单卡：Question Understanding（在 Evidences 之后） -->
                    <div class="section mt-4 intermediate-section">
                      <h6 class="section-title">Question Understanding</h6>
                      <div class="row g-3 bg-white px-3 py-0 shadow-sm mt-3 rounded">
                        <div class="col-12">
                          <small class="text-muted fw-bold">Current Question:</small>
                          <p class="border-bottom pb-2">
                            {{ (intermediateQuestionText || question) || 'No question' }}
                          </p>
                        </div>
                        <h6 class="m-0 fw-bold section-title text-dark">Time-aware Structured Frame</h6>
                        <div class="col-md-6 detail">
                          <small class="text-muted fw-bold">Entity:</small>
                          <p class="mb-2">{{ intermediateTemporalInfo.entity || 'No information' }}</p>
                        </div>
                        <div class="col-md-6 detail">
                          <small class="text-muted fw-bold">Temporal Category:</small>
                          <p class="mb-2">
                            {{ intermediateTemporalInfo.category === 'implicit' ? 'implicit' : 'non-implicit' }}
                          </p>
                        </div>
                        <div class="col-12 detail">
                          <small class="text-muted fw-bold">Relation:</small>
                          <p class="mb-2">{{ intermediateTemporalInfo.relation || 'No information' }}</p>
                        </div>
                        <div class="col-md-6 detail">
                          <small class="text-muted fw-bold">Answer type:</small>
                          <p class="mb-2">{{ intermediateTemporalInfo.answerType || 'No information' }}</p>
                        </div>
                        <div class="col-md-6 detail">
                          <small class="text-muted fw-bold">Temporal signal:</small>
                          <p class="mb-2">{{ intermediateTemporalInfo.temporalSignal || 'No information' }}</p>
                        </div>
                        <div class="col-12 mb-2">
                          <small class="text-muted fw-bold">Temporal value:</small>
                          <div class="list-group list-group-flush">
                            <div
                              v-for="(timeRange, index) in intermediateTemporalInfo.temporalValues || []"
                              :key="index"
                              class="temporal-value-item"
                            >
                              <small class="text-muted fw-bold">Time range {{ index + 1 }}:</small>
                              <div class="d-flex">
                                <span>{{ formatDate(timeRange[0]) }}</span>
                                <i class="bi bi-arrow-right mx-2"></i>
                                <span>{{ formatDate(timeRange[1]) }}</span>
                              </div>
                            </div>
                            <div v-if="!(intermediateTemporalInfo.temporalValues?.length)" class="list-group-item text-muted">
                              No time value information
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- 单卡：Evidences Retrieval（在 Understanding 之后） -->
                    <div class="section mt-4 intermediate-section">
                      <h6 class="section-title fw-bold">Evidences Retrieval</h6>
                      <div class="intermediate-charts">
                        <div class="chart-wrapper">
                          <h6 class="fw-bold">Heterogeneous Retrieval ({{ intermediateInitialEvidencesLength || 0 }})</h6>
                          <div ref="sInitRef" class="pie-container"></div>
                        </div>
                        <div class="chart-arrow">
                          <i class="bi bi-arrow-right-circle-fill"></i>
                        </div>
                        <div class="chart-wrapper">
                          <h6 class="fw-bold">Temporal Pruning ({{ intermediatePrunedEvidencesLength || 0 }})</h6>
                          <div ref="sPruneRef" class="pie-container"></div>
                        </div>
                        <div class="chart-arrow">
                          <i class="bi bi-arrow-right-circle-fill"></i>
                        </div>
                        <div class="chart-wrapper">
                          <h6 class="fw-bold">Evidence Scoring ({{ intermediateTopkEvidencesLength || 0 }})</h6>
                          <div ref="sTopkRef" class="pie-container"></div>
                        </div>
                      </div>
                    </div>

                    <!-- 单卡：Graphs -->
                    <div class="intermediate-graph-section mt-4" v-if="iterativeGraphs && iterativeGraphs.length">
                      <h3 id="singleCard" class="fw-bold h3-with-dash">
                        <span>Below are <span class="tp-emph">{{ totalPagesSingle }}</span> heterogeneous graphs:</span>
                      </h3>
                      <BPopover
                        target="singleCard"
                        placement="bottom"
                        triggers="hover"
                        html
                        custom-class="popover-wide"
                      >
                        <div style="max-width: 800px;">
                          <p style="margin:0;">
                            1: Graphs in each <strong>pruning</strong> iteration, starting from the graph with initial top-100 evidence, to smaller ones.
                          </p>
                          <p style="margin:6px 0 0;">
                            When <strong>the number of pruning iterations is 0</strong>, the graph with the initial top-100 evidence is in the answer prediction.
                          </p>
                          <p style="margin:6px 0 0;">
                            2: Graph with answers and their supporting top-5 evidence in the answer prediction.
                          </p>
                        </div>
                      </BPopover>
                      <div class="btn-group mt-2">
                        <button class="btn btn-outline-secondary" :disabled="pageSingle <= 1" @click="goPrevSingle">
                          <p class="fw-bold">&larr; Prev</p>
                        </button>
                        <button
                          class="btn btn-outline-secondary"
                          :disabled="pageSingle >= totalPagesSingle"
                          @click="goNextSingle"
                        >
                          <p class="fw-bold">Next &rarr;</p>
                        </button>
                      </div>

                      
                      <GraphCard
                        v-if="currentGraphSingle"
                        :graph-data="currentGraphSingle"
                        :ranked-answers="answers"
                        :is-final="pageSingle === totalPagesSingle"
                        :highlight="highlightSingle"
                      />
                    </div>
                  </b-card>
                </div>
              </div>
            </transition>
          </div>
        </div>

        <!-- 双卡模式：一个总折叠，里面有两个子折叠（上下排列） -->
        <div class="col-12 mt-3" v-if="isDual">
          <h6 class="text-muted fw-bold section-title">Implicit Question Resolver</h6>

          <div class="intermediate-question-section">
            <p @click="toggleOuter()" class="clickable-text" :class="{ 'text-primary': !outerOpen }">
              {{ intermediateQuestionText || 'Intermediate sub-questions' }}
              <i :class="['bi', outerOpen ? 'bi-chevron-up' : 'bi-chevron-down']"></i>
            </p>

            <transition name="slide-fade">
              <div v-if="outerOpen" class="intermediate-details">
                <div class="intermediate-details-content">
                  <h6 class="text-muted fw-bold section-title">The time values are derived from the following two generated questions.</h6>
                  <!-- 子卡 1（前三页） -->
                  <p class="clickable-text mt-2" @click="toggleChild(1)">
                    {{ dualItems[0]?.question || '' }}
                    <i :class="['bi', child1Open ? 'bi-chevron-up' : 'bi-chevron-down']" class="ms-2"></i>
                  </p>

                  <transition name="slide-fade">
                    <div v-if="child1Open" class="subcard-body">
                      <div class="intermediate-details-content">
                        <!-- 子卡1：Question Understanding（在 Evidences 之后，但为了结构清晰，先放位于此处，最终展示顺序仍按要求） -->
                        
                        <b-card class="AR-SE no-hover">
                          <!-- 子卡1：Ranked Answers -->
                          <div :class="['AR-SE-card', 'section', 'mt-2', 'no-hover', 'intermediate-section', { collapsed: !answersOpenC1 }]">
                            <h6 class="section-title header-toggle d-flex justify-content-between align-items-center" @click="toggleAnswersC1">
                              <span>Ranked Answers</span>
                              <i :class="answersOpenC1 ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
                            </h6>
                            <transition name="slide-fade">
                              <div v-show="answersOpenC1">
                                <div class="row g-3">
                                  <template v-if="dualItems[0]?.rankedAnswers?.length">
                                    <div
                                      v-for="(answer, idx) in dualItems[0].rankedAnswers.slice(0,5)"
                                      :key="answer.id || idx"
                                      class="col-md-6 col-lg-4"
                                    >
                                      <div class="card h-100 intermediate-card shadow-sm">
                                        <div class="card-body">
                                          <div class="d-flex justify-content-between align-items-center mb-2">
                                            <span class="badge rounded-pill bg-secondary">TOP {{ idx + 1 }}</span>
                                            <span class="badge bg-light text-dark">{{ Number(answer.score ?? 0).toFixed(3) }}</span>
                                          </div>
                                          <h6 class="card-title text-truncate fw-bold" :title="answer.label">
                                            {{ answer.label }}
                                          </h6>
                                          <p class="card-text small text-muted mb-0 fw-bold">
                                            ID:
                                            <template v-if="answer.id && answer.id.startsWith('Q')">
                                              <a
                                                :href="`https://www.wikidata.org/wiki/${answer.id}`"
                                                target="_blank"
                                                rel="noopener noreferrer"
                                              >
                                                {{ answer.id }}
                                              </a>
                                            </template>
                                            <template v-else>{{ answer.id }}</template>
                                          </p>
                                        </div>
                                      </div>
                                    </div>
                                  </template>
                                  <div v-else class="col-12">
                                    <div class="alert alert-info mb-0">No answer ranking information</div>
                                  </div>
                                </div>
                              </div>
                            </transition>
                          </div>

                          <!-- 子卡1：Supporting Evidences -->
                          <div :class="['AR-SE-card', 'section', 'mt-2', 'no-hover', 'intermediate-section', { collapsed: !evidencesOpenC1 }]">
                            <h6 class="section-title header-toggle d-flex justify-content-between align-items-center" @click="toggleEvidencesC1">
                              <span>Supporting Evidences</span>
                              <i :class="evidencesOpenC1 ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
                            </h6>
                            <transition name="slide-fade">
                              <div v-show="evidencesOpenC1">
                                <div class="row g-3">
                                  <template v-if="dualItems[0]?.evidences?.length">
                                    <div
                                      v-for="(ev, idx) in dualItems[0].evidences.slice(0,5)"
                                      :key="idx"
                                      class="col-12"
                                    >
                                      <div
                                        class="card h-100 intermediate-card shadow-sm"
                                        v-if="selectedTypes.includes(ev.source)"
                                      >
                                        <div class="card-body">
                                          <div class="d-flex justify-content-between align-items-start mb-2">
                                            <div class="d-flex align-items-center">
                                              <span class="badge bg-secondary rounded-pill me-2">
                                                <a
                                                  v-if="ev.url"
                                                  :href="ev.url"
                                                  target="_blank"
                                                  rel="noopener noreferrer"
                                                  class="evidence-link"
                                                >
                                                  Evidence {{ idx + 1 }}
                                                </a>
                                                <template v-else>Evidence {{ idx + 1 }}</template>
                                              </span>
                                            </div>
                                            <div class="d-flex align-items-center">
                                              <span class="badge bg-light text-dark me-2">
                                                {{ Number(ev.score ?? 0).toFixed(3) }}
                                              </span>
                                              <span class="badge bg-light text-dark" :title="'Source'">
                                                <i :class="getSourceIcon(ev.source)"></i>
                                                {{ getSourceName(ev.source) }}
                                              </span>
                                            </div>
                                          </div>
                                          <p class="card-text mb-0 evidence-text fw-bold" v-html="ev.text"></p>
                                        </div>
                                      </div>
                                    </div>
                                  </template>
                                  <div v-else class="col-12">
                                    <div class="alert alert-info mb-0">No evidence information</div>
                                  </div>
                                </div>
                              </div>
                            </transition>
                          </div>
                        </b-card>

                        <b-card class="QU-ER-HA no-hover">
                          <!-- 子卡1：Question Understanding（在 Supporting Evidences 后） -->
                          <div class="section mt-2 intermediate-section">
                            <h6 class="section-title">Question Understanding</h6>
                            <div class="row g-3 bg-white px-3 py-0 shadow-sm mt-3 rounded">
                              <div class="col-12">
                                <small class="text-muted fw-bold">Current Question:</small>
                                <p class="border-bottom pb-2">
                                  {{ dualItems[0]?.question || 'No question' }}
                                </p>
                              </div>
                              <h6 class="m-0 fw-bold section-title text-dark">Time-aware Structured Frame</h6>
                              <div class="col-md-6 detail">
                                <small class="text-muted fw-bold">Entity:</small>
                                <p class="mb-2">{{ dualItems[0]?.temporalInfo?.entity || 'No information' }}</p>
                              </div>
                              <div class="col-md-6 detail">
                                <small class="text-muted fw-bold">Temporal Category:</small>
                                <p class="mb-2">
                                  {{ dualItems[0]?.temporalInfo?.category === 'implicit' ? 'implicit' : 'non-implicit' }}
                                </p>
                              </div>
                              <div class="col-12 detail">
                                <small class="text-muted fw-bold">Relation:</small>
                                <p class="mb-2">{{ dualItems[0]?.temporalInfo?.relation || 'No information' }}</p>
                              </div>
                              <div class="col-md-6 detail">
                                <small class="text-muted fw-bold">Answer type:</small>
                                <p class="mb-2">{{ dualItems[0]?.temporalInfo?.answerType || 'No information' }}</p>
                              </div>
                              <div class="col-md-6 detail">
                                <small class="text-muted fw-bold">Temporal signal:</small>
                                <p class="mb-2">{{ dualItems[0]?.temporalInfo?.temporalSignal || 'No information' }}</p>
                              </div>
                              <div class="col-12 mb-2">
                                <small class="text-muted fw-bold">Temporal value:</small>
                                <div class="list-group list-group-flush">
                                  <div
                                    v-for="(timeRange, index) in dualItems[0]?.temporalInfo?.temporalValues || []"
                                    :key="index"
                                    class="temporal-value-item"
                                  >
                                    <small class="text-muted fw-bold">Time range {{ index + 1 }}：</small>
                                    <div class="d-flex align-items-center">
                                      <span>{{ formatDate(timeRange[0]) }}</span>
                                      <i class="bi bi-arrow-right mx-2"></i>
                                      <span>{{ formatDate(timeRange[1]) }}</span>
                                    </div>
                                  </div>
                                  <div v-if="!(dualItems[0]?.temporalInfo?.temporalValues?.length)" class="list-group-item text-muted">
                                    No time value information
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>

                          <!-- 子卡1：Evidences Retrieval（在 Understanding 后） -->
                          <div class="section mt-2 intermediate-section">
                            <h6 class="section-title fw-bold">Evidences Retrieval</h6>
                            <div class="intermediate-charts">
                              <div class="chart-wrapper">
                                <h6 class="fw-bold">Heterogeneous Retrieval ({{ dualItems[0]?.initialEvidencesLength || 0 }})</h6>
                                <div ref="c1InitRef" class="pie-container"></div>
                              </div>
                              <div class="chart-arrow">
                                <i class="bi bi-arrow-right-circle-fill"></i>
                              </div>
                              <div class="chart-wrapper">
                                <h6 class="fw-bold">Temporal Pruning ({{ dualItems[0]?.prunedEvidencesLength || 0 }})</h6>
                                <div ref="c1PruneRef" class="pie-container"></div>
                              </div>
                              <div class="chart-arrow">
                                <i class="bi bi-arrow-right-circle-fill"></i>
                              </div>
                              <div class="chart-wrapper">
                                <h6 class="fw-bold">Evidence Scoring ({{ dualItems[0]?.topkEvidencesLength || 0 }})</h6>
                                <div ref="c1TopkRef" class="pie-container"></div>
                              </div>
                            </div>
                          </div>

                          <!-- 子卡1：Graphs (first 3 pages) -->
                          <div class="intermediate-graph-section mt-3" v-if="firstGraphs.length">
                            <h3 id="Page1" class="fw-bold h3-with-dash">
                              <span>Below are <span class="tp-emph">{{ totalPages1 }}</span> heterogeneous graphs:</span>
                            </h3>
                            <BPopover
                              target="Page1"
                              placement="bottom"
                              triggers="hover"
                              html
                              custom-class="popover-wide"
                            >
                              <div style="max-width: 800px;">
                                <p style="margin:0;">
                                  1: Graphs in each <strong>pruning</strong> iteration, starting from the graph with initial top-100 evidence, to smaller ones.
                                </p>
                                <p style="margin:6px 0 0;">
                                  When <strong>the number of pruning iterations is 0</strong>, the graph with the initial top-100 evidence is in the answer prediction.
                                </p>
                                <p style="margin:6px 0 0;">
                                  2: Graph with answers and their supporting top-5 evidence in the answer prediction.
                                </p>
                              </div>
                            </BPopover>
                            <div class="btn-group mt-2">
                              <button class="btn btn-outline-secondary" :disabled="page1 <= 1" @click="goPrev1">
                                <p class="fw-bold">&larr; Prev</p>
                              </button>
                              <button
                                class="btn btn-outline-secondary"
                                :disabled="page1 >= totalPages1"
                                @click="goNext1"
                              >
                                <p class="fw-bold">Next &rarr;</p>
                              </button>
                            </div>

                            <GraphCard
                              v-if="currentGraph1"
                              :graph-data="currentGraph1"
                              :ranked-answers="dualItems[0]?.rankedAnswers || []"
                              :is-final="page1 === totalPages1"
                              :highlight="highlightC1"
                            />
                          </div>
                        </b-card>
                      </div>
                    </div>
                  </transition>


                  <!-- 子卡 2（后三页） -->
                  <p class="clickable-text mt-2" @click="toggleChild(2)">
                    {{ dualItems[1]?.question || '' }}
                    <i :class="['bi', child2Open ? 'bi-chevron-up' : 'bi-chevron-down']" class="ms-2"></i>
                  </p>

                  <transition name="slide-fade">
                    <div v-if="child2Open" class="subcard-body">
                      <div class="intermediate-details-content">
                        <b-card class="AR-SE no-hover">
                          <!-- 子卡2：Ranked Answers -->
                          <div :class="['AR-SE-card', 'section', 'mt-2', 'no-hover', 'intermediate-section', { collapsed: !answersOpenC2 }]">
                            <h6 class="section-title header-toggle d-flex justify-content-between align-items-center" @click="toggleAnswersC2">
                              <span>Ranked Answers</span>
                              <i :class="answersOpenC2 ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
                            </h6>
                            <transition name="slide-fade">
                              <div v-show="answersOpenC2">
                                <div class="row g-3">
                                  <template v-if="dualItems[1]?.rankedAnswers?.length">
                                    <div
                                      v-for="(answer, idx) in dualItems[1].rankedAnswers.slice(0,5)"
                                      :key="answer.id || idx"
                                      class="col-md-6 col-lg-4"
                                    >
                                      <div class="card h-100 intermediate-card shadow-sm">
                                        <div class="card-body">
                                          <div class="d-flex justify-content-between align-items-center mb-2">
                                            <span class="badge rounded-pill bg-secondary">TOP {{ idx + 1 }}</span>
                                            <span class="badge bg-light text-dark">{{ Number(answer.score ?? 0).toFixed(3) }}</span>
                                          </div>
                                          <h6 class="card-title text-truncate fw-bold" :title="answer.label">
                                            {{ answer.label }}
                                          </h6>
                                          <p class="card-text small text-muted mb-0 fw-bold">
                                            ID:
                                            <template v-if="answer.id && answer.id.startsWith('Q')">
                                              <a
                                                :href="`https://www.wikidata.org/wiki/${answer.id}`"
                                                target="_blank"
                                                rel="noopener noreferrer"
                                              >
                                                {{ answer.id }}
                                              </a>
                                            </template>
                                            <template v-else>{{ answer.id }}</template>
                                          </p>
                                        </div>
                                      </div>
                                    </div>
                                  </template>
                                  <div v-else class="col-12">
                                    <div class="alert alert-info mb-0">No answer ranking information</div>
                                  </div>
                                </div>
                              </div>
                            </transition>
                          </div>

                          <!-- 子卡2：Supporting Evidences -->
                          <div :class="['AR-SE-card', 'section', 'mt-2', 'no-hover', 'intermediate-section', { collapsed: !evidencesOpenC2 }]">
                            <h6 class="section-title header-toggle d-flex justify-content-between align-items-center" @click="toggleEvidencesC2">
                              <span>Supporting Evidences</span>
                              <i :class="evidencesOpenC2 ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
                            </h6>
                            <transition name="slide-fade">
                              <div v-show="evidencesOpenC2">
                                <div class="row g-3">
                                  <template v-if="dualItems[1]?.evidences?.length">
                                    <div
                                      v-for="(ev, idx) in dualItems[1].evidences.slice(0,5)"
                                      :key="idx"
                                      class="col-12"
                                    >
                                      <div
                                        class="card h-100 intermediate-card shadow-sm"
                                        v-if="selectedTypes.includes(ev.source)"
                                      >
                                        <div class="card-body">
                                          <div class="d-flex justify-content-between align-items-start mb-2">
                                            <div class="d-flex align-items-center">
                                              <span class="badge bg-secondary rounded-pill me-2">
                                                <a
                                                  v-if="ev.url"
                                                  :href="ev.url"
                                                  target="_blank"
                                                  rel="noopener noreferrer"
                                                  class="evidence-link"
                                                >
                                                  Evidence {{ idx + 1 }}
                                                </a>
                                                <template v-else>Evidence {{ idx + 1 }}</template>
                                              </span>
                                            </div>
                                            <div class="d-flex align-items-center">
                                              <span class="badge bg-light text-dark me-2">
                                                {{ Number(ev.score ?? 0).toFixed(3) }}
                                              </span>
                                              <span class="badge bg-light text-dark" :title="'Source'">
                                                <i :class="getSourceIcon(ev.source)"></i>
                                                {{ getSourceName(ev.source) }}
                                              </span>
                                            </div>
                                          </div>
                                          <p class="card-text mb-0 evidence-text fw-bold" v-html="ev.text"></p>
                                        </div>
                                      </div>
                                    </div>
                                  </template>
                                  <div v-else class="col-12">
                                    <div class="alert alert-info mb-0">No evidence information</div>
                                  </div>
                                </div>
                              </div>
                            </transition>
                          </div>
                        </b-card>

                        <b-card class="QU-ER-HA no-hover">
                          <!-- 子卡2：Question Understanding（在 Supporting Evidences 后） -->
                          <div class="section mt-2 intermediate-section">
                            <h6 class="section-title">Question Understanding</h6>
                            <div class="row g-3 bg-white px-3 py-0 shadow-sm mt-3 rounded">
                              <div class="col-12">
                                <small class="text-muted fw-bold">Current Question:</small>
                                <p class="border-bottom pb-2">
                                  {{ dualItems[1]?.question || 'No question' }}
                                </p>
                              </div>
                              <h6 class="m-0 fw-bold section-title text-dark">Time-aware Structured Frame</h6>
                              <div class="col-md-6 detail">
                                <small class="text-muted fw-bold">Entity:</small>
                                <p class="mb-2">{{ dualItems[1]?.temporalInfo?.entity || 'No information' }}</p>
                              </div>
                              <div class="col-md-6 detail">
                                <small class="text-muted fw-bold">Temporal Category:</small>
                                <p class="mb-2">
                                  {{ dualItems[1]?.temporalInfo?.category === 'implicit' ? 'implicit' : 'non-implicit' }}
                                </p>
                              </div>
                              <div class="col-12 detail">
                                <small class="text-muted fw-bold">Relation:</small>
                                <p class="mb-2">{{ dualItems[1]?.temporalInfo?.relation || 'No information' }}</p>
                              </div>
                              <div class="col-md-6 detail">
                                <small class="text-muted fw-bold">Answer type:</small>
                                <p class="mb-2">{{ dualItems[1]?.temporalInfo?.answerType || 'No information' }}</p>
                              </div>
                              <div class="col-md-6 detail">
                                <small class="text-muted fw-bold">Temporal signal:</small>
                                <p class="mb-2">{{ dualItems[1]?.temporalInfo?.temporalSignal || 'No information' }}</p>
                              </div>
                              <div class="col-12 mb-2">
                                <small class="text-muted fw-bold">Temporal value:</small>
                                <div class="list-group list-group-flush">
                                  <div
                                    v-for="(timeRange, index) in dualItems[1]?.temporalInfo?.temporalValues || []"
                                    :key="index"
                                    class="temporal-value-item"
                                  >
                                    <small class="text-muted fw-bold">Time range {{ index + 1 }}：</small>
                                    <div class="d-flex align-items-center">
                                      <span>{{ formatDate(timeRange[0]) }}</span>
                                      <i class="bi bi-arrow-right mx-2"></i>
                                      <span>{{ formatDate(timeRange[1]) }}</span>
                                    </div>
                                  </div>
                                  <div v-if="!(dualItems[1]?.temporalInfo?.temporalValues?.length)" class="list-group-item text-muted">
                                    No time value information
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>

                          <!-- 子卡2：Evidences Retrieval（在 Understanding 后） -->
                          <div class="section mt-2 intermediate-section">
                            <h6 class="section-title fw-bold">Evidences Retrieval</h6>
                            <div class="intermediate-charts">
                              <div class="chart-wrapper">
                                <h6 class="fw-bold">Heterogeneous Retrieval ({{ dualItems[1]?.initialEvidencesLength || 0 }})</h6>
                                <div ref="c2InitRef" class="pie-container"></div>
                              </div>
                              <div class="chart-arrow">
                                <i class="bi bi-arrow-right-circle-fill"></i>
                              </div>
                              <div class="chart-wrapper">
                                <h6 class="fw-bold">Temporal Pruning ({{ dualItems[1]?.prunedEvidencesLength || 0 }})</h6>
                                <div ref="c2PruneRef" class="pie-container"></div>
                              </div>
                              <div class="chart-arrow">
                                <i class="bi bi-arrow-right-circle-fill"></i>
                              </div>
                              <div class="chart-wrapper">
                                <h6 class="fw-bold">Evidence Scoring ({{ dualItems[1]?.topkEvidencesLength || 0 }})</h6>
                                <div ref="c2TopkRef" class="pie-container"></div>
                              </div>
                            </div>
                          </div>

                          <!-- 子卡2：Graphs (last 3 pages) -->
                          <div class="intermediate-graph-section mt-3" v-if="lastGraphs.length">
                            <h3 id="Page2" class="fw-bold h3-with-dash">
                              <span>Below are <span class="tp-emph">{{ totalPages2 }}</span> heterogeneous graphs:</span>
                            </h3>
                            <BPopover
                              target="Page2"
                              placement="bottom"
                              triggers="hover"
                              html
                              custom-class="popover-wide"
                            >
                              <div style="max-width: 800px;">
                                <p style="margin:0;">
                                  1: Graphs in each <strong>pruning</strong> iteration, starting from the graph with initial top-100 evidence, to smaller ones.
                                </p>
                                <p style="margin:6px 0 0;">
                                  When <strong>the number of pruning iterations is 0</strong>, the graph with the initial top-100 evidence is in the answer prediction.
                                </p>
                                <p style="margin:6px 0 0;">
                                  2: Graph with answers and their supporting top-5 evidence in the answer prediction.
                                </p>
                              </div>
                            </BPopover>
                            <div class="btn-group mt-2">
                              <button class="btn btn-outline-secondary" :disabled="page2 <= 1" @click="goPrev2">
                                <p class="fw-bold">&larr; Prev</p>
                              </button>
                              <button
                                class="btn btn-outline-secondary"
                                :disabled="page2 >= totalPages2"
                                @click="goNext2"
                              >
                                <p class="fw-bold">Next &rarr;</p>
                              </button>
                            </div>

                            <GraphCard
                              v-if="currentGraph2"
                              :graph-data="currentGraph2"
                              :ranked-answers="dualItems[1]?.rankedAnswers || []"
                              :is-final="page2 === totalPages2"
                              :highlight="highlightC2"
                            />
                          </div>
                        </b-card>
                      </div>
                    </div>
                  </transition>


                </div>
              </div>
            </transition>
          </div>
        </div>
        <!-- /双卡模式 -->
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import type { TemporalInfo, GraphData } from '@/types'
import GraphCard from './Graphcard.vue'

defineOptions({ name: 'QuestionCard' })

interface Answer {
  id: string
  label: string
  score: number
  isCorrect: boolean
}
interface Evidence {
  text: string
  source: string
  score: number
  isAnswering: boolean
  url?: string
}

const props = withDefaults(defineProps<{
  /* 外层（或单卡） */
  question: string
  temporalInfo: TemporalInfo
  intermediateQuestionText: string
  intermediateTemporalInfo: TemporalInfo
  answers: Answer[]
  evidences: Evidence[]
  selectedTypes: string[]
  iterativeGraphs?: GraphData[]
  currentIntermediatePage?: number

  /* 单卡饼图统计 */
  intermediateInitialEvidencesLength?: number
  intermediateInitialEvidencesSource?: Record<string, number>
  intermediatePrunedEvidencesLength?: number
  intermediatePrunedEvidencesSource?: Record<string, number>
  intermediateTopkEvidencesLength?: number
  intermediateTopkEvidencesSource?: Record<string, number>

  /* 双卡 */
  hasDual?: boolean
  dualItems?: Array<{
    question: string
    generated_q?: string
    temporalInfo: TemporalInfo
    rankedAnswers: Answer[]
    evidences: Evidence[]
    initialEvidencesLength?: number
    initialEvidencesSource?: Record<string, number>
    prunedEvidencesLength?: number
    prunedEvidencesSource?: Record<string, number>
    topkEvidencesLength?: number
    topkEvidencesSource?: Record<string, number>
  }>

  /* 覆盖外层 Answer type（如 intermediate_q_answer_type） */
  overrideAnswerType?: string
}>(), {
  question: '',
  temporalInfo: () => ({
    entity: '',
    category: '',
    relation: '',
    answerType: '',
    temporalSignal: '',
    temporalValues: []
  }),
  intermediateQuestionText: '',
  intermediateTemporalInfo: () => ({
    entity: '',
    category: '',
    relation: '',
    answerType: '',
    temporalSignal: '',
    temporalValues: []
  }),
  answers: () => [],
  evidences: () => [],
  iterativeGraphs: () => [],
  currentIntermediatePage: 1,

  intermediateInitialEvidencesLength: 0,
  intermediateInitialEvidencesSource: () => ({}),
  intermediatePrunedEvidencesLength: 0,
  intermediatePrunedEvidencesSource: () => ({}),
  intermediateTopkEvidencesLength: 0,
  intermediateTopkEvidencesSource: () => ({}),

  hasDual: false,
  dualItems: () => [],
  overrideAnswerType: ''
})

/** —— 判定 —— */
const isDual = computed(
  () => props.hasDual && Array.isArray(props.dualItems) && props.dualItems.length === 2
)

/** —— 折叠控制 —— */
const outerOpen = ref(false)   // 单卡/双卡总折叠
const child1Open = ref(false)  // 子卡1
const child2Open = ref(false)  // 子卡2
function toggleOuter() {
  outerOpen.value = !outerOpen.value
  if (outerOpen.value) {
    // 打开时初始化单卡饼图（仅单卡时）
    if (!isDual.value) initSinglePies()
  } else {
    // 关闭总折叠，清理单卡饼图
    disposeGroup('single')
  }
}

/** —— 单卡模式分页 —— */
const pageSingle = ref(props.currentIntermediatePage || 1)
const totalPagesSingle = computed(() => props.iterativeGraphs?.length || 0)
const currentGraphSingle = computed(() => {
  const arr = props.iterativeGraphs || []
  return arr[pageSingle.value - 1] || null
})
function goPrevSingle() { if (pageSingle.value > 1) pageSingle.value-- }
function goNextSingle() { if (pageSingle.value < totalPagesSingle.value) pageSingle.value++ }

/** —— 双卡图分页：前3/后3 —— */
const firstGraphs = computed(() => (props.iterativeGraphs || []).slice(0, 3))
const lastGraphs  = computed(() => {
  const arr = props.iterativeGraphs || []
  return arr.slice(Math.max(0, arr.length - 3))
})
const page1 = ref(1)
const totalPages1 = computed(() => firstGraphs.value.length || 0)
const currentGraph1 = computed(() => firstGraphs.value[page1.value - 1] || null)
function goPrev1() { if (page1.value > 1) page1.value-- }
function goNext1() { if (page1.value < totalPages1.value) page1.value++ }

const page2 = ref(1)
const totalPages2 = computed(() => lastGraphs.value.length || 0)
const currentGraph2 = computed(() => lastGraphs.value[page2.value - 1] || null)
function goPrev2() { if (page2.value > 1) page2.value-- }
function goNext2() { if (page2.value < totalPages2.value) page2.value++ }

/** —— 是否显示单卡折叠 —— */
const hasIntermediateInfo = computed(() => {
  const t = props.intermediateTemporalInfo || {}
  return Object.keys(t).length > 0 || (props.answers?.length ?? 0) > 0 || (props.evidences?.length ?? 0) > 0
})

/** —— 饼图：refs —— */
/* 单卡 */
const sInitRef = ref<HTMLElement | null>(null)
const sPruneRef = ref<HTMLElement | null>(null)
const sTopkRef  = ref<HTMLElement | null>(null)
/* 子卡1 */
const c1InitRef = ref<HTMLElement | null>(null)
const c1PruneRef = ref<HTMLElement | null>(null)
const c1TopkRef  = ref<HTMLElement | null>(null)
/* 子卡2 */
const c2InitRef = ref<HTMLElement | null>(null)
const c2PruneRef = ref<HTMLElement | null>(null)
const c2TopkRef  = ref<HTMLElement | null>(null)

/** —— 饼图实例分组管理 —— */
const chartGroups: Record<'single' | 'c1' | 'c2', echarts.ECharts[]> = {
  single: [],
  c1: [],
  c2: []
}
function addChart(group: 'single' | 'c1' | 'c2', c: echarts.ECharts) { chartGroups[group].push(c) }
function disposeGroup(group: 'single' | 'c1' | 'c2') {
  chartGroups[group].forEach(c => c.dispose())
  chartGroups[group] = []
}
function resizeAll() {
  ;(['single','c1','c2'] as const).forEach(g => chartGroups[g].forEach(c => c.resize()))
}

/** —— 渲染饼图 —— */
function renderPie(el: HTMLElement, dataObj: Record<string, number>) {
  const inst = echarts.init(el)
  const data = [
    { name: 'KB',    value: dataObj?.kb    || 0 },
    { name: 'Text',  value: dataObj?.text  || 0 },
    { name: 'Info',  value: dataObj?.info  || 0 },
    { name: 'Table', value: dataObj?.table || 0 }
  ]
  inst.setOption({
    color: ['#5470C6', '#91CC75', '#9A60B4', '#FAC858'],
    tooltip: { trigger: 'item' },
    legend: {
      orient: 'vertical', right: 0, top: 'bottom',
      data: data.map(d => d.name),
      itemWidth: 12, itemHeight: 12,
      textStyle: { fontSize: 10, color: '#333' }
    },
    series: [{
      type: 'pie', radius: ['40%', '70%'], center: ['50%', '55%'],
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 12, fontWeight: 'bold' } },
      data
    }]
  })
  return inst
}

/** —— 初始化各组饼图 —— */
async function initSinglePies() {
  await nextTick()
  disposeGroup('single')
  if (sInitRef.value) addChart('single', renderPie(sInitRef.value, props.intermediateInitialEvidencesSource || {}))
  if (sPruneRef.value) addChart('single', renderPie(sPruneRef.value, props.intermediatePrunedEvidencesSource  || {}))
  if (sTopkRef.value)  addChart('single', renderPie(sTopkRef.value,  props.intermediateTopkEvidencesSource    || {}))
}
async function initChildPies(which: 1 | 2) {
  await nextTick()
  if (which === 1) {
    disposeGroup('c1')
    if (c1InitRef.value) addChart('c1', renderPie(c1InitRef.value, props.dualItems?.[0]?.initialEvidencesSource || {}))
    if (c1PruneRef.value) addChart('c1', renderPie(c1PruneRef.value, props.dualItems?.[0]?.prunedEvidencesSource  || {}))
    if (c1TopkRef.value)  addChart('c1', renderPie(c1TopkRef.value,  props.dualItems?.[0]?.topkEvidencesSource    || {}))
  } else {
    disposeGroup('c2')
    if (c2InitRef.value) addChart('c2', renderPie(c2InitRef.value, props.dualItems?.[1]?.initialEvidencesSource || {}))
    if (c2PruneRef.value) addChart('c2', renderPie(c2PruneRef.value, props.dualItems?.[1]?.prunedEvidencesSource  || {}))
    if (c2TopkRef.value)  addChart('c2', renderPie(c2TopkRef.value,  props.dualItems?.[1]?.topkEvidencesSource    || {}))
  }
}

/** —— 子折叠切换 —— */
function toggleChild(which: 1 | 2) {
  if (which === 1) {
    child1Open.value = !child1Open.value
    if (child1Open.value) initChildPies(1)
    else disposeGroup('c1')
  } else {
    child2Open.value = !child2Open.value
    if (child2Open.value) initChildPies(2)
    else disposeGroup('c2')
  }
}

/** —— 监听与清理 —— */
if (typeof window !== 'undefined') {
  window.addEventListener('resize', resizeAll)
}
onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', resizeAll)
  }
  disposeGroup('single')
  disposeGroup('c1')
  disposeGroup('c2')
})

/** —— 小工具 —— */
function toOrdinal(n: number): string {
  const s = ['th', 'st', 'nd', 'rd'] as const
  const v = n % 100
  const suf = (s as any)[(v - 20) % 10] || (s as any)[v] || s[0]
  return `${n}${suf}`
}
const formatDate = (dateStr: string) => {
  if (!dateStr) return 'Invalid date'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return /^\d{4}$/.test(dateStr) ? dateStr : dateStr
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}
const getSourceIcon = (source?: string): string => {
  if (!source) return 'bi-question-circle'
  switch (source) {
    case 'kb': return 'bi-database-fill'
    case 'text': return 'bi-file-text-fill'
    case 'table': return 'bi-table'
    case 'web': return 'bi-globe'
    case 'info': return 'bi-info-square-fill'
    default: return 'bi-question-circle'
  }
}
const getSourceName = (source?: string): string => {
  if (!source) return 'Unknown source'
  const map: Record<string, string> = { kb: 'Kb', text: 'Text', table: 'Table', web: 'Web', NERD: 'NERD', info: 'Info' }
  return map[source] || 'Unknown source'
}
// —— 折叠状态（单卡）——
const answersOpenSingle = ref(false)
const evidencesOpenSingle = ref(false)
function toggleAnswersSingle() { answersOpenSingle.value = !answersOpenSingle.value }
function toggleEvidencesSingle() { evidencesOpenSingle.value = !evidencesOpenSingle.value }

// —— 折叠状态（双卡 child1）——
const answersOpenC1 = ref(false)
const evidencesOpenC1 = ref(false)
function toggleAnswersC1() { answersOpenC1.value = !answersOpenC1.value }
function toggleEvidencesC1() { evidencesOpenC1.value = !evidencesOpenC1.value }

// —— 折叠状态（双卡 child2）——
const answersOpenC2 = ref(false)
const evidencesOpenC2 = ref(false)
function toggleAnswersC2() { answersOpenC2.value = !answersOpenC2.value }
function toggleEvidencesC2() { evidencesOpenC2.value = !evidencesOpenC2.value }
const TOPK = 5

function stripHtmlToText(html: string): string {
  if (typeof window !== 'undefined') {
    const el = document.createElement('div')
    el.innerHTML = html || ''
    return (el.textContent || el.innerText || '').replace(/\s+/g, ' ').trim()
  }
  return (html || '').replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim()
}

function topEvidenceTexts(
  evs: Evidence[] | undefined,
  allowed: string[],
  k = TOPK
): string[] {
  if (!Array.isArray(evs) || !evs.length) return []
  return evs
    .filter(e => !allowed || allowed.includes(e.source))
    .slice() // 拷贝
    .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
    .slice(0, k)
    .map(e => stripHtmlToText(e.text))
    .filter(Boolean)
}

// —— 单卡：证据前五 —— 
const topEvidenceTextsSingle = computed(() =>
  topEvidenceTexts(props.evidences, props.selectedTypes, TOPK)
)

// —— 双卡 child1 / child2：证据前五 ——
const topEvidenceTextsC1 = computed(() =>
  topEvidenceTexts(props.dualItems?.[0]?.evidences as any, props.selectedTypes, TOPK)
)
const topEvidenceTextsC2 = computed(() =>
  topEvidenceTexts(props.dualItems?.[1]?.evidences as any, props.selectedTypes, TOPK)
)
type HighlightSpec =
  | { kind: 'candidate_text'; texts: string[] }
  | { kind: 'answers'; ids: string[] }

// —— 单卡：前两页按证据文本高亮；最后一页按答案 id 高亮
const highlightSingle = computed<HighlightSpec | undefined>(() => {
  if (pageSingle.value < totalPagesSingle.value) {
    return { kind: 'candidate_text', texts: topEvidenceTextsSingle.value }
  }
  if (pageSingle.value === totalPagesSingle.value) {
    const ids = (props.answers || []).slice(0, 5).map(a => a.id).filter(Boolean)
    return ids.length ? { kind: 'answers', ids } : undefined
  }
  return undefined
})

// —— 子卡1
const highlightC1 = computed<HighlightSpec | undefined>(() => {
  if (page1.value < totalPages1.value) {
    return { kind: 'candidate_text', texts: topEvidenceTextsC1.value }
  }
  if (page1.value === totalPages1.value) {
    const ids = (props.dualItems?.[0]?.rankedAnswers || []).slice(0, 5).map(a => a.id).filter(Boolean)
    return ids.length ? { kind: 'answers', ids } : undefined
  }
  return undefined
})

// —— 子卡2
const highlightC2 = computed<HighlightSpec | undefined>(() => {
  if (page2.value < totalPages2.value) {
    return { kind: 'candidate_text', texts: topEvidenceTextsC2.value }
  }
  if (page2.value === totalPages2.value) {
    const ids = (props.dualItems?.[1]?.rankedAnswers || []).slice(0, 5).map(a => a.id).filter(Boolean)
    return ids.length ? { kind: 'answers', ids } : undefined
  }
  return undefined
})
</script>

<style scoped>
.section.collapsed {
  padding-bottom: 5px !important;
}
.AR-SE {
  background-color: #b4d7b4 !important
}
.QU-ER-HA {
  background-color: #bbc8da !important
}
.temporal-value-item {
  background-color: #f8f9fa;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  margin-bottom: 0.5rem;
  border-left: 3px solid #3498db;
}
.temporal-value-item:last-child { 
  margin-bottom: 0; 
}

.section { 
  padding: 1rem; 
  background: #e9f0fc; 
  border-radius: 8px; 
  margin-bottom: 1rem; 
  padding: 20px; 
}
.section-title { 
  color: #2c3e50; 
  margin-bottom: 1rem; 
  font-weight: 600; 
  font-size: 1.15rem; 
}

.clickable-text {
  cursor: pointer; 
  padding: 1rem; 
  border-radius: 4px; 
  margin-bottom: 0;
  font-weight: bold; 
  font-size: 20px;
  background: linear-gradient(90deg, #b0d48c 0%, #f8f9fa 100%);
  background-size: 200% 100%; 
  background-position: 0% 0%;
  transition: background-position 0.5s ease-in-out;
}
.clickable-text:hover { 
  background-position: 100% 0%; 
}

.intermediate-details {
  background: #e4eff9;
  border-radius: 16px; 
  margin-top: 1.5rem; 
  position: relative; 
  padding: 1rem;
  box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
  border: 2px dashed #0080FF;
}
.intermediate-details-content { 
  overflow: hidden; 
  transition: all 0.6s cubic-bezier(0.4,0,0.2,1); 
}
.header-toggle { 
  cursor: pointer; 
  user-select: none; 
}
.intermediate-card {
  background: rgba(255,255,255,0.9);
  border: 1px solid rgba(226,232,240,0.8);
  backdrop-filter: blur(8px);
}

.intermediate-graph-section { 
  text-align: center; 
  border-top: 1px solid #e9ecef; 
  padding-top: 1rem; 
}
.btn-group .btn { 
  min-width: 100px; 
  max-height: 40px; 
}

.slide-fade-enter-active, .slide-fade-leave-active { 
  transition: all 0.4s ease; 
}
.slide-fade-enter-from, .slide-fade-leave-to { 
  opacity: 0; 
  max-height: 0; 
  transform: translateY(-10px); 
}
.slide-fade-enter-to, .slide-fade-leave-from { 
  opacity: 1; 
  max-height: 2000px; 
  transform: translateY(0); 
}

.evidence-text { 
  white-space: pre-wrap; 
  font-size: 0.9rem; 
  line-height: 1.5; 
}
.evidence-link { 
  color: #fff; 
  text-decoration: none; 
}
.evidence-link:hover { 
  color: #e0e0e0; 
  text-decoration: none; 
}

/* 饼图布局 */
.intermediate-charts {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: nowrap;
  margin-top: 1rem;
}
.chart-wrapper {
  flex: 1 1 calc(33.333% - 1rem);
  min-width: 200px;
  background: #fff;
  border: 1px solid #dee2e6;
  border-radius: .5rem;
  padding: .75rem;
  text-align: center;
}
.pie-container { 
  width: 100%; 
  height: 150px; 
}
@media (max-width: 768px) {
  .intermediate-charts { flex-wrap: wrap; }
  .chart-wrapper { flex: 1 1 100%; }
}
.chart-arrow { 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  padding: 0 0.5rem; 
}
.chart-arrow i { 
  font-size: 1.5rem; 
  color: #6c757d; 
}

/* 子折叠容器：上下排列 */
.subcard-wrap {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  margin-bottom: 12px;
  overflow: hidden;
}
.subcard-header {
  background: linear-gradient(90deg, #b0d48c1f, #ecf7ee);
  padding: 12px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}
.subcard-body {
  padding: 10px;
  background: #eaf3fc;
}
.no-hover {
  transition: none !important;
  box-shadow: none !important;
}
.no-hover:hover {
  box-shadow: none !important;
  transform: none !important;
}
</style>
<style>
.AR-SE-card {
  background-color: #f3faf5 !important;
}
.detail {
  border-left: 4px solid #6C8CA1;
}
.h3-with-dash { display: block; }
.h3-with-dash > span {
  display: inline-block;
  border-bottom: 2px dashed rgba(50,50,50,.35);
  padding-bottom: 4px;
  line-height: 1.2;
}
.h3-with-dash::after {
  content: "";
  position: absolute;
  left: 0; right: 0; bottom: 0;
  border-bottom: 2px dashed rgba(50, 50, 50, .35);
}
.popover.popover-wide { 
  max-width: 820px !important;
}
.tp-emph {
  color: #283c64;
  font-weight: 800;
}
</style>