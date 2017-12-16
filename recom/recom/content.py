import recom as WebCrawl
import time


def t_trans(timestr):
    # 将格式化后的时间字符串转时间戳，便于数据库中比较排序

    try:
        time_struct = time.strptime(timestr, "%Y-%m-%d %H:%M:%S")
        time_stamp = str(int(time.mktime(time_struct)))  # float转int转str
    except ValueError:
        time_stamp = '0'

    return time_stamp


def getcontent(url, soup2):
    # 提取链接中的正文内容和发布时间

    if url == WebCrawl.urls[0]:  # 新华网
        tag = WebCrawl.tags[0]
        contents = soup2.select('div#p-detail p')
        try:
            tcontents = soup2.select('span.h-time')
            itime = tcontents[0].get_text().strip()
        except IndexError:
            itime = ' '

        if len(contents) == 0:
            contents = soup2.select('div#message_ p')
            try:
                tcontents = soup2.select('li.fr > span')
                itime = tcontents[3].get_text()
            except IndexError:
                itime = ' '

            if len(contents) == 0:
                contents = soup2.select('div#content p')

                if len(contents) == 0:
                    contents = soup2.select('div.article p')

                    if len(contents) == 0:
                        contents = soup2.select('div.txt_zw p')
                        try:
                            tcontents = soup2.select('p.thedate2')
                            itime = ('2017-' + tcontents[0].get_text().split()[1] + ' '
                                     + tcontents[0].get_text().split()[2]).replace('/', '-')
                        except IndexError:
                            itime = ' '

                        if len(contents) == 0:
                            contents = soup2.select('div#contentblock p')
                            try:
                                tcontents = soup2.select('div#pubtimeandfrom')
                                itime = tcontents[0].get_text().split("\r\n")[1]
                            except IndexError:
                                itime = ' '

    elif url == WebCrawl.urls[1]:  # 中国新闻网
        tag = WebCrawl.tags[1]
        contents = soup2.select("div.left_zw p")
        try:
            tcontents = soup2.select('div.left-t')
            time0 = tcontents[0].get_text().split('来源')[0]
            itime = time0.replace("年", "-").replace("月", "-").replace("日", "").strip() + ':00'
        except IndexError:
            itime = ' '

    '''elif url == WebCrawl.urls[2]:  # 新浪新闻
        tag = WebCrawl.tags[2]
        contents = soup2.select("div#artibody p")
        if len(contents) == 0:
            contents = soup2.select('div.page-content p')
        try:
            tcontents = soup2.select('span.time-source')
            if len(tcontents) == 0:
                tcontents = soup2.select('span.article-a__time')
                if len(tcontents) == 0:
                    tcontents = soup2.select('span#pub_date')
            itime = '2017-' + (tcontents[0].get_text().split('2017')[1]
                               .replace("月", "-").replace("日", " "))[1:12] + ':00'
        except IndexError:
            itime = ' '

    elif url == WebCrawl.urls[3]:  # 环球网
        tag = WebCrawl.tags[3]
        contents = soup2.select("div#text p")
        if len(contents) == 0:
            contents = soup2.select('div#content p')
        try:
            tcontents = soup2.select('strong.timeSummary')
            itime = tcontents[0].get_text()
        except IndexError:
            itime = ' '

    elif url == WebCrawl.urls[4]:  # 腾讯新闻
        tag = WebCrawl.tags[4]
        contents = soup2.select("div.bd p")
        try:
            tcontents = soup2.select('span.a_time')
            if len(tcontents) == 0:
                tcontents = soup2.select('span.article-time')
            itime = tcontents[0].get_text()+':00'
        except IndexError:
            itime = ' ' '''

    textlist = []
    for n in contents:
        data = n.get_text()
        textlist.append(data)
    p_time = t_trans(itime)

    return tag, p_time, textlist
