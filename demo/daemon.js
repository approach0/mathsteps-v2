const express = require('express')
const bodyParser = require('body-parser')
const cors = require('cors')
const {spawn} = require('child_process');

var app = express()
app.use(bodyParser.json())
app.use(cors())

process.on('SIGINT', async function() {
  console.log('')
  console.log('Bye bye.')
  process.exit()
})

const port = 3889
app.listen(port)
console.log(`Listen on ${port}`)

function run(script, qry) {
  return new Promise((resolve, reject) => {
    const process = spawn('python', [script, qry])
    process.stdout.on('data', (data) => {
      const steps = data.toString()
      resolve(steps)
    })

    process.stderr.on('data', (data) => {
      reject(data)
    })
  })
}

app.post('/query', async function (req, res) {
  let qry = req.body.query
  console.log('[query]', qry)

  try {
    if (qry === undefined)
      throw 'internal undefined query'

    let steps = await run('../dfs.py', qry)
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
}).get('/', async function (req, res) {
    res.json({
      'hello': 'world'
    })
})
