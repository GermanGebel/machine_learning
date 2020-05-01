from bs4 import BeautifulSoup
import requests as req
import csv
import time
import logging


PATH = '../../data.csv'


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
    def get_other_data(soup_company: BeautifulSoup):  # находим параметры другие параметры, такие как статус и тд
        other_data = [["Наименование компании", soup_company.find(id='nameCompCard').text.split('\n')[0]]]
        try:  # Оценки может не быть
            other_data.append(['Оценка', soup_company.find(class_="box-rating").text])
        except:
            other_data.append(['Оценка', '-'])

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
        soup = Zachestnyibiznes.get_soup(url)
        status = soup.find('a', itemprop='legalName').find_next('td').find_next('span').text[1:]
        if status == 'Ликвидировано ':
            return None
        return Parser.get_soup('https://zachestnyibiznes.ru' + soup.find(itemprop='legalName')['href'])

    @staticmethod
    def collect_company_data(soup_finance_table: BeautifulSoup,
                             other_data):  # сборка всех данных о компании в один список
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


class Audit():  # больше данных чем на Зачестный бизнес
    pass


def csv_writer(path):
    with open(path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=';')
        for i in range(100):
            data = parse_data(i)
            if not data is None:
                for line in data:
                    writer.writerow(line)
        csv_file.close()


def parse_data(id):  # пошагойвый парсинг данных одной компании
    url = Rusprofile.make_url_company(id)
    soup = Parser.get_soup(url)
    inn = Rusprofile.get_inn(soup)
    if not inn is None:
        soup_company = Zachestnyibiznes.find_company(inn)
        if not soup_company is None:
            Zachestnyibiznes.get_other_data(soup_company)
            params = Zachestnyibiznes.get_params_for_finance(soup_company)
            other_data = Zachestnyibiznes.get_other_data(soup_company)
            fin_soup = Parser.get_soup(Zachestnyibiznes.make_url_finance_table(params))
            data = Zachestnyibiznes.collect_company_data(fin_soup, other_data)
            return data
    return None


if __name__ == '__main__':
    # for i in range(5):
    #     url = Rusprofile.make_url_company(i)
    #     soup = Parser.get_soup(url)
    #     inn = Rusprofile.get_inn(soup)
    #     print(inn)
    start = time.clock()
    csv_writer(PATH)
    time_working = time.clock() - start
    print("Время выполнения: {}".format(time_working),'FINISH!!!!!!!!!!')
