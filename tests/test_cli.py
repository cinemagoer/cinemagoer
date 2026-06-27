from imdb.cli import list_results


class _FakeItem:
    def __init__(self, item_id, label, field='name'):
        self.personID = item_id if field == 'name' else None
        self.movieID = item_id if field == 'title' else None
        self._label = label
        self._field = field

    def __getitem__(self, key):
        if key == f'long imdb {self._field}':
            return self._label
        raise KeyError(key)


def test_list_results_aligns_variable_width_ids(capsys):
    items = [
        _FakeItem(12584561, 'Fred Astaire'),
        _FakeItem(1, 'Fred Astaire'),
        _FakeItem(9056407, 'Alistair Ford'),
    ]

    list_results(items, type_='person')

    out = capsys.readouterr().out.splitlines()
    assert out[0] == '  # IMDb id name'
    assert out[1] == '=== ======== ===='
    assert out[2].startswith('  1 12584561 ')
    assert out[3].startswith('  2        1 ')
    assert out[4].startswith('  3  9056407 ')