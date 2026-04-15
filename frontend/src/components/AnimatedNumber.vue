<template>
  <span>{{ displayValue }}</span>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';

const props = defineProps({
  value: {
    type: Number,
    required: true,
    default: 0
  },
  duration: {
    type: Number,
    default: 800
  }
});

const displayValue = ref(0);

const animateValue = (start, end, duration) => {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    // easeInOutQuad
    const ease = progress < 0.5 ? 2 * progress * progress : 1 - Math.pow(-2 * progress + 2, 2) / 2;
    displayValue.value = Math.floor(ease * (end - start) + start);
    if (progress < 1) {
      window.requestAnimationFrame(step);
    } else {
      displayValue.value = end;
    }
  };
  window.requestAnimationFrame(step);
};

watch(() => props.value, (newVal, oldVal) => {
  animateValue(oldVal || 0, newVal, props.duration);
});

onMounted(() => {
  animateValue(0, props.value, props.duration);
});
</script>
