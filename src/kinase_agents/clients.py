"""Public REST clients. Source records are retained verbatim for auditability."""
import time
import requests

class APIClient:
    def __init__(self, timeout=30, retries=3, delay=0.3):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "KinaseAgenticAI/0.1 (academic research)"})
        self.timeout, self.retries, self.delay = timeout, retries, delay

    def get(self, url, params=None):
        for attempt in range(self.retries):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code in (429, 500, 502, 503, 504) and attempt < self.retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                response.raise_for_status()
                time.sleep(self.delay)
                return response.json()
            except (requests.Timeout, requests.ConnectionError):
                if attempt == self.retries - 1:
                    raise
                time.sleep(2 ** attempt)
        raise RuntimeError(f"Unable to retrieve {url}")

    def pages(self, url, params=None, max_pages=20):
        """Follow ChEMBL's API pagination links, with a bounded page count."""
        for _ in range(max_pages):
            data = self.get(url, params=params)
            yield data
            next_url = data.get('page_meta', {}).get('next')
            if not next_url:
                break
            url, params = requests.compat.urljoin(url, next_url), None

class PubChemAgent:
    BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    def __init__(self, api): self.api = api
    def compound(self, name="dovitinib"):
        url = f"{self.BASE}/compound/name/{requests.utils.quote(name, safe='')}/property/CanonicalSMILES,IsomericSMILES,InChIKey,MolecularFormula,MolecularWeight/JSON"
        return self.api.get(url)["PropertyTable"]["Properties"][0]

class ChEMBLAgent:
    BASE = "https://www.ebi.ac.uk/chembl/api/data"
    def __init__(self, api): self.api = api
    def search_molecules(self, name="dovitinib"):
        data = self.api.get(f"{self.BASE}/molecule/search.json", {"q": name, "limit": 100})
        return data.get("molecules", [])
    def activities(self, molecule_id, max_pages=20):
        url = f"{self.BASE}/activity.json"
        params = {"molecule_chembl_id": molecule_id, "limit": 1000}
        for page in self.api.pages(url, params, max_pages):
            yield from page.get("activities", [])

class LiteratureAgent:
    BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    def __init__(self, api): self.api = api
    def search(self, query='dovitinib OR TKI258', page_size=100):
        return self.api.get(self.BASE, {"query": query, "format": "json", "pageSize": page_size}).get("resultList", {}).get("result", [])

class StructuralAgent:
    BASE = "https://search.rcsb.org/rcsbsearch/v2/query"
    def __init__(self, api): self.api = api
    def search_by_ligand_name(self, name="dovitinib", rows=100):
        """Full-text candidate search; matches require manual or ligand-ID verification."""
        query = {"query": {"type": "terminal", "service": "full_text", "parameters": {"value": name}},
                 "return_type": "entry", "request_options": {"paginate": {"start": 0, "rows": rows}}}
        return self.api.get(self.BASE, {"json": __import__('json').dumps(query)}).get("result_set", [])
