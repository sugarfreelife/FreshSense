from types import SimpleNamespace

import pytest

from app.services import image_storage


def test_private_images_survive_loss_of_local_files_and_can_be_deleted(tmp_path, monkeypatch):
    objects = {}

    class Store:
        def put_blob(self, key, body, **options):
            assert options["access"] == "private"
            objects[key] = body

        def get_blob(self, key, **options):
            assert options["access"] == "private"
            return SimpleNamespace(body=objects[key])

        def delete_blob(self, keys):
            for key in keys:
                objects.pop(key, None)

    monkeypatch.setattr(image_storage, "enabled", lambda: True)
    monkeypatch.setattr(image_storage, "_blob", Store)
    image = tmp_path / ("a" * 32 + ".jpg")
    image.write_bytes(b"normalized photo")
    original = image.with_suffix(".source")
    original.write_bytes(b"original photo")
    stored = image_storage.persist(image)
    assert stored.startswith("blob://")
    image.unlink()
    original.unlink()
    assert image_storage.local_copy(stored, tmp_path).read_bytes() == b"normalized photo"
    image_storage.remove(stored)
    assert objects == {}


def test_incomplete_blob_upload_removes_already_uploaded_image(tmp_path, monkeypatch):
    removed = []

    class Store:
        def put_blob(self, key, body, **options):
            if key.endswith(".source"):
                raise ConnectionError("Upload interrupted")

        def delete_blob(self, keys):
            removed.extend(keys)

    monkeypatch.setattr(image_storage, "enabled", lambda: True)
    monkeypatch.setattr(image_storage, "_blob", Store)
    image = tmp_path / ("b" * 32 + ".jpg")
    image.write_bytes(b"normalized")
    image.with_suffix(".source").write_bytes(b"original")
    with pytest.raises(ConnectionError):
        image_storage.persist(image)
    assert removed == [f"scans/{image.name}"]
