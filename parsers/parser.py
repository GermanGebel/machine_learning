from bs4 import BeautifulSoup
import requests as req


def urls():  # возврат списка юрл или генерация их
    pass


def get_soup(url):
    page = req.get(url)
    print(page)
    soup = BeautifulSoup(page.text, 'html.parser')

    return soup


def finance_soup(soup: BeautifulSoup):
    finance = soup.find(class_='well background-light-blue hidden-print m-t-15')
    a = finance.find('a').find_next('a')
    url = a['href']
    print(url)
    return get_soup(url)


def load_info(soup: BeautifulSoup):
    table = soup.find('div', id_='fin-stat')
    print(table)
    # tbody = table.findChild('tbody')
    # rows = tbody.find_all('tr')
    # data = {}
    # count = 0
    # for tr in rows:
    #     table_name = ''
    #     data_mini = {}
    #     if tr['style'] == "background: #dddddd;":
    #         if count != 0: data.update({table_name: data_mini})
    #         table_name = tr.find('td').text
    #         count += 1
    #     else:
    #         tr_name = tr.find('td').text
    #         d = {}
    #         for td in tr.find_all_next('td'):
    #             d.update({td['data-th']: td.text})
    #         data_mini.update({tr_name: d})
    # return data

def main():
    URL = 'https://zachestnyibiznes.ru/company/ul/1027700092661_7712040126_PAO-AEROFLOT/balance#'  # пример
    f = get_soup(URL)
    data = load_info(f)

if __name__ == '__main__':
    main()