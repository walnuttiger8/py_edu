import requests
from bs4 import BeautifulSoup as bs


class Edu:
    URL_LOG = 'https://edu.tatar.ru/logon'

    MAIN_URL = "https://edu.tatar.ru/"

    auth_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ru,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Length": "40",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "edu.tatar.ru",
        "Origin": "https://edu.tatar.ru",
        "Referer": "https://edu.tatar.ru/logon/",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/78.0.3904.108 '
                      'YaBrowser/19.12.3.320 Yowser/2.5 Safari/537.36 ',
    }

    @staticmethod
    def validate(login: str, password: str):
        password.strip()
        try:
            login = int(login)
        except ValueError:
            return None
        data = {
            "main_login": login,
            "main_password": password,
        }
        return data

    @staticmethod
    def Auth(login, password):
        """

        :param login: логин пользователя
        :param password: пароль пользователя
        :return: Объект класса EduUser
        """
        data = Edu.validate(login, password)
        session = requests.Session()
        response = session.post(url=Edu.URL_LOG, data=data, headers=Edu.auth_headers)
        if response.url != Edu.MAIN_URL:
            return None
        cookies = response.cookies
        content = response.content
        return EduUser(data, cookies, content)


class EduUser:
    def __init__(self, data, cookies, content):
        """

        :param data: словарь пользовательских данных, получается из метода Edu.Auth()
        :param cookies: cookies авторизованного пользоваеля (метод Edu.Auth())
        :param content: основная страница пользователя (метод Edu.Auth())
        """
        self.DIARY_URL = "https://edu.tatar.ru/user/diary/term"
        self.HOMEWORK_URL = "https://edu.tatar.ru/user/diary/day"
        self.data = data
        self.cookies = cookies
        self.login = data["main_login"]
        self.password = data["main_password"]
        self.main_html = bs(content, 'html.parser')
        self.data = EduParser.get_data(self.main_html)
        self.name = self.data['Имя']
        self.marks = None

    @staticmethod
    def connection_is_correct(url, prefer):
        return True if url == prefer else False

    def get_marks(self):
        """
        Возвращает словарь оценок пользователя
        :return: dict{'subject' : 'marks'} marks - СТРОКА!
        """
        response = self.make_request(self.DIARY_URL)

        html = bs(response.content, "html.parser")
        marks = EduParser.get_data(html)
        del marks['Предмет']
        del marks['ИТОГО']
        self.marks = marks

        return marks

    def get_homework(self, today=False):
        """
        Возвращает словарь домашнего задания пользователя
        :return: dict{'subject' : 'tasks'}
        """

        response = self.make_request(self.HOMEWORK_URL)

        html = bs(response.content, "html.parser")
        if not today:
            url = EduParser.next_day_url(html)
            response = self.make_request(url)
        html = bs(response.content, "html.parser")
        homework = EduParser.get_data(html, 1, key_index=1, value_index=2, start=1)

        return homework

    def update_cookies(self):
        self.cookies = Edu.Auth(self.login, self.password).cookies

    def make_request(self, url):
        session = requests.Session()
        session.cookies = self.cookies
        response = session.get(url)
        if not self.connection_is_correct(response.url, url):
            self.update_cookies()
            session.cookies = self.cookies
            response = session.get(url)

        return response


class EduParser:

    @staticmethod
    def get_data(soup, table_number=0, key_index=0, value_index=1, start=0, end=0):
        table = EduParser.get_table(soup)[table_number]
        end = end or len(table) + 1
        data = {}
        for row in table[start:end]:
            key = str(row[key_index]).replace(':', "")
            value = EduParser.remove_tags(row[value_index])
            data[key] = value

        return data

    @staticmethod
    def get_table(html):

        tables = list()

        for table in html.findAll('table'):
            rows = []
            for row in table.findAll('tr'):
                cells = [td.text for td in row.findAll('td')]
                rows.append(cells)
            tables.append(rows)

        return tables

    @staticmethod
    def next_day_url(soup):
        span = soup.find('span', {'class': 'nextd'})
        url = span.find('a')['href']
        return url

    @staticmethod
    def remove_tags(text):
        tbd = ["\n", '\r']
        for tag in tbd:
            text = text.replace(tag, "")

        return text
