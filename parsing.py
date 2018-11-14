import requests
from bs4 import BeautifulSoup
import sqlite3
import time

BASE_url = 'http://vseotzyvy.ru'
N = 0

def get_html(url):
    response = requests.get(url)
    # print(response.text)
   # print(response.status_code)
    return response.text

def get_list (html, div, classs, metka_classov):
    soup = BeautifulSoup(html, features="html.parser")
    main_block = soup.find('%s' %div, class_='%s' %classs)
    if metka_classov == False:
        return main_block
    else:
        return main_block.find_all('%s' % metka_classov)

def get_href (list):
    pr = []
    for i in list:
        if i.get('href') is None:
            continue
        pr.append(i.get('href'))
    return pr

def get_name(list):
    pr = []
    for i in list:
        if i.get('href') is None:
            continue
        if i.find('img') is None:
            pr.append(i.text)
        else:
            pr.append(i.find('img').get('alt'))
    return pr

def get_kovichestvo_page(html):
    soup = BeautifulSoup(html, features="html.parser")
    classs = soup.find('div', class_='pagination')#так называется сласс со станицами в конкретных товарах
    kolichestvo = []
    kolichestvo.append(0)
    if classs is not None:
        list_a = classs.find_all('a')[:-1]
        for l in list_a:
            kolichestvo.append(l.get('href'))
    print(kolichestvo)
    return kolichestvo

def save(category, link_cat, goods, link_goods, feedback, score, link):
    conn = sqlite3.connect("DataSet.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS DataSet (id integer, category text, link_cat text, goods text, link_goods text, link text, feedback text, score text)")
    global N
    N += 1
    zapis = [('%d' %N, '%s' %category, '%s' %link_cat, '%s' %goods, '%s' %link_goods, '%s' %link, '%s' %feedback, '%s' %score)]
    print(zapis)
    cursor.executemany("INSERT INTO DataSet Values (?,?,?,?,?,?,?,?)", zapis)
    conn.commit()
    conn.close()

def check_availability(feedback):
    try:
        conn = sqlite3.connect("DataSet.db")
        cursor = conn.cursor()
        z = ['%s' %feedback]
        cursor.execute("SELECT * FROM DataSet WHERE feedback = ?", z)
        res = cursor.fetchall()
        if res == []:
            return 0
        cursor.execute("SELECT * FROM DataSet WHERE id = (SELECT MAX(id) FROM DataSet)")
        global N
        N = cursor.fetchone()[0]
        conn.close()
        return 1
    except BaseException:
        return 0



category = get_list(get_html(BASE_url), 'div', 'home_categories clearfix', 'a')[:-3]
print(category)
name_cat = get_name(category)
number_of_category = get_href(category)
# for i in range(1, len(number_of_category)):
#     print(i, number_of_category[i])
chetcik = -1
for cat in number_of_category:#проходимся по всем категориям
    chetcik += 1
    if cat is None or cat[-3] == '/' or cat[-3] == '1' or cat[-4::] == '/20/' or cat[-4::] == '/21/' or cat[-4::] == '/22/':
      continue
    print('Category: ', BASE_url + '%s' % cat)
    print(name_cat[chetcik])
    for page in get_kovichestvo_page(get_html(BASE_url + '%s' % cat)):#пройтись по всем страницам в категории и достать список товаров
        try:
            chetcik2 = -1
            print(page)
            if page == 0:
                list_a = get_list(get_html(BASE_url + '%s' % cat), 'div', 'col_cat_main', 'a')[5:-8:4]
            else:
                list_a = get_list(get_html(BASE_url + '%s' % cat + '%s' % page), 'div', 'col_cat_main', 'a')[5:-8:4]
            list_goods = get_href(list_a)
            name_goods = get_name(list_a)
            for goods in list_goods:#зайти во все товары и достать все отзывы с них
                chetcik2 += 1
                print('Goods: ', BASE_url + '%s' % goods)
                print(name_goods[chetcik2])
                for page_goods in get_kovichestvo_page(get_html(BASE_url + '%s' % goods)):
                    print(page_goods)
                    if page_goods == 0:
                        list = get_list(get_html(BASE_url + '%s' % goods), 'div', 'col_main', False)
                    else:
                        list = get_list(get_html(BASE_url + '%s' % goods + '%s' % page_goods), 'div', 'col_main', False)
                    list_feedback = list.find_all(class_='review_block clearfix hreview')
                    for fdback in list_feedback:  # вытащить все оценки и отзывы
                        score = fdback.find('span', class_='rating bold').text
                        if fdback.find('a', class_='blink permalink') is None:
                            feedback = fdback.find('span', class_='summary item').text
                            link_otziv = fdback.find('a', class_='permalink').get('href')
                            link = BASE_url + '%s' % link_otziv
                        else:
                            link_dalee = fdback.find('a', class_='blink permalink').get('href')
                            link = BASE_url + '%s' % link_dalee
                            dalee = get_list(get_html(BASE_url + '%s' % link_dalee), 'div', 'rev_buble rate_%s' % score, False)
                            feedback = dalee.find('span', class_='description item').text
                        if check_availability(feedback) == 0:
                            save(name_cat[chetcik], BASE_url + '%s' % cat, name_goods[chetcik2], BASE_url + '%s' % goods, feedback, score, link)
                        else:
                            print(N, 'Отзыв есть в базе')
                        if N % 100 == 0:
                            time.sleep(7)
        except BaseException:
            continue