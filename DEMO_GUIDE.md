# 🎓 OER AI Agent: Project Demo Guide

Welcome to the **OER AI Agent Developer Project**! This guide is designed to help anyone—from faculty to student developers—demonstrate the power of **Retrieval-Augmented Generation (RAG)** applied to Open Educational Resources (OER).

## 🌍 Quick "Run from Anywhere" Cheat Sheet
To run these from **any** folder in your terminal, use these full paths:

| Task | Absolute Command |
| :--- | :--- |
| **Initial Setup** | `/Users/farhanarahman/IdeaProjects/oer-ai-project/setup.sh` |
| **Ingest Syllabus** | `/Users/farhanarahman/IdeaProjects/oer-ai-project/run_ingest.sh` |
| **Index OER Library** | `/Users/farhanarahman/IdeaProjects/oer-ai-project/run_ingest_oer.sh` |
| **Run AI Agent** | `/Users/farhanarahman/IdeaProjects/oer-ai-project/run_agent.sh` |

### **✅ Verified Course Codes for Demo**
Use any of these codes when prompted in Step 2 and Step 3:
*   **Computing (ITEC)**: `ITEC 1001`, `ITEC 2150`
*   **Biology**: `BIOL 1101K`, `BIOL 1102`, `BIOL 1107K`, `BIOL 3400K`
*   **Chemistry**: `CHEM 2211K`, `CHEM 2212K`, `BCHM 3100K`
*   **Math/Other**: `MATH 1001`, `MATH 1111`, `ENGL 1101`, `ISCI 3800`

---

## 🚀 Overview
The OER AI Agent solves a real-world problem for the **GGC OER Working Group**: Faculty lack the time to manually search large OER collections like **Open ALG**. This agent automates the search by analyzing a course syllabus and semantically matching it with high-quality, free resources.

---

## 🛠️ Step 0: Initial Setup
Before the first demo, ensure the environment is correctly configured. Open your terminal in the project root and run:

```bash
./setup.sh
```
*   **What this does**: Installs Python dependencies (Playwright, ChromaDB, Sentence-Transformers), sets up the Browser engines, and fixes all file permissions.

---

## 🎭 The Three-Step Demo Flow

### **Step 1: Scrape the Syllabus**
Start by showing how the agent gathers data from existing campus systems.

```bash
./run_ingest.sh
```
*   **Demo Action**: Follow the on-screen prompts. Log in to the Simple Syllabus library, navigate to the **School of Science and Technology**, and let the agent extract the `BIOL 1101K` syllabus.
*   **Key Talking Point**: *"The agent isn't just looking at filenames; it’s extracting the raw text and lesson plans from real course documents."*

### **Step 2: Index the OER Library**
Next, show how the agent "learns" about the Open Educational Resources available for that course.

```bash
./run_ingest_oer.sh
# Enter: BIOL 1101K
```
*   **Demo Action**: Enter the course code. Watch the agent query the **Open ALG REST API** and index the results into **ChromaDB**.
*   **Key Talking Point**: *"We are building a custom 'Knowledge Base' for this course. The agent extracts keywords from the syllabus to find relevant books and lab manuals automatically."*

### **Step 3: Generate the AI Recommendation Report**
The "Grand Finale"—perform the RAG analysis and see the Agent’s professional evaluation.

```bash
./run_agent.sh
# Enter: BIOL 1101K
```
*   **Demo Action**: Show the color-coded table and the detailed evaluations of each book’s **Licensing**, **Accessibility**, and **Pedagogical Alignment**.
*   **Key Talking Point**: *"This is the AI Agent in action! It uses Semantic Search to find the best materials and evaluates them against the OER Software Rubric without any manual searching required."*

---

## 🛡️ Why it’s "Production Ready"
In your demo, feel free to mention these **Senior QE-level features**:
*   **Semantic Matching**: It understands that "Organismal Biology" is related to "Intro to Biology" even if the titles aren't identical.
*   **Conflict Prevention**: The database is designed with `upsert` logic, meaning running the demo multiple times won't create duplicates or crash.
*   **Mac Compatibility**: Includes a project-local model cache (`.cache/`) to avoid permission errors on student laptops.

---

## ❓ Frequently Asked Questions (FAQ)
**Q: Where is the data stored?**  
A: All syllabi and the vector database are stored locally in the `/data` folder for privacy and speed.

**Q: Can I use this for other courses?**  
A: Absolutely! Just scrape a different syllabus in Step 1 and run the ingestion for that course code in Step 2.

---
**Developed for the GGC OER Working Group**
*(Farhana Rahman, Karen Armendariz, Scott Barre)*
