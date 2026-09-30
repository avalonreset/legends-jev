"""Offline candidate contract check, without changing any live catalog."""
import argparse
import copy
import json
from pathlib import Path
import sys
from unittest.mock import patch

p=argparse.ArgumentParser()
p.add_argument("router",type=Path)
a=p.parse_args()
sys.path.insert(0,str(a.router))
from cto_legends import discovery, manager
root=Path(__file__).resolve().parents[1]
row=json.loads((root/"release/catalog-entry.candidate.json").read_text())
assert row["commit"] is None and row["sha256"] is None
# Synthetic pins exist only in memory for a validator test; never an install.
row.update(commit="1"*40,sha256="2"*64)
catalog=copy.deepcopy(manager.catalog())
catalog["modules"]["legends-jev"]=row
manager.validate_catalog(catalog)
phrases=["Choose a browser action from accessibility evidence", "computer use action selection", "application control", "legends-jev"]
with patch.object(discovery,"_catalog",return_value=catalog):
    for phrase in phrases:
        result=discovery.route(phrase)
        assert result["matches"][0]["id"]=="legends-jev",result
for path in row["discovery"]["instructions"]:
    assert (root/path).is_file()
assert (root/"skills/cto-legends/SKILL.md").read_bytes()==(a.router/"cto_legends/SKILL.md").read_bytes()
print(json.dumps({"candidate_schema":"pass","outcome_routes":len(phrases),"router_bytes":"identical","live_catalog_modified":False,"public_install_verified":False}))
