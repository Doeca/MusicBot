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
    res = '🗒歌曲列表（🅿️正在播放）：'
    id = currentPlay()
    if length == 0:
        return '😗当前歌曲列表为🈳️'
    else:
        for v in orderList:
            res += "\n"
            if v['id'] == id:
                res += '🅿️'
            elif (v['played'] == 1):
                res += '✅'
            else:
                res += '💮'
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
        return '👁‍🗨当前没有在播放歌曲'
    return f"🅿️当前歌曲【{orderList[id-1]['name']} - {orderList[id-1]['author']}】"


def generateBlack():
    blackList = config.getValue('blackList')
    length = len(blackList)
    res = '📄歌曲黑名单：\n'
    i = 0
    for v in blackList:
        res += f"《{v}》"
        if i != length - 1:
            res += "，"
        i += 1
    return res
