# 互传网页版下载脚本

## 简介

互传网页版批量下载时会压缩文件，导致传输速率极慢，而单独下载每个文件则不会压缩，下载速度较快。因此，本脚本通过模拟浏览器请求，实现了互传网页版快速批量下载文件的功能。

## 爬取网页分析

一个示例图片元素：

```html
<img class="image" src="http://192.168.1.103:55666/thumb?fileuri=%2Fstorage%2Femulated%2F0%2FDCIM%2FCamera%2Fvideo_20230730_124151.mp4&amp;filelength=0">
```

下载请求url：

```html
http://192.168.1.103:55666/download/downloadfile?fileuri=%2Fstorage%2Femulated%2F0%2FDCIM%2FCamera%2Fvideo_20230730_124151.mp4&id=&ts=1738030744744&filename=video_20230730_124151.mp4&singleDownloadId=b8a43a721689d211e529959d8e676301&filelength=9859806
```

```html
http://192.168.1.103:55666/download/downloadfile?fileuri=%2Fstorage%2Femulated%2F0%2FDCIM%2FCamera%2Fvideo_20230730_123612.mp4&id=&ts=1738030937140&filename=video_20230730_123612.mp4&singleDownloadId=d8ccd81271c40cc06cfc9a2836962cde&filelength=103831010
```
