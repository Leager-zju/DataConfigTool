import yaml
from pathlib import Path

from utils.models import ConfigTable, ColumnDef
from utils.enums import KeyType
from utils.storage import save_table, load_table


def test_save_and_load_roundtrip(tmp_path: Path):
    table = ConfigTable(table_name='s', group_name='g', key_type=KeyType.GROUP)
    table.columns = [ColumnDef('id', 'int'), ColumnDef('name', 'string')]
    table.data = [{'id': 1, 'name': 'a'}, {'id': 2, 'name': 'b'}]

    p = tmp_path / 's.yaml'
    save_table(table, p)

    loaded = load_table(p)
    assert loaded.table_name == 's'
    assert loaded.group_name == 'g'
    assert len(loaded.columns) == 2
    assert [c.name for c in loaded.columns] == ['id', 'name']
    assert [r['id'] for r in loaded.data] == [1,2]
