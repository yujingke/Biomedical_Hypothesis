# llm_kg

# Automated Disease Knowledge Discovery with Multi‑Agent AI

*Leveraging multiple AI agents, a biomedical knowledge graph, and literatures to automate hypothesis generation in disease research.*

## Project Overview

This project is an **automated scientific research system** focused on disease-related knowledge discovery. It uses a team of AI agents (powered by large language models) that collaborate to generate and refine research hypotheses about diseases. The agents draw on two major sources of information: a **biomedical knowledge graph** and the **scientific literature**. The knowledge graph used is **PrimeKG**, a precision medicine knowledge graph that integrates data on over 17,000 diseases and 4 million related entities and relationships ([GitHub - mims-harvard/PrimeKG: Precision Medicine Knowledge Graph (PrimeKG)](https://github.com/mims-harvard/PrimeKG#:~:text=Precision%20Medicine%20Knowledge%20Graph%20,CSV%20file%20to%20get%20started)). The literature source is **PubMed**, which provides scientific publications (e.g. abstracts of biomedical research articles). By combining these sources, the system can uncover connections (such as gene-disease associations or drug repurposing opportunities) and propose plausible hypotheses. An *iterative refinement loop* is employed, where one agent proposes hypotheses and another agent critiques them. This mimics a scientific peer-review process, improving the hypothesis through each cycle.

At the core, the project uses the **AutoGen framework** for multi-agent orchestration. AutoGen is an open-source framework from Microsoft Research for building AI agents and enabling them to cooperate on tasks ([AutoGen - Microsoft Research](https://www.microsoft.com/en-us/research/project/autogen/#:~:text=AutoGen%20is%20an%20open,and%20research%20on%20agentic%20AI)). Using AutoGen, the project defines specialized agents (for example, a *Knowledge Graph Agent*, a *Literature Agent*, a *Hypothesis Agent*, and a *Critic Agent*) that communicate with each other. The Knowledge Graph agent extracts facts from the Neo4j graph database, the Literature agent fetches relevant information from PubMed, the Hypothesis agent synthesizes a theory, and the Critic agent provides feedback. This collaboration allows the system to automatically cycle through **hypothesis generation and validation**, aiming to emulate how a team of human researchers might brainstorm and refine a scientific hypothesis.

## Key Features

- **Multi-Agent Collaboration**: Utilizes the AutoGen multi-agent framework to coordinate several AI agents with different roles. These agents converse and cooperate to solve the complex task of knowledge discovery, rather than relying on a single monolithic model. This design enables a division of labor (one agent can specialize in querying data, another in analysis, etc.) and leads to more coherent and validated outcomes through agent-to-agent dialogue.

- **Knowledge Graph Integration**: Incorporates **PrimeKG**, a comprehensive biomedical knowledge graph, as a core knowledge source. PrimeKG (loaded into a Neo4j database) provides structured information about diseases, genes, proteins, drugs, symptoms, and their interrelations ([GitHub - mims-harvard/PrimeKG: Precision Medicine Knowledge Graph (PrimeKG)](https://github.com/mims-harvard/PrimeKG#:~:text=Precision%20Medicine%20Knowledge%20Graph%20,CSV%20file%20to%20get%20started)). The system can query this graph to find relevant connections (for example, all genes associated with a disease, or known drug targets) and use that as evidence or context for hypothesis generation. This graph-powered reasoning helps ensure the hypotheses are grounded in known biomedical facts.

- **Literature Mining (PubMed)**: Includes an agent that automatically searches PubMed (the database of biomedical research papers) for up-to-date information. Given an emerging idea or a query (such as a specific gene-disease pair), the Literature agent will retrieve relevant abstracts or findings from recent publications. This ensures that the hypotheses consider current scientific evidence and not just static database facts. It adds a layer of *textual evidence* to support or refute the connections found in the knowledge graph.

- **Iterative Hypothesis Generation & Critique**: Implements an iterative loop where hypotheses are generated and then refined through feedback. The Hypothesis agent uses information from both the knowledge graph and literature to propose a scientific hypothesis (e.g., *"Gene X could be a therapeutic target for Disease Y because... "*). The Critic agent then reviews this hypothesis, checking for logical consistency, missing evidence, or unsupported claims. The Critic provides feedback or questions (much like a peer reviewer or a skeptical collaborator), prompting the Hypothesis agent to revise or strengthen the hypothesis. This back-and-forth cycle continues for multiple iterations, leading to progressively more refined and credible hypotheses.

- **Graph Reasoning and Analysis**: The project uses the **GraphReasoning** library alongside Neo4j to perform advanced reasoning on the knowledge graph. This may include finding shortest paths between entities, discovering subgraphs that connect a drug to a disease through intermediate nodes, or identifying key hubs in the network that might be of interest. Such analytical capabilities allow the agents to not only fetch direct facts but also *infer indirect relationships* (for instance, if Drug A targets Protein B, and Protein B is involved in Disease C, the system might hypothesize Drug A could have relevance for Disease C). The integration of **NetworkX** and **pyvis** further allows for analysis and visualization of these relationship graphs, which can help in understanding and explaining the hypotheses.

- **Configurable LLM Settings**: Through the `llm_config.py` module, the project allows configuration of the large language model parameters and API keys. This means developers can plug in their preferred LLM service (such as OpenAI GPT-4 or others) by setting the appropriate API keys or endpoints in this config file. The design is flexible to accommodate different model backends or adjustments (like temperature, max tokens, etc.), which can be tuned to balance creativity and factuality in the agents' outputs.

## Installation Guide

Follow these steps to set up the project environment and dependencies:

1. **Prerequisites**: Ensure you have **Python 3.8+** installed. Also, install **Neo4j** (version 5.x recommended) on your local machine or have access to a Neo4j database server. You will need permissions to create a database and import data into Neo4j. 

2. **Project Code**: Clone the project repository to your local machine.

3. **Python Environment**: It is recommended to create a virtual environment for this project to avoid dependency conflicts. 

4. **Dependencies Installation**: Install the required Python packages. The project provides a list of dependencies (see `requirements.txt` or similar). You can install them with pip:
   ```bash
   pip install -r requirements.txt
   ``` 
   This will install all needed libraries with the specific versions tested. Key dependencies include:
   - **AutoGen 0.3.2** (multi-agent framework for LLMs)  
   - **GraphReasoning 0.2.0** (graph analysis utilities)  
   - **Neo4j Python Driver 5.27.0** (to connect to the Neo4j database)  
   - **NetworkX 3.x** and **pyvis 0.3.2** (for graph algorithms and visualization)  
   - **LangChain 0.3.19** (LLM orchestration toolkit, optionally used)  
   - **Transformers 4.x and Torch 2.x** (for deep learning and possibly using local language models or embeddings)  
   - **Pandas 2.2.3, NumPy 1.24.3, SciPy 1.11.3** (for data manipulation and any scientific computing needs)  
   - **scikit-learn 1.3.x** and **seaborn 0.13.2** (possibly for data analysis or plotting if needed)  
   - **Markdown/markdown2 3.x** (for formatting outputs or reports in Markdown)  
   - **pdfkit 1.0.0 and WeasyPrint 64.1** (for generating PDF reports from HTML/Markdown content)  
   - **tqdm 4.66+** (for progress bars in long-running processes)  
   Make sure the installation completes without errors. (Some packages like WeasyPrint may require additional system dependencies, such as Cairo or Pango on certain systems. Refer to WeasyPrint documentation if you encounter installation issues.)

5. **Setting up PrimeKG in Neo4j**: The project requires a local instance of the **PrimeKG** knowledge graph. To set this up:
   - Download the PrimeKG dataset. The PrimeKG authors provide a CSV file of the knowledge graph (nodes and edges) on Harvard Dataverse ([GitHub - mims-harvard/PrimeKG: Precision Medicine Knowledge Graph (PrimeKG)](https://github.com/mims-harvard/PrimeKG#:~:text=Precision%20Medicine%20Knowledge%20Graph%20,CSV%20file%20to%20get%20started)). You can obtain the dataset via the PrimeKG GitHub page or directly from its DOI (e.g., search for "PrimeKG Harvard Dataverse" to find the download link). Make sure you have the CSV file (or files) that contain the nodes and relationships of the graph.
   - Start your Neo4j server (e.g., using Neo4j Desktop or Neo4j Server). Create a new database (if using Neo4j Desktop, you can create a new local graph database).
   - **Import data**: Use neo4j-admin import to import PrimeKG into the database. 
   - After import, verify that the data is in Neo4j by running some test queries in the Neo4j browser 

6. **Configure Access and Keys**: Open the file `llm_config.py` in the project. This file contains configuration settings for connecting to external services and models. You should check and update the following:
   - **Neo4j Connection**: Ensure the Neo4j connection URL, username, and password are set correctly.
   - **LLM API Keys**: If the agents use an external Large Language Model service (such as OpenAI's GPT-4o-mini)
   - **PubMed Access**: The project likely uses the `requests` library or an API to fetch data from PubMed. 

7. **Final Setup Check**: Once dependencies are installed and configurations are set, ensure that everything is ready:
   - The Python environment has all needed packages (you can run `pip list` to double-check versions).
   - Neo4j is running and the PrimeKG data is loaded (you can test connectivity by running a small Python snippet using the Neo4j driver to query something, or simply proceed to run the project which will test the connection).
   - API keys and configurations are in place in `llm_config.py`. 

With the above in place, you are ready to run the project.
