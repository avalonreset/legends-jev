"""Install the actual wheel in an isolated temp environment outside checkout."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import venv
import zipfile

root=Path(__file__).resolve().parents[1]
wheel=next((root/"dist").glob("*.whl"))
with zipfile.ZipFile(wheel) as archive:
    names=archive.namelist()
    for required in ("legends_jev/data/cases.json", "legends_jev/docs/recipe.md"):
        assert required in names, required
    assert not any(".dpapi" in n or "/var/" in n or ".env" in n for n in names)
with tempfile.TemporaryDirectory(prefix="legends-jev-wheel-") as temp:
    folder=Path(temp)
    venv.create(folder/"env",with_pip=True)
    python=folder/"env"/("Scripts/python.exe" if __import__("os").name=="nt" else "bin/python")
    subprocess.run([str(python),"-m","pip","install","--no-deps",str(wheel)],cwd=folder,check=True,capture_output=True)
    for args in (["doctor"],["guide"],["benchmark"]):
        result=subprocess.run([str(python),"-m","legends_jev",*args],cwd=folder,check=True,capture_output=True,text=True)
        if args[0]=="doctor":
            assert json.loads(result.stdout)["offline_ok"]
    print(json.dumps({"wheel":wheel.name,"sha256":hashlib.sha256(wheel.read_bytes()).hexdigest(),"isolated_outside_checkout":True,"doctor_guide_baseline":"pass"}))
