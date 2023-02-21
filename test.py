import re

regex = r"id=([0-9]{1,12})"

test_str = "[CQ:json,data={\"app\":\"com.tencent.structmsg\"&#44;\"desc\":\"音乐\"&#44;\"view\":\"music\"&#44;\"ver\":\"0.0.0.1\"&#44;\"prompt\":\"&#91;分享&#93;知交共逍遥\"&#44;\"meta\":{\"music\":{\"action\":\"\"&#44;\"android_pkg_name\":\"\"&#44;\"app_type\":1&#44;\"appid\":100495085&#44;\"ctime\":1676796800&#44;\"desc\":\"洛天依\"&#44;\"jumpUrl\":\"https:\\/\\/y.music.163.com\\/m\\/song?id=1962337778&amp;uct2=bSV%2FmiIRQqQ2n1j0KssAbA%3D%3D&amp;dlt=0846&amp;app_version=8.9.22\"&#44;\"musicUrl\":\"http:\\/\\/music.163.com\\/song\\/media\\/outer\\/url?id=1962337778&amp;userid=1625999421&amp;sc=wmv&amp;tn=\"&#44;\"preview\":\"http:\\/\\/p1.music.126.net\\/a86kJURKJpACGbPb17v01A==\\/109951167641870422.jpg\"&#44;\"sourceMsgId\":\"0\"&#44;\"source_icon\":\"https:\\/\\/i.gtimg.cn\\/open\\/app_icon\\/00\\/49\\/50\\/85\\/100495085_100_m.png\"&#44;\"source_url\":\"\"&#44;\"tag\":\"网易云音乐\"&#44;\"title\":\"知交共逍遥\"&#44;\"uin\":2249938124}}&#44;\"config\":{\"ctime\":1676796800&#44;\"forward\":true&#44;\"token\":\"be7ac10841b423e7cdfa3692358afadc\"&#44;\"type\":\"normal\"}}]"

matchObj = re.search(regex, test_str, re.M | re.I)
#print(matchObj)
print(int('1333'))