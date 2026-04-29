import json
import os
import tempfile
#import pytest
from unittest.mock import patch

from genealias.gene_alias import fetch_hugo, AliasDict


# --- fetch_hugo ---

class TestFetchHugo:
    def test_return_from_symbol(self):
        response = fetch_hugo('TP53', field='symbol')
        assert response is not None
        assert response['docs'][0]['symbol'] == 'TP53'

    def test_return_from_alias(self):
        response = fetch_hugo('P53', field='alias_symbol')
        assert response is not None
        assert response['docs'][0]['symbol'] == 'TP53'

# --- AliasDict.__init__ ---

class TestAliasDictInit:
    def test_initializes_empty_aliases(self):
        assert AliasDict().aliases == {}

# --- AliasDict.__call__ ---

class TestAliasDictCall:
    def test_returns_mapped_genes(self):
        ad = AliasDict()
        ad.aliases = {'P53': 'TP53', 'TP53': 'TP53'}
        assert ad(['P53', 'TP53']) == ['TP53', 'TP53']

    def test_skips_unknown_genes(self):
        ad = AliasDict()
        result = ad(['UNKNOWN'])
        assert result == []

# --- AliasDict.build ---

class TestAliasDictBuild:
    def test_builds_from_symbol(self):
        ad = AliasDict()
        ad.build(['TP53'])

        assert ad.aliases['TP53'] == 'TP53'
        assert ad.aliases['P53'] == 'TP53'
        assert ad.aliases['LFS1'] == 'TP53'

    def test_builds_from_alias(self):
        ad = AliasDict()
        ad.build(['P53'])

        assert ad.aliases['TP53'] == 'P53'
        assert ad.aliases['P53'] == 'P53'
        assert ad.aliases['LFS1'] == 'P53'

    def test_non_gene_symbol(self):
        ad = AliasDict()
        ad.build(['FAKEGENE'])

        assert ad.aliases['FAKEGENE'] == 'FAKEGENE'

# --- AliasDict.save ---

class TestAliasDictSave:
    def test_saves_aliases_to_json_file(self):
        ad = AliasDict()
        ad.aliases = {'P53': 'TP53', 'TP53': 'TP53'}

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'aliases.json')
            ad.save(path)
            with open(path) as f:
                loaded = json.load(f)

        assert loaded == {'P53': 'TP53', 'TP53': 'TP53'}

    def test_appends_json_extension_if_missing(self):
        ad = AliasDict()
        ad.aliases = {'TP53': 'TP53'}

        with tempfile.TemporaryDirectory() as tmpdir:
            base = os.path.join(tmpdir, 'aliases')
            ad.save(base)
            assert os.path.isfile(base + '.json')

    def test_does_not_double_append_json_extension(self):
        ad = AliasDict()
        ad.aliases = {'TP53': 'TP53'}

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'aliases.json')
            ad.save(path)
            assert os.path.isfile(path)
            assert not os.path.isfile(path + '.json')

    def test_creates_intermediate_directories(self):
        ad = AliasDict()
        ad.aliases = {'TP53': 'TP53'}

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'subdir', 'aliases.json')
            ad.save(path)
            assert os.path.isfile(path)

# --- AliasDict.load ---

class TestAliasDictLoad:
    def test_loads_aliases_from_json_file(self):
        ad = AliasDict()
        data = {'TP53': 'TP53', 'P53': 'TP53'}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            path = f.name

        try:
            ad.load(path)
            assert ad.aliases == data
        finally:
            os.unlink(path)
