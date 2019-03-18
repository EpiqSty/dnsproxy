#!/usr/bin/env python
import signal,os,ssl
from maproxy.iomanager import IOManager
from maproxy.proxyserver import ProxyServer

iomanager = IOManager()

DoT_IP=os.getenv('DoT_IP','1.1.1.1')
DoT_Port=int(os.getenv('DoT_Port',853))
DNS_Port=int(os.getenv('DNS_Port',53))
DoT_SSL_cert=os.getenv('DoT_SSL_cert','/etc/ssl/certs/ca-certificates.crt')

if __name__ == '__main__':
  # calls the "stop()" when asked to exit
  signal.signal(signal.SIGINT, lambda sig, frame: iomanager.stop())
  signal.signal(signal.SIGTERM, lambda sig, frame: iomanager.stop())

  # define SSL context
  ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
  ssl_ctx.verify_mode = ssl.CERT_REQUIRED
  ssl_ctx.load_verify_locations(DoT_SSL_cert)
  DoT_SSL_options=ssl_ctx

  # define proxy server settings
  server = ProxyServer(DoT_IP, DoT_Port, server_ssl_options = DoT_SSL_options)
  server.listen(DNS_Port)
  iomanager.add(server)
  print('''
  [dns2dot-proxy] tcp://127.0.0.1:%s -> tcp+tls://%s:%s with SSL Cert verification.
  You'll get an error, if the target server's CA is not listed in %s''' % (str(DNS_Port), DoT_IP, str(DoT_Port), str(DoT_SSL_cert)))

  # the next call to start() is blocking (thread=False)
  iomanager.start(thread = False)

  print("[dns2dot-proxy] Stopping...")
  iomanager.stop(gracefully = True, wait = False)
  print("[dns2dot-proxy] Stopped !")
