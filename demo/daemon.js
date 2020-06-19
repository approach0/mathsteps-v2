const express = require('express')
const bodyParser = require('body-parser')

var app = express()
app.use(bodyParser.json())

process.on('SIGINT', async function() {
  console.log('')
  console.log('Bye bye.')
  process.exit()
})

const port = 3889
app.listen(port)
console.log(`Listen on ${port}`)

app.get('/query/:qry', async function (req, res) {
  const qry = req.params.qry
  console.log('[query]', qry)

  try {

    res.json({
      "qry": qry
    })

  } catch (err) {

    res.json({
      "qry": qry,
      "res": err.toString()
    })
  }
})
