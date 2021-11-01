from time import sleep
import requests
from bs4 import BeautifulSoup
import json
import time
from random import randint

#******************************************
#Получаем ссылки на разделы

main_url = 'https://abcnews.go.com/'
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
    }
req = requests.get(main_url, headers=headers)
src = req.text
n = 0
soup = BeautifulSoup(src, "lxml")
news_links = soup.find('div', class_='block row-section__column__quadraColumn').find_all('a')

section_url = []
for link in (news_links):
    link_url = main_url + link['href'].__str__().replace("/",'')
    section_url.append(link_url)
    n += 1
    print(str(link_url))
print("Всего разделов:" + str(n))
sleep(randint(3, 8))

#*******************************************
#Проходим по разделам и получаем ссылки на новости
links_url = []
for link in section_url:

    req = requests.get(link, headers=headers)
    src = req.text
    n = 0
    soup = BeautifulSoup(src, "lxml")
    news_links = soup.find_all('div', class_="ContentRoll__Headline")
    #print(news_links)


    for link in (news_links):
        link_url = link.find('a', class_='AnchorLink')['href']
        links_url.append(link_url)


    sleep(randint(3, 8))

print('Ссылки из разделов получены')

#*******************************************************************************
#Открываем каждую отдельную ссылку и парсим  нужную инфу

#для сохранения файла
all_data = []
DATA = []


k=1
for article_link in links_url:
    # Парсим первые 50 статей
    if k > 50:
        break

    # Получаем айдишник
    unique_id = int(time.time())

    print('Обрабатываем '+str(k)+'-ую новость из 50 по ссылке: ' + str(article_link))
    k += 1

    #запрос
    artiсle = requests.get(article_link, headers=headers).text
    soup = BeautifulSoup(artiсle, 'lxml')
    sleep(randint(3, 8))


    #ищет заголовок
    article_name = soup.find('h1', class_='Article__Headline__Title')
    name = article_name.text
    sleep(randint(3, 8))

    #ищет текст статьи
    article_text = soup.find('section', class_="Article__Content story")
    text = article_text.text
    sleep(randint(3, 8))

    #поиск ссылок
    news_links = soup.find('section', class_="Article__Content story").find_all("a")

    list_of_links = []
    try:
        for link in (news_links):
            link_url = link['href']
            list_of_links.append(str(link_url))
            sleep(randint(3, 8))
    except:
        pass

    # Получение ID новости
    article_name = soup.find('span', class_="disqus-comment-count")
    article_id = article_name['data-disqus-identifier']


    #**************************************
    #Открывает страницу, на которой по ID новости можно получить ID беседы на disqus и колличество комментов

    forum_url = 'https://disqus.com/embed/comments/?base=default&f=abcnewsdotcom&t_i='+str(article_id)

    html_text = requests.get(forum_url, headers=headers).text
    soup = BeautifulSoup(html_text, 'lxml')

    # Как и весь дискус, эта страница также отдает не html код, а скрипт, который "чиститься" до json файла, в котором уже ищется нужная информация.
    mata = soup.find("script", id="disqus-threadData")
    mata = mata.__str__().replace('<script id="disqus-threadData" type="text/json">', '')
    mata = mata.__str__().replace('</script>', '')
    data = json.loads(mata)

    # данные трай/эксепты нужны для редких случаев, когда комментариев на странице либо вообще нет, либо не удается их получить
    try:
        discuss_id = data['response']['posts'][0]['thread']
        total_posts = data['cursor']['total']
    except:
        pass
    try:
        #**********************************************
        # сбор комментариев, на этих страницах дискус отдает чистый скрипт, который не нужно чистить и можно обрабатывать сразу
        i=0
        comments = []
        iteration = 1
        forum_url = 'https://disqus.com/api/3.0/threads/listPostsThreaded?limit=100&thread='+str(discuss_id)+'&forum=abcnewsdotcom&order=asc&cursor='+str(iteration)+'%3A0%3A0&api_key=E8Uh5l5fHZ6gD8U3KycjAIAk46f68Zw7C6eW8WSjZvCLXebZ7p0r1yrYDrLilk2F'
        html_text = requests.get(forum_url).text
        data = json.loads(html_text)

        # Дискусс готов отдавать максимум по 100 коментариев, но при этом часто выбивает ошибки, поэтому пришлось грузить по 50, поэтому вычисляем сколько страниц нужно загрузить и сколько коментов записать с последней страницы
        number_of_repeats = total_posts // 50
        last_iteration = total_posts - number_of_repeats * 50

        forum_url = 'https://disqus.com/api/3.0/threads/listPostsThreaded?limit=50&thread=' + str(
            discuss_id) + '&forum=abcnewsdotcom&order=asc&cursor=' + str(
            iteration) + '%3A0%3A0&api_key=E8Uh5l5fHZ6gD8U3KycjAIAk46f68Zw7C6eW8WSjZvCLXebZ7p0r1yrYDrLilk2F'
        html_text = requests.get(forum_url, headers=headers).text
        data = json.loads(html_text)
        for i in range(last_iteration):
            comments.append(data["response"][i]["raw_message"])

        print('Сохраняем ' + str(last_iteration) + ' комментариев')

        # если коментов больше 100 парсит по 100 комментов за раз
        if number_of_repeats > 0:

            for iter in range(number_of_repeats):
                iteration += 1
                forum_url = 'https://disqus.com/api/3.0/threads/listPostsThreaded?limit=50&thread=' + str(
                    discuss_id) + '&forum=abcnewsdotcom&order=asc&cursor=' + str(
                    iteration) + '%3A0%3A0&api_key=E8Uh5l5fHZ6gD8U3KycjAIAk46f68Zw7C6eW8WSjZvCLXebZ7p0r1yrYDrLilk2F'
                html_text = requests.get(forum_url, headers=headers).text
                data = json.loads(html_text)
                for i in range(50):
                    comments.append(data["response"][i]["raw_message"])

                sleep(randint(3, 8))
                print(str((iteration + 1)) + '-ай пак из 50  комментариев сохранен')

        #не уверен, что нужно удалять технические символы, поэтому оставляю их на всякий случай, убирать их планировал строчкой ниже
        #comments = comments.__str__().replace('\n', '').replace('\"', '').replace('</i>', '').replace('<i>', '').replace('\\n',' ').replace('\\','')
    except:
        print('Не удалось получить часть комментариев')
        pass




    #*********************************************************
    #сохранение в json


    DATA.append(
        {'ID': unique_id,
         'News_name': name,
         'News_url': article_link,
         'Page_url': list_of_links,
         'Text': text,
         'Comments': comments}
    )



with open('ABC_NEWS_SCR.json',"w",encoding='utf-8') as file:
    json.dump(DATA, file, indent=4, ensure_ascii=False)

print("готово")