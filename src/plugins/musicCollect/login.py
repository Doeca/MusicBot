from selenium import webdriver
from selenium.webdriver.common.by import By
from nonebot import logger
import asyncio
options = webdriver.ChromeOptions()
options.binary_location = "/usr/bin/google-chrome"
options.add_argument('--no-sandbox')
options.add_argument('--headless')
browser = None
temp_str = ""


def dots(func):
    def wrapper(*args, **kwargs):
        result = False
        id = 0
        while result == False:
            try:
                func(*args, **kwargs)
                result = True
                logger.info(f"{func.__name__}执行完成")
            except:
                id = id+1
                if (id == 10):
                    return False
                else:
                    logger.info(f"{func.__name__}执行出错，正在重试......")
                    asyncio.run(asyncio.sleep(0.5))
        return True
    return wrapper


@dots
def click_login():
    element = browser.find_element(By.CLASS_NAME, "top_login__link")
    element.click()


@dots
def switch_frame():
    loginFrame = browser.find_element(By.ID, "login_frame")
    browser.switch_to.frame(loginFrame)


@dots
def switch_frame2():
    ptlogin_iframe = browser.find_element(By.ID, "ptlogin_iframe")
    browser.switch_to.frame(ptlogin_iframe)


@dots
def img_get():
    global temp_str
    element = browser.find_element(By.ID, "qrlogin_img")
    temp_str = element.get_attribute("src")


@dots
def cookie_get():
    global temp_str
    cookie_script = "return document.cookie"
    temp_str = browser.execute_script(cookie_script)


def strProcedure(*functions):
    for func in functions:
        result = func()
        if result is not True:
            raise Exception(f"Function {func.__name__} returned False")
    global temp_str
    local_src = temp_str
    temp_str = ""
    return local_src


def getImgUrl():
    global browser
    if (browser != None):
        browser.quit()
        return {'res': -1, 'msg': '实例未正确关闭'}
    browser = webdriver.Chrome(options=options)
    url = 'https://y.qq.com'
    browser.get(url)  # 打开网页
    src = ""
    try:
        src = strProcedure(click_login, switch_frame, switch_frame2, img_get)
    except:
        browser.quit()
        browser = None
        return {'res': -1, 'msg': '执行出错，请之后重试'}
    return {'res': 0, 'msg': src}


def getCookie():
    global browser
    if (browser == None):
        return {'res': -1, 'msg': '实例未正确开启'}
    cookie = strProcedure(cookie_get)
    browser.quit()
    browser = None
    return {'res': 0, 'msg': cookie}
