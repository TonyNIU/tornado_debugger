#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web
import tornado.wsgi
import tornado.ioloop
from tornado.options import options, define

from werkzeug.serving import run_simple
from werkzeug.debug.tbtools import get_current_traceback
from werkzeug.debug import DebuggedApplication


define("debug", default=True, type=bool)


class Handler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        if options.debug:
            debugger = self.application.debugger
            traceback = get_current_traceback()
            html = traceback.render_full(evalex=True,
                                         secret=debugger.secret)
            for frame in traceback.frames:
                debugger.frames[frame.id] = frame
            debugger.tracebacks[traceback.id] = traceback
            self.write(html.encode('utf-8', 'replace'))
        else:
            super(Handler, self).write_error(status_code, **kwargs)


class DebugApplication(DebuggedApplication):
    def __init__(self, app, *args, **kwargs):
        app.debugger = self
        super(DebugApplication, self).__init__(app, *args, **kwargs)


class IndexHandler(Handler):
    def get(self):
        self.write("hello world")


class ErrorHandler(Handler):
    def get(self):
        a = 1
        b = 0
        c = a / b
        self.write("hello world")


def main():
    handlers = [
        ('/$', IndexHandler),
        ('/error$', ErrorHandler),
    ]

    if options.debug:
        application = DebugApplication(tornado.wsgi.WSGIApplication(handlers), evalex=True)
        run_simple("0.0.0.0", 8800, application)
    else:
        application = tornado.web.Application(handlers)
        application.listen(8800)
        tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()