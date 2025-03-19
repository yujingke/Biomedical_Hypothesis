# from ScienceDiscovery.utils import *
# from ScienceDiscovery.llm_config import *
# from ScienceDiscovery.graph import *
# from ScienceDiscovery.neo4j_query import neo4j_graph
# # from utils import *
# # from llm_config import *
# # from graph import *
# # from neo4j_query import neo4j_graph

# from typing import List, Dict
# from typing import Union
# import autogen
# from autogen import AssistantAgent
# from autogen.agentchat.contrib.img_utils import get_pil_image, pil_to_data_uri
# from autogen import register_function
# from autogen import ConversableAgent
# from typing import Dict, List
# from typing import Annotated, TypedDict
# from autogen import Agent

# user = autogen.UserProxyAgent(
#     name="user",
#     is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
#     human_input_mode="ALWAYS",
#     system_message="user. You are a human admin. You pose the task.",
#     llm_config=False,
#     code_execution_config=False,
# )

# planner = AssistantAgent(
#     name="planner",
#     system_message = '''Planner. You are a helpful AI assistant specialized in biomedical research. Your task is to suggest a comprehensive plan to generate and evaluate novel hypotheses about relationships in a biomedical knowledge graph.

# Explain the Plan: Begin by providing a clear overview of how to explore potential relationships (e.g., between diseases, genes, or proteins) in the graph.
# Break Down the Plan: For each step in the process, explain the reasoning behind it, and describe the specific actions that need to be taken.
# No Execution: Your role is strictly to suggest the plan. Do not take any actions to execute it.
# No Tool Call: If a tool call is required, include the name of the tool and the agent who calls it in the plan. However, you are not allowed to call any tool or function yourself.
# ''',
#     llm_config=gpt4turbo_mini_config,
#     description='Who can suggest a step-by-step plan to solve the task by breaking down the task into simpler sub-tasks.',
# )





# assistant = AssistantAgent(
#     name="assistant",
#     system_message = '''You are a helpful AI assistant.
    
# Your role is to call the appropriate tools and functions as suggested in the plan. You act as an intermediary between the planner's suggested plan and the execution of specific tasks using the available tools. 
# You ensure that the correct parameters are passed to each tool and that the results are accurately reported back to the team.
# Return "TERMINATE" in the end when the task is over.
# ''',
#     llm_config=gpt4turbo_mini_config,
#     description='''An assistant who calls the tools and functions as needed and returns the results. Tools include "rate_novelty_feasibility" and "generate_path".''',
# )



# ontologist = AssistantAgent(
#     name="ontologist",
#     system_message = '''
# Ontologist. You are a sophisticated ontologist specializing in biomedical knowledge graphs.

# Your task:
# 1. Define each concept (e.g., genes, proteins, metabolites, or diseases) in the provided knowledge path. Each definition must be based on the knowledge graph and include the following details:
#    - **Biological role**: Describe the biological function of the concept.
#    - **Relevance**: Explain its importance to human health or disease.

# 2. Discuss each relationship in the provided path with detailed context. For each relationship, provide:
#    - **Type**: Specify if the relationship is causal, associative, or regulatory.
#    - **Nature**: Indicate whether the effect is direct or indirect (e.g., mediated by pathways or networks).
#    - **Direction and Effect**: Specify the effect (e.g., promotes, inhibits, or neutral) and its impact.

# ### Response Format:
# ### Definitions:
# - {Node Name}: {Type} - {Definition}
#   Example: BRCA1: gene/protein - A tumor suppressor gene involved in DNA repair and associated with breast and ovarian cancer.

# ### Relationships:
# - {Node Name 1} -> {Node Name 2}: {Relation Type}
#   Example: BRCA1 -> ATR: protein-protein interaction (BRCA1 activates ATR in response to DNA damage, promoting DNA repair pathways).

# ### Instructions:
# - Strictly use concepts and relationships from the provided knowledge path. Do NOT add new concepts or relationships.
# - Begin your response directly with "### Definitions".
# - Perform ONLY the tasks assigned to you in the plan and do NOT execute any tools or functions.
# ''',
#     llm_config=gpt4turbo_mini_config,
#     description='I can define each of the terms and discusses the relationships in the path.',
# )


# scientist = AssistantAgent(
#     name="scientist",
#     system_message = '''
# Scientist. You are a biomedical researcher specializing in hypothesis generation and scientific innovation.

# Your task:
# 1. Analyze the definitions and relationships provided by the Ontologist from the given knowledge path.
# 2. Propose **exactly 5 structured hypotheses** about the potential roles of biomedical entities (e.g., genes, proteins, metabolites) in the occurrence, progression, pathology, or dysfunction of diseases.
# 3. Each hypothesis must be **strictly based on the nodes and relationships in the knowledge path**. Do not introduce new nodes, diseases, or relationships that are not part of the provided path.

# 1. **Disease**: ...
#    **Entity**: ...
#    **Relationship Type**: Causal/Indirect
#    **Effect**: Promotes/Inhibits/Neutral
#    **Rationale**: (One or two lines)

# 2. **Disease**: ...
#    **Entity**: ...
#    ...

# 3...
# 4...
# 5...

# No concluding statements, no disclaimers. 
# No partial lines. 
# Strictly 5 items, labeled "1." through "5.".
# '''
# ,
#     llm_config=gpt4turbo_mini_config_graph,
#     description='I can craft the research proposal with key aspects based on the definitions and relationships acquired by the ontologist. I am **ONLY** allowed to speak after `Ontologist`',
# )


# hypothesis_agent = AssistantAgent(
#     name="hypothesis_agent",
#     system_message='''
# hypothesis_agent. 
# You receive:
# (1) The 5 raw hypotheses from Scientist 
# (2) The function_call results for each Entity (a map: { entityName: [ {related_name, relation_type} ...] }).

# Task: 
# Produce "### Expanded Hypothesis" combining each hypothesis with the related info from the map.
# ''',
#     llm_config=gpt4o_mini_config_graph,
#     description='Refines the final hypothesis with Neo4j data.'
# )

# # outcome_agent = AssistantAgent(
# #     name="outcome_agent",
# #     system_message = '''outcome_agent. Carefully expand on the ```{outcome}``` of the research proposal developed by the scientist.

# # Critically assess the original content and improve on it. \
# # Add more specifics, quantitive scientific information (such as chemical formulas, numbers, sequences, processing conditions, microstructures, etc.), \
# # rationale, and step-by-step reasoning. When possible, comment on specific modeling and simulation techniques, experimental methods, or particular analyses. 

# # Start by carefully assessing this initial draft from the perspective of a peer-reviewer whose task it is to critically assess and improve the science of the following:

# # <outcome>
# # where <outcome> is the outcome aspect of the research proposal.  

# # Do not add any introductory phrases. Your response begins with your response, with a heading: ### Expanded ... 
# # ''',
# #     llm_config=gpt4o_mini_config_graph,
# #     description='''I can expand the "outcome" aspect of the research proposal crafted by the "scientist".''',
# # )

# # mechanism_agent = AssistantAgent(
# #     name="mechanism_agent",
# #     system_message = '''mechanism_agent. Carefully expand on this particular aspect: ```{mechanism}``` of the research proposal.

# # Critically assess the original content and improve on it. \
# # Add more specifics, quantitive scientific information (such as chemical formulas, numbers, sequences, processing conditions, microstructures, etc.), \
# # rationale, and step-by-step reasoning. When possible, comment on specific modeling and simulation techniques, experimental methods, or particular analyses. 

# # Start by carefully assessing this initial draft from the perspective of a peer-reviewer whose task it is to critically assess and improve the science of the following:

# # <mechanism>
# # where <mechanism> is the mechanism aspect of the research proposal.  

# # Do not add any introductory phrases. Your response begins with your response, with a heading: ### Expanded ... 
# # ''',
# #     llm_config=gpt4o_mini_config_graph,
# #     description='''I can expand the "mechanism" aspect of the research proposal crafted by the "scientist"''',
# # )

# # design_principles_agent = AssistantAgent(
# #     name="design_principles_agent",
# #     system_message = '''design_principles_agent. Carefully expand on this particular aspect: ```{design_principles}``` of the research proposal.

# # Critically assess the original content and improve on it. \
# # Add more specifics, quantitive scientific information (such as chemical formulas, numbers, sequences, processing conditions, microstructures, etc.), \
# # rationale, and step-by-step reasoning. When possible, comment on specific modeling and simulation techniques, experimental methods, or particular analyses. 

# # Start by carefully assessing this initial draft from the perspective of a peer-reviewer whose task it is to critically assess and improve the science of the following:

# # <design_principles>
# # where <design_principles> is the design_principles aspect of the research proposal.  

# # Do not add any introductory phrases. Your response begins with your response, with a heading: ### Expanded ...
# # ''',
# #     llm_config=gpt4o_mini_config_graph,
# #     description='''I can expand the "design_principle" aspect of the research proposal crafted by the "scientist".''',
# # )

# # unexpected_properties_agent = AssistantAgent(
# #     name="unexpected_properties_agent",
# #     system_message = '''unexpected_properties_agent. Carefully expand on this particular aspect: ```{unexpected_properties}``` of the research proposal.

# # Critically assess the original content and improve on it. \
# # Add more specifics, quantitive scientific information (such as chemical formulas, numbers, sequences, processing conditions, microstructures, etc.), \
# # rationale, and step-by-step reasoning. When possible, comment on specific modeling and simulation techniques, experimental methods, or particular analyses. 

# # Start by carefully assessing this initial draft from the perspective of a peer-reviewer whose task it is to critically assess and improve the science of the following:

# # <unexpected_properties>
# # where <unexpected_properties> is the unexpected_properties aspect of the research proposal.  

# # Do not add any introductory phrases. Your response begins with your response, with a heading: ### Expanded ...
# # ''',
# #     llm_config=gpt4o_mini_config_graph,
# #     description='''I can expand the "unexpected_properties" aspect of the research proposal crafted by the "scientist.''',
# # )

# # comparison_agent = AssistantAgent(
# #     name="comparison_agent",
# #     system_message = '''comparison_agent. Carefully expand on this particular aspect: ```{comparison}``` of the research proposal.

# # Critically assess the original content and improve on it. \
# # Add more specifics, quantitive scientific information (such as chemical formulas, numbers, sequences, processing conditions, microstructures, etc.), \
# # rationale, and step-by-step reasoning. When possible, comment on specific modeling and simulation techniques, experimental methods, or particular analyses. 

# # Start by carefully assessing this initial draft from the perspective of a peer-reviewer whose task it is to critically assess and improve the science of the following:

# # <comparison>
# # where <comparison> is the comparison aspect of the research proposal.  

# # Do not add any introductory phrases. Your response begins with your response, with a heading: ### Expanded ...
# # ''',
# #     llm_config=gpt4o_mini_config_graph,
# #     description='''I can expand the "comparison" aspect of the research proposal crafted by the "scientist".''',
# # )

# # novelty_agent = AssistantAgent(
# #     name="novelty_agent",
# #     system_message = '''novelty_agent. Carefully expand on this particular aspect: ```{novelty}``` of the research proposal.

# # Critically assess the original content and improve on it. \
# # Add more specifics, quantitive scientific information (such as chemical formulas, numbers, sequences, processing conditions, microstructures, etc.), \
# # rationale, and step-by-step reasoning. When possible, comment on specific modeling and simulation techniques, experimental methods, or particular analyses. 

# # Start by carefully assessing this initial draft from the perspective of a peer-reviewer whose task it is to critically assess and improve the science of the following:

# # <novelty>
# # where <novelty> is the novelty aspect of the research proposal.  

# # Do not add any introductory phrases. Your response begins with your response, with a heading: ### Expanded ...
# # ''',
# #     llm_config=gpt4o_mini_config_graph,
# #     description='''I can expand the "novelty" aspect of the research proposal crafted by the "scientist".''',
# # )

# critic_agent = AssistantAgent(
#     name="critic_agent",
#     system_message = '''
# critic_agent. You are a biomedical AI expert tasked with evaluating structured hypotheses generated by the Scientist.

# Your task:
# 1. **Summarize the hypotheses**:
#    - Provide a concise summary of the 10 structured hypotheses, focusing on the key disease-entity relationships, relationship types (causal/indirect), and their predicted effects (promotes/inhibits/neutral).

# 2. **Critically review the hypotheses**:
#    - Evaluate the strengths and weaknesses of the hypotheses, with specific focus on:
#      - Biological plausibility.
#      - Scientific depth.
#      - Logical consistency.
#    - Suggest improvements, including potential refinements to the hypotheses, missing considerations, or additional data sources.

# 3. **Identify impactful scientific questions**:
#    - From the hypotheses, identify:
#      1. The single most impactful hypothesis that can be tested using **molecular modeling**. Provide detailed steps for setting up and conducting the modeling, including specific techniques or analyses.
#      2. The single most impactful hypothesis that can be tested using **synthetic biology**. Outline the experimental design and key steps, highlighting innovative aspects of the work.

# ### Response Format:
# Your response should be structured as follows:
# 1. **Summary of Hypotheses**:
#    - Hypothesis 1: [Brief description of the disease-entity relationship, type, and effect].
#    - ...
#    - Hypothesis 10: [Brief description].

# 2. **Critical Review**:
#    - Strengths: [Detailed review of strengths].
#    - Weaknesses: [Detailed review of weaknesses].
#    - Suggested Improvements: [Specific suggestions for refinement].

# 3. **Impactful Questions**:
#    - **Molecular Modeling**:
#      - Hypothesis: [The most relevant hypothesis].
#      - Key Steps: [Detailed steps for setting up and conducting modeling].
#    - **Synthetic Biology**:
#      - Hypothesis: [The most relevant hypothesis].
#      - Key Steps: [Detailed steps for designing and conducting experiments].

# ### Instructions:
# - Ensure your response is concise, professional, and follows the structured format.
# - Focus strictly on the hypotheses provided by the Scientist.
# - Do NOT evaluate novelty or feasibility. This is outside your scope.
# '''
# ,
#     llm_config=gpt4o_mini_config_graph,
#     description='''I can summarizes, critique, and suggest improvements after all seven aspects of the proposal have been expanded by the agents.''',
# )


# novelty_assistant = autogen.AssistantAgent(
#     name="novelty_assistant",
#     system_message='''
# You are a critical AI assistant specializing in evaluating biomedical research hypotheses.

# Task:
# 1. For each hypothesis provided:
#    - Extract the **key terms** (e.g., disease name, biomedical entity, relationship type).
#    - Use the PubMed API to retrieve the top 5 relevant articles based on the key terms.
# 2. Evaluate the hypothesis using the retrieved literature:
#    - **Novelty**: Assess the originality of the hypothesis. Does it explore new areas or concepts not extensively covered in the literature?
#    - **Feasibility**: Evaluate the practicality of testing the hypothesis experimentally or computationally. Are there established methods or evidence supporting the feasibility of this hypothesis?

# Output Format:
# - For each hypothesis:
#    1. **PubMed Articles**: List the titles and URLs of the top 5 articles.
#    2. **Novelty Rating**: Score from 1 (low) to 10 (high). Justify the rating with evidence from the articles.
#    3. **Feasibility Rating**: Score from 1 (low) to 10 (high). Justify the rating with evidence from the articles.
# - Conclude the evaluation by stating "TERMINATE".

# Instructions:
# - Ensure each hypothesis is evaluated independently.
# - Provide concise, evidence-based justifications for your ratings.
# - Use only the retrieved PubMed articles for evaluation. Avoid external assumptions or unsupported claims.
# ''',
#     llm_config=gpt4turbo_mini_config,
# )

# novelty_admin = autogen.UserProxyAgent(
#     name="novelty_admin",
#     human_input_mode="NEVER",
#     max_consecutive_auto_reply=10,
#     is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
#     code_execution_config=False,  # Please set use_docker=True if docker is available to run the generated code. Using docker is safer than running the generated code directly.
#     llm_config=False,
# )


# @novelty_admin.register_for_execution()
# @novelty_assistant.register_for_llm(description='''This function searches for academic papers using the PubMed API based on a specified query.
# The query should be constructed with relevant keywords separated by "+". It retrieves the top 5 articles.''')
# def response_to_query(query: Annotated[str, 'The query for the paper search. The query must consist of relevant keywords separated by +.']) -> str:
#     # Define the API endpoint URL
#     search_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
#     fetch_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'

#     # Query parameters for search
#     search_params = {
#         'db': 'pubmed',
#         'term': query,
#         'retmax': 5,
#         'retmode': 'json'
#     }

#     # API key (optional)
#     api_key = os.getenv("PUBMED_API_KEY")
#     if api_key:
#         search_params['api_key'] = api_key

#     # Search PubMed
#     response = requests.get(search_url, params=search_params)
#     if response.status_code == 200:
#         search_data = response.json()
#         if 'esearchresult' in search_data and 'idlist' in search_data['esearchresult']:
#             article_ids = search_data['esearchresult']['idlist']

#             # Fetch article details
#             fetch_params = {
#                 'db': 'pubmed',
#                 'id': ','.join(article_ids),
#                 'retmode': 'json'
#             }
#             fetch_response = requests.get(fetch_url, params=fetch_params)
#             if fetch_response.status_code == 200:
#                 fetch_data = fetch_response.json()
#                 articles = []
#                 for article_id in article_ids:
#                     if article_id in fetch_data['result']:
#                         article = fetch_data['result'][article_id]
#                         title = article.get('title', 'No title available')
#                         url = f"https://pubmed.ncbi.nlm.nih.gov/{article_id}/"
#                         articles.append(f"- {title} ({url})")
#                 return "\n".join(articles)
#             else:
#                 return f"Error fetching article details: {fetch_response.status_code}"
#         else:
#             return "No articles found for the given query."
#     else:
#         return f"Error during search: {response.status_code}"

# @user.register_for_execution()
# @planner.register_for_llm()
# @assistant.register_for_llm(description='''This function can be used to create a knowledge path. The function may either take two keywords as the input or randomly assign them and then returns a path between these nodes. 
# The path contains several concepts (nodes) and the relationships between them (edges). THe function returns the path.
# Do not use this function if the path is already provided. If neither path nor the keywords are provided, select None for the keywords so that a path will be generated between randomly selected nodes.''')
# def generate_path(keyword_1: str = "TP53", keyword_2: str = "BRCA1") -> str:
    
#     if keyword_1 is None:
#         keyword_1 = random.choice(list(G.nodes))
#     if keyword_2 is None:
#         keyword_2 = random.choice(list(G.nodes))

#     print(f"Selected nodes: {keyword_1} and {keyword_2}")

#     # Generate random paths
#     path_list_for_vis, path_list_for_vis_string = create_path(
#         G, embedding_tokenizer, embedding_model, node_embeddings,
#         generate_graph_expansion=None, randomness_factor=0.8, num_random_waypoints=10,
#         shortest_path=False,  
#         second_hop=False, data_dir='./', save_files=False, verbatim=True,
#         keyword_1=keyword_1, keyword_2=keyword_2
#     )

    
#     return path_list_for_vis_string

# @user.register_for_execution()
# @planner.register_for_llm()
# @assistant.register_for_llm(description='''Use this function to rate the novelty and feasibility of a research idea against the literature. The function uses PubMed to access the literature articles.  
# The function will return the novelty and feasibility rate from 1 to 10 (lowest to highest). The input to the function is the hypothesis with its details.''')
# def rate_novelty_feasibility(hypothesis: Annotated[str, 'the research hypothesis.']) -> str:
#     res = novelty_admin.initiate_chat(
#     novelty_assistant,
#         clear_history=True,
#         silent=False,
#         max_turns=10,
#     message=f'''Rate the following research hypothesis\n\n{hypothesis}. \n\nCall the function three times at most, but not in parallel. Wait for the results before calling the next function. ''',
#         summary_method="reflection_with_llm",
#         summary_args={"summary_prompt" : "Return all the results of the analysis as is."}
#     )

#     return res.summary


# ###############################################################################
# # 2) Tools: query_entity_definitions / query_related_entities
# ###############################################################################
# @user.register_for_execution()
# @assistant.register_for_llm(description="Retrieve definitions for a given entity from Neo4j.")
# def query_entity_definitions(entity_name: str) -> List[Dict]:
#     return neo4j_graph.get_entity_definitions(entity_name)

# @user.register_for_execution()
# @assistant.register_for_llm(description="Retrieve related entities and their relationships from Neo4j.")
# def query_related_entities(entity_name: str) -> List[Dict]:
#     return neo4j_graph.get_related_entities(entity_name)
# ###############################################################################
# # Custom Manager
# ###############################################################################
# class MyGroupChatManager(autogen.GroupChatManager):
#     def __init__(self, groupchat, llm_config, system_message):
#         super().__init__(groupchat, llm_config, system_message)
#         self.onto_done = False
#         self.scientist_done = False
#         self.scientist_retry = 0
#         self.collected_hypotheses = ""
#         self.entities_list = []
#         self.entities_data = {}  # {entName: [ {related_name, relation_type}, ...], ...}
#         self.query_in_progress = False
#         self.refine_done = False
#         self.critic_done = False

#     def _on_llm_response(self, speaker_name, message_dict):
#         super()._on_llm_response(speaker_name, message_dict)

#         content = message_dict["message"].get("content","")
#         finish_reason = message_dict.get("finish_reason")

#         #
#         # step 1: Planner -> Ontologist
#         #
#         if speaker_name=="planner" and not self.onto_done:
#             self.onto_done = True
#             self.groupchat.post_message(
#                 speaker_name="ontologist",
#                 content="(Please define the knowledge path now...)"
#             )
#             return

#         #
#         # step 2: Ontologist -> Scientist
#         #
#         if speaker_name=="ontologist" and not self.scientist_done:
#             self.scientist_done = True
#             self.groupchat.post_message(
#                 speaker_name="scientist",
#                 content="(Now produce EXACTLY 5 structured hypotheses, no function calls. Strictly 1..5 format.)"
#             )
#             return

#         #
#         # step 3: Scientist -> parse or re-ask
#         #
#         if speaker_name=="scientist" and not self.refine_done:
#             # check if 5. in text => 5 items
#             # also see if they used correct lines
#             if "5." in content:
#                 # store
#                 self.collected_hypotheses = content
#                 # parse out "Entity: X" lines
#                 pattern = r"Entity\W*\:\W*([A-Za-z0-9_-]+)"
#                 found_ents = re.findall(pattern, content)
#                 self.entities_list = list(set(found_ents))  # unique
#                 # if none => skip queries
#                 if not self.entities_list:
#                     # just pass to hypothesis_agent
#                     self.refine_done = True
#                     self.groupchat.post_message(
#                         speaker_name="hypothesis_agent",
#                         content=f"(Scientist's base hypothesis:\n{content}\nNo entity found => no query.)"
#                     )
#                 else:
#                     # do queries
#                     ent = self.entities_list.pop()
#                     self.query_in_progress = True
#                     self.groupchat.post_message(
#                         speaker_name="assistant",
#                         content="(Auto function_call for entity...)",
#                         function_call={
#                             "name": "query_related_entities",
#                             "arguments": json.dumps({"entity_name": ent})
#                         }
#                     )
#             else:
#                 # re-ask scientist
#                 self.scientist_retry += 1
#                 if self.scientist_retry<3:
#                     self.groupchat.post_message(
#                         speaker_name="scientist",
#                         content="(You must produce 5 structured items labeled 1..5, no extra lines or disclaimers. Try again.)"
#                     )
#                 else:
#                     # fallback
#                     self.groupchat.post_message(
#                         speaker_name="assistant",
#                         content="Scientist failed to comply. Terminating. \nTERMINATE"
#                     )
#             return

#         #
#         # step 4: if finish_reason=="function_call" => manager calls the actual python function
#         # autogen typically does it automatically, but let's parse:
#         if finish_reason=="function_call":
#             fc = message_dict["message"].get("function_call", {})
#             fn_name = fc.get("name","")
#             fn_args = fc.get("arguments","{}")
#             try:
#                 fn_args_obj = json.loads(fn_args)
#             except:
#                 fn_args_obj = {}

#             if fn_name=="query_related_entities":
#                 entity_name = fn_args_obj.get("entity_name","UNKNOWN")
#                 results = query_related_entities(entity_name)
#                 # store
#                 self.entities_data[entity_name] = results
#                 # post result
#                 self.groupchat.post_message(
#                     speaker_name="assistant",
#                     content=f"Function call result: query_related_entities({entity_name}): {results}"
#                 )
#                 # see if more entities
#                 if self.entities_list:
#                     next_ent = self.entities_list.pop()
#                     self.groupchat.post_message(
#                         speaker_name="assistant",
#                         content="(Auto next query...)",
#                         function_call={
#                             "name": "query_related_entities",
#                             "arguments": json.dumps({"entity_name": next_ent})
#                         }
#                     )
#                 else:
#                     # done all queries => pass to hypothesis_agent
#                     self.refine_done = True
#                     self.query_in_progress = False
#                     data_str = json.dumps(self.entities_data, indent=2)
#                     self.groupchat.post_message(
#                         speaker_name="hypothesis_agent",
#                         content=f"(Scientist's base hypothesis:\n{self.collected_hypotheses}\n\nrelated_entities_map:\n{data_str})"
#                     )
#             return

#         #
#         # step 5: HypothesisAgent -> Critic
#         #
#         if speaker_name=="hypothesis_agent" and not self.critic_done:
#             self.critic_done = True
#             self.groupchat.post_message(
#                 speaker_name="critic_agent",
#                 content="(Please evaluate final expanded hypothesis...)"
#             )
#             return

#         #
#         # step 6: Critic -> end
#         #
#         if speaker_name=="critic_agent":
#             self.groupchat.post_message(speaker_name="assistant", content="TERMINATE")
#             return


# ###############################################################################
# # create groupchat & manager
# ###############################################################################
# planner.reset()
# assistant.reset()
# ontologist.reset()
# scientist.reset()
# hypothesis_agent.reset()
# critic_agent.reset()

# groupchat = autogen.GroupChat(
#     agents=[user, planner, assistant, ontologist, scientist, hypothesis_agent, critic_agent],
#     messages=[],
#     max_round=50,
#     admin_name='user',
#     send_introductions=True,
#     allow_repeat_speaker=True,
#     speaker_selection_method='manual',
# )

# manager = MyGroupChatManager(
#     groupchat=groupchat,
#     llm_config=gpt4turbo_mini_config,
#     system_message='Plan->Ontologist->Scientist(5 items)->(function_call each entity)->HypothesisAgent->Critic->END.'
# )