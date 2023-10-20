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
        "url": f"http://{system.local_host}:{system.local_port}/wxpush",
        "timeout": "3000",
        "enableHttp": "1"
    }
    resp = await httpPost(url, json_data=payload)
    if resp == None:
        return False
    return resp['msg'] == 'success'


async def unhookSyncMsg():
    url = f"http://{system.wx_host}:{system.wx_port}/api/unhookSyncMsg"
    payload = {}
    headers = {}
    resp = await httpPost(url, head=headers, json_data=payload)
    if resp == None:
        return False
    return resp['msg'] == 'success'


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


async def changeCard(gid: str, wxid: str, cardname: str):
    url = f"http://{system.wx_host}:{system.wx_port}/api/modifyNickname"
    payload = {
        "chatRoomId": gid,
        "wxid": wxid,
        "nickName": cardname
    }
    resp = await httpPost(url, head={}, json_data=payload)
    if resp == None:
        return ""
    return resp['msg'] == 'success'
