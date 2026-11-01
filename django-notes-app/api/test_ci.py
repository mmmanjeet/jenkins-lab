"""API smoke tests used by the lab's CI pipeline."""
from django.test import TestCase
from rest_framework.test import APIClient


class NotesApiSmokeTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_empty_notes_list(self):
        response = self.client.get("/api/notes/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_note_lifecycle(self):
        response = self.client.post(
            "/api/notes/create/", {"body": "Created by CI"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        note_id = response.json()["id"]

        response = self.client.get(f"/api/notes/{note_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["body"], "Created by CI")

        response = self.client.put(
            f"/api/notes/{note_id}/update/", {"body": "Updated by CI"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(f"/api/notes/{note_id}/")
        self.assertEqual(response.json()["body"], "Updated by CI")

        response = self.client.delete(f"/api/notes/{note_id}/delete/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/notes/").json(), [])
