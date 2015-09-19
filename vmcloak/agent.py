# Copyright (C) 2014-2015 Jurriaan Bremer.
# This file is part of VMCloak - http://www.vmcloak.org/.
# See the file 'docs/LICENSE.txt' for copying permission.

import requests

from StringIO import StringIO

from vmcloak.misc import wait_for_host

class Agent(object):
    def __init__(self, ipaddr, port):
        self.ipaddr = ipaddr
        self.port = port

    def get(self, method, *args, **kwargs):
        """Wrapper around GET requests."""
        url = "http://%s:%s%s" % (self.ipaddr, self.port, method)
        return requests.get(url, *args, **kwargs)

    def post(self, method, **kwargs):
        """Wrapper around POST requests."""
        url = "http://%s:%s%s" % (self.ipaddr, self.port, method)
        return requests.post(url, data=kwargs)

    def postfile(self, method, files, **kwargs):
        """Wrapper around POST requests with attached files."""
        url = "http://%s:%s%s" % (self.ipaddr, self.port, method)
        return requests.post(url, files=files, data=kwargs)

    def ping(self):
        """Ping the machine."""
        return self.get("/", timeout=5)

    def execute(self, command, async=False):
        """Execute a command."""
        if async:
            return self.post("/execute", command=command, async="true")
        else:
            return self.post("/execute", command=command)

    def remove(self, path):
        """Remove a file or entire directory."""
        self.post("/remove", path=path)

    def shutdown(self):
        """Power off the machine."""
        self.execute("shutdown -s -t 0", async=True)

    def killprocess(self, process_name):
        """Terminate a process."""
        self.execute("taskkill /F /IM %s" % process_name)

    def static_ip(self, ipaddr, netmask, gateway):
        """Change the IP address of this machine."""
        command = \
            "netsh interface ip set address " \
            "name=\"Local Area Connection\" static " \
            "%s %s %s 1" % (ipaddr, netmask, gateway)
        try:
            requests.post("http://%s:%s/execute" % (self.ipaddr, self.port),
                          data={"command": command}, timeout=10)
        except requests.exceptions.ReadTimeout:
            pass

        # Now wait until the Agent is reachable on the new IP address.
        wait_for_host(ipaddr, self.port)
        self.ipaddr = ipaddr

    def upload(self, filepath, contents):
        """Upload a file to the Agent."""
        if isinstance(contents, basestring):
            contents = StringIO(contents)
        self.postfile("/store", {"file": contents}, filepath=filepath)
