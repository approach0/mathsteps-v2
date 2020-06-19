<template>
<mu-container>
  <h1>表达式求解 Demo</h1>
  <mu-button @click="all_show(false)">hide</mu-button>
  <mu-button @click="add">add</mu-button>
  <h1></h1>
  <mu-row gutter v-for="(step, i) in steps" class="step" align-items="center">

    <mu-col span="1" class="mu-transition-row">
      <mu-slide-left-transition>
        <div class="mu-transition-box" v-show="step.show">
          {{ i == 0 ? `原式` : `第 ${i} 步`}}
        </div>
      </mu-slide-left-transition>
    </mu-col>

    <mu-col span="7" class="mu-transition-row">
      <mu-slide-left-transition>
        <div class="mu-transition-box latex" v-show="step.show" v-html="step.html">
        </div>
      </mu-slide-left-transition>
    </mu-col>

    <mu-col span="2" class="mu-transition-row">
      <mu-slide-left-transition>
        <div class="mu-transition-box" v-show="step.show">
          {{step.info}}
        </div>
      </mu-slide-left-transition>
    </mu-col>

    <mu-divider v-show="step.show"></mu-divider>

  </mu-row>
</mu-container>
</template>

<script>
import $ from 'jquery'

export default {
  data () {
    return {
      show: true,
      'steps': [
        {
          show: true,
          latex: '$\\frac{a}{b}$',
          info: '去括号',
          html: '<b>i</b>j'
        }
      ]
    }
  },
  methods: {
    all_show(boolean) {
      for (var i = 0; i < this.steps.length; i++)
        this.$set(this.steps[i], 'show', boolean)
    },

    add() {
      let latex = '\\frac{a}{b}'
      let html = this.render(latex)
      this.steps.push(
        {
          show: false,
          latex: latex,
          info: '去括号',
          html: html
        }
      )

      this.$nextTick(() => {
        this.all_show(true)
        console.log(this.steps)
      })
    },

    render(latex) {
      return MathJax.tex2svg(latex, {display: false}).outerHTML
    }
  }
}
</script>

<style>
.step {
  min-height: 30px;
  padding: 10px 0;
}

.latex {
  font-size: 2em;
}
</style>
