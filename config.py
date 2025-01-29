import logging

### 配置参数 ###

DEBUG = False
# do not use "http://as.vivo.com/"; use the url which has already established connection
BASE_URL = "http://192.168.1.57:55666/"
# 下载保存目录
SAVE_DIR = "G:\\phoneT\\互传-网页传文件\\ScriptDownloads"  
# no cookies
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
}
BATCH_SIZE = 6
CONTENTS_TIMEOUT = 3000 # ms
# 日志配置
LOG_LEVEL = logging.INFO
