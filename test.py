from revChatGPT.V1 import Chatbot

cbList = list()
cbList.append(Chatbot(config={
    "email": "mr.doeca@gmail.com",
    "password": "Doeca1124468334",
    "proxy": "http://127.0.0.1:7890"
}))
cbList.append(Chatbot(config={
    "email": "msksbxps@hotmail.com",
    "password": "dTVAu5MH",
    "proxy": "http://127.0.0.1:7890"
}))


print("Chatbot: ")
prev_text = ""
for data in cbList[0].delete_conversation(
    convo_id='2eca7e72-9ae1-45a7-8913-fd3d6d49dbec'
):
    # message = data["message"][len(prev_text) :]
    # print(message, end="", flush=True)
    prev_text = data["message"]
    print(data)

print("split")
# prev_text = ""
# for data in chatbot.ask(
#     "请把诗翻译为法语",
# ):
#     # message = data["message"][len(prev_text) :]
#     # print(message, end="", flush=True)
#     prev_text = data["message"]
# print(prev_text)
