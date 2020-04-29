from bs4 import BeautifulSoup
import requests as req
import csv

global_data = []


class Parser:
    @staticmethod
    def get_soup(url, params=None):
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
    # def __init__(self):
    #     self.data = []

    @staticmethod
    def get_params_for_finance(soup):
        global global_data
        global_data.append(["Наименование компании", soup.find(id='nameCompCard').text.split('\n')[0]])
        global_data.append(['Оценка', soup.find(class_="box-rating box-rating-success").text])
        global_data.append(['Статус', soup.find('b', class_="").text])
        global_data.append(['Дата регистрации', soup.find(itemprop="foundingDate").text])
        cap = [i.text.split("Уставный капитал:") for i in soup.find_all('small') if "Уставный капитал:" in i.text]
        global_data.append(['Уставный капитал', cap[0]])

        okpo = soup.find('span', id="okpo").text
        inn = soup.find('span', id="inn").text
        date = soup.find(id='ogrn').find_next('a').text.split('.')[2]
        return {
            'okpo': okpo,
            'inn': inn,
            'date': date,
        }

    @staticmethod
    def parse_num(s: str):
        return ''.join(s[1:].split(' '))

    @staticmethod
    def url_finance_maker(params: dict):
        return 'https://zachestnyibiznes.ru/company/balance?okpo={}&inn={}&date={}&page='.format(params['okpo'],
                                                                                                 params['inn'],
                                                                                                 params['date'])

    @staticmethod
    def collect_company_data(soup: BeautifulSoup):
        global global_data
        data = [[]]
        for i in global_data:
            data.append(i)
        table = soup.find('div', id='fin-stat').find('table')
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
        return data


class Rusprofile(Parser):
    @staticmethod
    def get_inn(soup: BeautifulSoup):
        return soup.find(id='clip_inn').text

    @staticmethod
    def get_url_company(id):
        return 'https://www.rusprofile.ru/id/{}'.format(id)

    # @staticmethod
    # def run_urls():
    #     for i in range(max(int)):
    #         try:
    #             return req.get(Rusprofile.get_url_company(i))
    #         except TimeoutError:
    #             return None



class Audit(Parser):
    pass


def csv_writer(data, path):
    with open(path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=';')
        for line in data:
            writer.writerow(line)


if __name__ == '__main__':

    url_company = 'https://zachestnyibiznes.ru/company/ul/1027700092661_7712040126_PAO-AEROFLOT'  # пример
    params = Zachestnyibiznes.get_params_for_finance(Parser.get_soup(url_company))
    fin_soup = Parser.get_soup(Zachestnyibiznes.url_finance_maker(params))
    data = Zachestnyibiznes.collect_company_data(fin_soup)
    csv_writer(data, '../../data.csv')
    print('FINISH!!!!!!!!!!')
