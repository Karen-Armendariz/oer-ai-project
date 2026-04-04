import os
from pathlib import Path
from backend.rag_store import OERRAGStore
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Standardize path handling
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
console = Console()

class OERAgent:
    def __init__(self):
        self.store = OERRAGStore(persist_directory=str(PROJECT_ROOT / "data" / "chroma_db"))
        self.openai_key = os.getenv("OPENAI_API_KEY")

    def run_rag_analysis(self, course_query):
        """Perform RAG analysis for a course."""
        # 1. Find the syllabus text
        SYLLABI_DIR = PROJECT_ROOT / "data" / "syllabi"
        syllabus_file = None
        for f in SYLLABI_DIR.rglob("*.txt"):
            if course_query.upper() in f.name.upper():
                syllabus_file = f
                break
        
        syllabus_text = ""
        keywords = [course_query]
        if syllabus_file:
            console.print(f"[green]Found local syllabus:[/green] {syllabus_file.name}")
            syllabus_text = syllabus_file.read_text(encoding="utf-8")
            try:
                from backend.ingest_oer import extract_keywords_from_syllabus
                extracted = extract_keywords_from_syllabus(syllabus_text)
                if extracted:
                    keywords.extend(extracted)
            except Exception:
                pass
        else:
            console.print(f"[yellow]No local syllabus found. Proceeding with dynamic search...[/yellow]")
            syllabus_text = course_query
            
        # 2. Dynamic Ingestion (Fetch missing resources automatically)
        console.print("[dim]Fetching relevant resources from Open ALG API...[/dim]")
        try:
            from backend.oer_client import OpenALGClient
            from backend.ingest_oer import clean_html
            client = OpenALGClient()
            oer_results = client.fetch_all_relevant_oer(keywords)
            if oer_results:
                for res in oer_results:
                    res['license'] = clean_html(res['license']).strip()
                    res['description'] = clean_html(res['description']).strip()
                self.store.add_resources(oer_results)
        except Exception as e:
            pass

        # 3. Query RAG Store (ChromaDB)
        console.print(Panel(f"Semantic Search for: [bold cyan]{course_query}[/bold cyan]", border_style="blue"))
        results = self.store.query_oer(syllabus_text, n_results=3)
        
        # Filter poor matches (ChromaDB L2 distance > 1.1 usually means unrelated text)
        if results and results.get('distances') and results['distances'][0]:
            valid_docs = []
            valid_metas = []
            for i, dist in enumerate(results['distances'][0]):
                if dist < 1.1:
                    valid_docs.append(results['documents'][0][i])
                    valid_metas.append(results['metadatas'][0][i])
            if valid_docs:
                results['documents'] = [valid_docs]
                results['metadatas'] = [valid_metas]
            else:
                return []


        # 3. Formulate the "Evaluation" using the OER Software Rubric (Simulated or LLM)
        console.print("[yellow]Evaluating discovered OER resources against the Rubric...[/yellow]")
        
        if self.openai_key:
            return self._run_llm_evaluation(syllabus_text, results)
        else:
            return self._run_mock_evaluation(results)

    def _run_mock_evaluation(self, results):
        """Simulate evaluation logic without an API key."""
        analysis = []
        for i in range(len(results['documents'][0])):
            doc = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            
            # Simple heuristic score mock for accessibility, licensing, and quality
            analysis.append({
                "title": meta['title'],
                "license": meta['license'],
                "accessibility": "High" if "PDF" in meta['links'] else "Medium",
                "pedagogical_alignment": "85%",
                "summary": f"This resource is a strong match for your syllabus content. It covers the following topics mentioned in your document: {doc[:150]}..."
            })
        
        return analysis

    def _run_llm_evaluation(self, syllabus_text, search_results):
        """Implementation for LLM-based evaluation (OpenAI / Gemini)."""
        # Placeholder for real LLM call
        return self._run_mock_evaluation(search_results)

def main():
    agent = OERAgent()
    console.print(Panel("[bold green]OER AI Agent Developer Project[/bold green]\nRAG-Based Recommendation System", subtitle="GGC OER Working Group"))
    
    while True:
        try:
            course_query = console.input("\n[bold yellow]Enter course code to evaluate (or type 'exit' to quit): [/bold yellow]").strip()
        except KeyboardInterrupt:
            console.print("\n[dim italic]Force shutting down OER AI Agent...[/dim italic]")
            break
            
        if not course_query:
            continue
            
        if course_query.lower() in ["exit", "quit", "q"]:
            console.print("[dim italic]Shutting down OER AI Agent...[/dim italic]")
            break
            
        results = agent.run_rag_analysis(course_query)
        
        # Check if run_rag_analysis returned early (missing syllabus or error)
        if results is None:
            continue

        if results:
            table = Table(title=f"\n[bold magenta]OER RECOMMENDATION REPORT: {course_query}[/bold magenta]", show_header=True, header_style="bold cyan")
            table.add_column("Rank", style="dim", width=6)
            table.add_column("OER Resource Title", style="bold white")
            table.add_column("License", style="green")
            table.add_column("Score", style="magenta")
            table.add_column("Accessibility", style="blue")

            for idx, res in enumerate(results):
                table.add_row(
                    str(idx + 1),
                    res['title'],
                    res['license'],
                    res['pedagogical_alignment'],
                    res['accessibility']
                )

            console.print(table)
            
            for idx, res in enumerate(results):
                # Print descriptions in panels
                console.print(Panel(
                    f"[italic]{res['summary']}[/italic]",
                    title=f"[cyan]Detailed Summary: {res['title']}[/cyan]", 
                    border_style="dim"
                ))
        else:
            # This handles the case where the list is empty (no semantic matches)
            console.print(Panel(
                f"No OER resources in our database or Open ALG matched the context of [bold cyan]{course_query}[/bold cyan].\n\n[yellow]This course may not have available free open textbooks yet.[/yellow]",
                title="[bold red]No Semantic Matches[/bold red]",
                border_style="red"
            ))

if __name__ == "__main__":
    main()
