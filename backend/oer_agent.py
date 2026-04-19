from backend.config import Settings
from backend.logging_setup import configure_logging
from backend.oer_service import OERService
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
console = Console()

class OERAgent:
    def __init__(self):
        self.settings = Settings()
        configure_logging(self.settings.log_level)
        self.service = OERService(settings=self.settings)

    def run_rag_analysis(self, course_query):
        """Perform RAG analysis for a course."""
        console.print(Panel(f"Semantic Search for: [bold cyan]{course_query}[/bold cyan]", border_style="blue"))
        payload = self.service.search(course_query=course_query)
        results = payload["results"]
        console.print("[yellow]Evaluating discovered OER resources against the Rubric...[/yellow]")
        return self._run_mock_evaluation(results)

    def _run_mock_evaluation(self, results):
        """Simulate evaluation logic without an API key."""
        analysis = []
        for res in results:
            score = res.get("score", 0)
            alignment = f"{score:.0f}%"
            analysis.append({
                "title": res.get("title"),
                "license": res.get("license"),
                "accessibility": "High" if "pdf" in str(res.get("links", "")).lower() else "Medium",
                "pedagogical_alignment": alignment,
                "summary": f"This resource aligns with your syllabus keywords ({res.get('keyword_overlap', 0)} overlaps) and scores {alignment} relevance."
            })
        
        return analysis

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
