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
    fetch(`${apiUrl}/getLatestID`, { mode: "cors" }).then(res => {
        res.json().then((resp) => {
            id = resp.res;
            if (id != currentID) {
                currentID = id
                skipNext();
            }
        })
    }).catch(err => { })

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
        loadPlayer();
    })
}

function skipNext() {
    //停止播放，清空列表，获取下一首歌，加入列表然后播放
    let ap = window.ap1;
    ap.pause();
    ap.list.clear();
    fetch(`${apiUrl}/getPlayInfo?id=${currentID}`, { mode: "cors" }).then(res => {
        res.json().then((resp) => {
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
        })
    }).catch(err => { })
}


function operatePlayer() {
    fetch(`${apiUrl}/getOperations`, { mode: "cors" }).then((res) => {
        res.json().then((arr) => {
            console.log(arr);
            if (arr == null) return;
            if (arr.length != 0) {
                arr.forEach((v, i) => {
                    if (v.type == 'next') {
                        loadPlayer(true);
                    }
                })
            }
        })
    })
}