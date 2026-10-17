# Traces 2.9.3 scratch reuse

These files come from the nauty 2.9.3 source archive:
`http://archive.ubuntu.com/ubuntu/pool/universe/n/nauty/nauty_2.9.3.orig.tar.gz`.
The archive SHA-256 is recorded below. Copyright and Apache 2.0 license notices
are preserved. `sorttemplates.c` is unmodified.

The only functional change to `traces.c` guards its end-of-call
`traces_freedyn()`: with `SQTOPOLOGY_TRACES_CACHE_LIMIT` defined, retain the
existing TLS scratch arrays for graphs up to that many vertices. Larger graphs
use the stock cleanup. Explicit cleanup is unchanged. Canonical labeling,
refinement, and canonical graph construction are unchanged.

CMake builds this file only with matching nauty 2.9.3 headers/libraries. It
renames its three exported functions to private `sqtopology_` names; stock nauty
and all other backends remain available. A C++ thread-local guard explicitly
releases the retained arrays when the calling thread exits. The default cache
limit is 4096 vertices. Arrays grow to the largest graph under that limit;
topology, canonical result, group, and per-call search allocations are not cached.

Use `-DSQTOPOLOGY_CACHED_TRACES=OFF` for a stock-engine comparison and
`-DSQTOPOLOGY_STATIC_NAUTY=OFF` for shared-library linking. The cached engine
falls back to stock when a different nauty version is discovered.

Archive SHA-256: `1e7f595d42411ae2b1423af31f78fea94d0932e5e1abed01eeba04d90505c824`.
