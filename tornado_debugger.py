#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web
import tornado.wsgi
import tornado.ioloop
from tornado.httpclient import AsyncHTTPClient
from tornado.gen import coroutine
from tornado.options import options, define
from tornado.wsgi import WSGIContainer
from werkzeug.debug.tbtools import get_current_traceback
from werkzeug.debug import DebuggedApplication


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

    def write_error(self, status_code, **kwargs):
        if options.debug:
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