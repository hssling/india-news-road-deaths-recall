"""Polite HTTP fetcher: robots.txt obeyed, 1 request / 2 s per host, stop on 403/429.

Only used for the kill-check. Article bodies are never written to disk; callers
receive the text in memory and keep only extracted fields.
"""
import time
import urllib.robotparser
from urllib.parse import urlparse

import requests

UA = "research-feasibility-check (academic injury study)"
MIN_INTERVAL = 2.05  # seconds between requests to the same host

_last = {}
_robots = {}
_blocked = set()
_counts = {}
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})


class SiteStopped(Exception):
    pass


def _wait(host):
    gap = MIN_INTERVAL
    rp = _robots.get(host)
    if rp is not None:
        cd = rp.crawl_delay(UA) or rp.crawl_delay("*")
        if cd:
            gap = max(gap, float(cd))
    t = _last.get(host)
    if t is not None:
        dt = time.time() - t
        if dt < gap:
            time.sleep(gap - dt)
    _last[host] = time.time()


def robots_ok(url):
    p = urlparse(url)
    host = p.netloc
    if host not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        _wait(host)
        _counts[host] = _counts.get(host, 0) + 1
        try:
            r = SESSION.get(f"{p.scheme}://{host}/robots.txt", timeout=30)
            if r.status_code in (401, 403):
                rp.disallow_all = True
            elif r.status_code >= 400:
                rp.allow_all = True
            else:
                rp.parse(r.text.splitlines())
        except requests.RequestException:
            rp.allow_all = True
        _robots[host] = rp
    return _robots[host].can_fetch(UA, url)


def get(url, timeout=40):
    """Return requests.Response or None (robots-disallowed). Raises SiteStopped on 403/429."""
    host = urlparse(url).netloc
    if host in _blocked:
        raise SiteStopped(host)
    if not robots_ok(url):
        return None
    _wait(host)
    _counts[host] = _counts.get(host, 0) + 1
    r = SESSION.get(url, timeout=timeout)
    if r.status_code in (403, 429):
        _blocked.add(host)
        raise SiteStopped(f"{host} returned {r.status_code} for {url}")
    return r


def request_counts():
    return dict(_counts)
