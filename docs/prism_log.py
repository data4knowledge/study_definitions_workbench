INFO:     10.0.3.1:35664 - "GET /static/js/bootstrap.bundle.min.js HTTP/1.1" 200 OK
INFO:     10.0.3.1:35674 - "GET /static/images/background.jpg HTTP/1.1" 200 OK
INFO:     10.0.3.1:35688 - "GET /static/images/favicon.ico HTTP/1.1" 200 OK
INFO:     10.0.3.1:35690 - "GET /login HTTP/1.1" 307 Temporary Redirect
INFO      Base URL used to obtain server name: 'http://job-j719ggj038qv7b1qbqpfxbkv.dnanexus.cloud:8080/'
INFO      Base URL used to obtain server name: 'http://job-j719ggj038qv7b1qbqpfxbkv.dnanexus.cloud:8080/'
INFO:     10.0.3.1:35696 - "GET /index HTTP/1.1" 200 OK
INFO:     10.0.3.1:35710 - "GET /static/images/wide_logo.png HTTP/1.1" 200 OK
INFO:     10.0.3.1:35726 - "GET /static/js/htmx.ws.js HTTP/1.1" 200 OK
INFO:     10.0.3.1:35728 - "GET /index/page?page=1&size=12&initial=true HTTP/1.1" 200 OK
INFO:     10.0.3.1:35742 - "WebSocket /alerts/1" [accepted]
INFO:     connection open
INFO      Base URL used to obtain server name: 'http://job-j719ggj038qv7b1qbqpfxbkv.dnanexus.cloud:8080/'
INFO      Base URL used to obtain server name: 'http://job-j719ggj038qv7b1qbqpfxbkv.dnanexus.cloud:8080/'
INFO:     10.0.3.1:49992 - "GET /help/about HTTP/1.1" 200 OK
INFO:     connection closed
INFO:     10.0.3.1:49996 - "WebSocket /alerts/1" [accepted]
INFO:     connection open
INFO      Base URL used to obtain server name: 'http://job-j719ggj038qv7b1qbqpfxbkv.dnanexus.cloud:8080/'
INFO      Base URL used to obtain server name: 'http://job-j719ggj038qv7b1qbqpfxbkv.dnanexus.cloud:8080/'
INFO:     10.0.3.1:42356 - "GET /index HTTP/1.1" 200 OK
INFO:     10.0.3.1:42372 - "GET /index/page?page=1&size=12&initial=true HTTP/1.1" 200 OK
INFO:     connection closed
INFO:     10.0.3.1:42388 - "WebSocket /alerts/1" [accepted]
INFO:     connection open
INFO      Base URL used to obtain server name: 'http://job-j719ggj038qv7b1qbqpfxbkv.dnanexus.cloud:8080/'
INFO:     10.0.3.1:42396 - "GET /import/m11-docx HTTP/1.1" 200 OK
INFO:     10.0.3.1:42400 - "GET /fileList?dir=/mount/localfiles&url=/import/m11 HTTP/1.1" 200 OK
INFO:     connection closed
INFO:     10.0.3.1:42410 - "WebSocket /alerts/1" [accepted]
INFO:     connection open
INFO:     10.0.3.1:42420 - "GET /fileList?dir=/mount/localfiles/sample_files&url=/import/m11 HTTP/1.1" 200 OK
INFO:     10.0.3.1:57520 - "GET /fileList?dir=/mount/localfiles&url=/import/m11 HTTP/1.1" 200 OK
INFO:     10.0.3.1:57528 - "GET /fileList?dir=/mount/localfiles/user_data&url=/import/m11 HTTP/1.1" 200 OK
INFO      Local file download: /mount/localfiles/user_data/ICH_M11_Template_ASP8062_Example_Mods.docx
ERROR     Exception uploading files

Details: ''NoneType' object is not subscriptable'

Trace:

Traceback (most recent call last):
  File "/code/app/imports/request_handler.py", line 41, in process
    "filename": main_file["filename"],
                ~~~~~~~~~^^^^^^^^^^^^
TypeError: 'NoneType' object is not subscriptable

INFO:     10.0.3.1:54030 - "POST /import/m11?source=os HTTP/1.1" 200 OK