const express = require('express')
const bodyParser = require('body-parser')
const cors = require('cors')
const format = require('xml-formatter')
const {spawn} = require('child_process')
const he = require('he')

var app = express()
app.use(bodyParser.json())
app.use(cors())

const AIT_math_dir = './deps/math-board-tester/node_modules/ait-math'
const AIT_math_tester_dir = './deps/math-board-tester'
const AIT_math_tester_default_room = 'ga6840'

process.on('SIGINT', async function() {
  console.log('')
  console.log('Bye bye.')
  process.exit()
})

const port = 3889
app.listen(port)
console.log(`Listen on ${port}`)

function run(cmd, script, args) {
  return new Promise((resolve, reject) => {
    cmd_args = [script, ...args]
    console.log('[run]', cmd, cmd_args)
    let returnStr = ''
    const process = spawn(cmd, cmd_args)
    process.stdout.on('data', (data) => {
      returnStr += data.toString()
    })

    process.stdout.on('end', () => {
      resolve(returnStr)
    })

    process.stderr.on('data', (data) => {
      reject(data)
    })
  })
}

function html_entities_codes(input) {
  return input.replace(/&([^#]+);/g, function(match, name) {
    return he.encode(he.decode(match))
  })
}

app.post('/query', async function (req, res) {
  let qry = req.body.query
  console.log('[query]', qry)

  try {
    if (qry === undefined)
      throw 'internal undefined query'

    let steps = []
    if (qry.length == 0) {
      throw 'input query length is zero'

    //} else if (qry.length == 1 && !qry[0].includes('=')) {
    } else if (qry.length == 1) {
      steps = await run('python3', '../dfs.py', qry)
    } else {
      steps = await run('python3', '../../mathsteps-v1/mathstep.py', qry)
    }

    //console.log('[steps]', steps)
    steps = JSON.parse(steps)
    res.json({
      qry: qry,
      ret: 'successful',
      steps: steps
    })

  } catch (err) {
    console.error(err.toString())

    res.json({
      qry: qry,
      ret: 'failed',
      error: err.toString()
    })
  }

}).post('/json2mml', async function (req, res) {
  let json = req.body.json
  console.log('[json]', json)

  try {
    if (json === undefined)
      throw 'internal undefined query'

    let mml = await run('node', `${AIT_math_dir}/src/json2mathml.js`, [json])
    mml = html_entities_codes(mml)
    mml = mml.trim()

    res.json({
      json: json,
      ret: 'successful',
      mml: mml,
      pretty_mml: format(mml)
    })

  } catch (err) {
    console.error(err.toString())

    res.json({
      json: json,
      ret: 'failed',
      error: err.toString()
    })
  }

}).post('/aitmath-pg-upload', async function (req, res) {
  let mml = req.body.mathml
  console.log('[mml]', mml)

  try {
    if (mml === undefined)
      throw 'internal undefined query'

    let output = await run('ait-math-pg-tester', AIT_math_tester_default_room, [mml])

    res.json({
      ret: 'successful',
      mml: mml,
      output: output
    })

  } catch (err) {
    console.error(err.toString())

    res.json({
      ret: 'failed',
      error: err.toString()
    })
  }


}).get('/', async function (req, res) {
    res.json({
      'hello': 'world'
    })

}).post('/mathboard', async function (req, res) {
  const qry = req.body.query
  const room = req.body.room
  console.log('[mathboard query]', room, qry)

  try {
    if (qry === undefined)
      throw 'internal undefined query'

    let output = ''
    if (qry.length == 0) {
      throw 'input query length is zero'

    } else {
      output += await run('node', `${AIT_math_tester_dir}/index.js`, [qry[0], room])
    }

    res.json({
      qry: qry,
      room: room,
      ret: 'successful',
      output: output
    })

  } catch (err) {
    console.error(err.toString())

    res.json({
      qry: qry,
      ret: 'failed',
      error: err.toString()
    })
  }
})
