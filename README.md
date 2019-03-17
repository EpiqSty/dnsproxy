## dns2dot-proxy

**Problem statement:**

Implement a DNS to DNS-over-TLS proxy. It should listen on port 53 and resolve requests with an upsteam DNS server over TLS.

**Design notes:**

* After reviewing the [Cloudflare's explanation of DNS over TLS](https://developers.cloudflare.com/1.1.1.1/dns-over-tls/) and [RFC7858](https://tools.ietf.org/html/rfc7858), it was clear that the implementation to start with will basically be a TCP to TCP+TLS forwarder.

* This assumption was validated with `socat` utility:

````bash
$ socat tcp-listen:2253,reuseaddr,fork openssl:1.1.1.1:853,cafile=/etc/ssl/certs/ca-certificates.crt,commonname=cloudflare-dns.com

$ dig @localhost -p 2253 +tcp cloudflare-dns.com
;; ->>HEADER<<- opcode: QUERY; status: NOERROR; id: 25529
;; Flags: qr rd ra; QUERY: 1; ANSWER: 2; AUTHORITY: 0; ADDITIONAL: 0

;; QUESTION SECTION:
;; cloudflare-dns.com.          IN      A

;; ANSWER SECTION:
cloudflare-dns.com.     59      IN      A       104.16.112.25
cloudflare-dns.com.     59      IN      A       104.16.111.25

;; Received 68 B
;; Time 2019-03-17 22:12:44 STD
;; From 127.0.0.1@2253(TCP) in 74.9 ms

````

**Implementation notes:**

- It is a TCP to TCP+TLS forwarder written in Python, based on https://github.com/shyam/dnsproxy project.
- Uses [maproxy](https://pypi.org/project/maproxy/) library for handling proxy operations. It internally allows Nonblocking Network I/O, by using python [tornado](https://github.com/tornadoweb/tornado) framework, an asynchronous networking library developed at FriendFeed. This allows the implementation to handle multiple requests simultaneously.

**Running:**

````bash
$ docker-compose up
Starting dnsproxyepiq_dns2dot.proxy_1
Attaching to dnsproxyepiq_dns2dot.proxy_1
dns2dot.proxy_1  | [dns2dot-proxy] tcp://127.0.0.1:53 -> tcp+tls://1.0.0.1:853

$ docker ps
CONTAINER ID        IMAGE               COMMAND                CREATED              STATUS              PORTS                NAMES
ece9be629719        dns2dot.proxy       "python dnsproxy.py"   About a minute ago   Up 42 seconds       0.0.0.0:53->53/tcp   dnsproxyepiq_dns2dot.proxy_1

$ dig @localhost -p 53 +tcp cloudflare-dns.com

; <<>> DiG 9.10.3-P4-Ubuntu <<>> @localhost -p 53 +tcp cloudflare-dns.com
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 57085
;; flags: qr rd ra ad; QUERY: 1, ANSWER: 2, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 1452
; OPT=12: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 (".................................................................................................................................................................................................................................................................................................................................................................................................")
;; QUESTION SECTION:
;cloudflare-dns.com.            IN      A

;; ANSWER SECTION:
cloudflare-dns.com.     286     IN      A       104.16.111.25
cloudflare-dns.com.     286     IN      A       104.16.112.25

;; Query time: 44 msec
;; SERVER: 127.0.0.1#53(127.0.0.1)
;; WHEN: Sun Mar 17 22:44:23 STD 2019
;; MSG SIZE  rcvd: 468

````

**Performance profiling:**

Any software to be used in production should be performance profiled for capacity planning and future optmization.

- The results below are for 30 clients over 30 seconds with 60 queries a second. 
- The results compared socat and the python implementation here.
- Both setups were using the same network conditions; pointing to the same upstream. Testing was done using [dnsperf-tcp](https://github.com/Sinodun/dnsperf-tcp). Queryfile used in this test is from (ftp://ftp.nominum.com/pub/nominum/dnsperf/data/queryfile-example-current.gz).

With smaller number of clients and smaller timeframe, the Average RTT is nearly same. However with some load (larger number of clients and timeframe), the deviation is visible. 

```
[*] using socat

$ dnsperf -d queryfile-example-current -l 20 -c 10 -Q 30 -z -p 53
DNS Performance Testing Tool
Nominum Version 2.1.0.0

[Status] Command line: dnsperf -d queryfile-example-current -l 20 -c 10 -Q 30 -z -p 53
[Status] Sending queries (to 127.0.0.1) over TCP
[Status] Started at: Sun Mar 17 23:02:31 2019
[Status] Stopping after 20.000000 seconds
[Timeout] Query timed out: msg id 484
[Status] Testing complete (time limit)

Statistics:

  Queries sent:         600
  Queries completed:    599 (99.83%)
  Queries lost:         1 (0.17%)

  Response codes:       NOERROR 434 (72.45%), SERVFAIL 10 (1.67%), NXDOMAIN 155 (25.88%)
  Average packet size:  request 40, response 97
  Run time (s):         20.000920
  Queries per second:   29.948622

  TCP connections:      10
  Ave Queries per conn: 60
  TCP HS time per client (s):          0.000000  (0.00%)
  TLS HS time per client (s):          0.000000  (0.00%)
  Total HS time per client (s):        0.000000  (0.00%)
  TCP HS time per connection (s):      0.000000
  TLS HS time per connection (s):      0.000000
  Total HS time per connection (s):    0.000000
  Adjusted Queries/s:   29.948622


  Average RTT (s):      0.073684 (min 0.008143, max 4.232572)
  RTT StdDev (s):       0.357560


[*] using the python implementation

$ dnsperf -d queryfile-example-current -l 20 -c 10 -Q 30 -z -p 53
DNS Performance Testing Tool
Nominum Version 2.1.0.0

[Status] Command line: dnsperf -d queryfile-example-current -l 20 -c 10 -Q 30 -z -p 53
[Status] Sending queries (to 127.0.0.1) over TCP
[Status] Started at: Sun Mar 17 22:56:57 2019
[Status] Stopping after 20.000000 seconds
[Timeout] Query timed out: msg id 484
[Status] Testing complete (time limit)

Statistics:

  Queries sent:         600
  Queries completed:    599 (99.83%)
  Queries lost:         1 (0.17%)

  Response codes:       NOERROR 435 (72.62%), SERVFAIL 9 (1.50%), NXDOMAIN 155 (25.88%)
  Average packet size:  request 40, response 98
  Run time (s):         20.434241
  Queries per second:   29.313543

  TCP connections:      10
  Ave Queries per conn: 60
  TCP HS time per client (s):          0.000000  (0.00%)
  TLS HS time per client (s):          0.000000  (0.00%)
  Total HS time per client (s):        0.000000  (0.00%)
  TCP HS time per connection (s):      0.000000
  TLS HS time per connection (s):      0.000000
  Total HS time per connection (s):    0.000000
  Adjusted Queries/s:   29.313543


  Average RTT (s):      0.138459 (min 0.009746, max 4.328004)
  RTT StdDev (s):       0.387683
```

**Applications:**

* In a microservices environment -- service discovery is one of the most common paintpoints. When an org. is handling sensitive data like financial and medical records, we will need a way to ensure that even the DNS resolution which is integral to service discovery is secured and **resistant eavesdropping and tampering**. That is where a DNS stub proxy that allows existing services to work as-is without any major changes would help.

**Deployment Strategy:**

* It is very common to orchestrate microservices deployment using Kubernetes `(k8s)`. It is possible to run this application as a part of the system namespace `(kube-system)`. The cluster's upstream DNS resolution can be modified to use this as the upstream DNS resolver, or, even individual deployments/pod's could have  DNS policy that would use this.
  * Note: Since the implementation only supports TCP, we will have to configure the `/etc/resolv.conf` (libc) within the containers to ensure TCP based DNS resolution.

**Security Concerns and other areas of improvement:**

* Python 2.7 will retire in 2020, this case can't be considered as long-term solution.
  
* Implement proper validation of SSL/TLS certificates including SPKI Pinning. 
  * This is particularly important to ensure that the upstream DNS service is not compromised. 

* Reduce latency by having long lived / persistent connections with upstream.

* TCP resolution can easily take up a lot of connections/open files. It has to be monitored and additional instances have to be setup so that this doesn't become a bottlenect.
  * Caching of dns responses could also help here, as it would not make sense to contact upstream each time.

* Refactor the application to be more modular and add test coverage.

* Ability to handle multiple upstream resolvers.
  * Will help in redundancy in case an upstream resolver goes offline.

* Ability to handle custom rules
  * There will always be cases where we would want to rewrite queries. Similar to the query rewriting capabilities of `coredns` and `dnsmasq`.

* Ability to handle UDP based DNS resolution.

**Author:**

[Shyam Sundar C S](mailto:csshyamsundar@gmail.com) 

updated by [Epiq Sty](mailto:epiq.sty@gmail.com)