# coding: utf-8

"""命令行火车票查看器

Usage:
    tickets [-gdtkzs] <from> <to> <date>

Options:
    -h,--help   显示帮助菜单
    -g          高铁
    -d          动车
    -t          特快
    -k          快速
    -z          直达
    -s          查找学生票

Example:
    tickets 北京 上海 2016-10-10
    tickets -dg 成都 南京 2016-10-10
"""

from docopt import docopt
from stations import stations
from prettytable import PrettyTable
from colorama import init, Fore
import requests
import datetime

class TrainsCollection:

    header = '车次 车站 时间 历时 一等 二等 软卧 硬卧 硬座 无座'.split()

    def __init__(self, available_trains, options):
        """查询到的火车班次集合

        :param available_trains: 一个列表, 包含可获得的火车班次, 每个
                                 火车班次是一个字典
        :param options: 查询的选项, 如高铁, 动车, etc...
        """
        self.available_trains = available_trains
        self.options = options

    def _get_duration(self, raw_train):
        duration = raw_train.get('lishi').replace(':', '小时') + '分'
        #排除停运车次
        if raw_train['start_time'] == raw_train['arrive_time']:
        	duration = '暂 不 运 行'
        if duration.startswith('00'):
            return duration[4:]
        if duration.startswith('0'):
            return duration[1:]
        return duration

    @property
    def trains(self):
        for raw_train in self.available_trains:
            train_no = raw_train['station_train_code']
            #取车次的首位，即为该车次类型
            initial = train_no[0].lower()
            if not self.options or initial in self.options:
                train = [
                    train_no,
                    #对始发站，始发时间，到达站，到达时间上色        
                    '\n'.join([Fore.BLUE + raw_train['from_station_name'] + Fore.RESET,
                              Fore.RED + raw_train['to_station_name'] + Fore.RESET]),
                    '\n'.join([Fore.BLUE + raw_train['start_time'] + Fore.RESET,
                              Fore.RED + raw_train['arrive_time'] + Fore.RESET]),
                    self._get_duration(raw_train),
                    raw_train['zy_num'],
                    raw_train['ze_num'],
                    raw_train['rw_num'],
                    raw_train['yw_num'],
                    raw_train['yz_num'],
                    raw_train['wz_num'],
                ]
                yield train

    def pretty_print(self):
        pt = PrettyTable()
        pt._set_field_names(self.header)
        for train in self.trains:
            pt.add_row(train)
        print(pt)

def cli():
    """command-line interface"""
    arguments = docopt(__doc__)
    
    #处理输入始发站和到达站
    if (arguments['<from>'] in stations)==False:
    	err('始发站错输入错误')
    	return
    from_station = stations.get(arguments['<from>'])

    if (arguments['<to>'] in stations)==False:
    	err('到达站输入错误')
    	return
    to_station = stations.get(arguments['<to>'])

    #处理输入日期，如早于当天则不能查询
    inputdate = arguments['<date>'].split("-")
    year = int(inputdate[0])
    month = int(inputdate[1])
    day = int(inputdate[2])
    date = datetime.date(year,month,day)	
    
    if datetime.date.today() > date:
    	err('无法查询今天之前的车次')
    	return

    #判断是否请求学生票
    if arguments.get("-s") == False:
        people = 'ADULT'
    else:
        people = '0X00'

    url = 'https://kyfw.12306.cn/otn/lcxxcx/query?purpose_codes={}&queryDate={}&from_station={}&to_station={}'.format(
    	people, date, from_station, to_station
    	)
    #print(url)

    #将值为true的选项组合成options
    options = ''.join([
        key for key, value in arguments.items() if value is True
    ])
    #print(options)
    r = requests.get(url, verify=False)
    available_trains = r.json()['data']['datas']
    TrainsCollection(available_trains, options).pretty_print()

def err(msg):
	print('错误：' + msg)

#def print_log(msg)


init()

if __name__ == '__main__':
    cli()
