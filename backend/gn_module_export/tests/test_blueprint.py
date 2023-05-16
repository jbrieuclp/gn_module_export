import pytest
from jsonschema import validate as validate_json
from flask import url_for

from geonature.tests.fixtures import *
from geonature.tests.utils import set_logged_user_cookie
from pypnusershub.tests.utils import set_logged_user_cookie

from gn_module_export.tests.fixtures import exports

from .fixtures import *


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestExportsBlueprints:
    def test_private_export_without_token_or_login(self, users, exports):
        # private without token and without loggin
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_user_associated"].id,
            )
        )
        assert response.status_code == 403

    def test_private_export_with_fake_token(self, users, exports):
        # with fake token
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_user_associated"].id,
                token="fake_token",
            )
        )
        assert response.status_code == 403

    def test_private_export_with_good_token(self, users, exports):
        # with good token
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_user_associated"].id,
                token=exports["private_user_associated"].cor_roles_exports[0].token,
            )
        )
        assert response.status_code == 200

    def test_private_export_with_allowed_id_role(self, users, exports):
        # with an allowed user and without token
        set_logged_user_cookie(self.client, users["self_user"])
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_user_associated"].id,
            )
        )
        assert response.status_code == 200

    def test_private_export_with_allowed_group(self, group_and_user, exports):
        # log with a user which is in a group associated with "private_group_associated" export
        set_logged_user_cookie(self.client, group_and_user["user"])
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_group_associated"].id,
            )
        )
        assert response.status_code == 200

    def test_private_export_with_scope_3(self, users, exports):
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_user_associated"].id,
            )
        )
        assert response.status_code == 200

    def test_private_export_with_unautorized_user(self, users, exports):
        # with an not allowed user and without token
        set_logged_user_cookie(self.client, users["noright_user"])
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_user_associated"].id,
            )
        )
        assert response.status_code == 403

    def test_get_one_export_api_public(self, exports):
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["public"].id,
            )
        )
        assert response.status_code == 200

    def test_export_schema(self, exports, users):
        schema = {
            "type": "object",
            "properties": {
                "license": {
                    "type": "object",
                    "properties": {
                        "href": {"type": "string"},
                        "name": {"type": "string"},
                    },
                },
                "items": {"type": "array"},
                "limit": {"type": "number"},
                "page": {"type": "number"},
                "total": {"type": "number"},
                "total_filtered": {"type": "number"},
            },
        }
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_user_associated"].id,
            )
        )
        assert response.status_code == 200
        validate_json(instance=response.json, schema=schema)

    def test_unknown_export(self, exports, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.get(
            url_for("exports.get_one_export_api", id_export=1000000)
        )
        assert response.status_code == 404

    def test_get_all_exports_with_scope_3(self, exports, users):
        fixtures_export_id = set([export.id for _, export in exports.items()])
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.get(url_for("exports.get_exports"))
        assert response.status_code == 200
        response_id_export = set([exp["id"] for exp in response.json])
        assert fixtures_export_id.issubset(response_id_export)

    def test_get_all_exports_with_scope_1_2_no_group(self, exports, users):
        allowed_fixture_ids = set()
        for _, exp in exports.items():
            if exp.public or exp.label == "Private2":
                allowed_fixture_ids.add(exp.id)
        set_logged_user_cookie(self.client, users["self_user"])
        response = self.client.get(url_for("exports.get_exports"))
        assert response.status_code == 200
        response_id_export = set([exp["id"] for exp in response.json])
        assert allowed_fixture_ids.issubset(response_id_export)

    def test_get_all_exports_with_scope_1_2_group(self, exports, users, group_and_user):
        allowed_fixture_ids = set()
        allowed_fixture_label = set()
        for _, exp in exports.items():
            if exp.public or exp.label in ("Private1"):
                allowed_fixture_ids.add(exp.id)
                allowed_fixture_label.add(exp.label)
        set_logged_user_cookie(self.client, group_and_user["user"])
        response = self.client.get(url_for("exports.get_exports"))
        assert response.status_code == 200
        response_id_export = set([exp["id"] for exp in response.json])
        assert allowed_fixture_ids.issubset(response_id_export)
        response_label_export = set([exp["label"] for exp in response.json])
        assert allowed_fixture_label.issubset(response_label_export)

    def test_get_all_exports_with_scope_0(self, exports, users, group_and_user):
        # Only public exports OR 403 ????
        allowed_fixture_ids = set()
        for _, exp in exports.items():
            if exp.public:
                allowed_fixture_ids.add(exp.id)

        set_logged_user_cookie(self.client, users["noright_user"])

        response = self.client.get(url_for("exports.get_exports"))
        assert response.status_code == 200

        response_id_export = set([exp["id"] for exp in response.json])
        assert allowed_fixture_ids.issubset(response_id_export)
