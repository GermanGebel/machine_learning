import csv
import logging
import time
from fake_useragent import UserAgent
import requests as req
from bs4 import BeautifulSoup

DATA_PATH = 'data.csv'
LOGGER_PATH = 'logger.log'

# Setup a custom logger
logger = logging.getLogger('parser_logger')
logger.setLevel("INFO")
lhandler = logging.FileHandler(filename=LOGGER_PATH)
lhandler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s]: %(message)s"))
logger.addHandler(lhandler)


class Parser:
    @staticmethod
    def get_soup(url, params=None) -> BeautifulSoup:
        try:
            page = req.post(url, data=params, headers={'User-Agent': UserAgent().chrome})
            soup = BeautifulSoup(page.text, 'html.parser')
            return soup
        except req.exceptions.Timeout:
            return None


class Zachestnyibiznes(Parser):
    @staticmethod
    # находим другие параметры, такие как статус и тд
    def collect_other_data(soup_company: BeautifulSoup, inn):
        other_data = {'ИНН': inn}

        rating_box = soup_company.find(class_="box-rating")
        other_data['Оценка'] = rating_box.text.lower() if rating_box else None

        founding_date = soup_company.find(itemprop="foundingDate")
        other_data['Дата регистрации'] = founding_date.text.split('\n')[1] if founding_date else None

        status = founding_date.find_previous('b')
        other_data['Статус'] = status.text if status else None
        return other_data

    @staticmethod
    # находим параметры для запроса, чтобы получить фин. отчетность
    def collect_params_for_finance(soup_company):
        # окпо есть не у всех компаний
        okpo = soup_company.find('span', id="okpo")
        okpo = okpo.text if okpo else ''
        inn = soup_company.find('span', id="inn").text
        date = soup_company.find(id='ogrn').find_next('a').text.split('.')[2]
        return {
            'okpo': okpo,
            'inn': inn,
            'date': date,
        }

    @staticmethod
    def make_url_finance_table(params: dict):
        return f"https://zachestnyibiznes.ru/company/balance?okpo=" \
               f"{params['okpo']}&" \
               f"inn={params['inn']}&" \
               f"date={params['date']}" \
               f"&page="

    @staticmethod
    def find_company(inn: str):  # находим компанию в поисковой строке по ИНН и возвращаем soup страницы компании
        url = 'https://zachestnyibiznes.ru/search?query={}'.format(inn)
        soup = Parser.get_soup(url)
        try:
            status = soup.find('a', itemprop='legalName').find_next('td').find_next('span').text[1:]
            if status == 'Ликвидировано ':
                return None
            return Parser.get_soup('https://zachestnyibiznes.ru' + soup.find(itemprop='legalName')['href'])
        except:
            return None

    @staticmethod
    def collect_finance_data(soup_finance_table: BeautifulSoup):
        finances = []
        table_rows = soup_finance_table.find('tbody').find_all(name='tr', attrs={'style': None}, limit=58)
        # названия всех статей
        headers = [x.find(name='td', attrs={'data-th': None}).text.strip() for x in table_rows]
        for i in range(2018, 2015, -1):
            # значения статей за конкретный год
            finances_for_year = [x.find('td', attrs={'data-th': f'{i}: '}).text.strip() for x in table_rows]
            # собираем все в массив типа [{финансы за 2018}, {финансы за 2017}, ...]
            finance_dict = dict(zip(headers, finances_for_year))
            finance_dict['Год'] = i
            finances.append(finance_dict)
        return finances


class Rusprofile(Parser):
    @staticmethod
    def get_inn(soup_company: BeautifulSoup):  # берем ИНН
        try:
            title = soup_company.find('title').text
            return title.split('ИНН ')[1].split(',')[0]
        except:
            return None

    @staticmethod
    def make_url_company(id):
        return 'https://www.rusprofile.ru/id/{}'.format(id)


class Audit(Parser):  # больше данных чем на Зачестный бизнес
    @staticmethod
    def session():
        params = {
            'backurl': '/forum/index.php',
            'AUTH_FORM': 'Y',
            'TYPE': 'AUTH',
            'USER_LOGIN': 'audit-it-ru',
            'USER_PASSWORD': 'audit-it',
            "USER_REMEMBER": "Y",
            "Login": '%C2%F5%EE%E4'
        }
        with req.Session() as session:
            # Ваш URL с формами логина
            url = "https://www.audit-it.ru/my/login.php?login=yes&back_url=%2Fforum%2Findex.php"
            session.post(url, params)  # Отправляем данные в POST, в session записываются наши куки
            return session

    @staticmethod
    def get_soup(url, session=req, params=None) -> BeautifulSoup:
        try:
            page = session.post(url, data=params, headers={'User-Agent': UserAgent().chrome})
            soup = BeautifulSoup(page.text, 'html.parser')
            return soup
        except req.exceptions.Timeout:
            return None

    @staticmethod
    # находим компанию в поисковой строке по ИНН и возвращаем soup страницы компании
    def find_company(inn: str, session):
        url = 'https://www.audit-it.ru/buh_otchet/index.php?q=+{}'.format(inn)
        soup = Audit.get_soup(url, session)
        try:
            href = soup.find(class_='resultsTable').find_next('a')['href']
            return Audit.get_soup('https://www.audit-it.ru' + href, session)
        except:
            return None


def parse_data(id):
    url = Rusprofile.make_url_company(id)
    soup = Parser.get_soup(url)
    inn = Rusprofile.get_inn(soup)
    if inn:
        session = Audit.session()
        soup_audit = Audit.find_company(inn, session)
        if soup_audit:
            soup_zachestnyi = Zachestnyibiznes.find_company(inn)
            if soup_zachestnyi:
                params = Zachestnyibiznes.collect_params_for_finance(soup_zachestnyi)
                other_data = Zachestnyibiznes.collect_other_data(soup_zachestnyi, inn)
                fin_soup = Parser.get_soup(Zachestnyibiznes.make_url_finance_table(params))
                finance_data = Zachestnyibiznes.collect_finance_data(fin_soup)
                data = [{**other_data, **finance} for finance in finance_data]
                return data
            else:
                logger.warning(f"[id:{id}]-->Компания не найдена на сайте zachestnyibiznes")
        else:
            logger.warning(f"[id:{id}]-->Компания не найдена на audit")
    else:
        logger.warning(f"[id:{id}]-->Компания не найдена на rusprofile'")
    return None


def csv_writer(path):
    with open(path, 'w', newline='', encoding='utf-8') as csv_file:
        # writer = csv.writer(csv_file, delimiter=';')
        writer = csv.DictWriter(csv_file, fieldnames='')
        flag = True
        for id in range(10):
            data = parse_data(id)
            if data:
                if flag:
                    fieldnames = list(data[0].keys())
                    fieldnames.remove('Год')
                    fieldnames.insert(1, 'Год')
                    writer.fieldnames = fieldnames
                    writer.writeheader()
                    flag = False
                writer.writerows(data)
                logger.info(f"[id:{id}]-->Успешная запись данных о компании")


if __name__ == '__main__':
    start = time.time()
    csv_writer(DATA_PATH)
    time_working = time.time() - start
    print("Время выполнения: {}".format(time_working), 'FINISH!!!!!!!!!!')
