import os,sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

SERVICE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(SERVICE))
from tz_api.settings import Settings
from tz_api.repository import Repository
from tz_api.main import create_app

@pytest.fixture(scope='session')
def project():
 root=Path(os.environ.get('TZ_TEST_PROJECT_ROOT',SERVICE.parents[1])).resolve()
 if not (root/'data/handoff_manifest.json').exists():pytest.fail('Run from the full repository or set TZ_TEST_PROJECT_ROOT')
 return root

@pytest.fixture(scope='session')
def csv_repo(project):return Repository(Settings(project=project,backend='csv')).warm()

@pytest.fixture(scope='session')
def client(csv_repo):
 with TestClient(create_app(repository=csv_repo)) as c:yield c
