import pytest

from utils.models import ConfigTable, ColumnDef
from utils.enums import KeyType
from utils import pk_cache


import pytest

from utils.models import ConfigTable, ColumnDef
from utils.enums import KeyType
from utils import pk_cache


def test_validate_all_primary_keys_group_level():
    pk_cache.clear_pk_caches()
    table = ConfigTable(table_name='t', group_name='g', key_type=KeyType.GROUP)
    table.columns = [ColumnDef('id', 'int'), ColumnDef('v', 'int')]
    table.data = [{'id': 1, 'v': 10}, {'id': 2, 'v': 20}]

    table.validate_all_primary_keys()
    assert 'g' in pk_cache._group_pk_caches
    assert 1 in pk_cache._group_pk_caches['g']


def test_validate_all_primary_keys_global_level():
    pk_cache.clear_pk_caches()
    table = ConfigTable(table_name='t', group_name='g', key_type=KeyType.GLOBAL)
    table.columns = [ColumnDef('id', 'int'), ColumnDef('v', 'int')]
    table.data = [{'id': 1, 'v': 10}, {'id': 2, 'v': 20}]

    table.validate_all_primary_keys()
    assert 1 in pk_cache._global_pk_cache
    # pk_cache stores as (group, table) not (table, group)
    assert pk_cache._global_pk_cache[1] == ('g', 't')

