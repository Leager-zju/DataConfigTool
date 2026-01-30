import pytest

from utils import pk_cache
from utils.enums import KeyType


def setup_function():
    pk_cache.clear_pk_caches()


def test_validate_primary_key_and_conflicts():
    # add pk 1 to group g, table t1
    pk_cache.validate_primary_key('g', 't1', 1, KeyType.GROUP)
    assert 1 in pk_cache._group_pk_caches['g']

    # adding same pk to same group should raise
    with pytest.raises(ValueError):
        pk_cache.validate_primary_key('g', 't2', 1, KeyType.GROUP)

    # global conflict: add as global then try to add again in other group
    pk_cache.clear_pk_caches()
    pk_cache.validate_primary_key('g1', 't1', 5, KeyType.GLOBAL)
    with pytest.raises(ValueError):
        pk_cache.validate_primary_key('g2', 't2', 5, KeyType.GROUP)


def test_apply_pk_diff_add_and_remove():
    pk_cache.clear_pk_caches()
    # initial add
    pk_cache.validate_primary_key('grp', 'tableA', 10, KeyType.GROUP)
    pk_cache.validate_primary_key('grp', 'tableA', 11, KeyType.GROUP)

    # apply diff: remove 10, add 12
    pk_cache.apply_pk_diff('grp', 'tableA', {10}, {12}, KeyType.GROUP)

    assert 10 not in pk_cache._group_pk_caches['grp']
    assert 12 in pk_cache._group_pk_caches['grp']
