import _csv as csv
import logging
import time

import requests as req
from bs4 import BeautifulSoup

DATA_PATH = 'data.csv'
LOGGER_PATH = 'logger.log'

breaking_companies = 0

logging.basicConfig(filename=LOGGER_PATH, filemode='w', level=logging.INFO)

class Parser:
    @staticmethod
    def get_soup(url, params=None) -> BeautifulSoup:
        try:
            page = req.post(url, data=params)
            # with open('page.html', 'w') as file:  # это для себя
            #     file.write(page.text)
            #     file.close()
            soup = BeautifulSoup(page.text, 'html.parser')
            return soup
        except req.exceptions.Timeout:
            return None


class Zachestnyibiznes(Parser):

    @staticmethod
    def get_other_data(soup_company: BeautifulSoup, inn):  # находим параметры другие параметры, такие как статус и тд

        other_data = [["Наименование компании", soup_company.find(id='nameCompCard').text.split('\n')[0]]]
        other_data.append(['ИНН', inn])
        try:  # Оценки может не быть
            other_data.append(['Оценка', soup_company.find(class_="box-rating").text])
        except:
            other_data.append(['Оценка', None])

        founding_date = soup_company.find(itemprop="foundingDate")
        other_data.append(['Дата регистрации', founding_date.text.split('ЗАЧЕСТНЫЙБИЗНЕС\n')[1]])
        status = founding_date.find_previous('b').text
        other_data.append(['Статус', status])
        try:
            capital = \
                soup_company.find(itemprop='founder').find_previous('small').text.split('ЗАЧЕСТНЫЙБИЗНЕС')[1].split(
                    ' руб')[
                    0]
            other_data.append(['Уставный капитал', capital])
        except:
            other_data.append(['Уставный капитал', 0])
        return other_data

    @staticmethod
    def get_params_for_finance(soup_company):  # находим параметры для юрл финансовой таблицы
        try:  # окпо есть не у всех компаний
            okpo = soup_company.find('span', id="okpo").text
        except:
            okpo = ''
        inn = soup_company.find('span', id="inn").text
        date = soup_company.find(id='ogrn').find_next('a').text.split('.')[2]
        return {
            'okpo': okpo,
            'inn': inn,
            'date': date,
        }

    @staticmethod
    def parse_num(s: str):  # парсер чисел в финансовой таблице
        return ''.join(s[1:].split(' '))

    @staticmethod
    def make_url_finance_table(params: dict):  # создаем юрл для финансовой таблицы
        return 'https://zachestnyibiznes.ru/company/balance?okpo={}&inn={}&date={}&page='.format(params['okpo'],
                                                                                                 params['inn'],
                                                                                                 params['date'])
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
    def collect_company_data(soup_finance_table: BeautifulSoup, other_data):  # сборка всех данных о компании
        # данные с основной страницы компании
        data = [[]]
        for i in other_data:
            data.append(i)
        # данные из таблицы
        table = soup_finance_table.find('div', id='fin-stat').find('table')
        thead = table.find('thead')
        data.append([i.text for i in thead.find_all('th')])
        tbody = table.find('tbody')
        tr = tbody.find_all('tr')
        for t in tr:
            td = t.find_all('td')
            mini_data = []
            for i in td:
                s = i.text
                if '\n' in s:
                    s = Zachestnyibiznes.parse_num(s)
                mini_data.append(s)
            data.append(mini_data)
        data.append([])
        return data


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
    def find_company(inn: str):  # находим компанию в поисковой строке по ИНН и возвращаем soup страницы компании
        url = 'https://www.audit-it.ru/buh_otchet/index.php?q=+{}'.format(inn)
        soup = Parser.get_soup(url)
        try:
            href = soup.find(class_='resultsTable').find_next('a')['href']
            return Parser.get_soup('https://www.audit-it.ru' + href)
        except:
            return None



    @staticmethod
    def get_other_data(soup:BeautifulSoup):
        data = []
        arr = soup.find_all(class_='firmInfo')
        for i in range(2, 6):
            text = arr[i].text
            name = text.split(':')[0]
            result_code = text.split(':')[1].split(' ')[0]
            result_name = text.split(':')[1].split(' ')[2]
            data.append([name, result_code, result_name])
        return data


    @staticmethod
    def collect_company_data(soup: BeautifulSoup):
        data = []

        table_1 = soup.find(id='tblIdx1')
        tr_1 = table_1.find_all('tr', class_='calcRow')
        for tr in tr_1:
            td = tr.find_all('td')
            tr_data = [td[0]]
            for i in range(2, len(td)):
                tr_data.append(td[i].text)
            data.append(tr_data)

        table_2 = soup.find('table', class_='tblFin').find('tbody')
        tr_2 = table_2.find_all('tr')
        for tr in tr_2:
            data.append([i.text for i in tr.find_all('td')])

        table_3 = soup.find()




def csv_writer(path):
    global breaking_companies
    with open(path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=';')
        for id in range(100):
            data = parse_data(id)
            if not data is None:
                for line in data:
                    writer.writerow(line)
                logging.info('[id:{}]-->Успешная запись компании'.format(id))
            else:
                logging.warning('[id:{}]-->Брак'.format(id))
                breaking_companies += 1
        csv_file.close()


def parse_data(id):  # пошагойвый парсинг данных одной компании
    url = Rusprofile.make_url_company(id)
    soup = Parser.get_soup(url)
    inn = Rusprofile.get_inn(soup)
    if not inn is None:
        soup_company = Zachestnyibiznes.find_company(inn)
        if not soup_company is None:
            params = Zachestnyibiznes.get_params_for_finance(soup_company)
            other_data = Zachestnyibiznes.get_other_data(soup_company, inn)
            fin_soup = Parser.get_soup(Zachestnyibiznes.make_url_finance_table(params))
            data = Zachestnyibiznes.collect_company_data(fin_soup, other_data)
            return data
        else:
            logging.warning('[id:{}]-->Компания не найдена на сайте Zachestnyibiznes'.format(id))
    else:
        logging.warning('[id:{}]-->Компании не существует'.format(id))
    return None


if __name__ == '__main__':
    # for i in range(5):
    #     url = Rusprofile.make_url_company(i)
    #     soup = Parser.get_soup(url)
    #     inn = Rusprofile.get_inn(soup)
    #     print(inn)

    start = time.time()
    csv_writer(DATA_PATH)
    time_working = time.time() - start
    print("Брак: {} компаний из 100".format(breaking_companies))
    print("Время выполнения: {}".format(time_working), 'FINISH!!!!!!!!!!')
