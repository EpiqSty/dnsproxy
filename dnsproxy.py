#!/usr/bin/env python
import signal,os
from maproxy.iomanager import IOManager
from maproxy.proxyserver import ProxyServer

iomanager = IOManager()
DoT_IP=os.getenv('DoT_IP','1.1.1.1')
DoT_Port=int(os.getenv('DoT_Port',853))
DNS_Port=int(os.getenv('DNS_Port',53))
DoT_SSL_options=bool(os.getenv('DoT_SSL_options',True))

if __name__ == '__main__':
  # calls the "stop()" when asked to exit
  signal.signal(signal.SIGINT, lambda sig, frame: iomanager.stop())
  signal.signal(signal.SIGTERM, lambda sig, frame: iomanager.stop())

  # "server_ssl_options=True" means reverse proxy to server with TLS
  server = ProxyServer(DoT_IP, DoT_Port, server_ssl_options = DoT_SSL_options)
  server.listen(DNS_Port)
  iomanager.add(server)
  print("[dns2dot-proxy] tcp://127.0.0.1:%s -> tcp+tls://%s:%s" % (str(DNS_Port), DoT_IP, str(DoT_Port)))

  # the next call to start() is blocking (thread=False)
  iomanager.start(thread = False)

  print("[dns2dot-proxy] Stopping...")
  iomanager.stop(gracefully = True, wait = False)
  print("[dns2dot-proxy] Stopped !")
