import logging
import os
import requests

logger = logging.getLogger(__name__)

class OpenALGClient:
    BASE_URL = "https://alg.manifoldapp.org/api/v1"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENALG_API_KEY")

    def _headers(self) -> dict:
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    def search_projects(self, query):
        """Search for projects (textbooks/resources) by keyword."""
        url = f"{self.BASE_URL}/projects"
        params = {
            "filter[keyword]": query
        }
        response = requests.get(url, params=params, headers=self._headers(), timeout=20)
        response.raise_for_status()
        return response.json().get('data', [])

    def get_project_details(self, project_id):
        """Get detailed metadata and resources for a specific project.
        Returns None on 401 so callers can fall back to search-list payload (no API key).
        """
        url = f"{self.BASE_URL}/projects/{project_id}"
        params = {
            "include": "resource_collections,resources"
        }
        response = requests.get(url, params=params, headers=self._headers(), timeout=20)
        if response.status_code == 401:
            return None
        response.raise_for_status()
        return response.json()

    def fetch_all_relevant_oer(self, keywords):
        """Fetch OER resources for a list of keywords and return structured data."""
        results = []
        seen_ids = set()

        for kw in keywords:
            try:
                projects = self.search_projects(kw)
            except requests.RequestException as exc:
                logger.warning("Open ALG search failed for '%s': %s", kw, exc)
                continue
            for p in projects:
                p_id = p['id']
                if p_id not in seen_ids:
                    try:
                        details = self.get_project_details(p_id)
                    except requests.RequestException as exc:
                        logger.warning("Open ALG detail fetch failed for '%s': %s", p_id, exc)
                        continue
                    if details is None:
                        logger.debug(
                            "Open ALG detail unauthorized for '%s'; using search data.",
                            p_id,
                        )
                        results.append(self._format_project_from_search(p))
                    else:
                        results.append(self._format_project(details))
                    seen_ids.add(p_id)
        
        return results

    def _format_project(self, details):
        project_data = details['data']
        attrs = project_data['attributes']
        
        # Extract license from metadata.rights if available
        license_info = attrs.get('metadata', {}).get('rights', "Unknown License")
        
        # Extract resource links
        included = details.get('included', [])
        links = []
        for item in included:
            if item['type'] == 'resources':
                # Manifold often stores files in attachmentStyles
                attach = item['attributes'].get('attachmentStyles', {})
                if 'original' in attach:
                    links.append({
                        "id": item['id'],
                        "title": item['attributes'].get('title'),
                        "url": attach['original']
                    })

        return {
            "id": project_data['id'],
            "title": attrs.get('title'),
            "description": attrs.get('description', ""),
            "creators": attrs.get('creatorNames', []),
            "license": license_info,
            "links": links
        }

    def _format_project_from_search(self, project):
        attrs = project.get("attributes", {})
        return {
            "id": project.get("id"),
            "title": attrs.get("title"),
            "description": attrs.get("description", ""),
            "creators": attrs.get("creatorNames", []),
            "license": attrs.get("metadata", {}).get("rights", "Unknown License"),
            "links": [],
        }

if __name__ == "__main__":
    client = OpenALGClient()
    test_results = client.fetch_all_relevant_oer(["Biology"])
    print(f"Found {len(test_results)} results for 'Biology'")
