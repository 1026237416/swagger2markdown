__version__ = "0.1.10"

import argparse
import json
import os
import sys
import requests


class MarkDownEditor(object):
    def __init__(self, dist_file):
        self.dist_file = dist_file

    def add_new_line(self, text, new_lines=True):
        if new_lines:
            self.dist_file.write("%s%s" % (str(text), os.linesep))
        else:
            self.dist_file.write(str(text))

    def add_h1(self, text):
        self.add_new_line("# {}".format(text))

    def add_h2(self, text):
        self.add_new_line("## {}".format(text))

    def add_h3(self, text):
        self.add_new_line("### {}".format(text))

    def add_h4(self, text):
        self.add_new_line("#### {}".format(text))

    def add_h5(self, text):
        self.add_new_line("###### {}".format(text))

    def add_h6(self, text):
        self.add_new_line("####### {}".format(text))

    def add_unordered_line(self, text, level=0):
        self.add_new_line("%s- %s" % ("\t" * level, text))

    def add_ordered_line(self, text, level=0):
        self.add_new_line("%s1. %s" % ("\t" * level, text))

    def add_new_table(self, table_header):
        if isinstance(table_header, list):
            self.add_new_line(" | ".join(table_header), new_lines=False)
            self.add_new_line("\n", new_lines=False)
            self.add_new_line(" | ".join(["---"] * len(table_header)), new_lines=False)
            self.add_new_line("\n", new_lines=False)

    def add_new_column(self, data):
        if isinstance(data, list):
            self.add_new_line("%s\n" % " | ".join(map(str, data)), new_lines=False)

    def add_code(self, code, code_type=None):
        if code_type:
            self.add_new_line("``` {}\n".format(code_type), new_lines=False)
        else:
            self.add_new_line("```\n", new_lines=False)
        self.add_new_line(code, new_lines=False)
        self.add_new_line("\n", new_lines=False)
        self.add_new_line("```")

    def add_new_link(self, text, link, new_lines=True):
        self.add_new_line("[%s](%s)" % (text, link), new_lines=new_lines)


class Swagger2Markdown(object):
    def __init__(self, swagger_data, dist_dir, template=None):
        self.swagger_data = swagger_data
        self.template = template
        self.dist_dir = os.path.join(dist_dir, "xview-api")
        self.summary_file_path = os.path.join(dist_dir, "SUMMARY.md")

        if not os.path.exists(self.dist_dir):
            os.makedirs(self.dist_dir)

    @staticmethod
    def add_summary_catalog(md_editor, text, link, new_lines=True):
        md_editor.add_new_line("* [%s](%s)" % (text, link), new_lines=new_lines)

    def write_introduction_info(self):
        with open(self.summary_file_path, "w", encoding="utf8") as summary_fs:
            summary_fs.truncate()
            md_editor = MarkDownEditor(dist_file=summary_fs)
            md_editor.add_h1("概述")
            for title, value in self.swagger_data.items():
                if title in ["info", "consumes", "produces", "schemes", "swagger"]:
                    if isinstance(value, dict):
                        md_editor.add_h2(title)
                        for k, v in value.items():
                            md_editor.add_unordered_line("%s: %s" % (k, v))
                    elif isinstance(value, list):
                        md_editor.add_h2(title)
                        [md_editor.add_unordered_line(item) for item in value]
                    elif isinstance(value, str):
                        md_editor.add_h2("%s: %s" % (title, value))
            md_editor.add_h1("API接口设计")

    def write_api_info(self):
        # 对api接口进行分类，按资源类型进行整理
        resource_map = {resource.get("name"): {
            "description": resource.get("description"),
            "api": []
        } for resource in self.swagger_data.get("tags")}

        api_data = self.swagger_data.get("paths")
        for api_path, info in api_data.items():
            resource_map[api_path.split("/")[1]]["api"].append({api_path: info})

        resource_num = 1
        for resource_type, info in resource_map.items():
            # 每一类api接口单独一个文件，文件名以资源类型命名，如desktop-pool.md
            api_file_name = "%s.md" % resource_type
            with open(os.path.join(self.dist_dir, api_file_name), "w", encoding="utf8") as api_fs:
                # 清空源文件的内容
                api_fs.truncate()
                md_editor = MarkDownEditor(dist_file=api_fs)
                # 这里记录的是资源类型，表示接口大的分类，一级标题，比如桌面、桌面池，用户等
                resource_title = "%s. %s" % (resource_num, resource_type)
                md_editor.add_h2(resource_title)
                md_editor.add_new_line(info.get("description"))
                with open(self.summary_file_path, "a", encoding="utf8") as summary_fs:
                    summary_md_editor = MarkDownEditor(dist_file=summary_fs)
                    self.add_summary_catalog(
                        md_editor=summary_md_editor,
                        text=resource_type,
                        link="./xview-api/%s" % api_file_name
                    )

                second_level_num = 1
                for api_item in info.get("api"):
                    for request_url, request_params in api_item.items():
                        for request_method, api_info in request_params.items():
                            # 这里是具体的接口，如获取桌面列表
                            md_editor.add_h3("%s.%s %s" % (resource_num, second_level_num, api_info.get("summary")))
                            md_editor.add_unordered_line("api地址：%s" % request_url)
                            md_editor.add_unordered_line("请求方法：%s" % request_method)
                            # 接口的请求信息
                            self.write_api_request(request_params=api_info.get("parameters"),
                                                   md_editor=md_editor)

                            # 接口的返回值
                            self.write_api_response(response_info=api_info.get("responses"),
                                                    md_editor=md_editor)

                            md_editor.add_new_line(os.linesep)
                            second_level_num += 1

                md_editor.add_new_line(os.linesep)
                resource_num += 1

    def write_api_request(self, request_params, md_editor):
        md_editor.add_h4("请求: ")

        # 接口的相关参数信息
        url_params = []
        for param in request_params:
            if param.get("in") == "body":
                self.format_object_to_tables(
                    object_data=param.get("schema"),
                    object_name="body",
                    md_editor=md_editor,
                )

            elif param.get("in") in ["path", "query"]:
                url_params.append(param)
        if url_params:
            md_editor.add_unordered_line("url参数：")
            md_editor.add_new_table(["名称", "位置", "类型", "是否必选", "描述"])
            for param in url_params:
                md_editor.add_new_column([
                    param.get("name"),
                    param.get("in"),
                    param.get("type"),
                    param.get("required"),
                    param.get("description", "")
                ])

    def write_api_response(self, response_info, md_editor):
        md_editor.add_h4("返回值：")
        code_list = []
        for status_code in response_info:
            code_list.append(status_code)
        code_list.sort()
        for status_code in code_list:
            response_description = response_info[status_code].get("description", "")
            md_editor.add_new_line("- **%s: %s**" % (status_code, response_description))

            response_type = response_info[status_code].get("schema", {}).get("type")
            response_properties = {}
            if response_type == "object":
                response_properties = response_info[status_code].get("schema", {}).get("properties")
            elif response_type == "array":
                response_properties = response_info[status_code].get("schema", {}).get("item").get("properties")

            md_editor.add_new_line("**返回值类型：%s**" % response_type)
            md_editor.add_new_table(
                table_header=["参数名称", "参数类型", "描述"]
            )
            for item_name, item_info in response_properties.items():
                if item_info.get("type") in ["object", "array"]:
                    desc = "%s 具体格式请参考后面【%s】中的定义" % (item_info.get("description"), item_name)
                else:
                    desc = item_info.get("description", "")
                if len(desc) > 50:
                    desc = "<br/>".join([desc[i * 50: (i + 1) * 50] for i in range(len(desc) // 50 + 1)])

                md_editor.add_new_column([
                    item_name,
                    item_info.get("type", ""),
                    desc
                ])
            if response_properties.get("data"):
                self.format_object_to_tables(
                    object_data=response_properties.get("data"),
                    object_name="data",
                    md_editor=md_editor
                )

    def format_object_to_tables(self, object_data, object_name, md_editor, table_headers=None, table_object_item=None):
        """

        :param object_data:
        :param object_name:
        :param table_headers:
        :param table_object_item:
        :return:
        """
        if not object_data:
            return
        if not table_headers:
            table_headers = ["名称", "类型", "最小长度", "最大长度", "可选值", "是否必选", "描述"]
        if not table_object_item:
            table_object_item = ["name", "type", "minLength", "maxLength", "enum", "required", "description"]

        data_type = object_data.get("type")
        required_items = object_data.get("required", [])
        if data_type == "object":
            properties = object_data.get("properties")
        elif data_type == "array":
            properties = object_data.get("items", {}).get("properties")
        else:
            properties = {}

        if properties:
            md_editor.add_new_line("**其中[%s]参数格式如下：**" % object_name)
            md_editor.add_new_table(table_header=table_headers)
            need_next_parser_map = {}
            for item, item_info in properties.items():
                column_data = []
                if item_info.get("type") in ["object", "array"]:
                    if item_info.get("description"):
                        desc = "%s, 具体格式请参考后面【%s】中的定义" % (item_info.get("description"), item)
                    else:
                        desc = "具体格式请参考后面【%s】中的定义" % item
                    need_next_parser_map[item] = item_info
                else:
                    desc = item_info.get("description", "")
                if len(desc) > 50:
                    desc = "<br/>".join([desc[i * 50: (i + 1) * 50] for i in range(len(desc) // 50 + 1)])

                for raw in table_object_item:
                    if raw == "name":
                        column_data.append(item)
                    elif raw == "required":
                        column_data.append("True" if raw in required_items else "False")
                    elif raw == "description":
                        column_data.append(desc)
                    else:
                        column_data.append(item_info.get(raw, ""))

                md_editor.add_new_column(column_data)
            for item, item_info in need_next_parser_map.items():
                self.format_object_to_tables(item_info, item, md_editor)

            if object_data.get("example"):
                md_editor.add_unordered_line("样例：")
                md_editor.add_code(code=object_data.get("example"), code_type="json")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-i", "--input",
        default="../../xview/common/swagger/xview_api.json",
        help="path to or URL of the Swagger JSON file (default: ../../xview/common/swagger/xview_api.json)",
        metavar="SWAGGER_LOCATION"
    )

    parser.add_argument(
        "-a", "--additional",
        default=None,
        help="path to or URL of an complementary Swagger JSON file",
        metavar="SWAGGER_LOCATION"
    )

    parser.add_argument(
        "-o", "--output",
        default="target",
        help="path to the output Markdown directory (default: target)",
        metavar="OUTPUT"
    )

    args = parser.parse_args()

    print("Parsing Swagger JSON... ", end="")

    if args.input:
        try:
            swagger_data = json.load(open(args.input, encoding="utf8"))
        except (FileNotFoundError, OSError):
            sys.exit("No Swagger file found.")
    else:
        if args.additional:
            try:
                swagger_data = requests.get(args.additional).json()
            except requests.exceptions.MissingSchema:
                sys.exit('Please specify the URL with schema, e.g. "http://"')
            except requests.exceptions.ConnectionError:
                sys.exit("No Swagger file found.")
        else:
            swagger_data = {}
    print("Done!")

    print("Baking Markdown... ", end="")

    test = Swagger2Markdown(swagger_data=swagger_data, dist_dir=args.output)
    test.write_introduction_info()
    test.write_api_info()
    print("Done!")

    print("--------------------------------->>>")

    print("Result: ", args.output)


main()
