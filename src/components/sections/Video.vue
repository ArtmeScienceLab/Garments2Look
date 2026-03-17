<script setup lang="ts">
</script>

<template>
  <div>
    <el-divider />

    <el-row justify="center">
      <el-col :xs="24" :sm="22" :md="20" :lg="16" :xl="14">
        <h2 style="text-align: center; margin-bottom: 16px;">Video</h2>
        <video
          autoplay
          loop
          muted
          playsinline
          preload="metadata"
          style="width: 100%; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);"
        >
          <source src="/video/g2l.mp4" type="video/mp4" />
          Your browser does not support the video tag.
        </video>
      </el-col>
    </el-row>

  </div>
</template>

<style scoped>
</style>

