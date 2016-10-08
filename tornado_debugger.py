#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.ioloop
import tornado.web
import tornado.wsgi
from lib.mail import Mail
from tornado.gen import coroutine
from tornado.httpclient import AsyncHTTPClient
from tornado.options import options, define
from tornado.wsgi import WSGIContainer
from werkzeug.debug import DebuggedApplication
from werkzeug.debug.tbtools import get_current_traceback

from lib.debug import get_debug_context
from settings import EXCEPTION_REPORT_SMTP, EXCEPTION_REPORT_PASSWORD, EXCEPTION_REPORT_ACCOUNT, \
    EXCEPTION_REPORT_RECEIVERS, EXCEPTION_DEBUGGABLE

define("debug", default=True, type=bool)
options.parse_command_line()


class BaseHandler(tornado.web.RequestHandler):
    debug_application = None
    wsgi_container = None

    def initialize(self):
        if options.debug:
            if not self.debug_application:
                self.__class__.debug_application = DebuggedApplication(self.application, evalex=True)
                self.__class__.wsgi_container = WSGIContainer(self.debug_application)

            if '__debugger__' in self.request.uri:
                return self.wsgi_container(self.request)
        else:
            super(BaseHandler, self).initialize()

    def render_exception(self):
        traceback = get_current_traceback()

        for frame in traceback.frames:
            self.debug_application.frames[frame.id] = frame
        self.debug_application.tracebacks[traceback.id] = traceback

        return traceback.render_full(evalex=True,
                                     secret=self.debug_application.secret)

    def alarm_exception(self, exc_info):
        """
        发送邮件,报警

        :param exc_info:
        :return:
        """
        context = get_debug_context(exc_info)
        t, v, tb = exc_info
        if context:
            context["arguments"] = self.request.arguments
            context["url"] = self.request.uri
            context["cookies"] = self.cookies
            debug_url = "%s://%s%s" % (self.request.protocol, self.request.host, self.request.uri)
            if "?" in self.request.uri:
                if self.request.uri.endswith("?"):
                    debug_url += "debugging=debugging"
                else:
                    debug_url += "&debugging=debugging"
            else:
                debug_url += "?debugging=debugging"
            context["debug_url"] = debug_url if EXCEPTION_DEBUGGABLE else ""
            html = self.render_string("templates/error.html", **context)

            mail = Mail(EXCEPTION_REPORT_SMTP, EXCEPTION_REPORT_ACCOUNT, EXCEPTION_REPORT_PASSWORD)
            subject = repr(v) if v else "代码异常"
            mail.send(subject,
                      html,
                      EXCEPTION_REPORT_RECEIVERS,
                      plugins=[{'subject': '%s.html' % (v.__class__.__name__
                                                        if v else "error"),
                                'content': html}])

    def write_error(self, status_code, **kwargs):
        exc_info = kwargs["exc_info"]
        if options.debug and EXCEPTION_DEBUGGABLE:
            if self.get_argument("debugging", "") != "debugging":
                self.alarm_exception(exc_info)
                super(BaseHandler, self).write_error(status_code, **kwargs)
            else:
                html = self.render_exception()
                self.write(html.encode('utf-8', 'replace'))
        else:
            super(BaseHandler, self).write_error(status_code, **kwargs)


class IndexHandler(BaseHandler):
    def get(self):
        self.write("hello world")


class AsyncHandler(BaseHandler):
    @coroutine
    def get(self):
        resp = yield AsyncHTTPClient().fetch("http://www.baidu.com")
        self.write(resp.body)


class ErrorHandler(BaseHandler):
    def get(self):
        raise Exception("测试")
        self.write("hello world")


def main():
    handlers = [
        ('/$', IndexHandler),
        ('/async$', AsyncHandler),
        ('/error$', ErrorHandler),
    ]
    application = tornado.web.Application(handlers)
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()