let apiUrl = '{{ apiUrl }}';
let delay = 1000;
let currentID = 0;
let playStatus = 0; // 未在播放

docute.init({
    landing: 'landing.html',
    title: '小老虎食堂音乐播放器',
    nav: {},
    plugins: [
        evanyou(),
        player()
    ]
});

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
}

function player() {
    return function (context) {
        context.event.on('landing:updated', function () {
            aplayer1();
            setInterval(async (handler) => {
                await operatePlayer();
                await loadPlayer();
                console.log('fetch new operations');
            }, delay);
        });
    };
}

async function loadPlayer(skipCheck) {
    if (!skipCheck) {
        if (playStatus == 1)
            return;
    }
    //获取最新id，获取播放信息然后进行
    let res = await fetch(`${apiUrl}/getLatestID`, { mode: "cors" }).catch(err => { })
    let resp = await res.json();

    id = resp.res;
    if (id != currentID) {
        currentID = id
        await skipNext();
    }

}


async function skipNext() {
    //停止播放，清空列表，获取下一首歌，加入列表然后播放
    let ap = window.ap1;
    ap.pause();
    ap.list.clear();
    let res = await fetch(`${apiUrl}/getPlayInfo?id=${currentID}`, { mode: "cors" });

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
    let res = await fetch(`${apiUrl}/getOperations`, { mode: "cors" });
    let arr = await res.json();
    if (arr == null) return;
    if (arr.length != 0) {
        await arr.forEach(async (v, i) => {
            if (v.type == 'next')
                await loadPlayer(true);
            if (v.type == 'volume')
                window.ap1.volume(v.para, true);
        })
    }
}