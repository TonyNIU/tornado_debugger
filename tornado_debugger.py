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
    def write_error(self, status_code, **kwargs):
        if options.debug:
            html = self.application.render_exception()
            self.write(html.encode('utf-8', 'replace'))
        else:
            super(BaseHandler, self).write_error(status_code, **kwargs)


class RequestDispatcher(tornado.web._RequestDispatcher):
    def set_request(self, request):
        super(RequestDispatcher, self).set_request(request)
        if '__debugger__' in request.uri:
            return self.application.wsgi_container(request)


class DebugApplication(tornado.web.Application):
    def __init__(self, *args, **kwargs):
        super(DebugApplication, self).__init__(*args, **kwargs)
        self.debugger = DebuggedApplication(self, evalex=True)
        self.wsgi_container = WSGIContainer(self.debugger)

    def start_request(self, connection):
        return RequestDispatcher(self, connection)

    def render_exception(self):
        traceback = get_current_traceback()

        for frame in traceback.frames:
            self.debugger.frames[frame.id] = frame
        self.debugger.tracebacks[traceback.id] = traceback

        return traceback.render_full(evalex=True,
                                     secret=self.debugger.secret)


class IndexHandler(BaseHandler):
    def get(self):
        self.write("hello world")


class AsyncHandler(BaseHandler):
    @coroutine
    def get(self):
        resp = yield AsyncHTTPClient().fetch("http://cpython.net")
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
    if options.debug:
        application = DebugApplication(handlers)
    else:
        application = tornado.web.Application(handlers)
    application.listen(8800)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()