# Compatibility

The supported envelope is Python `>=3.8`, FastAPI
`>=0.112.2,<0.140.0`, and `nacos-sdk-python>=2.0.0,<3.0.0`. FastAPI's own
`Requires-Python` metadata selects the newest compatible release for each
interpreter. In particular, Python 3.8 resolves at most FastAPI 0.124.4.

The CI compatibility matrix covers:

- Python 3.8 with FastAPI 0.112.2 and 0.124.4, crossed with Nacos SDK 2.0.0
  and 2.0.11.
- Python 3.9 with FastAPI 0.125.0 and 0.128.8.
- Python 3.10 with FastAPI 0.129.0 and 0.139.2.

The integration fixture continues to use Nacos server 2.3.2.

Only the classic synchronous `nacos.NacosClient` API is used. Calls are moved
to Starlette's worker thread pool. Newer async SDK surfaces are outside 0.1.0.
Python 3.8 is the syntax and typing baseline, and `py.typed` is included.
