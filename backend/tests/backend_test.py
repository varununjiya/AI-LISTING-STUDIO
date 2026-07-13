"""AI Listing Studio - backend regression tests.

Uses seeded session token `test_session_fixed_123` for user `test-user-1`.
Covers: auth, products CRUD, AI generation & regeneration, listing edits,
stats, uploads (CSV), bulk generate, exports (xlsx binary), settings.
"""
from __future__ import annotations

import io
import os
import zipfile

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://commerce-ai-craft.preview.emergentagent.com").rstrip("/")
TOKEN = "test_session_fixed_123"


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    })
    return s


@pytest.fixture(scope="module")
def created_product_id(api):
    # create a product for reuse (must be draft first for status flow)
    r = api.post(
        f"{BASE_URL}/api/products?status=draft",
        json={"product_name": "TEST_Steel Water Bottle", "brand": "TEST_Brand",
              "category": "Kitchen", "material": "Stainless Steel", "color": "Silver"},
    )
    assert r.status_code == 200, r.text
    pid = r.json()["id"]
    yield pid
    api.delete(f"{BASE_URL}/api/products/{pid}")


# ---------------- Auth ---------------- #
class TestAuth:
    def test_me_with_bearer(self, api):
        r = api.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 200
        d = r.json()
        assert d["user_id"] == "test-user-1"
        assert d["email"] == "qa@example.com"

    def test_me_unauthenticated(self):
        r = requests.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 401

    def test_products_unauthenticated(self):
        r = requests.get(f"{BASE_URL}/api/products")
        assert r.status_code == 401


# ---------------- Products CRUD ---------------- #
class TestProducts:
    def test_create(self, api):
        r = api.post(
            f"{BASE_URL}/api/products?status=draft",
            json={"product_name": "TEST_Product One", "brand": "TEST_B"},
        )
        assert r.status_code == 200
        d = r.json()
        assert d["product_name"] == "TEST_Product One"
        assert d["status"] == "draft"
        assert "id" in d
        # cleanup
        api.delete(f"{BASE_URL}/api/products/{d['id']}")

    def test_list_and_search_filter(self, api, created_product_id):
        r = api.get(f"{BASE_URL}/api/products")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        r2 = api.get(f"{BASE_URL}/api/products?search=Steel")
        assert r2.status_code == 200
        assert any(p["id"] == created_product_id for p in r2.json())
        r3 = api.get(f"{BASE_URL}/api/products?status=draft")
        assert r3.status_code == 200
        assert all(p["status"] == "draft" for p in r3.json())

    def test_get_single(self, api, created_product_id):
        r = api.get(f"{BASE_URL}/api/products/{created_product_id}")
        assert r.status_code == 200
        d = r.json()
        assert "product" in d and "listing" in d
        assert d["product"]["id"] == created_product_id

    def test_update(self, api, created_product_id):
        r = api.put(
            f"{BASE_URL}/api/products/{created_product_id}",
            json={"product_name": "TEST_Updated Bottle", "brand": "TEST_Brand",
                  "category": "Kitchen", "material": "Stainless Steel", "color": "Silver"},
        )
        assert r.status_code == 200
        assert r.json()["product_name"] == "TEST_Updated Bottle"
        # verify persistence
        g = api.get(f"{BASE_URL}/api/products/{created_product_id}").json()
        assert g["product"]["product_name"] == "TEST_Updated Bottle"

    def test_delete_and_404(self, api):
        r = api.post(
            f"{BASE_URL}/api/products?status=draft",
            json={"product_name": "TEST_ToDelete"},
        )
        pid = r.json()["id"]
        d = api.delete(f"{BASE_URL}/api/products/{pid}")
        assert d.status_code == 200
        g = api.get(f"{BASE_URL}/api/products/{pid}")
        assert g.status_code == 404


# ---------------- AI Generation ---------------- #
class TestGeneration:
    def test_generate_full_listing(self, api, created_product_id):
        r = api.post(f"{BASE_URL}/api/products/{created_product_id}/generate")
        assert r.status_code == 200, r.text
        d = r.json()
        for key in ["amazon_title", "amazon_bullets", "amazon_description",
                    "amazon_backend_keywords", "flipkart_title", "flipkart_highlights",
                    "flipkart_description", "seo_keywords", "meta_description",
                    "product_specifications"]:
            assert key in d, f"missing {key}"
        assert isinstance(d["amazon_bullets"], list) and len(d["amazon_bullets"]) == 5
        # product status becomes completed
        p = api.get(f"{BASE_URL}/api/products/{created_product_id}").json()["product"]
        assert p["status"] == "completed"

    def test_regenerate_section(self, api, created_product_id):
        r = api.post(f"{BASE_URL}/api/products/{created_product_id}/regenerate/amazon_bullets")
        assert r.status_code == 200
        d = r.json()
        assert d["section"] == "amazon_bullets"
        assert isinstance(d["value"], list) and len(d["value"]) == 5

    def test_update_listing_persists_and_appends_history(self, api, created_product_id):
        r = api.put(
            f"{BASE_URL}/api/products/{created_product_id}/listing",
            json={"amazon_title": "TEST_Edited Title"},
        )
        assert r.status_code == 200
        d = r.json()
        assert d["amazon_title"] == "TEST_Edited Title"
        assert isinstance(d.get("history"), list) and len(d["history"]) >= 1
        assert any(h.get("action") == "edited" for h in d["history"])


# ---------------- Stats ---------------- #
class TestStats:
    def test_stats(self, api):
        r = api.get(f"{BASE_URL}/api/stats")
        assert r.status_code == 200
        d = r.json()
        for k in ["total", "draft", "completed", "exported"]:
            assert k in d and isinstance(d[k], int)


# ---------------- Uploads ---------------- #
class TestUploads:
    def test_upload_csv_and_list(self, api):
        csv = "product_name,brand,category\nTEST_Bulk1,TEST_B,Home\nTEST_Bulk2,TEST_B,Home\n"
        headers = {"Authorization": f"Bearer {TOKEN}"}
        files = {"file": ("bulk.csv", csv, "text/csv")}
        r = requests.post(f"{BASE_URL}/api/uploads", headers=headers, files=files)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["row_count"] == 2
        upload_id = d["id"]

        lst = api.get(f"{BASE_URL}/api/uploads")
        assert lst.status_code == 200
        assert any(u["id"] == upload_id for u in lst.json())

        gen = api.post(f"{BASE_URL}/api/uploads/{upload_id}/generate-all")
        assert gen.status_code == 200
        assert gen.json()["created"] == 2


# ---------------- Exports ---------------- #
class TestExports:
    @pytest.mark.parametrize("etype", ["amazon", "flipkart", "generic"])
    def test_export_xlsx(self, api, etype):
        r = api.post(f"{BASE_URL}/api/exports", json={"export_type": etype})
        assert r.status_code == 200, r.text
        # xlsx = zip file with [Content_Types].xml
        assert zipfile.is_zipfile(io.BytesIO(r.content)), "not a valid xlsx"
        assert "spreadsheetml" in r.headers.get("content-type", "")

    def test_list_exports(self, api):
        r = api.get(f"{BASE_URL}/api/exports")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------------- Settings ---------------- #
class TestSettings:
    def test_get_defaults(self, api):
        r = api.get(f"{BASE_URL}/api/settings")
        assert r.status_code == 200
        d = r.json()
        assert d["ai_provider"] in ("mock", "openai", "gemini", "ollama")

    def test_update_persists(self, api):
        payload = {
            "ai_provider": "mock", "api_key": "TEST_key",
            "default_marketplace": "flipkart", "brand_tone": "luxury",
            "language": "English", "title_char_limit": 180,
            "description_char_limit": 1500, "default_export_format": "amazon",
        }
        r = api.put(f"{BASE_URL}/api/settings", json=payload)
        assert r.status_code == 200
        d = r.json()
        assert d["brand_tone"] == "luxury"
        assert d["title_char_limit"] == 180
        # revert
        api.put(f"{BASE_URL}/api/settings", json={
            "ai_provider": "mock", "api_key": "", "default_marketplace": "amazon",
            "brand_tone": "professional", "language": "English",
            "title_char_limit": 200, "description_char_limit": 2000,
            "default_export_format": "generic",
        })
