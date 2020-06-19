<template>
<mu-container>
  <mu-row justify-content="center">
  <h2>表达式求解 Demo</h2>
  </mu-row>

  <mu-row gutter align-items="start" justify-content="center">
    <mu-text-field v-model="input" placeholder="请输入 TeX 表达式">
    </mu-text-field>

    <mu-button icon @click="clear">
      <mu-icon value="clear"></mu-icon>
    </mu-button>

    <mu-button icon @click="add">
      <mu-icon value="control_point"></mu-icon>
    </mu-button>

    <mu-button @click="calc" color="primary" style="margin-left: 40px">
       求解
    </mu-button>
  </mu-row>

  <h3 v-if="preview.length > 0">预览</h3>
  <div id="preview" class="latex" v-html="preview" v-if="preview.length > 0"></div>

  <mu-row v-for="(step, i) in steps" :key="step.latex" class="step" align-items="center">

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

    <mu-col span="2" class="mu-transition-row" fill>
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
      input: '',
      preview: '',
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

  computed: {
  },

  watch: {
    input: function(newval, oldval) {
      if (newval.trim().length == 0)
        this.preview = ''
      else
        this.preview = this.render(newval, true)
    }
  },

  methods: {
    clear() {
      this.input = ''
    },

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

    render(latex, display=false) {
      return MathJax.tex2svg(latex, {
        display
      }).outerHTML
    },

    calc() {
      let query = this.input 
    }
  }
}
</script>

<style>
div.mu-input {
  width: 600px;
}

#preview {
  margin-bottom: 60px;
}

.step {
  min-height: 30px;
  padding: 10px 0;
}

.latex {
  font-size: 2.0em;
}
</style>
