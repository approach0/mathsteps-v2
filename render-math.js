const mathjax = require('mathjax')
const fs = require('fs')

var args = process.argv.slice(2)
var output_file = args[0]
var input_tex = args[1]

if (args.length != 2) {
    console.log('bad arg.')
    process.exit(1)
}

mathjax.init({
    loader: {
        load: ['input/tex', 'output/svg']
    }
}).then(async jax => {
    let svg = await jax.tex2svgPromise(input_tex, { display: true });
    svg = jax.startup.adaptor.innerHTML(svg)

    html = '<html><style></style><body><div id="frame">' + svg + '<addons/></div></body></html>'
    fs.writeFileSync(output_file, html)

}).catch(err => {
    console.error(err)
})
