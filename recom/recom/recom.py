# -*- coding:utf8 -*-
#encoding = utf-8
from flask import Flask,request, session, g, redirect, url_for, abort,render_template, flash, _app_ctx_stack
import pymysql
import threading
import re
import hashlib
import content
import website
import kmeans
import time
import requests
import os
import shutil
from bs4 import BeautifulSoup
from threading import Thread
from queue import Queue
from time import sleep

database=['mydb','redb']
flag=[0]

start = time.clock()
urls = ['http://www.xinhuanet.com/', 'http://www.chinanews.com/']
tags = ['新华网', '中国新闻网']

conn0 = pymysql.Connect(host='127.0.0.1', port=3306, user='root', password='0502', db=database[0],charset = 'utf8')
cur0 = conn0.cursor()
conn1 = pymysql.Connect(host='127.0.0.1', port=3306, user='root', password='0502', db=database[1],charset = 'utf8')
cur1 = conn1.cursor()

class ThreadLink(Thread):
    """链接下载任务线程"""

    def __init__(self, queue, url1):
        Thread.__init__(self)
        self.queue = queue
        self.url = url1

    def run(self):
        while True:
            element = self.queue.get()
            download(self.url, element)
            # signals to queue job is done
            self.queue.task_done()


def get_charset_from_html(html):
    # 从HTML中提取编码类型

    search = re.search('charset=\w+', html)

    if not search:
        return None

    search_result = search.group()
    if search_result.find('=') != -1:
        # 返回切分后的第一个元组
        return search_result.split('=')[1]

    return None


def getsoup(all_url):
    # 向链接网页发送请求，获取解析后的页面

    try:
        wbdata = requests.get(all_url)
        # 不少网站不会返回charset，这种情况下Requests默认为ISO-8859-1字符
        if wbdata.text and wbdata.encoding == 'ISO-8859-1':
            wbdata.encoding = get_charset_from_html(wbdata.text)
        # 对获取到的文本进行解析
        soup = BeautifulSoup(wbdata.text, 'lxml')

    except Exception as e:  # 网络连接错误
        print(e)
        soup = None

    return soup


def getfilename(title):
    # 将新闻标题转化为合法的文件名

    illegal = '？，：“”/?,:""\n\r'
    filename = ''
    for a in title:
        if a in illegal:
            a = ' '
        filename = filename + a

    return filename


def crawl(url1):
    # 爬取不同新闻网站首页上的标题和链接

    websoup = getsoup(url1)
    # 定义在website.py中的函数:提取首页新闻标题和链接
    newslist = website.analyze(url1, websoup)

    return newslist


def download(url1, element):
    # 提取正文内容，下载到本地【新闻链接|发布时间*正文内容】

    link = element[1]
    filename = getfilename(element[0])
    print('trying to download text from', link, '\n')

    pagesoup = getsoup(link)
    if pagesoup is not None:
        # 定义在content.py中的函数：获取网页正文
        tag, p_time, article = content.getcontent(url1, pagesoup)
        txtpath = 'C:/Users/asus1/Desktop/实验/实验四/collection'
        local = os.path.join(txtpath,
                             tag, filename + '.txt')
        artilen = len(''.join(article))
        try:
            # 将所需内容写入文本文件
            if artilen > 100:
                head = link+'|'+p_time+'*'
                text = open(local, "w", encoding='utf-8')
                text.writelines(head)
                text.writelines(article)
                text.close()
                print('正文下载完成：' + local + '\n')

            else:
                print("[下载过滤]非文本内容网页或其他无效网页", link, "\n")

        except IOError:
            print("IOError:" + local)

    else:
        print('连接错误，跳过正文提取', link)


def crawl_all():
    # 爬取五个网站全部新闻链接并下载
    while True:
        global flag
        if flag[0] == 0:
            connection = conn1
            cursor = cur1
        else:
            connection = conn0
            cursor = cur0
        '''for t in tags:  # 清空五个文件夹
            file = os.path.join('C:/Users/asus1/Desktop/实验/实验四/collection/', t)
            shutil.rmtree(file)
            os.mkdir(file)'''

        for url in urls:
            myqueue = Queue()
            print('【爬取开始】', url)
            webpages = crawl(url)

            for webpage in webpages:
                myqueue.put(webpage)

            print('-------------新闻终极筛选与下载开始-------------')
            # 启用多线程执行下载任务
            for i in range(10):
                print('Thread', i, 'start!')
                t = ThreadLink(myqueue, url)
                t.setDaemon(True)
                t.start()

            myqueue.join()
            print('【All threads terminate!】', url,
                  '\n------------------------------------------------')

        elapsed = (time.clock() - start)
        print("Time used:", elapsed)
        kmeans.gather(connection, cursor)
        if flag[0] == 0:
            flag[0] = 1
        else:
            flag[0] = 0
        sleep(60 * 60)  # 每隔一小时爬取一次
    return

app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
@app.route('/',methods=['GET','POST'])
def page1():
    if request.method == 'POST':
        if request.form["action"] == "login":
          return redirect("http://127.0.0.1:5000/login")
        elif request.form["action"] == "signup":
          return redirect("http://127.0.0.1:5000/signup")
    return render_template('home.html')
@app.route('/login',methods=['GET','POST'])
def page2():
    global flag
    if flag[0] == 0:
        conn = conn0
        cur = cur0
    else:
        conn = conn1
        cur = cur1
    cur.execute("update type_words set num=0")
    conn.commit()
    if request.method == 'POST':
        username = request.form['username']
        session['username'] =username
        password = request.form['password']
        passwordhash=hashlib.md5(password.encode("utf8")).hexdigest()
        cur.execute("select loginkey from login where id=%s",username)
        getkey=cur.fetchall()
        if username=='sa' and passwordhash==getkey[0][0]:
            return redirect("http://127.0.0.1:5000/login/admin")
        elif getkey[0][0]==passwordhash:
            return redirect("http://127.0.0.1:5000/login/show")
        else:
            message = "您输入的用户名或密码有误"
            print(message)
            return render_template('index.html', message=message)


    return render_template('index.html')
@app.route('/signup',methods=['GET','POST'])
def page3():
    if request.method == 'POST':
        username=request.form['username']
        password=request.form['password']
        passwordhash = hashlib.md5(password.encode("utf8")).hexdigest()
        interest='无'
        value=[username,interest,passwordhash]
        cur0.execute("insert into login values(%s,%s,%s)",value)
        conn0.commit()
        cur1.execute("insert into login values(%s,%s,%s)", value)
        conn1.commit()
        return redirect("http://127.0.0.1:5000/")
    return render_template('signup.html')
@app.route('/login/show',methods=['GET','POST'])
def page4():
    global flag
    if flag[0] == 0:
        conn = conn0
        cur = cur0
    else:
        conn = conn1
        cur = cur1
    if 'username' in session:
        user_id = session['username']
        cur.execute("select * from type_words")
        response = cur.fetchall()
        response1 = list(response)
        response1.sort(key=lambda x: x[3], reverse=True)
        responsen = list(response)
        responsen.sort(key=lambda x: x[2], reverse=True)
        words = []
        for i in range(10):
            words.append(responsen[i][1])
        num = response1[0][3]
        if num > 0:
            cur.execute("select words from type_words where num=%s", num)
            getwords = cur.fetchall()
            interestword = getwords[0][0]
            print(interestword)
            value = (interestword, user_id)
            cur.execute("update login set interest=%s where id=%s", value)
            conn.commit()
            cur.execute("select word1,word2,word3 from type_words where words=%s", interestword)
            gettwoword = cur.fetchall()
            str1 = gettwoword[0][0]
            str2 = gettwoword[0][1]
            str3=gettwoword[0][2]
            cur.execute("select * from type_words")
            allwords = cur.fetchall()
            interestwords = []
            for t in range(len(allwords)):
                m = allwords[t][1].find(str1)
                n = allwords[t][1].find(str2)
                l=allwords[t][1].find(str3)
                if m >= 0 or n >= 0 or l>=0:
                    interestwords.append(allwords[t][1])

        else:
            cur.execute("select interest from login where id=%s", user_id)
            getinterest = cur.fetchall()
            if getinterest[0][0] == '无':
                interestwords = '猜不到诶~'
            else:
                cur.execute("select word1,word2,word3 from type_words where words=%s", getinterest[0][0])
                gettwoword = cur.fetchall()
                if len(gettwoword)>0:
                    str1 = gettwoword[0][0]
                    str2 = gettwoword[0][1]
                    str3 = gettwoword[0][2]
                    cur.execute("select * from type_words")
                    allwords = cur.fetchall()
                    interestwords = []
                    for t in range(len(allwords)):
                        m = allwords[t][1].find(str1)
                        n = allwords[t][1].find(str2)
                        l = allwords[t][1].find(str3)
                        if m >= 0 or n >= 0 or l >= 0:
                            interestwords.append(allwords[t][1])
                else:
                    interestwords = '猜不到诶~'
        #print(interestwords)
        return render_template('show.html', words=words, interestwords=interestwords)
    else:
        return redirect("http://127.0.0.1:5000/login")


@app.route('/login/admin',methods=['GET','POST'])
def page5():
    cur=cur0
    conn=conn0
    cur.execute("select * from website")
    keywords=cur0.fetchall()
    keyword=[]
    for i in range(len(keywords)):
        keyword.append(keywords[i][0])
    if request.method == 'POST':
        if request.form["action"] == "add0":
            try:
                cur.execute("insert into website values(%s)", '中国新闻网')
            except:
                return render_template('admin.html', keyword=keyword)
        elif request.form["action"] == "delete0":
            try:
                cur.execute("delete from website where webname=%s", '中国新闻网')
            except:
                return render_template('admin.html', keyword=keyword)
        elif request.form["action"] == "add1":
            try:
                cur.execute("insert into website values(%s)", '新华网')
            except:
                return render_template('admin.html', keyword=keyword)
        elif request.form["action"] == "delete1":
            try:
                cur.execute("delete from website where webname=%s", '新华网')
            except:
                return render_template('admin.html', keyword=keyword)
        elif request.form["action"] == "add2":
            try:
                cur.execute("insert into website values(%s)", '环球网')
            except:
                return render_template('admin.html', keyword=keyword)
        elif request.form["action"] == "delete2":
            try:
                cur.execute("delete from website where webname=%s", '环球网')
            except:
                return render_template('admin.html', keyword=keyword)
        elif request.form["action"] == "add3":
            try:
                cur.execute("insert into website values(%s)", '腾讯')
            except:
                return render_template('admin.html', keyword=keyword)
        elif request.form["action"] == "delete3":
            try:
                cur.execute("delete from website where webname=%s", '腾讯')
            except:
                return render_template('admin.html', keyword=keyword)
        elif request.form["action"] == "add4":
            try:
                cur.execute("insert into website values(%s)", '新浪')
            except:
                return render_template('admin.html', keyword=keyword)
        elif request.form["action"] == "delete4":
            try:
                cur.execute("delete from website where webname=%s", '新浪')
            except:
                return render_template('admin.html', keyword=keyword)

        conn.commit()
        #conn1.commit()
        return redirect("http://127.0.0.1:5000/login/admin")
    return render_template('admin.html',keyword=keyword)
@app.route('/login/show/news/',methods=['GET','POST'])
def page6():
    global flag
    if flag[0] == 0:
        conn = conn0
        cur = cur0
    else:
        conn = conn1
        cur = cur1
    if 'username' in session:
         a = request.args.get('id')
         cur.execute("update type_words set num=num+1 where words=%s", a)
         conn.commit()
         cur.execute("select path from txt_type,type_words where txt_type.type=type_words.type and type_words.words=%s",a)
         path=cur.fetchall()
         paths=[]
         purls=[]
         temp=[]
         cur0.execute("select * from website")
         keywords = cur0.fetchall()
         keyword = []
         for i in range(len(keywords)):
             keyword.append(keywords[i][0])
         for i in range(len(path)):
             for m in range(len(keyword)):
                 if path[i][0].find(keyword[m])>0:
                     paths.append(path[i][0])
         print('path',paths)
         for j in range(len(paths)):
             cur.execute("select path,url,time from txt_url where path=%s",paths[j])
             #print(paths[j])
             purl=cur.fetchall()
             if len(purl)>0:
                 #print(purl)
                 temp.append(purl[0])
         temp.sort(key=lambda x: x[2], reverse=True)
         for t in range(len(temp)):
             ll=[temp[t][0],temp[t][1]]
             purls.append(tuple(ll))

         return render_template('news.html',purls=purls)
    else:
         return redirect("http://127.0.0.1:5000/login")


if __name__ == '__main__':
    t1 = threading.Thread(target=crawl_all)
    t1.start()
    #t1.join()
    app.run()
    cur0.close()
    conn0.close()
    cur1.close()
    conn1.close()