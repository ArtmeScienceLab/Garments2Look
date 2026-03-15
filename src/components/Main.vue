<script>
import Title from './sections/Title.vue'
import ImageMatrix from './sections/ImageMatrix.vue'
import Abstract from './sections/Abstract.vue'
import Markdown from './sections/Markdown.vue'
import BibTeX from './sections/BibTeX.vue'

export default {
  components: {
    Title,
    ImageMatrix,
    Abstract,
    Markdown,
    BibTeX,
  },
  data() {
    return {
      // 第 1 页（最多 16 个：两行 × 每行最多 8 个）
      imageOrderPage1: [
        "P00787009_b1",
        "P01004083_b1",
        "P01018992_b1",
        "P01053755_b1",
        "P01056255_b1",
        "P01099875_d2",
        "P01112310_b1",
        "P01127323_b1",
        "P00431909-P00958883-P00999111-P01006546-P01045238-P01086791-P01088627",
        "P00528279-P01056783-P01067920-P01072580-P01086754",
        "P00632317-P00947443-P00951042-P01004526-P01012440-P01115433",
        "P00697636-P00806175-P00956525-P01078473-P01081516",
        "P00741922-P00779847-P01005949-P01025038-P01052972-P01099646-P01114937",
        "P00749634-P01023448-P01039809-P01056408-P01058346-P01075105-P01100395",
        "P00762543-P00779803-P01054091-P01084304-P01092943-P01115291",
        "P00871983-P00908493-P00993397-P01063506-P01101088"
      ],
      // 第 2 页（最多 16 个）
      imageOrderPage2: [
        "P00686444-P00891202-P01055167-P01076636-P01124047",
        "P01050689-P01050696-P01079464-P01103160-P01126809",
        "P00716431-P00824148-P00844694-P01024135-P01076632-P01141112",
        "P00846007-P00909296-P01071680-P01087782-P01117573",
        "P00917480-P01029305-P01092562-P01093017-P01093221",
        "P00951606-P01029121-P01041987-P01073080-P01073331-P01076616-P01123803",
        "P00966252-P01019368-P01072233-P01081078-P01095233",
        "P00987729-P01055351-P01092514-P01093208-P01128003",
        "P00761840-P01055343-P01057717-P01074004-P01128005",
        "P00748211-P01071665-P01093042",
        "P00587268-P01003420-P01076974-P01093024-P01126937",
        "P00650083-P00874266-P01010871-P01111675",
        "P00769560-P00968353-P00973034-P01055218-P01057723",
        "P00861620-P01057710-P01058114-P01081092",
        "P00940662-P01010865-P01055356-P01092606-P01093135",
        "P01050319-P01055352-P01075052-P01077226-P01126948"
      ],
      // 第 3 页（最多 16 个）
      imageOrderPage3: [
        // 在这里填写第三页的 outfit id
      ],
      // 第 4 页（最多 16 个）
      imageOrderPage4: [
        // 在这里填写第四页的 outfit id
      ],
    }
  },
  computed: {
    // 按页传：每一页只显示该页自己的图像列表，不混用
    imageOrderPages() {
      return [
        this.imageOrderPage1,
        this.imageOrderPage2,
        // this.imageOrderPage3,
        // this.imageOrderPage4,
      ].filter((page) => Array.isArray(page) && page.length > 0)
    },
  },
}
</script>

<template>
  <Title/>
  <ImageMatrix :order-pages="imageOrderPages" />
  <Abstract/>
  <Markdown/>
  <BibTeX/>
</template>