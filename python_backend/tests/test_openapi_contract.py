"""Contract-style checks that do not require a live database."""
import unittest


class TestOpenAPIContract(unittest.TestCase):
    def test_openapi_paths_include_core_endpoints(self):
        try:
            from main import app
        except ModuleNotFoundError as exc:
            self.skipTest(f"Install python_backend/requirements.txt to run this test ({exc})")

        from fastapi.openapi.utils import get_openapi

        schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=getattr(app, "description", None),
            routes=app.routes,
        )
        paths = schema.get("paths") or {}
        self.assertIn("/health", paths)
        self.assertIn("/api/auth/login", paths)
        self.assertIn("/api/auth/refresh", paths)
