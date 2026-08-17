<script setup>
const emit = defineEmits(['close'])
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-ink/35 p-6" @click.self="emit('close')">
    <slot />
  </div>
</template>
