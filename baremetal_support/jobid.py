# Copyright (C) 2020-2021 SUSE LLC
# SPDX-License-Identifier: GPL-3.0

import os
import bottle
import socket
from openqa_client.client import OpenQA_Client


class LatestJobNotFound(Exception):
    """Raised when no job is found"""
    pass


class LatestJob:
    def __init__(self, app, logger, instance='http://openqa.suse.de'):
        route = '/v1/latest_job/<arch>/<distri>/<flavor>/<version>/<test>'
        self.bootscript = {}
        self._instance = instance
        self._app = app
        self.log = logger
        self._app.route(route,
                        method="GET",
                        callback=self.http_get_latest_job)

    def get_latest_job(self, filter):
        try:
            client = OpenQA_Client(server=self._instance)
            result = client.openqa_request('GET', 'jobs', filter)
            jobs = sorted(result['jobs'], key=lambda x: str(x['t_finished']))
            if jobs:
                return ([[job] for job in jobs if job['result']
                        in ['passed', 'softfailed']][-1][0])
            else:
                raise LatestJobNotFound("no such job found")
        except Exception:
            raise LatestJobNotFound("no such job found")

    def http_get_latest_job(self, arch, distri, flavor, version, test):
        filter = {}
        filter['arch'] = arch
        filter['distri'] = distri
        filter['flavor'] = flavor
        filter['version'] = version
        filter['test'] = test
        self.log.info("HTTP: get latest job for " + distri + " " + version
                      + " " + arch + " " + flavor + " " + test)
        try:
            job = self.get_latest_job(filter)
            bottle.response.content_type = 'text/text; charset=utf-8'
            result = job['id']
            self.log.info("found job with ID " + result)
            return str(result)
        except LatestJobNotFound:
            self.log.info("No such job found")
            bottle.response.body = 'not found'
            bottle.response.status = '404 Not Found'
