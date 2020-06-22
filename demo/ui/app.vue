<template>
<mu-container>
  <mu-row justify-content="center">
    <h2>表达式求解 Demo</h2>
  </mu-row>

  <mu-row gutter align-items="start" justify-content="center">
    <div>
      <mu-text-field v-model="input" placeholder="请输入 TeX 表达式">
      </mu-text-field>

      <mu-tooltip content="清除输入">
        <mu-button icon @click="clear">
          <mu-icon value="clear"></mu-icon>
        </mu-button>
      </mu-tooltip>

      <mu-row v-for="(eq, i) in equations" :key="i + eq" class="equations" justify-content="center">
        <mu-text-field v-model="equations[i]" disabled>
        </mu-text-field>

        <mu-tooltip content="删除方程">
          <mu-button icon @click="dele_eq(i)">
            <mu-icon value="delete"></mu-icon>
          </mu-button>
        </mu-tooltip>
      </mu-row>
    </div>

    <mu-tooltip content="添加表达式（方程组）">
      <mu-button icon @click="add_eq">
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

  <mu-alert color="error" v-if="error_msg.length > 0">
    <mu-icon left value="warning"></mu-icon> {{error_msg}}
  </mu-alert>

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
      equations: [],
      input: '',
      preview: '',
      error_msg: '',
      steps: [],
      last_random_idx: -1
    }
  },

  computed: {
  },

  watch: {
    input: function(newval, oldval) {
      this.refresh_preview()
      this.steps = ''
      this.error_msg = ''
    }
  },

  methods: {
    clear() {
      this.input = ''
      this.equations = []
    },

    all_equations() {
      let input = this.input
      let equations = this.equations
      if (input.trim().length > 0)
        equations = [input, ...equations]
      return equations
    },

    refresh_preview() {
      let equations = this.all_equations()
      let preview_tex = equations[0] || ''
      if (equations.length >= 2) {
        preview_tex =
          '\\left\\{ \\begin{array}{rl}' +
          equations.join('\\\\') +
          '\\end{array} \\right.'
      }

      if (preview_tex.trim().length == 0)
        this.preview = ''
      else
        this.preview = this.render(preview_tex, true)
    },

    add_eq() {
      if (this.input.includes('=')) {
        this.equations = [this.input, ...this.equations]
        this.input = ''
      } else {
        this.error_msg = '添加的必须是等式'
      }
    },

    dele_eq(idx) {
      this.equations.splice(idx, 1)
      this.refresh_preview()
    },

    steps_animation(boolean) {
      for (var i = 0; i < this.steps.length; i++)
        this.$set(this.steps[i], 'show', boolean)
    },

    append_step(step) {
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
        this.steps_animation(true)
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

    async show_steps(steps) {
      let vm = this
      for (var i = 0; i < steps.length; i ++) {
        let step = steps[i]
        vm.append_step(step)
        await new Promise(resolve => {
          setTimeout(() => {
            resolve()
          }, 500)
        })
      }
    },

    calc() {
      let query = this.input
      let equations = this.equations
      this.error_msg = ''
      if (query.trim().length == 0 && equations.length == 0) {
        this.error_msg = '空表达式'
        return
      }

      console.log('[query]', query)
      let vm = this
      $.ajax({
        url: '/api/query',
        type: "POST",
        data: JSON.stringify({
          query: vm.all_equations()
        }),
        contentType:"application/json; charset=utf-8",
        dataType:"json",
        success: function(res){
          if (res.ret == 'successful') {
            vm.steps = []
            vm.show_steps(res.steps)
          } else {
            console.error(res.error)
            vm.error_msg = res.error
          }
        },
        error: function(err) {
          console.error(err)
          vm.error_msg = '服务器好像出了问题……'
        }
      })
    },

    random() {
      let list = random_list.list
      //let idx = Math.floor(Math.random() * list.length)
      let idx = (this.last_random_idx + 1) % list.length
      this.last_random_idx = idx
      if (typeof list[idx] == 'object') {
        this.equations = list[idx]
        this.input = ''
      } else {
        this.equations = []
        this.input = list[idx]
      }
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
