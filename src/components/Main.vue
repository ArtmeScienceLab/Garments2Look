<script>
import Title from './sections/Title.vue'
import Abstract from './sections/Abstract.vue'
import Markdown from './sections/Markdown.vue'
import BibTeX from './sections/BibTeX.vue'

export default {
  components: {
    Title,
    Abstract,
    Markdown,
    BibTeX,
  }
}
</script>

<template>
  <Title/>
  <Abstract/>
  <Markdown/>
  <BibTeX/>
</template>