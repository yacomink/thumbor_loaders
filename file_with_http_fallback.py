#!/usr/bin/python
# -*- coding: utf-8 -*-

import thumbor.loaders.http_loader

from os.path import join, exists, abspath
from urllib import unquote

import re
from urlparse import urlparse
from functools import partial

import tornado.httpclient

from thumbor.utils import logger

def load(context, path, callback):
    file_path = join(context.config.FILE_LOADER_ROOT_PATH.rstrip('/'), unquote(path).lstrip('/'))
    file_path = abspath(file_path)
    inside_root_path = file_path.startswith(context.config.FILE_LOADER_ROOT_PATH)

    if inside_root_path and exists(file_path):
        with open(file_path, 'r') as f:
            callback(f.read())
    else:
    	http_load(context, 'http://s.buzzfed.com/' + path, callback)


def return_contents(response, url, callback):
    if response.error:
        logger.warn("ERROR retrieving image {0}: {1}".format(url, str(response.error)))
        callback(None)
    elif response.body is None or len(response.body) == 0:
        logger.warn("ERROR retrieving image {0}: Empty response.".format(url))
        callback(None)
    else:
        callback(response.body)


def http_load(context, url, callback):
    if context.config.HTTP_LOADER_PROXY_HOST and context.config.HTTP_LOADER_PROXY_PORT:
        tornado.httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    client = tornado.httpclient.AsyncHTTPClient()

    user_agent = None
    if context.config.HTTP_LOADER_FORWARD_USER_AGENT:
        if 'User-Agent' in context.request_handler.request.headers:
            user_agent = context.request_handler.request.headers['User-Agent']
    if user_agent is None:
        user_agent = context.config.HTTP_LOADER_DEFAULT_USER_AGENT

    req = tornado.httpclient.HTTPRequest(
        url=encode(url),
        connect_timeout=context.config.HTTP_LOADER_CONNECT_TIMEOUT,
        request_timeout=context.config.HTTP_LOADER_REQUEST_TIMEOUT,
        follow_redirects=context.config.HTTP_LOADER_FOLLOW_REDIRECTS,
        max_redirects=context.config.HTTP_LOADER_MAX_REDIRECTS,
        user_agent=user_agent,
        proxy_host=encode(context.config.HTTP_LOADER_PROXY_HOST),
        proxy_port=context.config.HTTP_LOADER_PROXY_PORT,
        proxy_username=encode(context.config.HTTP_LOADER_PROXY_USERNAME),
        proxy_password=encode(context.config.HTTP_LOADER_PROXY_PASSWORD)
    )

    client.fetch(req, callback=partial(return_contents, url=url, callback=callback))

def encode(string):
    return None if string is None else string.encode('ascii')
