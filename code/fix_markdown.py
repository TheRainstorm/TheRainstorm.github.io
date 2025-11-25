import re
import os
import argparse

def process_datetime(dir):
    '''修复不正确的date格式
    '''
    for f in os.listdir(dir):
        path = os.path.join(dir, f)
        flag = False
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
            # date: 2023-03-23 23:56
            m = re.search(r'date: (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})(?!:)', content)
            if m:
                print(f"date: {f}")
                flag = True
                content_mod = re.sub(r'date: (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})(?!:)', 'date: \g<1> \g<2>:00', content)
        if flag:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(content_mod)

def process_title(dir):
    '''删除title中的日期
    '''
    for f in os.listdir(dir):
        path = os.path.join(dir, f)
        flag = False
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
            # title: 2023-11-21-title
            RE = r'title: (\d{4}-\d{2}-\d{2})-'
            m = re.search(RE, content)
            if m:
                print(f"title: {f}")
                flag = True
                content_mod = re.sub(RE, 'title: ', content)
        if flag:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(content_mod)

def print_tag_miss(dir):
    '''打印缺失tag的文件
    '''
    for f in os.listdir(dir):
        path = os.path.join(dir, f)
        flag = False
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
            if 'tags:' not in content:
                print(f"tag miss: {f}")
            if re.search(r'tags:\n\w*:', content):
                print(f"tag miss: {f}")
    
def fix_image_url(dir, new_prefix, old_prefix="images/", debug=False):
    '''查找所有图片链接
    '''
    if not new_prefix.endswith('/'):
        new_prefix += '/'
    for f in os.listdir(dir):
        path = os.path.join(dir, f)
        flag = False
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
            # start with '/'
            RE = fr'!\[(.*?)\]\(/{old_prefix}(.*?)\)'
            m1 = re.findall(RE, content)
            if m1:
                print(f"image: {f}")
                flag = True
                content = re.sub(RE, f'![\g<1>]({new_prefix}\g<2>)', content)
                
            RE = fr'!\[(.*?)\]\({old_prefix}(.*?)\)'
            m2 = re.findall(RE, content)
            if m2:
                print(f"image: {f}")
                flag = True
                content = re.sub(RE, f'![\g<1>]({new_prefix}\g<2>)', content)
        if flag:
            print(re.findall(r'!\[(.*?)\]\((.*?)\)', content))
            if debug:
                continue
            with open(path, 'w', encoding='utf-8') as file:
                file.write(content)

def fix_tags(dir, debug=False):
    '''修复tag，单个tag也要是列表
    '''
    for f in os.listdir(dir):
        path = os.path.join(dir, f)
        flag = False
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
            RE = r'tags: ([^[\]]*?)\n'
            m = re.search(RE, content)
            if m:
                print(f"tag: {f}")
                flag = True
                content = re.sub(RE, 'tags: [\g<1>]\n', content)
        if flag:
            if debug:
                continue
            with open(path, 'w', encoding='utf-8') as file:
                file.write(content)
    
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--dir', required=True, default='../posts/')
args = parser.parse_args()

if __name__ == '__main__':
    # process_datetime(args.dir)
    # process_title(args.dir)
    # print_tag_miss(args.dir)
    # fix_image_url(args.dir, "../../images/")
    fix_tags(args.dir)
    