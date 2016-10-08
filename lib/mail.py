#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
send mail
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


class Mail(object):
    """
    邮件操作类
    """

    def __init__(self, smtp, user, pwd):
        """
        初始化
        :param smtp: SMTP服务器
        :param user: 用户名
        :param pwd: 密码
        return: None
        """
        self.smtp = smtp
        self.user = user
        self.pwd = pwd
        self.isauth = True

    def send(self, subject, content, tolist, cclist=None, plugins=None):
        """
        发送邮件
        :param subject: 标题
        :param content: 内容
        :param tolist: 收件人列表
        :param cclist: 抄送人列表
        :param plugins: 附件列表
        return: 是否发送成功
        """
        # 构造邮件消息
        msg = MIMEMultipart()
        msg.set_charset('utf-8')
        msg['from'] = self.user
        msg['to'] = ','.join(tolist)
        if cclist:
            msg['cc'] = ','.join(cclist)
        msg['subject'] = subject
        msg.attach(MIMEText(content, 'html', 'utf-8'))
        if plugins:
            for i in plugins:
                f = MIMEApplication(i['content'])
                f.add_header('content-disposition', 'attachment', filename=i['subject'])
                msg.attach(f)

        # 连接SMTP服务器
        s = smtplib.SMTP(self.smtp)
        s.set_debuglevel(smtplib.SMTP.debuglevel)
        if self.isauth:
            s.docmd('EHLO %s' % self.smtp)
        try:
            s.starttls()
        except smtplib.SMTPException, e:
            logging.error('fail to starttls: %s', str(e), exc_info=True)
        s.login(self.user, self.pwd)
        r = s.sendmail(self.user, tolist, msg.as_string())
        s.close()
        return r


if __name__ == '__main__':
    mail = Mail('smtp.exmail.qq.com', '*******', '*******')
    mail.send('发送邮件测试',
              ['****'],
              None,
              [{'subject': '附件.txt', 'content': '附件内容'}])
    print('mail send')
