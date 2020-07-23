## Daemon
Build docker image and run daemon:
```sh
$ sudo ./Docker-build.sh
$ sudo docker run --network host -it mathsteps-v2 /usr/bin/node daemon.js
```
Daemon is listening on port `3889`.

## Demo UI
```sh
$ cd ./demo
$ npm install
$ npm run dev
$ cd ./deps
$ (cd math-board-tester && npm install)
$ cp ait-math-json2mathml.js ./math-board-tester/node_modules/ait-math/src/json2mathml.js
$ ln -s `pwd`/ait-math-fix-runtime.sh ./math-board-tester/node_modules/ait-math/src/
$ (cd ./math-board-tester/node_modules/ait-math/src/ && ./ait-math-fix-runtime.sh)
```
which generates `./demo/dist` HTML files and starts a HTTP server listening at `19985`.

## Configure Nginx
```sh
$ apt install nginx
```
Edit `/etc/nginx/sites-enabled/default` and insert
```
location /demo/ {
        proxy_pass http://localhost:19985/;
}

location /api/ {
        proxy_pass http://localhost:3889/;
}
```
to your `server` entry and restart `nginx` server.


## Demo Example
Visit `http://localhost/demo/?q=(3+6+7)(a+b)` in browser.
