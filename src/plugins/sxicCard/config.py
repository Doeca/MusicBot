import os
import json


raw_set:dict = json.loads(s=open("./config/sxic/setting.json","r").read())

system = {}
system['groups'] = raw_set['groups']
system['auths'] = raw_set['auths']

userList = dict()

if os.path.exists(f"./config/sxic/info.json"):
    fs = open(f"./config/sxic/info.json", 'r')
    userList: dict = json.load(fs)
    fs.close()

fs = open(f"./config/sxic/room.json", 'r')
roomList: dict = json.load(fs)
fs.close()

print(roomList)
