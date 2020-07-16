const fetch = require("node-fetch");
const mathResultPgConverter = require("./dependencies/math-result-pg-converter");

//==============================================================================================
// DEV CONFIG
// BOARD:  http://ait-tutor-board-ait.dev.dm-ai.cn/#/tutor-board?fromCpm=1&roomId={{ROOMID}}
const AIT_EAOG_RUNNER_URL = "http://ait-eaog-runner-ait.dev.dm-ai.cn";
const MATH_SERVICE_URL = "http://localhost:3889";
//==============================================================================================


//==============================================================================================
// query
const args = process.argv.slice(2)
let QUERY = ["11-18-12+19"]
let ROOM_ID = "ga6840"

if (args.length == 2) {
  QUERY = [args[0]]
  ROOM_ID = args[1]
}
console.log(QUERY, ROOM_ID)
//==============================================================================================


/**
 * 调用接口获得步骤信息.
 */
async function solveToSteps(query) {
    const url = `${MATH_SERVICE_URL}/query`;
    const body = { query };
    const resp = await fetch(url, {
        method: "POST",
        body: JSON.stringify(body),
        headers: {"Content-Type": "application/json"}
    });
    const respJson = await resp.json();
    console.log(`Result steps: ${JSON.stringify(respJson)}`)
    if (respJson.ret !== "successful") {
        console.log(respJson);
        throw new Error(`Failed to solve to steps: ${respJson.ret}`);
    }
    return respJson.steps;
}

/**
 * 调用接口将JSON转为MML
 */
async function convertJsonToMML(json) {
    const url = `${MATH_SERVICE_URL}/json2mml`;
    const body = { json };
    const resp = await fetch(url, {
        method: "POST",
        body: JSON.stringify(body),
        headers: {"Content-Type": "application/json"}
    });
    const respJson = await resp.json();
    console.log(`Result mml: ${JSON.stringify(respJson)}`)
    if (respJson.ret !== "successful") {
        console.log(respJson);
        throw new Error(`Failed to convert to mml: ${respJson.ret}`);
    }
    return respJson.mml;
}

/**
 * 将步骤转为MML.
 */
async function convertStepsToMML(steps) {
    const retList = [];
    for (const step of steps) {
        console.log(`Converting to mml: ${step.animate_json}`);
        const mml = await convertJsonToMML(step.animate_json);
        console.log(`Converted: ${mml}`);
        retList.push({
            mml: mml.trim(),
            text: step.axiom
        });
    }
    return retList;
}

/**
 * 开始执行.
 */
async function startPg(pg, appId) {
    const url = `${AIT_EAOG_RUNNER_URL}/api/pg/exec`;
    const body = {
        roomId: appId,
        eaogData: pg
    };
    const resp = await fetch(url, {
        method: "POST",
        body: JSON.stringify(body),
        headers: { "Content-Type": "application/json" }
    });
    if (!resp.ok && resp.status !== 401) {
        throw new Error(`Failed to start PG: ${resp.status} ${resp.statusText}`);
    }
    const respJson = await resp.json();
    if (respJson.code !== 0) {
        throw new Error(`Failed to start PG: ${respJson.error}`);
    }
}


/**
 * Entry
 */
async function start() {
    // 调用接口获得讲解步骤并转为mml
    const steps = await solveToSteps(QUERY);
    const mmlSteps = await convertStepsToMML(steps);    // Array of  { mml, text }

    // 转为PG
    const pg = await mathResultPgConverter.convertToPg("题目MML", mmlSteps);
    console.log("Generated PG: " + JSON.stringify(pg));

    // 执行
    await startPg(pg, ROOM_ID);
}

start().catch(err => console.error(err));
