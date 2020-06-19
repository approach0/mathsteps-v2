<template>
<mu-container>
  <mu-row justify-content="center">
  <h2>表达式求解 Demo</h2>
  </mu-row>

  <mu-row gutter align-items="start" justify-content="center">
    <mu-text-field v-model="input" placeholder="请输入 TeX 表达式">
    </mu-text-field>

    <mu-tooltip content="清除输入">
      <mu-button icon @click="clear">
        <mu-icon value="clear"></mu-icon>
      </mu-button>
    </mu-tooltip>

    <mu-tooltip content="添加表达式（方程组）">
      <mu-button icon @click="random">
        <mu-icon value="control_point"></mu-icon>
      </mu-button>
    </mu-tooltip>

    <mu-tooltip content="随机表达式">
      <mu-button icon @click="random">
        <mu-icon value="replay"></mu-icon>
      </mu-button>
    </mu-tooltip>

    <mu-button @click="calc" color="primary" style="margin-left: 40px">
      求解
    </mu-button>
  </mu-row>

  <h3 v-if="preview.length > 0">预览</h3>
  <div id="preview" class="latex" v-html="preview" v-if="preview.length > 0"></div>

  <mu-row v-for="(step, i) in steps" :key="i + step.latex" class="step" align-items="center">

    <mu-col span="1" class="mu-transition-row">
      <mu-slide-left-transition>
        <div class="mu-transition-box" v-show="step.show">
          {{ i == 0 ? `原式` : `第 ${i} 步`}}
        </div>
      </mu-slide-left-transition>
    </mu-col>

    <mu-col span="9" class="mu-transition-row">
      <mu-slide-left-transition>
        <div class="mu-transition-box latex" v-show="step.show" v-html="step.html">
        </div>
      </mu-slide-left-transition>
    </mu-col>

    <mu-col span="2" class="mu-transition-row" fill>
      <mu-slide-left-transition>
        <div class="mu-transition-box" v-show="step.show">
          {{ i == 0 ? '' : step.info}}
        </div>
      </mu-slide-left-transition>
    </mu-col>

    <mu-divider v-show="step.show"></mu-divider>

  </mu-row>
</mu-container>
</template>

<script>
import $ from 'jquery'
const random_list = require('./random-list')

export default {
  data () {
    return {
      input: '',
      preview: '',
      steps: []
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

    add(step) {
      let tex = step.tex
      let html = this.render(tex)
      this.steps.push(
        {
          show: false,
          latex: tex,
          info: step.axiom,
          html: html
        }
      )

      this.$nextTick(() => {
        this.all_show(true)
      })

      setTimeout(() => {
        $("html, body").animate({ scrollTop: $(document).height() + 500}, 0)
      }, 100)
    },

    render(latex, display=false) {
      return MathJax.tex2svg(latex, {
        display
      }).outerHTML
    },

    show_steps(steps) {
      let vm = this
      steps.forEach(async (step, i) => {
        setTimeout(() => {
          vm.add(step)
        }, i * 500)
      })
    },

    calc() {
      let query = this.input
      if (query.trim().length == 0)
        alert('空表达式')

      let enc_qry = encodeURIComponent(query)
      let vm = this
      $.ajax({
        url: 'http://localhost:3889/query/' + enc_qry,
        success: function(res){
          if (res.ret == 'successful') {
            vm.steps = []
            vm.show_steps(res.steps)
          } else {
            console.error(res)
          }
        }
      })
    },

    random() {
      let list = random_list.list
      let idx = Math.floor(Math.random() * list.length)
      this.input = list[idx]
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
  width: 95%;
  font-size: 2.0em;
  overflow-x: auto;
  overflow-y: hidden;
}
</style>
