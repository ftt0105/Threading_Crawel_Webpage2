import requests
import re
import queue
import threading

file_name_count  = 0 #当前保存文件的数量
def handle_url(url):#过滤url
    url=url.strip()#去掉url的前后空格
    if url.startswith("mailto"):#url开始是mailto的会被过滤掉，返回None
        return None
    #所有url包含ico\png\css\jgp\js的url都过滤掉，返回None
    elif url.endswith("ico") or url.endswith("png") \
or url.endswith("css") or url.endswith("jpg") or url.endswith("js"):
        return None
    #url开始是javascript，过滤掉返回None
    elif url.startswith("javascript"):
        return None
    elif url=="/":#url内容是/的，过滤掉，返回None
        return None
    elif  url.startswith("//"):#url开头是//的，在前面拼接一个Https
        url = "https:" +url
        return url
    else:#其他url不做处理，直接返回
        return url

#把网页源码保存到指定目录中，文件名使用数字不断累加1来命名
def save_page_file(page_source,save_dir_path,lock):
    global file_name_count
    lock.acquire()
    file_name_count+=1
    lock.release()
    with open(save_dir_path+str(file_name_count)+".html","w",encoding="utf-8") as fp:
        fp.write(page_source)

#从当前网页源码中，获取最新的url地址
def get_urls(q,url):  
    try:#获取当前网页源码， try为了防止网络服务端的连接问题报错
        html = requests.get(url,timeout=10).text
    except Exception as e:
        print("获取网页源码出现异常，url:%s" %url)
        print("异常信息是：",e)
        return 
    #使用正则获取全部url地址
    urls=re.findall(r'href="(.*?)"',html) #
    for url in urls:#遍历所有url,使用handle_url过滤，把合法url保存到队列中
        if handle_url(url):
            q.put(handle_url(url))
    print("当前队列大小：",q.qsize())
     
def crawl_task(q,lock):#爬虫的任务函数
    #从队列中取出一个url，判断是否被抓取过，没有抓取过，则获取源码，判断是否有篮球
    #如果有篮球两个关键字，则保存到文件中，没有则不保存。
    global crawl_urls
    global save_page_num
    global url_list
    global crawled_urls
    global size
    while size>=0:
        url = q.get()
        lock.acquire()
        crawl_urls+=1
        lock.release()
        print("当前一共爬了%s个网页"  %crawl_urls)
        print(url)
        get_urls(q,url)#把当前url网页进行解析，获得新的url放到队列中
        try:#判断当前网址是否被抓取过
            if url not in crawled_urls:
                lock.acquire() #加锁的范围尽可能小，这样并发效果好一点，执行效率高
                crawled_urls.append(url)
                lock.release()
            else:
                continue
            html = requests.get(url,timeout=10).text
        except Exception as e:
            print("获取网页源码出现异常，url:%s" %url)
            print("异常信息是：",e)
            continue
        if "篮球" in html:
            save_page_file(html,"D:\\phpStudy\\Threading_Crawel_Webpage2\\count_page\\",lock)
            lock.acquire()
            save_page_num+=1
            lock.release()
            print("当前一共保存了%s个网页"  %save_page_num)
        lock.acquire()
        print("******************************",size)
        size-=1
        lock.release()

crawl_urls=0  		#记录当前抓取了多少网页
save_page_num=0		#记录当前保存了多少个网页文件
url = "https://www.sohu.com" 	#种子网址
q= queue.Queue()	#保存所有待抓取url的队列
q.put(url)              #先把种子网址加入到队列中，作为第一个抓取的网址
size = 100             #设定本系统最多抓取多少网页
crawled_urls = []       #记录曾经抓取过的网址
threads = []            #存储线程对象

lock = threading.Lock() #声明一个线程锁       

for i in range(10):#声明10个线程对象，并且指定函数任务是crawl_task
    t=threading.Thread(target=crawl_task,args=(q,lock)) #循环 实例化2个Thread类，传递函数及其参数，并将线程对象放入一个列表中
    threads.append(t)#把线程对象添加到列表中

for thread in  threads:#遍历线程对象列表，启动全部线程
    thread.start() 
    

for thread in  threads:#遍历线程对象列表，等待全部线程执行任务函数完毕
    thread.join()
