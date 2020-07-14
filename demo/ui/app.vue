<template>
<mu-container>
  <mu-row justify-content="center">
    <h2>表达式求解 Demo</h2>
  </mu-row>

  <mu-row gutter align-items="start" justify-content="center" wrap="nowrap">
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

    <mu-button @click="mathboard" color="primary" style="margin-left: 40px">
      讲题板演示
    </mu-button>
  </mu-row>

  <mu-row justify-content="end">
    <mu-checkbox v-model="debug" label="Debug"></mu-checkbox>
  </mu-row>

  <h3 v-if="preview.length > 0">预览</h3>
  <div id="preview" class="latex" v-html="preview" v-if="preview.length > 0"></div>

  <mu-alert color="error" v-if="error_msg.length > 0">
    <mu-icon left value="warning"></mu-icon> {{error_msg}}
  </mu-alert>

  <mu-alert color="success" v-if="succ_msg.length > 0">
    <mu-icon left value="check_circle"></mu-icon> {{succ_msg}}
  </mu-alert>

  <mu-row justify-content="center">
    <iframe v-if="iframe_url !== null" v-bind:src="iframe_url" width="544" height="841"></iframe>
  </mu-row>

  <div v-for="(step, i) in steps" :key="i + step.latex">

    <mu-row class="step" align-items="center">
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
    </mu-row>

    <div v-if="debug">
      <pre style="display:inline-block; font-weight: 800">{{step.animate_tex}}</pre>
    </div>
    <div v-if="debug">
      <mu-button color="secondary" @click="json_show(i, step.animate_json)"> 查看 JSON </mu-button>
      <mu-button color="secondary" @click="json2mml(i, false)"> 查看 MML </mu-button>
      <mu-button color="secondary" @click="json2mml(i, true)"> 查看 oneline MML </mu-button>
      <mu-button color="secondary" @click="upload_pg(i)"> 上传 AIT-math PG </mu-button>
      <mu-button color="secondary" @click="json_show(i, null)"> 收起 </mu-button>
      <pre v-if="step.debug_content">{{step.debug_content}}</pre>
      <div v-if="Array.isArray(step.debug_content)">
        <a target="_blank" href="http://192.168.3.54:8080/playground.html">playground</a>:
        动画效果预览
      </div>
      <div v-if="Array.isArray(step.debug_content)">
        <a target="_blank" href="https://cpm-ait.dev.dm-ai.cn/board">对比 AIT-math 动画</a>:
        ait-math-pg-tester ROOM_ID MML
      </div>
    </div>

    <mu-divider v-show="step.show"></mu-divider>

  </div>
</mu-container>
</template>

<script>
import $ from 'jquery'
const random_list = require('./random-list')

export default {
  data () {
    return {
      debug: false,
      equations: [],
      input: '',
      preview: '',
      error_msg: '',
      succ_msg: '',
      steps: [],
      iframe_url: null,
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

  mounted: function () {
    const initQry = this.gup('q')
    const vm = this
    if (initQry !== null) {
      setTimeout(function() {
        vm.input = decodeURIComponent(initQry)
      }, 500)
    }
  },

  methods: {
    set_url_params(k, v) {
      const enc_v = decodeURIComponent(v)
      history.pushState({}, null, `/demo/?${k}=${enc_v}`)
    },

    gup(name, url) {
        if (!url) url = location.href;
        name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
        var regexS = "[\\?&]"+name+"=([^&#]*)";
        var regex = new RegExp( regexS );
        var results = regex.exec( url );
        return results == null ? null : results[1];
    },

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
      let animate_json = JSON.stringify(JSON.parse(step.animate_json), null, 4)
      this.steps.push(
        {
          show: false,
          latex: tex,
          animate_tex: step.animate_tex,
          animate_json: animate_json,
          info: step.axiom,
          html: html,
          debug_content: null
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
      if (MathJax === undefined) {
        return latex
      } else {
        return MathJax.tex2svg(latex, {
          display
        }).outerHTML
      }
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
      this.succ_msg = ''
      this.iframe_url = null
      this.set_url_params('q', query)

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
          console.log('[ajax]', res)
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

    mathboard() {
      let query = this.input
      let equations = this.equations

      this.error_msg = '请等待讲题板初始化和上传 PG ...'
      this.succ_msg = ''
      this.set_url_params('q', query)

      if (query.trim().length == 0 && equations.length == 0) {
        this.error_msg = '空表达式'
        return
      }

      const room = '' + new Date() / 1
      const url = `http://ait-tutor-board-ait.dev.dm-ai.cn/#/tutor-board?fromCpm=1&roomId=${room}`
      this.iframe_url = null
      this.$nextTick(() => {
        this.iframe_url = url
      })

      console.log('[mathboard query]', query)
      let vm = this
      $.ajax({
        url: '/api/mathboard',
        type: "POST",
        data: JSON.stringify({
          query: vm.all_equations(),
          room: room
        }),
        contentType:"application/json; charset=utf-8",
        dataType:"json",
        success: function(res){
          console.log('[ajax]', res)
          if (res.ret == 'successful') {
            const room = res.room
            const output = res.output
            vm.error_msg = ''
            vm.succ_msg = `room ${room} is ready!`
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
      let idx = Math.floor(Math.random() * list.length)
      //let idx = (this.last_random_idx + 1) % list.length
      this.last_random_idx = idx
      if (typeof list[idx] == 'object') {
        this.equations = list[idx]
        this.input = ''
      } else {
        this.equations = []
        this.input = list[idx]
      }
    },


    json_encode(input) {
      return input.replace(/\\n/g, "\\n")
                  .replace(/\\'/g, "\\'")
                  .replace(/\\"/g, '\\"')
                  .replace(/\\&/g, "\\&")
                  .replace(/\\r/g, "\\r")
                  .replace(/\\t/g, "\\t")
                  .replace(/\\b/g, "\\b")
                  .replace(/\\f/g, "\\f")
    },

    json2mml(i, oneline) {
      let json = this.steps[i].animate_json
      json = json.replace(/\n/g, '');
      json = json.replace(/ /g, '');
      console.log('[json]', json)
      let vm = this
      $.ajax({
        url: '/api/json2mml',
        type: "POST",
        data: JSON.stringify({ json: json }),
        contentType:"application/json; charset=utf-8",
        dataType:"json",
        success: function(res){
          console.log('[ajax]', res)
          if (res.ret == 'successful') {
            if (oneline)
                vm.$set(vm.steps[i], 'debug_content', [vm.json_encode(res.mml)])
            else
                vm.$set(vm.steps[i], 'debug_content', res.pretty_mml)

          } else {
            console.error(res.error)
          }
        },
        error: function(err) {
          console.error(err)
          vm.error_msg = '服务器好像出了问题……'
        }
      })
    },

    upload_pg(i) {
      const content = this.steps[i]['debug_content']
      if (!Array.isArray(content)) {
        this.succ_msg = ''
        this.error_msg = '请选择 oneline MML 再上传'
        return
      }

      console.log('[PG upload]', content[0])

      let vm = this
      $.ajax({
        url: '/api/aitmath-pg-upload',
        type: "POST",
        data: JSON.stringify({ mathml: content[0] }),
        contentType: "application/json; charset=utf-8",
        dataType:"json",
        success: function(res){
          console.log('[ajax]', res)
          if (res.ret == 'successful') {
            vm.succ_msg = res.output
            vm.error_msg = ''
          } else {
            console.error(res.error)
          }
        },
        error: function(err) {
          console.error(err)
          vm.error_msg = '服务器好像出了问题……'
        }
      })
    },

    json_show(i, content) {
        console.log('[debug show]', content)
        this.$set(this.steps[i], 'debug_content', content)
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
