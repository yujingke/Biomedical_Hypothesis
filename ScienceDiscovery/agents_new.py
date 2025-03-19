"""
agents_new.py

Implements an Autogen multi-agent system for generating disease-related hypotheses:
1) user -> planner -> diseaseExplorer -> ontologist -> scientist -> pubmedAgent -> criticAgent
   with "assistant" agent managing the tool calls (Neo4j query & PubMed query).
"""

import sys
sys.path.insert(0, r"D:\DFKI\SciAgentsDiscovery-openai\SciAgentsDiscovery-main")

from ScienceDiscovery.llm_config import (
    gpt4turbo_mini_config,
    gpt4turbo_mini_config_graph,
    gpt4o_mini_config_graph
)
from ScienceDiscovery.neo4j_query import Neo4jGraph
# 创建 Neo4j 连接实例
neo4j_graph = Neo4jGraph(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="12345678"
)
from ScienceDiscovery.pubmed_query import (
    query_pubmed_by_mesh,
    query_pubmed_by_keyword
)

from typing import List, Dict, Union, Optional
import autogen
from autogen import AssistantAgent, UserProxyAgent, register_function
from autogen.agentchat.contrib.img_utils import get_pil_image, pil_to_data_uri
from autogen import ConversableAgent
from autogen.agentchat import GroupChat, GroupChatManager

########################################
# 1) Agents
########################################

# user
user = UserProxyAgent(
    name="user",
    system_message=(
        "user. You will provide a disease or a combination of disease and entity (like a protein) to investigate "
        "new hypotheses. For example, 'Generate new hypotheses about Diabetes' or 'Generate new hypotheses about Breast Cancer and p53'."
    ),
    human_input_mode="ALWAYS",
    code_execution_config=False,
    llm_config=None,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
)

# planner
plannerAgent = AssistantAgent(
    name="plannerAgent",
    system_message = """
plannerAgent.
Task: Outline the multi-step plan:
1) diseaseExplorerAgent: Retrieve the relevant subgraph from Neo4j.
2) ontologist: Define terms and relationships from the subgraph.
3) scientist: Generate exactly 5 new hypotheses based on the subgraph and definitions.
4) pubmedAgent: Find literature references for each hypothesis.
5) criticAgent: Evaluate the support for each hypothesis.
""",
    llm_config=gpt4turbo_mini_config,
    description="Propose a multi-step plan. Do not call any tools directly."
)

# diseaseExplorer
diseaseExplorerAgent = AssistantAgent(
    name="diseaseExplorerAgent",
    system_message = """
diseaseExplorerAgent.
1) Analyze the user query to extract precise disease or entity keywords.
2) Retrieve the relevant subgraph from the knowledge graph using the appropriate tool.
3) Pass the subgraph summary to the ontologist.
""",
    llm_config=gpt4turbo_mini_config_graph,
    description="Extracts keywords and retrieves relevant knowledge graph information."
)

# ontologist
ontologist = AssistantAgent(
    name="ontologist",
    system_message = """
Ontologist.
Given a subgraph summary, perform the following:
1) Provide concise definitions for each node (including type, function, and relevance).
2) Describe each relationship (type, effect, direction) without adding extra nodes or edges.
Then, pass the subgraph summary and definitions to the scientist.
""",
    llm_config=gpt4turbo_mini_config,
    description="Define subgraph terms based on the textual summary."
)

# scientist
scientist = AssistantAgent(
    name="scientist",
    system_message = """
Scientist.
With only the subgraph summary and definitions available (no external literature), your tasks are:
1) Generate exactly 5 novel or incremental hypotheses about the disease, focusing on subgraph connections.
2) Format each hypothesis with:
   - **Disease**: ...
   - **Entity**: ...
   - **Relationship Type**: ...
   - **Effect**: ...
   - **Rationale**: ...
No disclaimers. Output exactly 5 enumerated items.
""",
    llm_config=gpt4turbo_mini_config_graph,
    description="Generate new hypotheses solely based on the subgraph information."
)

# pubmedAgent
pubmedAgent = AssistantAgent(
    name="pubmedAgent",
    system_message = """
pubmedAgent.
We have received 5 hypotheses from the Scientist.
Task:
1) For each hypothesis, extract key disease and entity terms.
2) For each key term:
   - First, attempt to retrieve relevant articles using query_articles_by_keyword.
   - If no articles are found, fall back to query_latest_articles.
3) Collect up to 5 relevant articles per hypothesis.
4) Pass each hypothesis along with its articles to criticAgent.
Ensure that each hypothesis is linked with its corresponding articles.
""",
    llm_config=gpt4turbo_mini_config_graph,
    description="Extract literature references for each hypothesis."
)

# criticAgent
criticAgent = AssistantAgent(
    name="criticAgent",
    system_message = """
criticAgent.
Given:
- 5 hypotheses from the Scientist.
- Literature references from PubMed.
Task:
1) Evaluate each hypothesis: determine if the articles provide strong, weak, or no support.
2) Optionally, note any contradictory evidence.
3) Conclude by outputting "TERMINATE".
""",
    llm_config=gpt4o_mini_config_graph,
    description="Assess the hypotheses based on literature support."
)

# assistant (Tool execution proxy)
assistant = AssistantAgent(
    name="assistant",
    system_message = """
assistant.
You are a tool execution proxy. Your role is to execute the tools and functions as suggested by the planner or other agents.
Return the tool call results directly.
""",
    llm_config=gpt4turbo_mini_config,
    description="Executes registered tools automatically as per the plan."
)

########################################
# 2) Tools: Register tools on assistant (with double registration on planner/pubmedAgent)
########################################

@user.register_for_execution()
@diseaseExplorerAgent.register_for_llm()
@assistant.register_for_llm(
    description="Retrieve subgraph summary from Neo4j using keywords and optional relationship types. Keywords must be comma-separated."
)
def query_filtered_subgraph_summary(
    keywords: str,
    important_rel_types: Optional[str] = None,
    max_level: int = 2,
    limit: int = 100
) -> str:
    """
    Call Neo4j to retrieve a disease subgraph:
    - keywords: comma-separated keywords.
    - important_rel_types: optional comma-separated relationship types.
    - max_level: query depth.
    - limit: maximum number of nodes.
    """
    keyword_list = [kw.strip() for kw in keywords.split(",")]
    rel_type_list = None
    if important_rel_types:
        rel_type_list = [rt.strip() for rt in important_rel_types.split(",")]
    return neo4j_graph.get_subgraph(
        keywords=keyword_list,
        relationship_types=rel_type_list,
        max_level=max_level,
        limit=limit
    )

@user.register_for_execution()
@pubmedAgent.register_for_llm(
    description="Query PubMed by MeSH term. Provide a mesh_term, start_date, and retmax. Returns article details."
)
@assistant.register_for_llm(
    description="Query PubMed by MeSH term. Provide a mesh_term, start_date, and retmax. Returns article details."
)
def query_latest_articles(mesh_term: str, start_date: str, retmax: int = 5) -> str:
    """
    Query PubMed using a MeSH term and a start date, returning the top retmax articles.
    """
    try:
        articles = query_pubmed_by_mesh(mesh_term, start_date, retmax=retmax)
        if not articles:
            return "No articles found."
        lines = []
        for art in articles:
            lines.append(f"{art['pub_date']}: {art['title']}")
            lines.append(f"Abstract: {art['abstract']}")
            lines.append(f"URL: {art['url']}\n")
        return "\n".join(lines)
    except Exception as e:
        return f"PubMed query error: {str(e)}"

@user.register_for_execution()
@pubmedAgent.register_for_llm(
    description="Query PubMed by a general keyword. Optionally filter by start date and limit results with retmax."
)
@assistant.register_for_llm(
    description="Query PubMed by a general keyword. Optionally filter by start date and limit results with retmax."
)
def query_articles_by_keyword(keyword: str, start_date: str = None, retmax: int = 5) -> str:
    """
    Query PubMed by a general keyword (e.g., 'BRCA1').
    If start_date is provided, filter accordingly.
    """
    try:
        articles = query_pubmed_by_keyword(keyword, start_date)
        if not articles:
            return "No articles found."
        lines = []
        for art in articles:
            lines.append(f"{art['pub_date']}: {art['title']}")
            lines.append(f"Abstract: {art['abstract']}")
            lines.append(f"URL: {art['url']}\n")
        return "\n".join(lines)
    except Exception as e:
        return f"PubMed query error: {str(e)}"

########################################
# 3) Create GroupChat and GroupChatManager (using auto speaker selection)
########################################

def create_group_chat():
    # Reset each agent
    user.reset()
    plannerAgent.reset()
    diseaseExplorerAgent.reset()
    ontologist.reset()
    scientist.reset()
    pubmedAgent.reset()
    criticAgent.reset()
    assistant.reset()

    from autogen import GroupChat

    groupchat = GroupChat(
        agents=[
            user,  
            plannerAgent, 
            diseaseExplorerAgent,
            ontologist,
            scientist,
            pubmedAgent,
            criticAgent,
            assistant
        ],
        messages=[],
        max_round=50,
        admin_name='user',
        send_introductions=True,
        allow_repeat_speaker=True,
        speaker_selection_method='auto'
    )
    return groupchat

def create_manager():
    groupchat = create_group_chat()
    from autogen import GroupChatManager
    manager = GroupChatManager(
        groupchat=groupchat,
        llm_config=gpt4turbo_mini_config,
        system_message="Please follow the plan: user -> plannerAgent -> diseaseExplorerAgent -> ontologist -> scientist -> pubmedAgent -> criticAgent."
    )
    return manager, groupchat

########################################
# 4) Main: Run the chat using GroupChatManager (auto speaker selection)
########################################

# if __name__ == "__main__":
#     manager, groupchat = create_manager()
#     messages = [
#       {
#         "role": "user",
#         "name": "user",
#         "content": "Generate new hypotheses about 'Parkinson disease' please."
#       }
#     ]
#     result = manager.run_chat(messages=messages, sender=user, config=groupchat)
#     print("=== FINAL RESULT ===")
#     for msg in groupchat.messages:
#         print(f"{msg['role']} ({msg['name']}): {msg['content']}")
