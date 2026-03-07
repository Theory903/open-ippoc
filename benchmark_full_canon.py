import time
import sys
import os
import re

class OldCanonScanner:
    def __init__(self):
        import re
        self.forbidden_patterns = [
            re.compile(r"(?i)modify.*identity"),
            re.compile(r"(?i)bypass.*authentication"),
            re.compile(r"(?i)override.*sovereignty"),
            re.compile(r"(?i)unlimited.*spending"),
            re.compile(r"(?i)budget.*bypass"),
            re.compile(r"(?i)free.*resources"),
            re.compile(r"(?i)disable.*safety"),
            re.compile(r"(?i)remove.*constraints"),
            re.compile(r"(?i)circumvent.*policy"),
        ]

class NewCanonScanner:
    import re
    _FORBIDDEN_PATTERNS = [
        re.compile(r"(?i)modify.*identity"),
        re.compile(r"(?i)bypass.*authentication"),
        re.compile(r"(?i)override.*sovereignty"),
        re.compile(r"(?i)unlimited.*spending"),
        re.compile(r"(?i)budget.*bypass"),
        re.compile(r"(?i)free.*resources"),
        re.compile(r"(?i)disable.*safety"),
        re.compile(r"(?i)remove.*constraints"),
        re.compile(r"(?i)circumvent.*policy"),
    ]

    def __init__(self):
        self.forbidden_patterns = self._FORBIDDEN_PATTERNS

def run_bench():
    # Setup
    n_iters = 100000

    t0 = time.time()
    for _ in range(n_iters):
        OldCanonScanner()
    t1 = time.time()
    old_time = t1 - t0

    t0 = time.time()
    for _ in range(n_iters):
        NewCanonScanner()
    t1 = time.time()
    new_time = t1 - t0

    print(f"Old: {old_time:.4f}s")
    print(f"New: {new_time:.4f}s")
    print(f"Improvement: {old_time / new_time:.2f}x")

if __name__ == "__main__":
    run_bench()
