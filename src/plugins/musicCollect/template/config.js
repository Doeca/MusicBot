let apiUrl = '{{ apiUrl }}';
let school_id = '{{ school_id }}';
let delay = 10000;
let currentID = 0;
let playStatus = 0; // 未在播放
let songLoaded = 0; // 没有加载完成歌曲信息
let reloadTime = {}; // 失败后重载次数
let tt = 0;
let version = 1.75;
docute.init({
    landing: 'landing.html',
    title: '小老虎食堂音乐播放器',
    nav: {},
    plugins: [
        evanyou(),
        player()
    ]
});
function sleep(time) {
    return new Promise((resolve) => setTimeout(resolve, time));
}

function addLog(text) {
    document.getElementById("logArea").innerHTML = document.getElementById("logArea").innerHTML + '\n' + text;
}

function aplayer1() {
    window.ap1 = new APlayer({
        container: document.getElementById('aplayer1'),
        theme: '#F57F17',
        lrcType: 3,
        loop: 'none',
        order: 'list',
        preload: 'auto',
        autoplay: true,
        audio: []
    });

    window.ap1.on('ended', () => {
        addLog(`歌曲:${currentID}播放完毕，加载新歌`)
        playStatus = 0;
        songLoaded = 0;

    })
    window.ap1.on('error', async () => {
        if (playStatus == 1) {
            await sleep(1000);
            playStatus = 0;
            songLoaded = 0;
            if (reloadTime[`id${currentID}`] >= 3) {
                addLog(`歌曲:${currentID}重载次数达到上限，准备切歌`);
                await loadPlayer();
            } else {
                addLog(`歌曲:${currentID}加载出错，准备重载`);
                reloadTime[`id${currentID}`]++;
                await skipNext();
            }

        }
    })
    window.ap1.on('loadedmetadata', () => {

        if (playStatus == 1) {
            songLoaded = 1;
            addLog(`歌曲:${currentID}加载完毕`)
        }

    })

    document.getElementById("title").innerHTML = document.getElementById("title").innerHTML + ' ' + version;
}

function player() {
    return function (context) {
        context.event.on('landing:updated', function () {
            aplayer1();
            setTimeout(async () => {
                while (true) {
                    let stage = 0;
                    try {
                        await operatePlayer();
                        stage = 1;
                        await loadPlayer();
                        stage = 2;

                        let playstatus = window.ap1.audio.paused
                        if (playStatus == 1 && playstatus) {
                            res = window.ap1.play();
                            console.log(res);
                            addLog(`歌曲:${currentID}未在播放，请求播放`)
                        }
                        await sleep(delay);

                    } catch (err) {
                        // try {
                        //     let text = `school_id:${school_id}\ncurrentID:${currentID}\nplayStatus:${playStatus}\nerr:${err}\nstage:${stage}`
                        //     text = window.btoa(text)
                        //     await fetch(`${apiUrl}/notify?text=${text}`, { mode: "cors" }).catch(err => { })
                        // } catch (error) {
                        // }
                    }
                }

            }, 1000)
        });
    };
}

async function loadPlayer(skipCheck) {
    //console.log(`第${tt++}次被调用,skipCheck:${skipCheck},currentID:${currentID},playStatus:${playStatus}`)
    if (!skipCheck) {
        if (playStatus == 1)
            return;
    }
    //获取最新id，获取播放信息然后进行
    try {
        let res = await fetch(`${apiUrl}/getLatestID?school_id=${school_id}`, { mode: "cors" }).catch(err => {
        })
        let resp = await res.json();
        id = resp.res;
    } catch (err) {
        addLog(`获取新歌ID时出错，准备重新获取`)
        id = -1;
    }

    if (id != currentID) {
        currentID = id
        reloadTime[`id${currentID}`] = 0; // 为这首歌的重载次数赋0
        addLog(`获取新歌ID:${currentID}`)
        await skipNext();
    }

}


async function skipNext() {
    //停止播放，清空列表，获取下一首歌，加入列表然后播放
    let ap = window.ap1;
    ap.pause();
    ap.list.clear();
    let res = await fetch(`${apiUrl}/getPlayInfo?id=${currentID}&school_id=${school_id}`, { mode: "cors" });

    let resp = await res.json();
    if (resp.res == -1) {
        return;
    }
    ap.list.add([{
        name: resp.name,
        artist: resp.author,
        url: resp.playUrl,
        cover: resp.cover,
        lrc: resp.lrcUrl,
        theme: '#ebd0c2'
    }]);

    playStatus = 1;
    while (songLoaded == 0)
        await sleep(100);
    await sleep(100);
    ap.play();
}


async function operatePlayer() {
    let res = await fetch(`${apiUrl}/getOperations?school_id=${school_id}`, { mode: "cors" });
    let arr = await res.json();
    //console.log(arr);
    if (arr == null) return;
    if (arr.length != 0) {
        for (let i = 0; i < arr.length; i++) {
            if (arr[i].type == 'next')
                await loadPlayer(true);
            if (arr[i].type == 'volume')
                window.ap1.volume(arr[i].para, true);
        }
    }
}