import requests
import base64
import json
 
 
def get_key_from_url(url: str, userid: str) -> str:
    """
    通过请求m3u8文件中的key的url,获取解密视频key的base64字符串密钥
    :param url: m3u8文件中获取key的url
    :param userid: 用户id，放视频时飘动的那一串
    :return: key的base64字符串
    """
    # url拼接uid参数
    url += f'&uid={userid}'
    # 发送get请求
    rsp = requests.get(url=url)
    rsp_data = rsp.content
    if len(rsp_data) == 16:
        userid_bytes = bytes(userid.encode(encoding='utf-8'))
        result_list = []
        for index in range(0, len(rsp_data)):
            result_list.append(
                rsp_data[index] ^ userid_bytes[index])
        #print(result_list)
        return base64.b64encode(bytes(result_list)).decode()
    else:
        print(f"获取异常，请求返回值：{rsp.text}")
        return ''
 
 
if __name__ == '__main__':
    l = list()
    for i in range(5):
        temp = dict()
        temp['in'] = '1'
        l.append(temp)
    for v in l:
        v['in'] = 2
    print(json.dumps(l))
    
    