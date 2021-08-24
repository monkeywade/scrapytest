#!/usr/bin/env python
# -*- coding:utf-8 -*-
import commands
import json
import os
import signal
import sys
import ConfigParser
import thread
import traceback
import time
import datetime
import logging
import re
import requests
from logging.handlers import RotatingFileHandler

__VERSION__ = "1.0.0"
SCRIPT_NAME = "log_transfer"
logger = logging.getLogger(__name__)
SCRIPT_SIGNAL_STOPPED = False
PACKAGE_TASK_STOPPED = False
UPLOAD_TASK_STOPPED = False
IP = os.popen("hostname -I").read().split()[0]


# 日志配置
def set_logging(enable_console=False):
    file_dir = os.path.dirname(os.path.realpath(__file__))
    log_dir = file_dir + "/logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logfile_dir = log_dir + "/%s.log" % SCRIPT_NAME
    formatter = logging.Formatter(fmt="%(asctime)s | %(levelname)s | %(threadName)s | %(filename)s:%(lineno)d | - %(message)s")
    file_handler = RotatingFileHandler(logfile_dir, mode="a", maxBytes=20 * 1024 * 1024, backupCount=3, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)


# 自动获取当前所在的aws地区
def get_current_aws_region():
    aws_url = "http://169.254.169.254/latest/dynamic/instance-identity/document"
    try:
        res = requests.get(aws_url, timeout=10)
        res.encoding = "utf-8"
        res.raise_for_status()
    except requests.HTTPError as e:
        logger.error("failed to get current region, %s, url=%s, res=%s" % (e, aws_url, res.text))
    except Exception as e:
        logger.error("failed to get current region, %s, url=%s" % (e, aws_url))
    else:
        region = json.loads(res.text)["region"]
        return region


# 日志上传功能的实现类
class LogTransfer(object):

    def __init__(self, s3_region, s3_bucket, module_paths, module_path_tags,
                 package_backup_file_number_threshold, package_schedule_seconds, upload_schedule_seconds):
        # s3日志存储桶
        self.s3_bucket = s3_bucket
        # s3日志存储桶所在地区
        self.s3_region = s3_region
        # 打包定时任务周期
        self.package_schedule_seconds = package_schedule_seconds
        # 达到多少个文件进行打包
        self.package_backup_file_number_threshold = package_backup_file_number_threshold
        self.package_immediately_date = {}
        # 上传定时任务周期
        self.upload_schedule_seconds = upload_schedule_seconds
        # 模块所在的路径
        self.module_paths = module_paths
        self.module_path_tags = module_path_tags
        # 脚本路径
        file_dir = os.path.dirname(os.path.realpath(__file__))
        # 临时日志文件夹
        self.dir_tmp_logs = file_dir + "/tmp"
        if not os.path.exists(self.dir_tmp_logs):
            os.makedirs(self.dir_tmp_logs)
        # zip文件夹
        self.dir_zips = file_dir + "/zips"
        if not os.path.exists(self.dir_zips):
            os.makedirs(self.dir_zips)
        # 模块路径名称格式
        self.reg_module_name = re.compile(r"^-([a-zA-Z0-9]+)$")
        # 模块版本路径名称格式
        self.reg_module_name_version = re.compile(r"^-([a-zA-Z0-9]+)-[0-9]+\.[0-9]+\.[0-9]+$")
        # 日志文件名称格式
        self.reg_module_log_name = re.compile(r"^-([a-zA-Z0-9-_]+)\.log$")
        # zip日志文件名称格式
        self.reg_zip_file_name = re.compile(r"^.+_\[([0-9]{4}-[0-9]{2}-[0-9]{2})_[0-9:]+\]_\[([0-9]{4}-[0-9]{2}-[0-9]{2})_[0-9:]+\].zip$")
        # 日志日期时间格式
        self.reg_log_time = "[0-9]{4}(-[0-9]{2}){2}.[0-2][0-9](:[0-5][0-9]){2}"
        logger.info("LogTransfer initialized, region: %s, bucket: %s, module_paths:%s" % (self.s3_region, self.s3_bucket, self.module_paths))

    # 打包的定时任务
    def run_package_schedule_task(self):
        global SCRIPT_SIGNAL_STOPPED
        global PACKAGE_TASK_STOPPED
        cur_timestamp = int(time.time())
        next_timestamp = cur_timestamp
        while True:
            if cur_timestamp >= next_timestamp:
                logger.info("run package schedule task")
                for path_key in self.module_paths:
                    path = self.module_paths[path_key]
                    if not os.path.isdir(path):
                        continue
                    try:
                        path_tag = None
                        if path_key in self.module_path_tags:
                            path_tag = self.module_path_tags[path_key]
                        package_immediately = self.__is_package_immediately()
                        self.package_in_path(path_tag, path, package_immediately)
                    except Exception as e:
                        logger.error("an error occurred in package in path %s, %s" %(path, traceback.format_exc()))
                    cur_timestamp = int(time.time())
                    next_timestamp = cur_timestamp + self.package_schedule_seconds
            time.sleep(5)
            cur_timestamp += 5
            if SCRIPT_SIGNAL_STOPPED:
                PACKAGE_TASK_STOPPED = True
                logger.info("package schedule task stopped")
                break

    # 打包
    def package_in_path(self, path_tag, path, package_immediately):
        for module_name_dir_name in os.listdir(path):
            module_name_match = re.match(self.reg_module_name, module_name_dir_name)
            if not module_name_match:
                continue
            module_name_dir_path = os.path.join(path, module_name_dir_name)
            if not os.path.isdir(module_name_dir_path):
                continue
            module_name = module_name_match.group(1)
            for module_name_version_dir_name in os.listdir(module_name_dir_path):
                if not re.match(self.reg_module_name_version, module_name_version_dir_name):
                    continue
                module_name_version_dir_path = os.path.join(module_name_dir_path, module_name_version_dir_name)
                if not os.path.isdir(module_name_version_dir_path):
                    continue
                # module_logs_path = os.path.join(module_name_version_dir_path, "logs")
                module_logs_path = module_name_version_dir_path
                module_log_names = self.find_module_log_name(module_logs_path)
                self.package_module_logs(module_name, module_logs_path, module_log_names, path_tag, package_immediately)

    # 打包指定目录下的模块日志文件
    def package_module_logs(self, module_name, module_logs_path, module_log_names, path_tag, package_immediately):
        for module_log_name in module_log_names:
            # 判断备份日志文件个数是否达到打包的条件
            check_log_count_cmd = "ls %s/%s.* 2>/dev/null|wc -l" %(module_logs_path, module_log_name)
            backup_log_count = int(commands.getoutput(check_log_count_cmd))
            logger.info("found %s %s backup log file in %s" %(backup_log_count, module_log_name, module_logs_path))
            if backup_log_count == 0:
                continue
            if (backup_log_count < self.package_backup_file_number_threshold) and (not package_immediately):
                continue
            module_tmp_logs_dir = "%s/%s" %(self.dir_tmp_logs, module_name)
            if not os.path.isdir(module_tmp_logs_dir):
                os.makedirs(module_tmp_logs_dir)
            # 移动到临时文件夹下
            mv_cmd = "mv %s/%s.* %s" %(module_logs_path, module_log_name, module_tmp_logs_dir)
            status, output = commands.getstatusoutput(mv_cmd)
            if status != 0:
                logger.error("failed to execute mv command: %s, status=%s, output=%s" % (mv_cmd, status, output))
                continue
            else:
                logger.info("mv success: %s" % mv_cmd)
            # 按时间排序合并多个备份的日志文件
            merge_log_file_name = "merged_%s" % module_log_name
            merge_log_file_path = os.path.join(module_tmp_logs_dir, merge_log_file_name)
            merge_cmd = "find %s -name %s.*|xargs ls -rt|xargs cat > %s" %(module_tmp_logs_dir, module_log_name, merge_log_file_path)
            status, output = commands.getstatusoutput(merge_cmd)
            if status != 0:
                logger.error("failed to execute merge command: %s, status=%s, output=%s" % (merge_cmd, status, output))
                continue
            else:
                logger.info("merge success: %s" % merge_cmd)
            # 删除备份的日志文件
            rm_cmd = "rm %s/%s.*" %(module_tmp_logs_dir, module_log_name)
            status, output = commands.getstatusoutput(rm_cmd)
            if status != 0:
                logger.error("failed to execute remove command: %s, status=%s, output=%s" % (rm_cmd, status, output))
                continue
            else:
                logger.info("remove success: %s" % rm_cmd)
            # 解析出开始和结束时间
            line_count_cmd = 'wc -l %s|awk \'{print $1}\'' %(merge_log_file_path)
            line_count = int(commands.getoutput(line_count_cmd))
            start_time_cmd = 'head -n %d ' + merge_log_file_path + '|grep -Eo "%s"' % (self.reg_log_time)
            log_start = self.__find_logtime_str(start_time_cmd, line_count)
            end_time_cmd = 'tail -n %d ' + merge_log_file_path + '| grep -Eo "%s"' % (self.reg_log_time)
            log_end = self.__find_logtime_str(end_time_cmd, line_count)
            # 重命名合并后的日志文件
            tag = ""
            if path_tag is not None:
                tag = "_%s" % path_tag
            renamed_log_file_name = "%s%s_%s_[%s]_[%s].log" % (module_log_name.replace(".log", ""), tag, IP, log_start, log_end)
            renamed_log_file_path = "%s/%s" % (module_tmp_logs_dir, renamed_log_file_name)
            rename_cmd = "mv %s %s" % (merge_log_file_path, renamed_log_file_path)
            status, output = commands.getstatusoutput(rename_cmd)
            if status != 0:
                logger.error("failed to execute rename command: %s, status=%s, output=%s" % (rename_cmd, status, output))
                continue
            else:
                logger.info("rename success: %s" % rename_cmd)
            # 压缩合并后的日志文件
            module_zip_logs_dir = "%s/%s" %(self.dir_zips, module_name)
            if not os.path.isdir(module_zip_logs_dir):
                os.makedirs(module_zip_logs_dir)
            target_zip_file_path = "%s/%s" %(module_zip_logs_dir, renamed_log_file_name.replace(".log", ".zip"))
            zip_cmd = "zip -rj %s %s" %(target_zip_file_path, renamed_log_file_path)
            status, output = commands.getstatusoutput(zip_cmd)
            if status != 0:
                logger.error("failed to execute zip command: %s, status=%s, output=%s" % (zip_cmd, status, output))
                continue
            else:
                logger.info("zip success: %s" % zip_cmd)
            # 删除压缩前的日志文件
            rm_cmd = "rm %s" % renamed_log_file_path
            status, output = commands.getstatusoutput(rm_cmd)
            if status != 0:
                logger.error("failed to execute remove command: %s, status=%s, output=%s" % (rm_cmd, status, output))
                continue
            else:
                logger.info("remove success: %s" % rm_cmd)

    # 每天凌晨2点将备份文件打包上传一次
    def __is_package_immediately(self):
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        hour_str = datetime.datetime.now().strftime("%H")
        if hour_str == "02":
            if date_str not in self.package_immediately_date:
                self.package_immediately_date = {}
                self.package_immediately_date.update({date_str: True})
                return True
        return False

    # 解析日志文件的时间字符串
    def __find_logtime_str(self, find_time_cmd, line_count):
        timestamp = None
        line_number = 1
        while (not timestamp and line_number <= line_count):
            find_in_line_cmd = find_time_cmd % (line_number)
            timestamps = commands.getoutput(find_in_line_cmd)
            timestamp = timestamps.split(os.linesep)[0]
            line_number += 1
        if timestamp is None:
            return datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        return timestamp.replace(' ', '_')

    # 查找目录下符合打包规范的日志文件名
    def find_module_log_name(self, module_logs_path):
        module_log_names = []
        for log_file_name in os.listdir(module_logs_path):
            log_file_path = os.path.join(module_logs_path, log_file_name)
            if not os.path.isfile(log_file_path):
                continue
            if not re.match(self.reg_module_log_name, log_file_name):
                continue
            if log_file_name.endswith("-error.log") or log_file_name.endswith("-Error.log"):
                continue
            module_log_names.append(log_file_name)
        return module_log_names

    # 上传s3的定时任务
    def run_upload_schedule_task(self):
        global SCRIPT_SIGNAL_STOPPED
        global UPLOAD_TASK_STOPPED
        cur_timestamp = int(time.time())
        next_timestamp = cur_timestamp
        while True:
            if cur_timestamp >= next_timestamp:
                logger.info("run upload schedule task")
                # 扫描各模块下的压缩文件夹
                for module_name in os.listdir(self.dir_zips):
                    module_zips_path = os.path.join(self.dir_zips, module_name)
                    if not os.path.isdir(module_zips_path):
                        continue
                    try:
                        self.upload_module_zip_logs(module_name, module_zips_path)
                    except Exception as e:
                        logger.error("an error occurred in upload module zip logs %s, %s" %(module_zips_path, traceback.format_exc()))
                cur_timestamp = int(time.time())
                next_timestamp = cur_timestamp + self.upload_schedule_seconds
            time.sleep(5)
            cur_timestamp += 5
            if SCRIPT_SIGNAL_STOPPED:
                UPLOAD_TASK_STOPPED = True
                logger.info("upload schedule task stopped")
                break

    # 上传模块的zip日志文件
    def upload_module_zip_logs(self, module_name, module_zips_path):
        for log_file in os.listdir(module_zips_path):
            zip_file_path = os.path.join(module_zips_path, log_file)
            if not log_file.endswith(".zip") or not os.path.isfile(zip_file_path):
                continue
            # yyyy/mm/dd
            is_match = re.match(self.reg_zip_file_name, log_file)
            if not is_match:
                continue
            log_date = is_match.group(1).replace("-", "/")
            target_s3_path = "s3://%s/-%s/%s/" % (self.s3_bucket, module_name, log_date)
            logger.info("uploading %s to %s" % (zip_file_path, target_s3_path))
            upload_s3_cmd = "aws s3 cp %s %s --region %s --storage-class STANDARD_IA" % (zip_file_path, target_s3_path, self.s3_region)
            status, output = commands.getstatusoutput(upload_s3_cmd)
            if status == 0:
                logger.info("upload %s to %s success" % (zip_file_path, target_s3_path))
                os.remove(zip_file_path)
            else:
                logger.error("failed to execute upload s3 command: %s, status=%s, output=%s" % (upload_s3_cmd, status, output))
                if self.check_disk_usage_percent_reach_threshold():
                    logger.warn("disk usage percent reach threshold, remove %s" % zip_file_path)
                    os.remove(zip_file_path)


    def check_disk_usage_percent_reach_threshold(self):
        try:
            disk_usage_percent_cmd = "df -h /|awk 'END{print $(NF-1)}'|awk -F '%' '{print $1}'"
            percent = int(commands.getoutput(disk_usage_percent_cmd))
            if percent > 95:
                logger.info("current disk usage: %s" % percent)
                return True
        except Exception as e:
            logger.error("an error occurred while check disk usage, %s" % e)
        return False


def read_config():
    cfg_file = os.sep + "conf" + os.sep + "%s.conf" % SCRIPT_NAME
    cfg_file_path = os.path.dirname(os.path.realpath(__file__)) + cfg_file
    if not os.path.exists(cfg_file_path):
        logger.error("config file not exist: %s" % cfg_file_path)
        sys.exit(1)
    cfg = ConfigParser.ConfigParser()
    cfg.read(cfg_file_path)
    return cfg


def check_environment():
    check_aws_cmd = "aws --version"
    status, output = commands.getstatusoutput(check_aws_cmd)
    logger.info("check if awscli installed, %s, status=%s, output=%s" % (check_aws_cmd, status, output))
    if status != 0:
        return False
    check_zip_cmd = "zip -h"
    status, output = commands.getstatusoutput(check_zip_cmd)
    logger.info("check if zip installed, %s, status=%s" % (check_aws_cmd, status))
    if status != 0:
        return True


# 脚本接收到kill信号
def onsignal_term(signum, frame):
    logger.info("process received SIGTERM")
    global SCRIPT_SIGNAL_STOPPED
    SCRIPT_SIGNAL_STOPPED = True


# 主函数
def main():
    global SCRIPT_SIGNAL_STOPPED
    global PACKAGE_TASK_STOPPED
    global UPLOAD_TASK_STOPPED
    set_logging(enable_console=False)
    signal.signal(signal.SIGTERM, onsignal_term)
    signal.signal(signal.SIGINT, onsignal_term)

    if check_environment():
        logger.error("check required environment error")
        sys.exit(1)
    # 获取当前环境所在的aws地区
    current_aws_region = get_current_aws_region()
    if current_aws_region is None:
        sys.exit(1)
    # 读取脚本的配置文件
    log_transfer_config = read_config()
    # aws地区名称和s3桶映射关系
    aws_region_s3_buckets_dic = {}
    for item in log_transfer_config.items("region-s3-buckets"):
        aws_region = item[0].strip()
        s3_bucket_name = item[1].strip()
        aws_region_s3_buckets_dic.update({aws_region: s3_bucket_name})
    if current_aws_region not in aws_region_s3_buckets_dic:
        logger.error("invalid region %s" % current_aws_region)
        sys.exit(1)
    # 模块路径配置
    module_paths = {}
    s = set()
    for item in log_transfer_config.items("module-paths"):
        key = item[0].strip()
        path = item[1].strip()
        if not os.path.isdir(path):
            logger.error("invalid module path %s" % path)
            sys.exit(1)
        if path in s:
            logger.error("duplicate module path %s" % path)
            sys.exit(1)
        s.add(path)
        module_paths.update({key: path})
    # 多个模块路径时，添加用于区分的文件名称标识
    module_path_tags = {}
    for item in log_transfer_config.items("module-path-tags"):
        key = item[0].strip()
        tag = item[1].strip()
        module_path_tags.update({key: tag})
    # 上传的s3桶名称
    s3_bucket = aws_region_s3_buckets_dic[current_aws_region]
    # 打包定时任务周期
    package_schedule_seconds = max(30, log_transfer_config.getint("package", "schedule-seconds"))
    # 备份文件达到多少个进行打包
    package_backup_file_number_threshold = max(20, log_transfer_config.getint("package", "backup-file-number-threshold"))
    # 上传定时任务周期
    upload_schedule_seconds = max(30, log_transfer_config.getint("upload", "schedule-seconds"))

    # 初始化日志上传实现类
    log_file_manager = LogTransfer(current_aws_region, s3_bucket, module_paths, module_path_tags,
                                   package_backup_file_number_threshold, package_schedule_seconds, upload_schedule_seconds)
    # 启动日志打包定时任务线程
    thread.start_new_thread( log_file_manager.run_package_schedule_task, ())
    # 启动日志上传定时任务线程
    thread.start_new_thread( log_file_manager.run_upload_schedule_task, ())

    while True:
        time.sleep(5)
        if SCRIPT_SIGNAL_STOPPED and PACKAGE_TASK_STOPPED and UPLOAD_TASK_STOPPED:
            logger.info("script exited.")
            break


if __name__ == "__main__":
    try:
        logging.info("Begin")
        main()
    except Exception as Ex:
        logger.error("internal server error, %s" % traceback.format_exc())

