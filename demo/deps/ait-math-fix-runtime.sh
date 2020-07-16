find -name '*.js' | xargs sed -i -e "s-require('.*formula.png')-'AAA'-g"
