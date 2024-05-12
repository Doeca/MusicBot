import requests
import urllib.parse
import json
import time
import os
import re


class LabControl:
    '实验室门禁管理相关接口'
    __cookie = ''
    __ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.43'

    def __init__(self, username="", password=""):
        filename = f'./config/sxic/{"cookies" if username == "" else username}.dat'
        if os.path.exists(filename):
            f = open(filename, "r")
            self.__cookie = f.read()
            f.close()
        if self.__check() is False:
            self.__login(username, password)
        pass

    def __check(self):
        '检查本地保存的cookie是否有效，无效则重新登陆 '
        url = 'https://sxic.cquluna.top/UserNew/Edit?Id=208228'
        resp = requests.get(url, headers={"Cookie": self.__cookie})
        if resp.text == "<script>parent.location.href='/home/login'</script>":
            print("登陆失效，需要重新登陆")
            return False
        cookie_dict = resp.cookies.get_dict()
        for val in cookie_dict:
            self.__cookie += f'{val}={cookie_dict[val]}; '
        return True

    def __login(self, username="", password=""):
        timestamp = int(round(time.time() * 1000))
        url = f'https://sxic.cquluna.top/Home/DoLogin?username={"C0424" if username == "" else username}&userpwd={"DYLxYnPyndt5h6yWnsQUBCGOmFLuTtTBjAa7g11SiCIDhmaL3b2tjxx0v0Zv8KWd2JjCEGDWbI4EHZ1YEuR5048QdR4zXGJcaf%2F5YmdrYIKmqWfLeH8S4Ovkinw4JFwdI7XKhz8tLYucYDW%2Bw8LRWZMIP2DvrhfPOY2ICOEOb2U%3D" if password == "" else password}&_={timestamp}'
        resp = requests.get(url)
        cookie_dict = resp.cookies.get_dict()
        res = ''
        for val in cookie_dict:
            res += f'{val}={cookie_dict[val]}; '
        self.__cookie = res
        filename = f'./config/sxic/{"cookies" if username == "" else username}.dat'
        f = open(filename, "w")
        f.write(res)
        f.close()

    def setAuth(self, stuid: str, newAuths: list):
        cardNumb = self.getCarNumb(stuid)
        if (cardNumb == ''):
            return False
        self.changeInfo(stuid)
        id = self.getID(stuid)
        url = f'https://sxic.cquluna.top/Control/AdminCard'
        data = f'CardNo={stuid}&type=&labRoomID=&Labid=&pageIndex=&PageSize=10'
        resp = requests.post(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded',
                             'User-Agent': self.__ua, "Cookie": self.__cookie, 'Referer': f'http://mjgl.cqu.edu.cn:2050/Control/AdminCard'})
        match = re.search(
            r'GetRecordData\(\'([0-9\,]*?)\'.*?data-id="([0-9]{1,})"[\s\S]*<td>数据加载中.<\/td>[\s\S]*?<td>([0-9]{1,})<\/td>', resp.text)
        userAuths = list()
        if match != None:
            status = False
            if (match.group(3) == cardNumb):
                status = True
            existAuths = match.group(1).split(',')
            for v in newAuths:
                if str(v) not in existAuths:
                    existAuths.append(str(v))
                    status = False
            userAuths = existAuths[:]
            if status:  # 如果既不是换卡号，也没有要加权限，那么就是已经开通，进行提示
                return False
            dataID = match.group(2)
        else:
            existAuths = list()
            for v in newAuths:
                existAuths.append(str(v))
            userAuths = existAuths[:]
            dataID = 0
        roomids: str = json.dumps(userAuths)
        print(f"为{stuid}赋权限：{roomids}\n")
        roomids = roomids.replace('["', "")
        roomids = roomids.replace('"]', "")
        roomids = roomids.replace('", "', "%2C")

        if dataID == 0:
            referurl = 'http://mjgl.cqu.edu.cn:2050/Control/EditAdminCard'
            requrl = 'https://sxic.cquluna.top/Control/EditAdminCard'
        else:
            requrl = f'https://sxic.cquluna.top/Control/EditAdminCard/{dataID}'
            referurl = f'http://mjgl.cqu.edu.cn:2050/Control/EditAdminCard/{dataID}'

        url = f'https://sxic.cquluna.top/Control/JY_?Id={dataID}&CardNo={cardNumb}&StartTime=2022%2F09%2F01+00%3A00%3A00&EndTime=2026%2F06%2F30+00%3A00%3A00&CardType=%E6%97%B6%E6%AE%B5%E5%8D%A1&ids={roomids}&PersonNo={id}&password='

        resp = requests.get(
            url, headers={'User-Agent': self.__ua, 'X-Requested-With': 'XMLHttpRequest', "Cookie": self.__cookie, "Referer": referurl}).text

        if (resp != '0'):
            return False

        data = f'Id={dataID}&Ids={roomids}&UserId={id}&PersonNo={id}&CardNo={cardNumb}&password=&CardType=%E6%97%B6%E6%AE%B5%E5%8D%A1&Remark=&StartTime=2022%2F09%2F01+00%3A00%3A00&EndTime=2026%2F06%2F30+00%3A00%3A00&contralType=%E4%BB%85%E7%9F%AD%E5%BC%80%E9%97%A8'
        resp = requests.post(requrl, data=data, headers={
            'Cache-Control': 'max-age=0',
            "Upgrade-Insecure-Requests": '1',
            'Origin': 'https://sxic.cquluna.top',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': self.__ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Referer': referurl,
            "Accept-Encoding": 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            "Cookie": self.__cookie
        })
        return True

    def changeInfo(self, stuid: str):
        cardNumb = self.getCarNumb(stuid)
        if (cardNumb == ''):
            return False
        id = self.getID(stuid)
        url = f'https://sxic.cquluna.top/UserNew/Edit?Id={id}'
        resp = requests.get(url, headers={"Cookie": self.__cookie}).text
        
        # open("./config/sxic/temp.txt","w").write(resp)

        match = re.search(r'name="Password".*?value="(.{35})', resp)
        userPwd = match.group(1)  # 用户密码

        match = re.search(r'checked="checked".*value="(男|女)"', resp)
        userSex = urllib.parse.quote_plus(match.group(1).encode('utf-8'))  # 性别

        match = re.search(r'name="RealName".*value="(.*)"', resp)
        userRealname = urllib.parse.quote_plus(
            match.group(1).encode('utf-8'))  # 真实姓名

        match = re.search(
            r'name="__RequestVerificationToken".*? value="(.*?)" />', resp)
        token = match.group(1)  # 当前会话的ID

        match = re.search(
            r'<option selected="selected" value="([0-9]{1,4})">.*?<\/option>', resp)
        collegeid = match.group(1)  # 按照原来的学院增加

        data = f'__RequestVerificationToken={token}&Id={id}&IDCardNo=&Picturer=&UserName={stuid}&RealName={userRealname}&PersonNo={stuid}&Sex={userSex}&Type=%E5%AD%A6%E7%94%9F&Password={userPwd}&NM_RoleIds=5&CardNo={cardNumb}&CheckPassword={stuid}&NM_CollegeIds={collegeid}&ClassMigration=False&level=100&Phone=&Email=&Grade=%E5%A4%A7%E5%AD%A6%E4%B8%93%E7%A7%91&Remark=%E6%95%B0%E6%8D%AE%E4%B8%AD%E5%BF%83%E5%90%8C%E6%AD%A5&file=&Picturer='
        url = 'https://sxic.cquluna.top/UserNew/Edit'
        resp = requests.post(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded',
                             "Cookie": self.__cookie, 'Referer': f'http://mjgl.cqu.edu.cn:2050/UserNew/Edit?Id={id}'})
        return True

    def rmCard(self, stuid: str):
        if (self.getCarNumb(stuid) == ''):
            return False
        id = self.getID(stuid)
        url = f'https://sxic.cquluna.top/UserNew/Edit?Id={id}'
        resp = requests.get(url, headers={"Cookie": self.__cookie}).text
        match = re.search(r'name="Password".*?value="(.{35})', resp)
        userPwd = match.group(1)
        match = re.search(r'checked="checked".*value="(男|女)"', resp)
        userSex = urllib.parse.quote_plus(match.group(1).encode('utf-8'))
        match = re.search(r'name="RealName".*value="(.*)"', resp)
        userRealname = urllib.parse.quote_plus(match.group(1).encode('utf-8'))
        match = re.search(
            r'name="__RequestVerificationToken".*? value="(.*?)" />', resp)
        token = match.group(1)

        data = f'__RequestVerificationToken={token}&Id={id}&IDCardNo=&Picturer=&UserName={stuid}&RealName={userRealname}&PersonNo={stuid}&Sex={userSex}&Type=%E5%AD%A6%E7%94%9F&Password={userPwd}&NM_RoleIds=5&CardNo=&CheckPassword={stuid}&NM_CollegeIds=317&NM_ClassesIds=5101&ClassMigration=False&level=100&Phone=&Email=&Grade=%E5%A4%A7%E5%AD%A6%E4%B8%93%E7%A7%91&Remark=%E6%95%B0%E6%8D%AE%E4%B8%AD%E5%BF%83%E5%90%8C%E6%AD%A5&file=&Picturer='
        url = 'https://sxic.cquluna.top/UserNew/Edit'
        resp = requests.post(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded',
                             "Cookie": self.__cookie, 'Referer': f'http://mjgl.cqu.edu.cn:2050/UserNew/Edit?Id={id}'})
        return True

    def getID(self, stuid: str):
        if (len(stuid) != 8):
            return ''
        url = f'https://sxic.cquluna.top/User/GetUserSelectAllSsr?UId=&term={stuid}&q={stuid}'
        resp = requests.get(url)
        res = resp.json()
        if res[0]['text'].find(stuid) == -1:
            return ''
        return res[0]['id']

    def getCarNumb(self, stuid: str):
        if (len(stuid) != 8):
            return ''
        id = self.getID(stuid)
        if (id == ''):
            return ''
        url = f'https://sxic.cquluna.top/User/GetUserModel?id={id}'
        resp = requests.get(url)
        res = resp.json()
        if res['LabCardNo'] == None:
            return ''
        return res['LabCardNo']

    def getCardInfo(self, stuid: str):
        url = f'https://sxic.cquluna.top/Control/AdminCard'
        data = f'CardNo={stuid}&type=&labRoomID=&Labid=&pageIndex=&PageSize=10'
        resp = requests.post(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded',
                             'User-Agent': self.__ua, "Cookie": self.__cookie, 'Referer': f'http://mjgl.cqu.edu.cn:2050/Control/AdminCard'})
        match = re.search(
            r'GetRecordData\(\'([0-9\,]*?)\'.*?data-id="([0-9]{1,})"[\s\S]*<td>数据加载中.<\/td>[\s\S]*?<td>([0-9]{1,})<\/td>', resp.text)
        if match != None:
            return match.group(1).split(',')
        else:
            return []

    def tigerRemove(self):

        url = f'https://sxic.cquluna.top/Control/AdminCard'
        data = f'CardNo=&type=&labRoomID=1945&Labid=&pageIndex=&PageSize=1000'
        resp = requests.post(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded',
                             'User-Agent': self.__ua, "Cookie": self.__cookie, 'Referer': f'http://mjgl.cqu.edu.cn:2050/Control/AdminCard'})

        pattern = re.compile(r'<tr onclick="GetRecordData.*?" data-id="(\d+)">\n                                <td style="text-align:center;">\n                                        <input type="checkbox" autocomplete="off" lay-skin="primary" />\n                                </td>\n                                <td>数据加载中.</td>\n                                <td>\d+</td>\n                                <td>仅短开门</td>\n                                <td>时段卡</td>\n                                <td>\n                                        <span>.*?</span>\n\n                                </td>\n                                    <td>\n                                        .*?\n                                        .*?\n                                    </td>\n                                <td>周博翰</td>')

        res = pattern.findall(resp.text.replace("\r", ""))
        ids = ",".join(res)
        if ids == '':
            return 'Clean'

        url = f'https://sxic.cquluna.top/Control/DeleteAdminCard?ids={ids}'
        data = ''
        resp = requests.post(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded',
                             'User-Agent': self.__ua, "Cookie": self.__cookie, 'Referer': f'http://mjgl.cqu.edu.cn:2050/Control/AdminCard'})

        return resp.text
