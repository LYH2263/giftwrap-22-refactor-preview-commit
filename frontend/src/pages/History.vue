<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'

const items = ref([])
const err = ref('')

onMounted(async () => {
  try {
    items.value = (await getJSON('/api/runs')).items
  } catch (e) {
    err.value = String(e.message || e)
  }
})
</script>

<template>
  <div class="page">
    <h1>用纸档</h1>
    <p class="lede">算纸页「写入用纸档」后的落库结果，按次保留盒名与面积。</p>
    <p v-if="err" class="bad">{{ err }}</p>
    <p v-else-if="!items.length" class="empty">还没有写入过。先去算纸试一单。</p>
    <ul v-else class="item-list">
      <li v-for="r in items" :key="r.id">
        <span>{{ r.box_name }}</span>
        <span class="meta">{{ r.paper_m2 ?? r.result?.paper_m2 ?? '—' }} m² · 丝带 {{ r.ribbon_m ?? r.result?.ribbon?.ribbon_m ?? '—' }} m</span>
      </li>
    </ul>
  </div>
</template>
