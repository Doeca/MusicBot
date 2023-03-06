import requests
import base64

q = "很不错，谢谢你"
data = base64.b64encode(q.encode("utf-8"))
rtx = requests.post("http://127.0.0.1:3000/chat/1124468334",
                    data=data.decode(), headers={'content-type': 'text/plain'})

print(rtx.text)
print(rtx.json()['msg'])