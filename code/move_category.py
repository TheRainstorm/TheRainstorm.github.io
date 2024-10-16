import re
import os
import argparse
import yaml

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--src', required=True, default='../posts/')
parser.add_argument('-d', '--dst', required=True, default='../')
args = parser.parse_args()

map_table = {
    '个人': 'personal',
    '阅读': 'reading',
    '学习笔记': 'learning',
    '软件工具': 'tools',
    '课程笔记': 'course',
    '折腾记录': 'play',
    '博客': 'blog',
}
def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
def move_category(src, dst):
    '''移动 category 到 directory
    '''
    for f in os.listdir(src):
        path = os.path.join(src, f)
        flag = False
        with open(path, 'r', encoding='utf-8') as file:
            content = '\n'.join(file.readlines()[:20])
            m = re.search(r'---\n(.*?)---', content, re.DOTALL)
            if not m:
                print(f"front matter miss: {f}")
                continue
            preamble = m.group(1)
            meta = yaml.load(preamble, Loader=yaml.FullLoader)
            if 'categories' not in meta:
                print(f"category miss: {f}")
                continue
            category = meta['categories'][0]
            if category not in map_table:
                print(f"category not in map table: {f}")
                continue
            d = map_table[category]
            check_dir(os.path.join(dst, d))
            dst_path = os.path.join(dst, d, f)
            os.rename(path, dst_path)
            print(f"move: {path} -> {dst_path}")

if __name__ == '__main__':
    move_category(args.src, args.dst)