let apiUrl = '{{ apiUrl }}';
let school_id = '{{ school_id }}';
let delay = 10000;
let currentID = 0;
let playStatus = 0; // 未在播放
let tt = 0;
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
        playStatus = 0;
    })
    window.ap1.on('error', () => {
        playStatus = 0;
    })
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

            }, delay)
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
    let res = await fetch(`${apiUrl}/getLatestID?school_id=${school_id}`, { mode: "cors" }).catch(err => { })
    let resp = await res.json();

    id = resp.res;
    if (id != currentID) {
        currentID = id
        await skipNext();
        //console.log(`skipNext了,playStatus:${playStatus}`)
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
        console.log(resp);
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
    ap.play();
    setInterval(5000, () => { window.ap1.play() });
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