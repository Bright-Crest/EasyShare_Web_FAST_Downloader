# 互传网页版下载脚本

## 简介

互传网页版批量下载时会压缩文件，导致传输速率极慢，而单独下载每个文件则不会压缩，下载速度较快。因此，本脚本通过模拟浏览器请求，实现了互传网页版快速批量下载文件的功能。



## 环境配置

1.  使用 Python 3.11 或以上版本。
1.  使用conda或virtualenv创建虚拟环境
1.  `pip install -r requirements.txt`
1.  `playwright install`



## 参数配置

1. 方法一：修改`config.py`
2. 方法二：命令行参数输入



优先级：

1. 命令行参数
2. `config.py`



## 使用方法

1. vivo手机打开互传APP，点击“传输文件”，点击“网页传文件”，按照手机上的说明进行操作。
2. 确保手机和电脑建立连接
   1. 方法一：电脑浏览器打开`as.vivo.com`或者相应网址，手机确认扫码成功
   2. 方法二：电脑运行脚本加上参数`-T 6000`，即等待页面加载6秒，此时查看手机并点击确认与电脑建立连接
3. 运行脚本
   1. 使用帮助：`python script.py -h`



注：
1. 手机和电脑若不在同一局域网，vivo会限制每天的传输大小。
2. `.tmp`文件夹可以删除
3. 如果运行报错，就再次运行脚本，可能的原因有：
   1. 网络连接不稳定
4. 如果网络非常不稳定，推荐运行`run_loop.bat`，脚本会自动循环运行，直到下载成功。
   1. 需要注意循环运行上述程序是否能达到预期
