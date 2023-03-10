from . import config


def unescape(str: str):
    return str.replace("&#44;", ",").replace("&#91;", "[").replace("&#93;", ']').replace("&amp;", "&")


def currentPlay():
    orderList = config.getValue('orderList')
    id = 0
    tmpID = 0
    for v in orderList:
        if (v['played'] == 1):
            tmpID = v['id']
        else:
            id = tmpID
            break
    id = tmpID
    return id


def generateList():
    orderList = config.getValue('orderList')
    length = len(orderList)
    res = 'ðæ­æ²åè¡¨ï¼ð¿ï¸æ­£å¨æ­æ¾ï¼ï¼'
    id = currentPlay()
    if length == 0:
        return 'ðå½åæ­æ²åè¡¨ä¸ºð³ï¸'
    else:
        for v in orderList:
            res += "\n"
            if v['id'] == id:
                res += 'ð¿ï¸'
            elif (v['played'] == 1):
                res += 'â'
            else:
                res += 'ð®'
            res += f"No.{v['id']} {v['name']} - {v['author']}"
        return res


def addOperation(type: str, para: str = '0'):
    opertaionList = config.getValue('opertaionList')
    temp = dict()
    temp['type'] = type
    temp['para'] = para
    opertaionList.append(temp)


def generatePlay():
    orderList = config.getValue('orderList')
    id = currentPlay()
    if (id == 0):
        return 'ðâð¨å½åæ²¡æå¨æ­æ¾æ­æ²'
    return f"ð¿ï¸å½åæ­æ²ã{orderList[id-1]['name']} - {orderList[id-1]['author']}ã"


def generateBlack():
    blackList = config.getValue('blackList')
    length = len(blackList)
    res = 'ðæ­æ²é»ååï¼\n'
    i = 0
    for v in blackList:
        res += f"ã{v}ã"
        if i != length - 1:
            res += "ï¼"
        i += 1
    if i == 0:
        res += "ðï¸ä»»ä½æ­æ²"

    blackKeyList = config.getValue('blackKeyList')
    length = len(blackKeyList)
    res += '\nå³é®è¯åè¡¨ï¼\n'
    j = 0
    for v in blackKeyList:
        res += f"'{v}'"
        if j != length - 1:
            res += "ï¼"
        j += 1
    if j == 0:
        res += "ðï¸ä»»ä½å³é®è¯\n"
    return res


def isBlack(name: str):
    blackList = config.getValue('blackList')
    blackKeyList = config.getValue('blackKeyList')
    if name in blackList:
        return True
    for v in blackKeyList:
        if name.find(v) != -1:
            return True
    return False


def getSongList(ex=None):
    songList = list()
    if (ex == None):
        orderList = config.getValue('orderList')
    else:
        orderList = ex
    for v in orderList:
        songList.append(v['name'])
    return songList


def getOrder(qq: int):
    songList = list()
    orderList = config.getValue('orderList')
    for v in orderList:
        if (v['uin'] == qq):
            songList.append(v)
    return songList


def changeOrder(fir: int, sec: int):
    orderList = config.getValue('orderList')[:]
    rawList: list = config.getValue('orderList')
    sec_data = orderList[sec-1]

    rawList.pop(sec-1)
    rawList.insert(fir, sec_data)
    
    id = 1
    for v in rawList:
        v['id'] = id
        id = id + 1
    return True
