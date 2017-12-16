import recom as WebCrawl


def is_title(title1):
    # 字符串是否为新闻标题（初判断:不含一个汉字）

    def is_chinese(char0):
        # 判断单个字符是否为汉字
        if '\u4e00' <= char0 <= '\u9fff':
            return True
        else:
            return False

    n = len(title1)
    count = 0
    for char in title1:
        if not is_chinese(char):
            count = count + 1
    if count == n:
        return False
    else:
        return True


def link_judge(url, link):
    # 链接是否为视频或图片链接等

    if url == WebCrawl.urls[0]:
        if link.startswith('http://www.xinhuanet.com/video/')\
                or link.startswith('http://news.xinhuanet.com/video/')\
                or link == 'http://fms.news.cn/swf/2017qmtt/7_3_2017_jj/index.html':
            return False

    if url == WebCrawl.urls[1]:
        if link.startswith('http://www.chinanews.com/gj/shipin/') \
                or link.startswith('http://www.chinanews.com/tp/')\
                or link.startswith('http://www.chinanews.com/shipin/'):
            return False

    '''if url == WebCrawl.urls[2]:
        if link.startswith('http://slide.blog.sina.com.cn/') \
                or link.startswith('http://blog.sina.com.cn/')\
                or link.startswith('http://vip.book.sina.com.cn/'):
            return False

    if url == WebCrawl.urls[3]:
        if link.startswith('http://slide.blog.sina.com.cn/') \
                or link.startswith('http://blog.sina.com.cn/')\
                or link.startswith('http://vip.book.sina.com.cn/')\
                or link.startswith('http://zx.jiaju.sina.com.cn/')\
                or link.startswith('http://video.sina.com.cn/'):
            return False

    if url == WebCrawl.urls[3]:
        if link.startswith('http://huanqiu.com/a1/')\
                or link.startswith('http://bbs.huanqiu.com/'):
            return False

    if url == WebCrawl.urls[4]:
        if link.startswith('http://view.inews.qq.com/'):
            return False'''

    return True


def analyze(url, soup1):
    # 提取链接中的正文内容

    init = 1  # 初始标题长度下限
    if url == WebCrawl.urls[0]:  # 新华网
        news0 = soup1.select("div.chaCom_con a")
        news1 = soup1.select("ul.dataList01 a")
        news2 = soup1.select("h3.focusWordBlue a")
        news = news0 + news1 + news2

    elif url == WebCrawl.urls[1]:  # 中国新闻网
        news0 = soup1.select('div.xwzxdd-xbt a')
        news1 = soup1.select('div.new_right_content a')
        news2 = soup1.select("div.new_con_yw a")
        news3 = soup1.select("div.rank_right_ul a")
        news4 = soup1.select("div.mt15 a")
        news = news0 + news1 + news2 + news3 + news4
        init = 4

    '''elif url == WebCrawl.urls[2]:  # 新浪新闻
        news0 = soup1.select("div.blk_04 a" and "div#blk_yw_01 a")
        news1 = soup1.select("div.p_left_2 a")
        news2 = soup1.select("div.p_middle a")
        news = news0 + news1 + news2
        init = 2

    elif url == WebCrawl.urls[3]:  # 环球网
        news0 = soup1.select("div.look a")
        news1 = soup1.select("div.lookOverseas a")
        news2 = soup1.select("div.midFir a")
        news3 = soup1.select("div.txtArea a")
        news4 = soup1.select("ul.iconBoxT14 a")
        news = news0 + news1 + news2 + news3 + news4
        init = 4

    elif url == WebCrawl.urls[4]:  # 腾讯新闻
        news0 = soup1.select("div.society a")
        news1 = soup1.select("div.military a")
        news2 = soup1.select("div.history a")
        news3 = soup1.select("div.media a")
        news4 = soup1.select("div.gongyi a")
        news5 = soup1.select("div.city a")
        news6 = soup1.select("div#subHot a")
        news7 = soup1.select("em.f14 > a")
        news8 = soup1.select("div.text > ul > li > a")
        news = news0 + news1 + news2 + news3 + news4 + news5 + news6 + news7 + news8
        init = 2'''

    print('根据网页排布初次筛选后的链接数：', len(news))

    newslist = []
    linklist = []

    for n in news:

        link = n.get("href")
        if url == WebCrawl.urls[1]:
            # 中国新闻网标签中给出的是站内地址
            if link.startswith('//'):
                link = link.replace('//', 'http://')
            else:
                if link.startswith('/'):
                    link = 'http://www.chinanews.com/' + link

        if link not in linklist and len(link) > 30:  # 链接判重，长度过滤
            title = n.get_text()
            if not link_judge(url, link):  # 自定义函数舍弃无效链接
                    title = ''
            if len(title) > init and is_title(title):  # 标题长度、内容过滤
                linklist.append(link)
                alist = [title, link]
                newslist.append(alist)

    print('链接判重及过滤后根据标题再次筛选所得的链接数：', len(newslist))
    print(newslist)

    return newslist
