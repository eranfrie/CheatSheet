import requests

from tests.test_e2e_base import TestE2eBase, URL


# pylint: disable=R0201 (no-self-use)
class TestE2edwiPreviewEndpointDisplayCheatsheets(TestE2eBase):
    def test_empty_snippet(self):
        response = requests.get(URL.PREVIEW.value)
        assert response.status_code == 200

    def test_preview_is_markdown_format(self):
        response = requests.get(URL.PREVIEW.value + "?snippet=```\n123\n```")
        assert response.status_code == 200
        assert "LightGray" in response.text \
            and "</pre>" in response.text \
            and "</code>" in response.text
