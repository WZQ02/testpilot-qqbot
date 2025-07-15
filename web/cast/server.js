const express = require('express')
const ws = require('nodejs-websocket')
const fs = require('fs')
const app = express()
const http_port = 8120
const ws_port = 8121

const http_server = app.listen(http_port, '0.0.0.0')
const ws_server = ws.createServer((con) => {
    con.on("text",(msg) => {
        //前端只接受消息，发送的任何信息都当成心跳包处理
        target({"type": 5},con.key)
    })
    con.on('close',() => {})
	con.on('error', (err) => {})
})
ws_server.listen(ws_port)

app.use(express.static('public'))

const bodyParser = require('body-parser')
app.use(bodyParser.json())
app.use(bodyParser.urlencoded({extended: true}))

const cors = require('cors')
app.use(cors())

const path = require('path')

app.post("/cast",(req,res) => {
    try {
        const con = req.body.castcontent
        if (con.casttype == "message") {
            picdata = ""
            if (con.picurl != "") {
                fetch(con.picurl).then(response => response.arrayBuffer())
                .then(buffer => {
                    buffer = Buffer.from(buffer)
                    //console.log(buffer.toString('base64'))
                    const base64Data = buffer.toString('base64')
                    const mimeType = 'image/png'
                    picdata = `data:${mimeType};base64,${base64Data}`
                    broadcast({
                        "type": 2,
                        "info": {
                            "pic": picdata
                        }
                    })
                }).catch(err => {console.log(err)})
            }
            broadcast({
                "type": 1,
                "info": {
                    "title": con.username,
                    "text": con.textcontent,
                    "desc": con.desc
                }
            })
        }
        const log = con.username+"："+con.textcontent
        console.log(log)
        res.status(200).send("已投放消息："+log)
    } catch(err) {
        console.log(err)
        res.status(500).send("未投放消息。")
    }
})

function broadcast(con) {
	ws_server.connections.forEach((ele)=>{
      	ele.send(JSON.stringify(con))
    });
}
function target(con,key) {
	ws_server.connections.forEach((ele)=>{
		if (ele.key == key) {
			ele.send(JSON.stringify(con))
		}
	});
}

