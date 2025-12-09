<!-- SearchComponent.vue -->
<template>
  <div class="search-component">
    <h3 class="mb-3">Question Search</h3>
    <div class="question-analysis-tab">
      <div class="input-area">
        <input 
          type="text" 
          placeholder="Please enter your question here" 
          v-model="questionInput" 
          class="form-control"
          @keyup.enter="handleQuestionSearch"
        >
        <button 
          class="btn btn-primary ms-2" 
          @click="handleQuestionSearch" 
          :disabled="isSearching"
        >
          <span v-if="!isSearching">
            <i class="bi bi-chat-dots me-1"></i>Answer
          </span>
          <span v-else>
            <span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
            Searching...
          </span>
        </button>
      </div>
      
      <!-- Analysis status -->
      <div class="analysis-status mt-2" v-if="analysisStatus">
        <div :class="['alert', analysisStatus.type === 'error' ? 'alert-danger' : 'alert-info', 'mb-0', 'py-2']">
          <i :class="['bi', analysisStatus.type === 'error' ? 'bi-exclamation-triangle' : 'bi-info-circle', 'me-2']"></i>
          {{ analysisStatus.message }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface StatusMessage {
  type: 'error' | 'info';
  message: string;
}

// Define component events
const emit = defineEmits(['question-analyzed']);

// Status variables
const questionInput = ref('');
const analysisStatus = ref<StatusMessage | null>(null);
const isSearching = ref(false);

// Handle question search
const handleQuestionSearch = async () => {
  if (!questionInput.value) {
    analysisStatus.value = { type: 'error', message: 'Please enter a question' };
    return;
  }
  
  try {
    isSearching.value = true;
    analysisStatus.value = { type: 'info', message: 'Searching question...' };
    
    // Call backend API
    const response = await fetch(`/api/process-question?question=${encodeURIComponent(questionInput.value)}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        analysisStatus.value = { type: 'info', message: 'No matching question found' };
        return;
      }
      const errorData = await response.json();
      throw new Error(errorData.message || errorData.error || 'Search request failed');
    }
    
    const result = await response.json();
    
    // Search successful
    if (result.success) {
      analysisStatus.value = { 
        type: 'info', 
        message: `Search successful! Match score: ${(result.matchScore * 100).toFixed(2)}%` 
      };
      
      // Trigger parent component event
      emit('question-analyzed', result);
    } else {
      analysisStatus.value = { 
        type: 'error', 
        message: result.message || 'No matching question found'
      };
    }
  } catch (error: any) {
    console.error('Question search error:', error);
    analysisStatus.value = { type: 'error', message: error.message || 'Error searching question' };
  } finally {
    isSearching.value = false;
  }
};
</script>

<style scoped>
.search-component {
  margin-bottom: 2rem;
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.input-area {
  display: flex;
  align-items: center;
}

.search-results {
  max-height: 300px;
  overflow-y: auto;
}
</style> 