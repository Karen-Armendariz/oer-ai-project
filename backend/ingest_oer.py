from pathlib import Path
from backend.oer_client import OpenALGClient
from backend.rag_store import OERRAGStore
from backend.keywording import clean_html, extract_keywords_from_syllabus

# Standardize path handling
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
SYLLABI_DIR = PROJECT_ROOT / "data" / "syllabi"

def find_syllabus_for_query(query):
    query = query.upper().strip()
    for f in SYLLABI_DIR.rglob("*.txt"):
        if query in f.name.upper():
            return f
    return None

def main():
    course_query = input("Enter course code (example: BIOL 1101K): ").strip()
    if not course_query:
        print("No course entered. Exiting.")
        return

    syllabus_file = find_syllabus_for_query(course_query)
    if not syllabus_file:
        print(f"No syllabus found for '{course_query}'. Please run ingest_data.py first.")
        return

    print(f"Reading syllabus: {syllabus_file.name}")
    syllabus_text = syllabus_file.read_text(encoding="utf-8")
    
    keywords = extract_keywords_from_syllabus(syllabus_text, course_query=course_query)
    print(f"Extracted keywords for OER search: {keywords}")

    # Search Open ALG
    client = OpenALGClient()
    print("Searching Open ALG Library...")
    oer_results = client.fetch_all_relevant_oer(keywords)
    
    # Process and Clean results
    for res in oer_results:
        res['license'] = clean_html(res['license']).strip()
        res['description'] = clean_html(res['description']).strip()

    print(f"Found {len(oer_results)} unique OER resources.")

    if not oer_results:
        print("\nNo resources found for the extracted keywords. Try updating your syllabus keywords or manually searching.")
        return

    # Store in ChromaDB
    store = OERRAGStore(persist_directory=str(PROJECT_ROOT / "data" / "chroma_db"))
    store.add_resources(oer_results)

if __name__ == "__main__":
    main()
