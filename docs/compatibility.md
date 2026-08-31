# Compatibility

The supported envelope is Python `>=3.8`, FastAPI
`>=0.112.2,<0.125.0`, and `nacos-sdk-python>=2.0.0,<3.0.0`. CI verifies
FastAPI 0.112.2 and the Python 3.8 ceiling 0.124.4, crossed with Nacos SDK
2.0.0 and 2.0.11. The integration fixture uses Nacos server 2.3.2.

Only the classic synchronous `nacos.NacosClient` API is used. Calls are moved
to Starlette's worker thread pool. Newer async SDK surfaces are outside 0.1.0.
Python 3.8 is the syntax and typing baseline, and `py.typed` is included.

