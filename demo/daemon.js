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

function run(qry) {
  return new Promise((resolve, reject) => {
    const process = spawn('python', ['../dfs.py', qry])
    process.stdout.on('data', (data) => {
      const steps = data.toString()
      resolve(steps)
    })

    process.stderr.on('data', (data) => {
      reject(data)
    })
  })
}

app.get('/query/:qry', async function (req, res) {
  const qry = req.params.qry
  console.log('[query]', qry)

  try {
    let steps = await run(qry)
    steps = JSON.parse(steps)
    console.log(steps)

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
})
