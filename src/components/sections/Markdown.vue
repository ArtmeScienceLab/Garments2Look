<script setup>
import ComparisonSection from '../mds/md-comparison.mdx';
import ConstructionSection from '../mds/md-construction.mdx';
import BasicInfoSection from '../mds/md-basic-info.mdx';
import ResultsSection from '../mds/md-results.mdx';
</script>

<template>
  <div>
    <el-divider />

    <el-row justify="center">
      <el-col :xs="24" :sm="20" :md="16" :lg="12" :xl="12">
        <ComparisonSection />
        <el-divider />
        <ConstructionSection />
        <el-divider />
        <BasicInfoSection />
        <el-divider />
        <ResultsSection />
      </el-col>
    </el-row>

  </div>
</template>