#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
debug 工具
"""

# 保存抛出的异常，相同的异常不再记录，发送日志
EXCEPTION_CACHE = set()


def _get_lines_from_file(filename, lineno, context_lines, loader=None, module_name=None):
    """
    根据文件名和行数，获取 lineno 所在行的上下 context_lines 行代码
    Returns context_lines before and after lineno from file.
    Returns (pre_context_lineno, pre_context, context_line, post_context).
    """
    source = None
    if loader is not None and hasattr(loader, "get_source"):
        try:
            source = loader.get_source(module_name)
        except ImportError:
            pass
        if source is not None:
            source = source.splitlines()
    if source is None:
        try:
            with open(filename, 'rb') as fp:
                source = fp.read().splitlines()
        except (OSError, IOError):
            pass
    if source is None:
        return None, [], None, []

    lower_bound = max(0, lineno - context_lines)
    upper_bound = lineno + context_lines

    pre_context = source[lower_bound:lineno]
    context_line = source[lineno]
    post_context = source[lineno + 1:upper_bound]

    return lower_bound, pre_context, context_line, post_context


def get_traceback_context(exc_info):
    frames = []
    t, v, tb = exc_info
    while tb is not None:
        # Support for __traceback_hide__ which is used by a few libraries
        # to hide internal frames.
        if tb.tb_frame.f_locals.get('__traceback_hide__'):
            tb = tb.tb_next
            continue
        filename = tb.tb_frame.f_code.co_filename
        function = tb.tb_frame.f_code.co_name
        lineno = tb.tb_lineno - 1
        loader = tb.tb_frame.f_globals.get('__loader__')
        module_name = tb.tb_frame.f_globals.get('__name__') or ''
        pre_context_lineno, pre_context, context_line, post_context = _get_lines_from_file(filename, lineno, 7, loader, module_name)
        if pre_context_lineno is not None:
            frames.append({
                'tb': tb,
                'type': 'django' if module_name.startswith('django.') else 'user',
                'filename': filename,
                'function': function,
                'lineno': lineno + 1,
                'vars': tb.tb_frame.f_locals,
                'id': id(tb),
                'pre_context': pre_context,
                'context_line': context_line,
                'post_context': post_context,
                'pre_context_lineno': pre_context_lineno + 1,
            })
        tb = tb.tb_next

    return {
        "frames": frames,
        "exception": v,
    }


def get_debug_context(exc_info, unique=True):
    """
    获取捕获到的异常的信息

    :param exc_info: 最近捕获的异常信息
    :param unique: 是否同一个异常只捕获一次
    :return:
    """
    context = get_traceback_context(exc_info)
    if unique:
        frames = context["frames"]
        last_frame = frames[-1]
        exception = context["exception"]
        lineno = last_frame["lineno"]
        filename = last_frame["filename"]
        unique_key = "%s_%s_%s" % (filename, lineno, repr(exception))
        if unique_key in EXCEPTION_CACHE:
            return {}
        EXCEPTION_CACHE.add(unique_key)
    return context
