import json
from types import SimpleNamespace
import pytest
import pack_c_analysis


def test_packaging_refuses_existing_target(tmp_path):
    with pytest.raises(ValueError,match='existing'):
        pack_c_analysis.package(tmp_path/'source',tmp_path,tmp_path)


def test_packaging_rejects_missing_gold_checks(tmp_path,monkeypatch):
    source=tmp_path/'source';source.mkdir()
    (source/'validation.json').write_text(json.dumps(dict(gold_checks={})),encoding='utf-8')
    (source/'schema.json').write_text('{}',encoding='utf-8')
    monkeypatch.setattr(pack_c_analysis,'Repository',lambda settings:SimpleNamespace(warm=lambda:object()))
    with pytest.raises(ValueError,match='checks'):
        pack_c_analysis.package(source,tmp_path/'output',tmp_path)
