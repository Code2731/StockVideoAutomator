import pytest

from app.models.database import DownloadDatabase


@pytest.fixture
def db(tmp_path):
    return DownloadDatabase(db_path=str(tmp_path / "test.db"))


def _add(db, video_id="vid1", title="제목"):
    db.add_record(
        url=f"https://youtu.be/{video_id}",
        video_id=video_id,
        title=title,
        channel="채널",
        thumbnail_url="",
        file_path=f"/tmp/{video_id}.mp4",
        fmt="mp4",
        quality="best",
        filesize=123,
        duration=60,
        download_type="video",
    )


def test_empty_database(db):
    assert db.get_all_records() == []


def test_add_and_get_record(db):
    _add(db)
    records = db.get_all_records()
    assert len(records) == 1
    assert records[0]["video_id"] == "vid1"
    assert records[0]["title"] == "제목"
    assert records[0]["status"] == "completed"


def test_delete_record(db):
    _add(db)
    record_id = db.get_all_records()[0]["id"]
    db.delete_record(record_id)
    assert db.get_all_records() == []


def test_clear_all(db):
    _add(db, "a")
    _add(db, "b")
    assert len(db.get_all_records()) == 2
    db.clear_all()
    assert db.get_all_records() == []


def test_limit(db):
    for i in range(5):
        _add(db, f"vid{i}")
    assert len(db.get_all_records(limit=3)) == 3
