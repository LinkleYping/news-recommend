import jieba.posseg as pseg
import jieba.analyse as anl
import codecs
import os
from gensim import corpora, models, similarities
import pymysql.cursors

def is_chinese(uchar):
    """判断一个unicode是否是汉字"""
    if uchar>=u'\u4e00' and uchar <= u'\u9fa5':
        return True
    else:
        return False

#分词且去掉停用词
def tokenization(filename,stopwords,stop_flag,connection,cursor):
    result = []
    ntype=0
    with codecs.open(filename, 'r',encoding='utf-8') as f:
        n = filename.rfind('/')
        str1 = filename[n + 1:len(filename) - 4]
        m = filename[0:n - 1].rfind('/')
        str2 = filename[m + 1:n]
        path='[' + str2 + ']' + str1
        str = ''
        tags = []
        #将文章标题复制多次增加标题的权重
        for i in range(20):
            str=str+str1
        text = f.read()
        for oneWord in text:
            if is_chinese(oneWord):
                str += oneWord
        words = pseg.cut(str)
        for word, flag in words:
            if flag not in stop_flag and word not in stopwords:
                result.append(word)
        cursor.execute("select type,keywords from txt_type where path=%s",path)
        temp = cursor.fetchall()
        if len(temp)>0:
            tags=temp[0][1].split(' ')
            ntype=temp[0][0]
        else:
            cursor.execute("select * from txt_url where path=%s", path)
            temp1 = cursor.fetchall()
            if len(temp1) == 0:
                p = text.find('|')
                q = text.find('*')
                url = text[0:p]
                # string.atoi(s, [，base])
                time = int(text[p + 1:q])
                sql = "insert into txt_url(path,url,time) values ('%s','%s','%d')"
                data = (path, url, time)
                cursor.execute(sql % data)
                connection.commit()
            seg = anl.extract_tags(str, topK=10, withWeight=False)

            for tag in seg:
                tags.append(tag)
            print(tags)
            print('change')

    return result,tags,ntype

#按照value值对字典排序
def sort_by_value(d):
    items=d.items()
    backitems=[[v[1],v[0]] for v in items]
    backitems.sort()
    return backitems[len(backitems)-1][0],backitems[len(backitems)-1][1]

#写数据库操作
def write_db(filenames,type,txt_key,keywords,connection,cursor):

    sql = "insert into txt_type(path,type,keywords) values ('%s','%d','%s')"
    for i in range(len(filenames)):
        cursor.execute("select * from txt_type where path=%s", filenames[i])
        temp = cursor.fetchall()
        if len(temp)!=0:
            continue
        str=''
        for j in range(len(txt_key[i])):
            str+=txt_key[i][j]+' '
        #print(len(filenames[i]))
        data=(filenames[i],type[i],str)
        cursor.execute(sql % data)
        connection.commit()

    sql = "insert into type_words(type,words,sum,num,word1,word2,word3) values ('%d','%s','%d','%d','%s','%s','%s')"
    for i in keywords:
        #print(i)
        cursor.execute("select * from type_words where type=%s",i)
        temp = cursor.fetchall()
        if len(temp)!=0:
            continue
        n = type.count(i)
        str=''
        for j in range(len(keywords[i])):
            str+=keywords[i][j]+' '
        data=(i,str,n,0,keywords[i][0],keywords[i][1],keywords[i][2])
        cursor.execute(sql % data)
        connection.commit()
        pass
    return

#聚类
def gather(connection,cursor):
    strs = ['中国新闻网/']
    #jieba.load_userdict("C:/Users/asus1/Desktop/dic.txt")
    stop_words = 'C:/Users/asus1/Desktop/实验/实验四/delete1.txt'
    stopwords = codecs.open(stop_words,'r',encoding='utf-8').readlines()
    stopwords = [ w.strip() for w in stopwords ]

    stop_flag = ['x', 'c', 'u','d', 'p', 't', 'uj', 'm', 'f', 'r'] #词性 特征词不为助词、连词...
    file_path="C:/Users/asus1/Desktop/实验/实验四/collection/"
    filenames=[]
    for str in strs:
        filenames.append([os.path.join(file_path+str, f) for f in os.listdir(file_path+str)]) #提取文件夹中的文件名
    dic=[]
    type=[]
    change=0

    #将所有文件中的词做成词典
    txt_key = []
    for n in range(len(strs)):
        for eachfile in filenames[n]:
            print(eachfile)
            dicc,tags,ntype=tokenization(eachfile, stopwords, stop_flag, connection, cursor)
            dic.append(dicc)
            txt_key.append(tags)
            type.append(ntype)
            if ntype==0:  #判断文章是否改变过，没有改变则不需要重新聚类
                change=1
    print('hhh')
    if change==0:
        print('没有需要重新聚类的文件')
        return

    '''all_tokens = sum(dic, [])
    token_once = set(word for word in set(all_tokens) if all_tokens.count(word) <=10)
    dic = [[word for word in text if word not in token_once] for text in dic]  # 去掉次数少于10的词'''
    print('get dic')
    # 得到每一个词的tf
    # print(nsize)
    print('get tfifd')
    dictionary = corpora.Dictionary(dic)  # 把dic里面的词做成词袋
    doc_vectors=[]
    flag = max(type)+1
    temp_type=[]
    print(flag)

    panchong = []
    if flag != 1:
        for m in range(len(type)):
            if type[m] != 0:
                if type[m] not in panchong:
                    temp = dic[m]
                    te = dictionary.doc2bow(temp)
                    doc_vectors.append(te)
                    temp_type.append(type[m])
                    panchong.append(type[m])
            else:
                pass
        for i in range(len(type)):
            if type[i]==0:
                temp=dic[i]
                tfidf = models.TfidfModel(doc_vectors)
                tfidf_vectors = tfidf[doc_vectors]  # 对已经聚类的文章表示成tf-idf形式
                # 将文档分词并使用doc2bow方法对每个不同单词的词频进行了统计，并将单词转换为其编号，然后以稀疏向量的形式返回结果
                query = dictionary.doc2bow(temp)
                query_bow = tfidf[query]  # 对将要聚类的文章表示成tf-idf形式
                index = similarities.MatrixSimilarity(tfidf_vectors)  # 创建索引（至少包含两篇文章，所以i==1单独计算
                sims = index[query_bow]
                dic_temp = {}
                for j in range(len(sims)):
                    dic_temp[j] = sims[j]
                    # print(dic_temp)
                nsim, ntxt = sort_by_value(dic_temp)  # 计算与哪一篇文章相似度最大
                if (nsim >= 0.36):  # 最大的相似度超过临界值，则与最相似的文章属于同一类
                    temp_type.append(temp_type[ntxt])
                    type[i]=temp_type[ntxt]
                else:  # 否则单独成为一个类
                    temp_type.append(flag)
                    type[i]=flag
                    flag = flag + 1
                te = dictionary.doc2bow(temp)
                doc_vectors.append(te)

    else:
        for i in range(len(type)):
            temp=dic[i]
            if i<=1: #第一篇文章单独一类
                type[i]=flag
                flag=flag+1
            else:
                # 初始化一个tfidf模型,可以用它来转换向量（词袋整数计数）表示方法为新的表示方法（Tfidf 实数权重）
                tfidf = models.TfidfModel(doc_vectors)
                tfidf_vectors = tfidf[doc_vectors]  # 对已经聚类的文章表示成tf-idf形式
                # 将文档分词并使用doc2bow方法对每个不同单词的词频进行了统计，并将单词转换为其编号，然后以稀疏向量的形式返回结果
                query = dictionary.doc2bow(temp)
                query_bow = tfidf[query]  # 对将要聚类的文章表示成tf-idf形式
                index = similarities.MatrixSimilarity(tfidf_vectors)  # 创建索引（至少包含两篇文章，所以i==1单独计算
                sims = index[query_bow]
                dic_temp = {}
                for j in range(len(sims)):
                    dic_temp[j] = sims[j]
                    # print(dic_temp)
                nsim, ntxt = sort_by_value(dic_temp)  # 计算与哪一篇文章相似度最大
                if (nsim >= 0.36):  # 最大的相似度超过临界值，则与最相似的文章属于同一类
                    type[i]=type[ntxt]
                else:  # 否则单独成为一个类
                    type[i]=flag
                    flag = flag + 1
            te = dictionary.doc2bow(temp)
            doc_vectors.append(te)
    print('聚类完毕')

    dickey={}   #相同类的特征词相加组成的词典
    #txt_key=[]  #每篇文章的特征词组成的列表
    print(len(type),len(txt_key))
    for t in range(len(type)):
        if type[t] in dickey:
            dickey[type[t]]=dickey[type[t]]+txt_key[t]
        else:
            dickey[type[t]]=txt_key[t]
    print('每个文档的特征词')
    #print(dickey)
    keywords={}  #每一类的特征词组成的词典
    #print(txt_key[2])
    print(type)
    #for i in range(1,flag):
    for i in dickey:
        word_set = set()
        for doc in dickey[i]:
            word_set.add(doc)
        word_set = list(word_set)
        #print(word_set)
        diclist=[]
        for word in word_set:
            n=dickey[i].count(word) * 1.0
            rep=[word,n]
            diclist.append(tuple(rep))
        diclist.sort(key=lambda x: x[1], reverse=True)
        #print(diclist)
        temp_list=[]
        j = 0
        m = 0
        while m<3 or j==10:
            ltemp=diclist[j][0]
            #print(ltemp)
            if len(ltemp)==1 or ltemp.isdigit==True:
                j = j + 1
            else:
                temp_list.append(ltemp)
                m=m+1
                j = j + 1
        keywords[i]=temp_list
        pass
    print('每个类的特征词')
    names=[]  #文件名的列表
    for n in range(len(strs)):
        for name in filenames[n]:
            n = name.rfind('/')
            str1 = name[n + 1:len(name) - 4]
            m = name[0:n - 1].rfind('/')
            str2 = name[m + 1:n]
            str = '[' + str2 + ']' + str1
            names.append(str)
    write_db(names,type,txt_key,keywords,connection,cursor)
    print('哇，更新了')
    return

'''if __name__ == '__main__':
    connection = pymysql.Connect(host='127.0.0.1', port=3306, user='root', password='0502', db='mydb', charset='utf8')
    cursor = connection.cursor()
    gather(connection,cursor)
    cursor.close()
    connection.close()'''