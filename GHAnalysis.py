# -*- coding: utf-8 -*-

import os
import argparse
import pickle
import re

DATA = ("PushEvent", "IssueCommentEvent", "IssuesEvent", "PullRequestEvent" )
# 匹配时使用
pattern = re.compile(r'"type":"(\w+?)".*?actor.*?"login":"(\S+?)".*?repo.*?"name":"(\S+?)"')
# 正则表达式的使用，优化匹配速度


class Data:
    def __init__(self):
        self._user = {}
        self._repo = {}
        self._user_repo = {}
    # 初始化记录读取的内存
    # 可使函数无参使用

    @staticmethod
    def __parse(file_path: str):

        # 从json文件中逐行抽取所需信息元组(event, user, repo)
        # 将有用信息存入此空间
        records = []
        # 打开json文件
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # 运用正则表达式匹配有效数据
                res = pattern.search(line)
                if res is None or res[1] not in DATA:
                    continue
                records.append(res.groups())
        return records

    def init(self, dir_path: str):
        records = []
        for cur_dir, sub_dir, filenames in os.walk(dir_path):
            # 保留后缀为json
            filenames = filter(lambda r: r.endswith('.json'), filenames)
            for name in filenames:
                records.extend(self.__parse(f'{cur_dir}/{name}'))

        for record in records:
            event, user, repo = record
            self._user.setdefault(user, {})
            self._user_repo.setdefault(user, {})
            self._repo.setdefault(repo, {})
            self._user_repo[user].setdefault(repo, {})
            self._user[user][event] = self._user[user].get(event, 0)+1
            self._repo[repo][event] = self._repo[repo].get(event, 0)+1
            self._user_repo[user][repo][event] = self._user_repo[user][repo].get(event, 0)+1

        # 将数据写入1、2、3.json
        with open('1.json', 'wb') as f:
            pickle.dump(self._user, f)
        with open('2.json', 'wb') as f:
            pickle.dump(self._repo, f)
        with open('3.json', 'wb') as f:
            pickle.dump(self._user_repo, f)

    def load(self):
        if not any((os.path.exists(f'{i}.json') for i in range(1, 3))):
            raise RuntimeError('error: data file not found')

        with open('1.json', 'rb') as f:
            self._user = pickle.load(f)
        with open('2.json', 'rb') as f:
            self._repo = pickle.load(f)
        with open('3.json', 'rb') as f:
            self._user_repo = pickle.load(f)

    def get_user(self, user: str, event: str) -> int:
        return self._user.get(user, {}).get(event, 0)

    def get_repo(self, repo: str, event: str) -> int:
        return self._repo.get(repo, {}).get(event, 0)

    def get_user_repo(self, user: str, repo: str, event: str) -> int:
        return self._user_repo.get(user, {}).get(repo, {}).get(event, 0)


class Run:

    # 参数设置
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.data = None
        self.arg_init()

    def arg_init(self):
        self.parser.add_argument('-i', '--init', type=str)
        self.parser.add_argument('-u', '--user', type=str)
        self.parser.add_argument('-r', '--repo', type=str)
        self.parser.add_argument('-e', '--event', type=str)

    def analyse(self):
        args = self.parser.parse_args()

        self.data = Data()
        if args.init:
            self.data.init(args.init)
            return 'init done'
        self.data.load()

        if not args.event:
            raise RuntimeError('error: the following arguments are required: -e/--event')
        if not args.user and not args.repo:
            raise RuntimeError('error: the following arguments are required: -u/--user or -r/--repo')

        if args.user and args.repo:
            res = self.data.get_user_repo(args.user, args.repo, args.event)
        elif args.user:
            res = self.data.get_user(args.user, args.event)
        else:
            res = self.data.get_repo(args.repo, args.event)
        return res


if __name__ == '__main__':
    a = Run()
    print(a.analyse())
