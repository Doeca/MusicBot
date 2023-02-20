let apiUrl = 'https://musicBot.doeca.cc';
let str = window.location.href;
let key = str.substr(str.indexOf("?") + 1, 12);
let currentID = 0

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
            setInterval((handler) => {
                operatePlayer()
                console.log('fetch new operations');
            }, 1000);
        });
    };
}

function loadPlayer() {

        //获取最新id，获取播放信息然后进行
}


function aplayer1() {
    window.ap1 = new APlayer({
        container: document.getElementById('aplayer1'),
        theme: '#F57F17',
        lrcType: 3,
        loop: 'none',
        order: 'list',
        preload: 'auto',
        audio: []
    });

    // window.ap1.on('play', () => {
    //     let i = window.ap1.list.index;
    //     let val = window.ap1.list.audios[i];
    //     console.log(`Now playing : ${i}`, val);
    //     postInf(`setMusicStatus?id=${val.id}`, "do", "");
    // })
}

function postInf(path, type, msg) {
    fetch(apiUrl + path)
}

function skipNext() {
    //停止播放，清空列表，获取下一首歌，加入列表然后播放
    
    fetch(`${apiUrl}/getPlayInfo?id=${currentID}`).then(res => {

    }).catch(err => {})
}


function operatePlayer() {
    fetch(`${apiUrl}/getOperations?key=${key}`).then((res) => {
        res.json().then((arr) => {
            if (arr == null) return;
            if (arr.length != 0) {
                let ap = window.ap1;
                arr.forEach((v, i) => {
                    switch (v.type) {
                        case 'play':
                            let info = v.para;
                            ap.
                                break;
                        default:
                            console.log(`未定义的操作:${v.type}`);
                    }

                    if (v.type == 'toggle') window.ap1.toggle();
                    if (v.type == 'next') window.ap1.skipForward();
                    if (v.type == 'last') window.ap1.skipBack();
                    if (v.type == 'play') window.ap1.play();
                    if (v.type == 'pause') window.ap1.pause();
                    if (v.type == 'load') loadPlayer();
                    if (v.type == 'switch') window.ap1.list.switch(v.para - 1);
                })
            }
        })
    })
}