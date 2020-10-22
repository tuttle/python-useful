from __future__ import division, print_function

import bisect
import hashlib
import sys

PY2 = sys.version_info[0] == 2

# noinspection PyUnresolvedReferences,PyShadowingBuiltins
range = xrange if PY2 else range


class ConsistentHashRing(object):
    """
    Spread the keys into a fixed set of buckets as uniformly as possible.
    Also maintain consistency so only a few keys change their assignment when the set of buckets change.

    See also https://en.wikipedia.org/wiki/Consistent_hashing
    Used code from http://techspot.zzzeek.org/2012/07/07/the-absolutely-simplest-consistent-hashing-example/
    """
    def __init__(self, buckets=None, replicas=1000):
        self.replicas = replicas
        self.keys = []
        self.bucket_map = {}

        if buckets:
            list(map(self.add_bucket, buckets))

    @staticmethod
    def hash(key):
        if not isinstance(key, bytes):  # unicode strings py2/3
            key_bytestring = key.encode('utf-8')
        else:
            key_bytestring = key

        return int(hashlib.md5(key_bytestring).hexdigest(), 16)

    def ireplicas(self, bucket):
        for r in range(self.replicas):
            yield self.hash(
                '%s:%d' % (bucket, r)
            )

    def add_bucket(self, bucket):
        for h in self.ireplicas(bucket):
            if h in self.bucket_map:
                raise ValueError("Bucket %r is already present." % bucket)

            self.bucket_map[h] = bucket
            bisect.insort(self.keys, h)

    def remove_bucket(self, bucket):
        for h in self.ireplicas(bucket):
            # will raise KeyError for nonexistent bucket
            del self.bucket_map[h]
            del self.keys[
                bisect.bisect_left(self.keys, h)
            ]

    def select_bucket(self, key):
        """
        Return a bucket, given a key.
        The bucket replica with a hash value nearest but not less than that of the given key is returned.
        If the hash of the given key is greater than the greatest hash, returns the lowest hashed bucket.
        """
        h = self.hash(
            str(key)
        )
        start = bisect.bisect(self.keys, h)

        if start == len(self.keys):
            start = 0

        return self.bucket_map[
            self.keys[start]
        ]


def demo():
    from collections import defaultdict

    ring1 = ConsistentHashRing('abcdefghijklm')
    ring2 = ConsistentHashRing('abcdefghijklmno')

    u1 = defaultdict(int)
    u2 = defaultdict(int)

    cnt = [0, 0]

    for key in range(4000):
        bucket1 = ring1.select_bucket(key)
        u1[bucket1] += 1

        bucket2 = ring2.select_bucket(key)
        u2[bucket2] += 1

        eq = bucket1 != bucket2
        cnt[eq] += 1

        print('%10d %10s %10s     ' % (key, bucket1, bucket2), ['', 'CHANGES!'][eq])

    print()
    print(
        cnt,
        '\t%.1f%% of keys change its bucket' % (
            100 * cnt[1] / sum(cnt),
        )
    )

    print()
    for k in set(u1) | set(u2):
        v1 = u1.get(k, 0)
        v2 = u2.get(k, 0)
        print(
            '%10s %10d   %-70s    %10d   %-70s' % (
                k,
                v1,
                '*' * (v1 // 5),
                v2,
                '*' * (v2 // 5),
            )
        )


if __name__ == '__main__':
    demo()
