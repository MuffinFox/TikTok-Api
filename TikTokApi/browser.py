import random
import time
import string
import requests
import logging
from threading import Thread
import time
import datetime
import random
import json
import re
from urllib.parse import splitquery, parse_qs, parse_qsl


# Import Detection From Stealth
from .stealth import stealth
from .get_acrawler import get_acrawler, get_tt_params_script
from playwright.sync_api import sync_playwright

playwright = None


def get_playwright():
    global playwright
    if playwright is None:
        try:
            playwright = sync_playwright().start()
        except Exception as e:
            raise e

    return playwright


class browser:
    def __init__(
        self,
        **kwargs,
    ):
        self.kwargs = kwargs
        self.debug = kwargs.get("debug", False)
        self.proxy = kwargs.get("proxy", None)
        self.api_url = kwargs.get("api_url", None)
        self.referrer = kwargs.get("referer", "https://www.tiktok.com/")
        self.language = kwargs.get("language", "en")
        self.executablePath = kwargs.get("executablePath", None)
        self.device_id = kwargs.get("custom_device_id", None)
        find_redirect = kwargs.get("find_redirect", False)

        args = kwargs.get("browser_args", [])
        options = kwargs.get("browser_options", {})

        if len(args) == 0:
            self.args = []
        else:
            self.args = args

        self.options = {
            "headless": True,
            "handle_sigint": True,
            "handle_sigterm": True,
            "handle_sighup": True,
            "ignore_default_args": ["--mute-audio", "--hide-scrollbars"]
        }

        if self.proxy is not None:
            if "@" in self.proxy:
                server_prefix = self.proxy.split("://")[0]
                address = self.proxy.split("@")[1]
                self.options["proxy"] = {
                    "server": server_prefix + "://" + address,
                    "username": self.proxy.split("://")[1].split(":")[0],
                    "password": self.proxy.split("://")[1].split("@")[0].split(":")[1],
                }
            else:
                self.options["proxy"] = {"server": self.proxy}

        self.options.update(options)

        if self.executablePath is not None:
            self.options["executablePath"] = self.executablePath

        try:
            self.browser = get_playwright().chromium.launch(
                args=self.args, **self.options
            )
        except Exception as e:
            raise e
            logging.critical(e)

        context = self.create_context(set_useragent=True)
        page = context.new_page()
        self.get_params(page)
        context.close()

    def get_params(self, page) -> None:
        self.browser_language = self.kwargs.get("browser_language", page.evaluate("""() => { return navigator.language; }"""))
        self.browser_version = page.evaluate("""() => { return window.navigator.appVersion; }""")

        if len(self.browser_language.split("-")) == 0:
            self.region = self.kwargs.get("region", "US")
            self.language = self.kwargs.get("language", "en")
        elif len(self.browser_language.split("-")) == 1:
            self.region = self.kwargs.get("region", "US")
            self.language = self.browser_language.split("-")[0]
        else:
            self.region = self.kwargs.get("region", self.browser_language.split("-")[1])
            self.language = self.kwargs.get("language", self.browser_language.split("-")[0])

        self.timezone_name = self.kwargs.get("timezone_name", page.evaluate("""() => { return Intl.DateTimeFormat().resolvedOptions().timeZone; }"""))
        self.width = page.evaluate("""() => { return screen.width; }""")
        self.height = page.evaluate("""() => { return screen.height; }""")

    def create_context(self, set_useragent=False):
        iphone = playwright.devices["iPhone 11 Pro"]
        iphone["viewport"] = {
            "width": random.randint(320, 1920),
            "height": random.randint(320, 1920),
        }
        iphone["device_scale_factor"] = random.randint(1, 3)
        iphone["is_mobile"] = random.randint(1, 2) == 1
        iphone["has_touch"] = random.randint(1, 2) == 1

        iphone['bypass_csp'] = True
        iphone["user_agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53"

        context = self.browser.new_context(**iphone)
        if set_useragent:
            self.userAgent = iphone["user_agent"]

        return context

    def base36encode(self, number, alphabet="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        """Converts an integer to a base36 string."""
        base36 = ""
        sign = ""

        if number < 0:
            sign = "-"
            number = -number

        if 0 <= number < len(alphabet):
            return sign + alphabet[number]

        while number != 0:
            number, i = divmod(number, len(alphabet))
            base36 = alphabet[i] + base36

        return sign + base36

    def gen_verifyFp(self):
        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"[:]
        chars_len = len(chars)
        scenario_title = self.base36encode(int(time.time() * 1000))
        uuid = [0] * 36
        uuid[8] = "_"
        uuid[13] = "_"
        uuid[18] = "_"
        uuid[23] = "_"
        uuid[14] = "4"

        for i in range(36):
            if uuid[i] != 0:
                continue
            r = int(random.random() * chars_len)
            uuid[i] = chars[int((3 & r) | 8 if i == 19 else r)]

        return f'verify_{scenario_title.lower()}_{"".join(uuid)}'

    def sign_url(self, calc_tt_params=False, **kwargs):
        def process(route):
            route.abort()

        url = kwargs.get("url", None)
        if url is None:
            raise Exception("sign_url required a url parameter")

        tt_params = None
        context = self.create_context()
        page = context.new_page()

        if calc_tt_params:
            page.route(re.compile(r"(\.png)|(\.jpeg)|(\.mp4)|(x-expire)|(video_mp4)"), process)
            page.goto(kwargs.get('default_url', 'https://www.tiktok.com/@redbull'), wait_until='load')

        verifyFp = "".join(
            random.choice(
                string.ascii_lowercase + string.ascii_uppercase + string.digits
            )
            for i in range(16)
        )
        if kwargs.get("gen_new_verifyFp", False):
            verifyFp = self.gen_verifyFp()
        else:
            verifyFp = kwargs.get(
                "custom_verifyFp",
                "verify_khgp4f49_V12d4mRX_MdCO_4Wzt_Ar0k_z4RCQC9pUDpX",
            )

        if kwargs.get("custom_device_id") is not None:
            device_id = kwargs.get("custom_device_id", None)
        elif self.device_id is None:
            device_id = str(random.randint(10000, 999999999))
        else:
            device_id = self.device_id

        url = '{}&verifyFp={}&device_id={}'.format(url, verifyFp, device_id)

        page.add_script_tag(content=get_acrawler())
        evaluatedPage = page.evaluate(
            '''() => {
            var url = "'''
            + url
            + """"
            var token = window.byted_acrawler.sign({url: url});
            
            return token;
            }"""
        )

        url = '{}&_signature={}'.format(url, evaluatedPage)

        if calc_tt_params:
            page.add_script_tag(content=get_tt_params_script())

            tt_params = page.evaluate(
                '''() => {
                    return window.genXTTParams(''' + json.dumps(dict(parse_qsl(splitquery(url)[1]))) + ''');
            
                }'''
            )

        cookies = page.context.cookies()

        if not kwargs.get('keep_open'):
            context.close()

        return (
            verifyFp,
            device_id,
            evaluatedPage,
            tt_params,
            page,
            context,
            cookies
        )

    def sign_url_open_context(self, calc_tt_params=False, **kwargs):
        def process(route):
            route.abort()

        tt_params = None
        context = self.create_context()
        page = context.new_page()

        if calc_tt_params:
            page.route(re.compile(r"(\.png)|(\.jpeg)|(\.mp4)|(x-expire)|(video_mp4)"), process)
            page.goto(kwargs.get('default_url', 'https://www.tiktok.com/@redbull'), wait_until='load', timeout=50000)

        verifyFp = "".join(
            random.choice(
                string.ascii_lowercase + string.ascii_uppercase + string.digits
            )
            for i in range(16)
        )
        if kwargs.get("gen_new_verifyFp", False):
            verifyFp = self.gen_verifyFp()
        else:
            verifyFp = kwargs.get(
                "custom_verifyFp",
                "verify_khgp4f49_V12d4mRX_MdCO_4Wzt_Ar0k_z4RCQC9pUDpX",
            )

        if kwargs.get("custom_device_id") is not None:
            device_id = kwargs.get("custom_device_id", None)
        elif self.device_id is None:
            device_id = str(random.randint(10000, 999999999))
        else:
            device_id = self.device_id

        page.add_script_tag(content=get_acrawler())

        if calc_tt_params:
            page.add_script_tag(content=get_tt_params_script())

        return (
            verifyFp,
            device_id,
            page,
            context
        )

    def url_open(self, url):
        def process(route):
            route.abort()

        context = self.create_context()
        page = context.new_page()

        page.route(re.compile(r"(\.png)|(\.jpeg)|(\.mp4)|(x-expire)|(video_mp4)"), process)
        page.goto(url, wait_until='load')
        content = page.content()

        context.close()

        return content

    def sign_static_url_open_page(self, url, page, calc_tt_params):

        evaluatedPage = page.evaluate(
            '''() => {
            var url = "'''
            + url
            + """"
            var token = window.byted_acrawler.sign({url: url});

            return token;
            }"""
        )

        if calc_tt_params:

            tt_params = page.evaluate(
                '''() => {
                    return window.genXTTParams(''' + json.dumps(dict(parse_qsl(splitquery(url)[1]))) + ''');

                }'''
            )

        return (
            None,
            None,
            evaluatedPage,
            tt_params
        )

    def sign_url_open_page(self, url, verify_fp, device_id, page, calc_tt_params):

        url = '{}&verifyFp={}&device_id={}'.format(url, verify_fp, device_id)

        evaluatedPage = page.evaluate(
            '''() => {
            var url = "'''
            + url
            + """"
            var token = window.byted_acrawler.sign({url: url});

            return token;
            }"""
        )

        url = '{}&_signature={}'.format(url, evaluatedPage)

        if calc_tt_params:

            tt_params = page.evaluate(
                '''() => {
                    return window.genXTTParams(''' + json.dumps(dict(parse_qsl(splitquery(url)[1]))) + ''');

                }'''
            )

        return (
            verify_fp,
            device_id,
            evaluatedPage,
            tt_params
        )

    def clean_up(self):
        try:
            self.browser.close()
        except Exception:
            logging.info("cleanup failed")
        # playwright.stop()

    def find_redirect(self, url):
        self.page.goto(url, {"waitUntil": "load"})
        self.redirect_url = self.page.url

    def __format_proxy(self, proxy):
        if proxy is not None:
            return {"http": proxy, "https": proxy}
        else:
            return None

    def __get_js(self):
        return requests.get(
            "https://sf16-muse-va.ibytedtos.com/obj/rc-web-sdk-gcs/acrawler.js",
            proxies=self.__format_proxy(self.proxy),
        ).text
