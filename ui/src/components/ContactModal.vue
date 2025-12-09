<template>
  <BModal
    v-model="modelValue"
    title="Contact"
    size="lg"
    centered
    @hide="handleClose"
  >
    <div class="contact-content">
      <p>For feedback and clarifications, please contact:</p>
      <ul>
        <li><a href="mailto:zjia@swjtu.edu.cn" target="_blank">Zhen Jia</a></li>
        <li><a href="https://people.mpi-inf.mpg.de/~pchristm/" target="_blank">Philipp Christmann</a></li>
        <li><a href="https://people.mpi-inf.mpg.de/~weikum/" target="_blank">Gerhard Weikum</a></li>
      </ul>

      <p>To know more about our group, please visit <a
          href="https://www.mpi-inf.mpg.de/departments/databases-and-information-systems/research/question-answering/"
          target="_blank">https://www.mpi-inf.mpg.de/departments/databases-and-information-systems/research/question-answering/</a>.
      </p>
    </div>

    <template #footer>
      <BButton variant="secondary" @click="handleClose">Close</BButton>
    </template>
  </BModal>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { BButton } from 'bootstrap-vue-3';

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
.contact-content {
  font-size: 1rem;
  line-height: 1.6;
}

.contact-section {
  margin-bottom: 2rem;
}

.contact-section:last-child {
  margin-bottom: 0;
}

h4 {
  color: #2c5282;
  margin-bottom: 1rem;
  font-size: 1.25rem;
}

ul {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

li {
  margin-bottom: 0.5rem;
}

a {
  color: #3498db;
  text-decoration: none;
  transition: color 0.3s ease;
}

a:hover {
  color: #2980b9;
  text-decoration: underline;
}

p {
  color: #4a5568;
  margin-bottom: 1rem;
}

@media (max-width: 768px) {
  .contact-info {
    padding: 1rem;
  }

  .info-item {
    flex-direction: column;
    align-items: flex-start;
    text-align: left;
  }

  .info-item i {
    margin-bottom: 0.5rem;
  }
}
</style> 