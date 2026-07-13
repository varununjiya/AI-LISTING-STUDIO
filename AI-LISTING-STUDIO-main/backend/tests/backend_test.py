"""AI Ecommerce Content Studio - backend regression tests (iteration 2).

Covers new upgrade endpoints:
    - Real AI multi-marketplace /generate
    - /quality, /versions, /restore, /regenerate/{section}
    - /image-presets (22)
    - /duplicate
    - /agent pipeline (text works, images may fail due to Universal Key budget)
    - Extended /exports: amazon, flipkart, meesho, generic (xlsx),
      shopify, woocommerce (csv), json, zip
    - Settings own-key toggle + empty api_key preserves existing
    - Stats analytics fields
    - Bulk upload + generate-all with real AI

Uses seeded session token `test_session_fixed_123` for user `test-user-1`.
NOTE: Text AI calls are expensive (~10-20s + Universal Key credits). This
suite is designed to minimize real /generate + /agent calls.
Existing seeded product `c908a257-c2be-48d1-a3c0-58378305d711` is reused
for read-only checks (quality/versions).
"""
from __future__ import annotations

import io
import json
import os
import zipfile

import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
TOKEN = "test_session_fixed_123"
SEEDED_PRODUCT_ID = "c908a257-c2be-48d1-a3c0-58378305d711"


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def api():
    s = requests.Session()
    s.headers.update({
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    })
    s.request_timeout = 60
    return s


@pytest.fixture(scope="session")
def test_product_with_ai(api):
    """Create a TEST_ product, generate a listing ONCE, and reuse across tests.

    This is the ONLY /generate call we make in the whole suite.
    """
    r = api.post(
        f"{BASE_URL}/api/products?status=draft",
        json={
            "product_name": "TEST_Bamboo Yoga Mat",
            "brand": "TEST_Brand",
            "category": "Fitness",
            "material": "Bamboo & Natural Rubber",
            "color": "Green",
            "size": "6mm x 72in",
            "features": "non-slip, eco-friendly, cushioned",
        },
    )
    assert r.status_code == 200, r.text
    pid = r.json()["id"]

    # Generate real AI listing (this hits Emergent Universal Key, ~10-20s)
    gen = api.post(f"{BASE_URL}/api/products/{pid}/generate", timeout=90)
    assert gen.status_code == 200, gen.text
    yield pid, gen.json()

    # cleanup
    api.delete(f"{BASE_URL}/api/products/{pid}")


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
class TestAuth:
    def test_me_bearer(self, api):
        r = api.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 200
        d = r.json()
        assert d["user_id"] == "test-user-1"
        assert d["email"] == "qa@example.com"

    def test_me_unauth(self):
        r = requests.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 401

    def test_products_unauth(self):
        r = requests.get(f"{BASE_URL}/api/products")
        assert r.status_code == 401


# --------------------------------------------------------------------------- #
# Products CRUD + Duplicate
# --------------------------------------------------------------------------- #
class TestProducts:
    def test_create_and_get(self, api):
        r = api.post(
            f"{BASE_URL}/api/products?status=draft",
            json={"product_name": "TEST_CrudProduct", "brand": "TEST_B", "sku": "TEST-SKU-001"},
        )
        assert r.status_code == 200
        d = r.json()
        assert d["product_name"] == "TEST_CrudProduct"
        assert d["status"] == "draft"
        assert d["sku"] == "TEST-SKU-001"
        pid = d["id"]

        g = api.get(f"{BASE_URL}/api/products/{pid}")
        assert g.status_code == 200
        assert g.json()["product"]["id"] == pid

        api.delete(f"{BASE_URL}/api/products/{pid}")

    def test_new_fields_persist(self, api):
        payload = {
            "product_name": "TEST_NewFields", "capacity": "1L", "sku": "SKU-NF",
            "model_number": "MDL-42", "benefits": "hydration",
            "usage_instructions": "shake well", "care_instructions": "hand wash",
        }
        r = api.post(f"{BASE_URL}/api/products?status=draft", json=payload)
        assert r.status_code == 200
        pid = r.json()["id"]
        g = api.get(f"{BASE_URL}/api/products/{pid}").json()["product"]
        for k, v in payload.items():
            assert g.get(k) == v, f"{k} mismatch"
        api.delete(f"{BASE_URL}/api/products/{pid}")

    def test_duplicate(self, api):
        # duplicate the seeded product
        r = api.post(f"{BASE_URL}/api/products/{SEEDED_PRODUCT_ID}/duplicate")
        assert r.status_code == 200, r.text
        d = r.json()
        assert "(Copy)" in d["product_name"]
        assert d["status"] == "draft"
        assert d["id"] != SEEDED_PRODUCT_ID
        api.delete(f"{BASE_URL}/api/products/{d['id']}")

    def test_delete_404(self, api):
        r = api.delete(f"{BASE_URL}/api/products/nonexistent-id-xyz")
        # deletes are idempotent (200 with success:true)
        assert r.status_code == 200
        g = api.get(f"{BASE_URL}/api/products/nonexistent-id-xyz")
        assert g.status_code == 404


# --------------------------------------------------------------------------- #
# Real AI listing generation (uses the shared fixture — no extra AI calls)
# --------------------------------------------------------------------------- #
class TestGeneration:
    def test_generate_returns_multi_marketplace(self, api, test_product_with_ai):
        pid, listing = test_product_with_ai
        required = [
            "amazon_title", "amazon_bullets", "amazon_description",
            "amazon_backend_keywords", "amazon_search_terms",
            "flipkart_title", "flipkart_highlights", "flipkart_description",
            "meesho_title", "meesho_highlights", "meesho_tags",
            "seo_primary_keywords", "seo_secondary_keywords", "meta_description",
        ]
        for k in required:
            assert k in listing, f"missing {k}"
        assert isinstance(listing["amazon_bullets"], list) and len(listing["amazon_bullets"]) >= 5
        assert listing["amazon_title"] and isinstance(listing["amazon_title"], str)
        assert listing["flipkart_title"]
        assert listing["meesho_title"]

    def test_product_status_completed_and_quality_set(self, api, test_product_with_ai):
        pid, _ = test_product_with_ai
        d = api.get(f"{BASE_URL}/api/products/{pid}").json()
        assert d["product"]["status"] == "completed"
        assert d["product"]["quality_score"] > 0


class TestQuality:
    def test_quality_shape(self, api, test_product_with_ai):
        pid, _ = test_product_with_ai
        r = api.get(f"{BASE_URL}/api/products/{pid}/quality")
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d["score"], int) and 0 <= d["score"] <= 100
        assert isinstance(d["breakdown"], dict) and len(d["breakdown"]) > 0
        assert isinstance(d["suggestions"], list)


class TestVersionsRestore:
    def test_versions_and_restore(self, api, test_product_with_ai):
        pid, _ = test_product_with_ai
        # Trigger a second listing update via edit (cheap, no AI) to grow versions.
        e = api.put(
            f"{BASE_URL}/api/products/{pid}/listing",
            json={"meta_description": "TEST_edited_meta_description_v1"},
        )
        assert e.status_code == 200
        v = api.get(f"{BASE_URL}/api/products/{pid}/versions")
        assert v.status_code == 200
        vdata = v.json()
        assert isinstance(vdata["versions"], list)
        assert len(vdata["versions"]) >= 1
        # Restore version index 0 (the original generated listing)
        r = api.post(f"{BASE_URL}/api/products/{pid}/restore/0")
        assert r.status_code == 200, r.text
        restored = r.json()
        # After restore, meta_description should match version-0 snapshot (not the edited value)
        assert restored.get("meta_description") != "TEST_edited_meta_description_v1"


# --------------------------------------------------------------------------- #
# Regenerate one section (AI call — 1 extra)
# --------------------------------------------------------------------------- #
class TestRegenerate:
    def test_regenerate_meta_description(self, api, test_product_with_ai):
        pid, _ = test_product_with_ai
        r = api.post(
            f"{BASE_URL}/api/products/{pid}/regenerate/meta_description",
            timeout=90,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["section"] == "meta_description"
        assert isinstance(d["value"], str) and len(d["value"]) > 0


# --------------------------------------------------------------------------- #
# Image presets (no AI)
# --------------------------------------------------------------------------- #
class TestImagePresets:
    def test_22_presets(self, api):
        r = api.get(f"{BASE_URL}/api/image-presets")
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, list) and len(d) == 22
        # required preset ids referenced by the frontend
        ids = {p["id"] for p in d}
        for req in ("white_bg", "lifestyle", "sale_banner", "instagram_post"):
            assert req in ids
        for p in d:
            for k in ("id", "label", "group", "prompt"):
                assert k in p


# --------------------------------------------------------------------------- #
# AI Agent (single call — image steps may fail; test agent still completes)
# --------------------------------------------------------------------------- #
class TestAgent:
    def test_agent_pipeline(self, api):
        # Create a small product WITHOUT images so agent skips analyze+images
        # (avoids extra image budget calls). Text listings step must still complete.
        r = api.post(
            f"{BASE_URL}/api/products?status=draft",
            json={
                "product_name": "TEST_AgentSmall",
                "brand": "TEST_B",
                "category": "Home",
                "material": "Plastic",
            },
        )
        pid = r.json()["id"]
        try:
            a = api.post(f"{BASE_URL}/api/products/{pid}/agent", json={}, timeout=120)
            assert a.status_code == 200, a.text
            d = a.json()
            steps = {s["step"]: s for s in d["steps"]}
            # analyze skipped (no image), listings done, images skipped (no image), quality done
            assert steps["listings"]["status"] == "done"
            assert steps["quality"]["status"] == "done"
            assert "score" in steps["quality"]
            assert d["listing"]["amazon_title"]
            assert d["product"]["status"] == "completed"
            assert d["quality"]["score"] > 0
        finally:
            api.delete(f"{BASE_URL}/api/products/{pid}")


# --------------------------------------------------------------------------- #
# Settings — including own-key toggle + empty api_key preservation
# --------------------------------------------------------------------------- #
class TestSettings:
    def test_get_returns_ai_flags(self, api):
        r = api.get(f"{BASE_URL}/api/settings")
        assert r.status_code == 200
        d = r.json()
        assert d["ai_configured"] is True
        assert d["emergent_key_available"] is True

    def test_update_own_key_and_empty_preserves(self, api):
        # Set an own key first
        p1 = {
            "ai_provider": "gemini", "api_key": "TEST_own_key_ABC123",
            "use_own_key": True, "default_marketplace": "amazon",
            "brand_tone": "luxury", "language": "English",
            "title_char_limit": 180, "description_char_limit": 1500,
            "default_export_format": "amazon",
        }
        r1 = api.put(f"{BASE_URL}/api/settings", json=p1)
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["brand_tone"] == "luxury"
        assert d1["use_own_key"] is True

        # Now send empty api_key — must preserve TEST_own_key_ABC123
        p2 = {**p1, "api_key": "", "brand_tone": "casual"}
        r2 = api.put(f"{BASE_URL}/api/settings", json=p2)
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["brand_tone"] == "casual"
        # api_key_set flag should still be true
        assert d2.get("api_key_set") is True

        # Reset back to sane defaults for other tests
        api.put(f"{BASE_URL}/api/settings", json={
            "ai_provider": "gemini", "api_key": "", "use_own_key": False,
            "default_marketplace": "amazon", "brand_tone": "professional",
            "language": "English", "title_char_limit": 200,
            "description_char_limit": 2000, "default_export_format": "generic",
        })


# --------------------------------------------------------------------------- #
# Dashboard stats
# --------------------------------------------------------------------------- #
class TestStats:
    def test_stats_analytics_fields(self, api):
        r = api.get(f"{BASE_URL}/api/stats")
        assert r.status_code == 200
        d = r.json()
        for k in [
            "total", "listings_generated", "images_generated", "exports_count",
            "avg_quality", "marketplace_distribution", "category_distribution",
            "recent_activity",
        ]:
            assert k in d, f"missing {k}"
        assert isinstance(d["marketplace_distribution"], dict)
        assert isinstance(d["category_distribution"], dict)
        assert isinstance(d["recent_activity"], list)


# --------------------------------------------------------------------------- #
# Exports — all 8 types
# --------------------------------------------------------------------------- #
class TestExports:
    @pytest.mark.parametrize("etype", ["amazon", "flipkart", "meesho", "generic"])
    def test_xlsx(self, api, etype, test_product_with_ai):
        # ensure at least the shared TEST_ product exists so query is not empty
        r = api.post(f"{BASE_URL}/api/exports", json={"export_type": etype})
        assert r.status_code == 200, r.text
        ctype = r.headers.get("content-type", "")
        assert "spreadsheetml" in ctype, ctype
        assert zipfile.is_zipfile(io.BytesIO(r.content)), "not a valid xlsx"

    @pytest.mark.parametrize("etype", ["shopify", "woocommerce"])
    def test_csv(self, api, etype, test_product_with_ai):
        r = api.post(f"{BASE_URL}/api/exports", json={"export_type": etype})
        assert r.status_code == 200, r.text
        assert "csv" in r.headers.get("content-type", "")
        text = r.content.decode("utf-8", errors="ignore")
        # header line present
        assert "," in text.splitlines()[0]

    def test_json(self, api, test_product_with_ai):
        r = api.post(f"{BASE_URL}/api/exports", json={"export_type": "json"})
        assert r.status_code == 200
        assert "json" in r.headers.get("content-type", "")
        data = json.loads(r.content.decode("utf-8"))
        assert isinstance(data, list) and len(data) >= 1
        assert "product" in data[0] and "listing" in data[0]

    def test_zip(self, api, test_product_with_ai):
        r = api.post(f"{BASE_URL}/api/exports", json={"export_type": "zip"})
        assert r.status_code == 200
        assert "zip" in r.headers.get("content-type", "")
        assert zipfile.is_zipfile(io.BytesIO(r.content))
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            names = zf.namelist()
            assert any(n.endswith(".xlsx") for n in names)

    def test_unknown_type_400(self, api, test_product_with_ai):
        r = api.post(f"{BASE_URL}/api/exports", json={"export_type": "bogus"})
        assert r.status_code == 400


# --------------------------------------------------------------------------- #
# Bulk upload + generate-all (1 AI call — CSV with 1 row)
# --------------------------------------------------------------------------- #
class TestBulkUpload:
    def test_upload_csv_and_generate_all(self, api):
        csv = "product_name,brand,category\nTEST_BulkOne,TEST_B,Home\n"
        r = requests.post(
            f"{BASE_URL}/api/uploads",
            headers={"Authorization": f"Bearer {TOKEN}"},
            files={"file": ("bulk.csv", csv, "text/csv")},
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["row_count"] == 1
        uid = d["id"]

        gen = api.post(f"{BASE_URL}/api/uploads/{uid}/generate-all", timeout=120)
        assert gen.status_code == 200, gen.text
        gd = gen.json()
        assert gd["created"] == 1
        assert isinstance(gd["failed"], list)

        # cleanup created products
        for p in api.get(f"{BASE_URL}/api/products?search=TEST_BulkOne").json():
            api.delete(f"{BASE_URL}/api/products/{p['id']}")
