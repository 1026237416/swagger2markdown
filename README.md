
# swagger2markdown工具介绍


本工具用于将swagger生成的json api文档或者swagger服务器api接口返回的json文档转换成markdown形式，用于输出对应的接口文档(markdown再转doc或者pdf均可，推荐使用gitbook工具)

本工具会对输入的json文件(-i本地文件或者-a通过swagger服务器获取的json格式文件)进行解析，会在用户指定的目录下(默认为当前目录的target目录)生成转换后的markdown文件。

同时采取的是根据接口的资源类型进行划分，一类接口资源生成一个markdown文件，如桌面、桌面池等类型资源的接口就会生成对应的desktop.md、desktop-pool.md文件。



关于Swagger的相关知识可参考[Swagger](http://swagger.io/)的官方文档



# 关于本工具使用方法


    usage: python swagger2markdown.py [-h] [-i LOCATION_SWAGGER] [-a SWAGGER_SERVER_URL]
                                      [-o OUTPUT]

    optional arguments:
    -h, --help            
           show this help message and exit
    -i LOCATION_SWAGGER, --input LOCATION_SWAGGER
           path of the location Swagger JSON file (default: ../../xview/common/swagger/xview_api.json)
    -a SWAGGER_SERVER_URL, --additional SWAGGER_SERVER_URL
           URL of an Swagger server api url, return a JSON file
    -o OUTPUT, --output OUTPUT
           path to the output Markdown file (default: target)

