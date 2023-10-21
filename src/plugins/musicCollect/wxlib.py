from .config import system
from .util import httpPost


async def checkLogin():
    url = f"http://{system.wx_host}:{system.wx_port}/api/checkLogin"
    payload = {}
    headers = {}
    resp = await httpPost(url, head=headers, json_data=payload)
    return resp


async def userInfo():
    url = f"http://{system.wx_host}:{system.wx_port}/api/userInfo"
    payload = {}
    headers = {}
    resp = await httpPost(url, head=headers, json_data=payload)
    return resp


async def hookSyncMsg():
    url = f"http://{system.wx_host}:{system.wx_port}/api/hookSyncMsg"
    payload = {
        "port": "19099",
        "ip": "127.0.0.1",
        "url": "http://127.0.0.1:19099/wxpush",
        "timeout": "15000",
        "enableHttp": "1"
    }
    resp = await httpPost(url, json_data=payload)
    if resp == None:
        return False
    return resp


async def unhookSyncMsg():
    url = f"http://{system.wx_host}:{system.wx_port}/api/unhookSyncMsg"
    payload = {}
    headers = {}
    resp = await httpPost(url, head=headers, json_data=payload)
    if resp == None:
        return False
    return resp


async def sendMsg(gid: str, msg: str, user_id: str = ""):
    if user_id != "":
        url = f"http://{system.wx_host}:{system.wx_port}/api/sendAtText"
        payload = {
            "wxids": user_id,
            "chatRoomId": gid,
            "msg": msg,
        }
    else:
        url = f"http://{system.wx_host}:{system.wx_port}/api/sendTextMsg"
        payload = {
            "wxid": gid,
            "msg": msg,
        }
    resp = await httpPost(url, head={}, json_data=payload)
    if resp == None:
        return False
    return resp['msg'] == 'success'


async def getWxid():
    url = f"http://{system.wx_host}:{system.wx_port}/api/userInfo"
    resp = await httpPost(url, head={}, json_data={})
    if resp == None:
        return ""
    return resp['data']['wxid']


async def changeCard(gid: str, cardname: str):
    url = f"http://{system.wx_host}:{system.wx_port}/api/modifyNickname"
    botid = await getWxid()
    payload = {
        "chatRoomId": gid,
        "wxid": botid,
        "nickName": cardname
    }
    resp = await httpPost(url, head={}, json_data=payload)
    if resp == None:
        return ""
    return resp['msg'] == 'success'


async def getMemberInfo(user_id):
    url = f"http://{system.wx_host}:{system.wx_port}/api/getContactProfile"
    payload = {
        "wxid": user_id
    }
    resp = await httpPost(url, head={}, json_data=payload)
    if resp == None:
        return ""
    return resp['data']


async def isAdmin(gid, userid):
    url = f"http://{system.wx_host}:{system.wx_port}/api/getMemberFromChatRoom"
    payload = {
        "chatRoomId": gid
    }
    resp = await httpPost(url, head={}, json_data=payload)
    if resp == None:
        return ""
    return resp['data']['admin'].find(userid) != -1
