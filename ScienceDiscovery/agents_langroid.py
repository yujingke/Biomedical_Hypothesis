"""
agents_langroid.py

This module implements a multi-agent system using Langroid v0.44+.
Overall Flow:
1. User Input: The user provides a research query.
2. PlannerAgent: Generates a detailed multi-step plan.
3. DiseaseExplorerAgent: Extracts a biomedical-related keyword from the user input and queries Neo4j for a KG summary.
4. ScientistAgent: Generates 2 initial biomedical hypotheses in a structured "Entity–Relation–Entity" format based on the KG summary.
5. For each hypothesis, perform an iterative refinement loop (up to 2 iterations):
   a. KGAgent: Retrieve extended KG context.
   b. PubmedAgent: Extract biomedical keywords and query PubMed using combinations of two keywords, returning detailed structured evidence.
   c. CriticAgent: Evaluate the hypothesis on multiple dimensions and return a JSON evaluation (including overall_score).
      - If overall_score < 5, discard the hypothesis.
      - If overall_score is high enough and CriticAgent outputs "TERMINATE", accept the hypothesis.
   d. RevisionAgent: Based on CriticAgent feedback, decide what additional external info is needed:
         - For "文献支持不足" or "不明确" → fetch extra PubMed evidence.
         - For "机制过于泛化"、"缺乏具体生物机制"、"关系机制缺乏科学依据"或"假设过于宽泛" → fetch more detailed KG info.
   e. RefineAgent: Refine the hypothesis by integrating the new external info.
6. DecisionAgent: Aggregate the refined hypotheses and produce the final decision.
"""

import sys, re, json
from itertools import combinations
from typing import Optional, List, Tuple
from pydantic import BaseModel

sys.path.insert(0, r"D:\DFKI\SciAgentsDiscovery-openai\SciAgentsDiscovery-main")

# ---------------------------
# 1. Import LLM configuration and query functions
# ---------------------------
from ScienceDiscovery.llm_config import (
    gpt4turbo_mini_config,
    gpt4turbo_mini_config_graph,
    gpt4o_mini_config_graph
)
from ScienceDiscovery.neo4j_query import Neo4jGraph, summarize_subgraph_aggregated
from ScienceDiscovery.pubmed_query import query_pubmed_by_keyword

# Create a Neo4j connection instance
neo4j_graph = Neo4jGraph(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="12345678"
)

# ---------------------------
# 2. Config cleaning and conversion functions
# ---------------------------
def clean_llm_config(llm_config):
    extra_keys = {"cache_seed", "config_list", "max_tokens"}
    if hasattr(llm_config, "dict"):
        config_dict = llm_config.dict()
        for key in extra_keys:
            config_dict.pop(key, None)
        return llm_config.__class__(**config_dict)
    elif isinstance(llm_config, dict):
        config_dict = llm_config.copy()
        for key in extra_keys:
            config_dict.pop(key, None)
        return config_dict
    else:
        return llm_config

from langroid.language_models.base import LLMConfig
from langroid.language_models.openai_gpt import OpenAIGPTConfig

def ensure_specific_llm_config(llm_config):
    if isinstance(llm_config, dict):
        return OpenAIGPTConfig(**llm_config)
    if type(llm_config) is LLMConfig:
        return OpenAIGPTConfig(**llm_config.dict())
    return llm_config

# ---------------------------
# 3. Helper functions: External query calls
# ---------------------------
def extract_overall_score(feedback: str) -> float:
    import re
    m = re.search(r"Overall Score:\s*(\d+(\.\d+)?)", feedback)
    if m:
        return float(m.group(1))
    return 0.0



def call_neo4j_subgraph(keyword: str, important_rel_types: Optional[str] = None,
                        max_level: int = 2, limit: int = 100) -> str:
    """
    Query Neo4j to retrieve a connected subgraph based on the biomedical-related keyword.
    Prints the query process and returns the complete KG summary as a string.
    (Assumes neo4j_graph.get_subgraph returns a string summary.)
    """
    print(f"[Neo4j Call] Querying Neo4j with keyword: '{keyword}'")
    summary = neo4j_graph.get_subgraph(
        keywords=[keyword],
        relationship_types=important_rel_types,
        max_level=max_level,
        limit=limit
    )
    print(f"[Neo4j Output] Aggregated KG Summary:\n{summary}\n")
    return summary


def call_pubmed_search(keywords: List[str], start_date: Optional[str] = None, retmax: int = 10) -> str:
    """
    Query PubMed using combinations of two keywords.
    For each keyword pair, perform a PubMed query and aggregate the actual results.
    If no results are found for any pair, then try single-keyword queries.
    Returns the aggregated result as a string.
    """
    results = []
    # 尝试两关键词组合检索
    for pair in combinations(keywords, 2):
        pair_list = list(pair)
        print(f"[PubMed Call] Searching PubMed with keyword pair: {pair_list}")
        result = query_pubmed_by_keyword(" ".join(pair_list), start_date)
        # 如果返回值是列表，则逐项转换为字符串
        if isinstance(result, list):
            result_str = "\n".join(
                json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else str(item)
                for item in result
            )
        else:
            result_str = str(result)
        if result_str and "No articles found" not in result_str:
            results.append(result_str)
    if results:
        combined = "\n".join(results)
    else:
        # 如果组合检索均未返回有效结果，尝试对每个关键词单独检索
        for kw in keywords:
            print(f"[PubMed Call] Searching PubMed with single keyword: {kw}")
            result = query_pubmed_by_keyword(kw, start_date)
            if isinstance(result, list):
                result_str = "\n".join(
                    json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else str(item)
                    for item in result
                )
            else:
                result_str = str(result)
            if result_str and "No articles found" not in result_str:
                results.append(result_str)
        if results:
            combined = "\n".join(results)
        else:
            combined = "No articles found for any keyword combination. Consider expanding search terms (e.g. using broader synonyms or aliases)."
    print(f"[PubMed Output] Aggregated Literature Evidence:\n{combined}\n")
    return combined


# ---------------------------
# 4. Define KeywordExtractorAgent for biomedical keywords
# ---------------------------
from langroid.agent.chat_agent import ChatAgent, ChatAgentConfig

class KeywordExtractorAgent(ChatAgent):
    def __init__(self):
        config = ChatAgentConfig(
            llm=ensure_specific_llm_config(clean_llm_config(gpt4turbo_mini_config)),
            system_message=(
                "KeywordExtractorAgent:\nTask: Extract all relevant biomedical keywords from the given text. "
                "Ignore generic words such as 'research', 'information', 'hypotheses', 'based', 'factors:', 'disease', 'genetic', 'initial', 'subgraph', 'related', 'provided'.\n"
                "Return the keywords as a comma-separated list."
            )
        )
        config.name = "KeywordExtractorAgent"
        super().__init__(config)

    def extract(self, text: str) -> List[str]:
        prompt = f"{self.config.system_message}\nText:\n{text}\nKeywords:"
        response = self.llm_response(prompt)
        if hasattr(response, 'content'):
            response = response.content
        print(f"[KeywordExtractor Output]\n{response}\n")
        stop_words = {"research", "information", "hypotheses", "based", "factors:", "disease", "genetic", "initial", "subgraph", "related", "provided"}
        keywords = [kw.strip() for kw in response.split(",") if kw.strip()]
        keywords = [kw for kw in keywords if kw.lower() not in stop_words]
        return keywords

# ---------------------------
# 5. Define KGAgent: Retrieve extended KG context for a hypothesis
# ---------------------------
class KGAgent(ChatAgent):
    def __init__(self):
        config = ChatAgentConfig(
            llm=ensure_specific_llm_config(clean_llm_config(gpt4turbo_mini_config_graph)),
            system_message=(
                "KGAgent:\nTask: Based on the given hypothesis, retrieve extended contextual information from the knowledge graph. "
                "Return important neighbor entities, multi-hop paths, and key network features concisely."
            )
        )
        config.name = "KGAgent"
        super().__init__(config)

    def step(self, hypothesis: str) -> str:
        keyword_extractor = KeywordExtractorAgent()
        keywords = keyword_extractor.extract(hypothesis)
        key = keywords[0] if keywords else " ".join(hypothesis.split()[:2])
        extended_info = call_neo4j_subgraph(key)
        print(f"[KGAgent Output] Extended KG info for hypothesis:\n{extended_info}\n")
        return extended_info

# ---------------------------
# 6. Define other agents (Planner, Scientist, Refine, PubMed, Critic, Revision, Decision)
# ---------------------------
class PlannerAgent(ChatAgent):
    def __init__(self):
        config = ChatAgentConfig(
            llm=ensure_specific_llm_config(clean_llm_config(gpt4turbo_mini_config)),
            system_message=(
                "PlannerAgent:\nTask: Develop a concise multi-step plan for the research query.\n"
                "Steps:\n"
                "1. Retrieve a KG summary from Neo4j (via DiseaseExplorerAgent).\n"
                "2. Generate 2 initial hypotheses in the 'Entity–Relation–Entity' format (via ScientistAgent).\n"
                "3. For each hypothesis, perform individual iterative refinement using KGAgent, PubMedAgent, CriticAgent, RevisionAgent, and RefineAgent.\n"
                "4. Finally, output a final decision (via DecisionAgent).\n"
            )
        )
        config.name = "PlannerAgent"
        super().__init__(config)


    def step(self, user_input: str) -> str:
        prompt = f"{self.config.system_message}\nUser Input: {user_input}\nPlease generate a detailed execution plan."
        response = self.llm_response(prompt)
        if hasattr(response, 'content'):
            response = response.content
        print(f"[Planner Output]\n{response}\n")
        return response

class DiseaseExplorerAgent(ChatAgent):
    def __init__(self):
        config = ChatAgentConfig(
            llm=ensure_specific_llm_config(clean_llm_config(gpt4turbo_mini_config_graph)),
            system_message="DiseaseExplorerAgent:\nTask: Extract a biomedical-related keyword from the user input and query Neo4j for a KG summary."
        )
        config.name = "DiseaseExplorerAgent"
        super().__init__(config)

    def step(self, user_input: str) -> str:
        m = re.search(r"'([^']+)'", user_input)
        if m:
            keyword = m.group(1)
        else:
            keyword = " ".join(user_input.split()[:2])
        kg_summary = call_neo4j_subgraph(keyword)
        print(f"[DiseaseExplorer Output]\n{kg_summary}\n")
        return kg_summary

class ScientistAgent(ChatAgent):
    def __init__(self):
        # Generate 2 hypotheses in "Entity–Relation–Entity" format.
        config = ChatAgentConfig(
            llm=ensure_specific_llm_config(clean_llm_config(gpt4turbo_mini_config_graph)),
            system_message=(
                "ScientistAgent:\nTask: Based on the KG summary provided, generate 2 initial biomedical hypotheses in the format 'EntityA may affect EntityB through RelationC'.\n"
                "Examples:\n  - 'DiseaseA may affect DiseaseB through GeneC'\n  - 'GeneX may influence DrugY efficacy via PathwayZ'\n"
                "Ensure the hypotheses are specific and clearly structured."
            )
        )
        config.name = "ScientistAgent"
        super().__init__(config)

    def step(self, kg_summary: str) -> str:
        prompt = f"{self.config.system_message}\nKG Summary:\n{kg_summary}\nPlease generate 2 initial hypotheses (one per line)."
        response = self.llm_response(prompt)
        if hasattr(response, 'content'):
            response = response.content
        print(f"[Scientist Output]\n{response}\n")
        return response

class RefineAgent(ChatAgent):
    def __init__(self):
        config = ChatAgentConfig(
            llm=ensure_specific_llm_config(clean_llm_config(gpt4turbo_mini_config_graph)),
            system_message="RefineAgent:\nTask: Refine the given hypothesis using the new external information provided."
        )
        config.name = "RefineAgent"
        super().__init__(config)

    def step(self, hypothesis: str, new_info: str) -> str:
        prompt = (
            f"{self.config.system_message}\n"
            f"Hypothesis:\n{hypothesis}\n"
            f"New Information:\n{new_info}\n"
            "Please produce a refined hypothesis that integrates both sources."
        )
        response = self.llm_response(prompt)
        if hasattr(response, 'content'):
            response = response.content
        print(f"[Refine Output]\n{response}\n")
        return response

class PubmedAgent(ChatAgent):
    def __init__(self):
        config = ChatAgentConfig(
            llm=ensure_specific_llm_config(clean_llm_config(gpt4turbo_mini_config_graph)),
            system_message=(
                "PubmedAgent:\nTask: For a given hypothesis, extract biomedical keywords (using KeywordExtractorAgent) and query PubMed using combinations of two keywords. "
                "Return structured evidence in JSON format with keys: 'support_count', 'oppose_count', 'representative_ids', and 'consensus'. "
                "Additionally, clearly state the number of articles found and provide details (title, link, PMID, abstract) for representative articles. "
                "If no articles are found, indicate so and suggest a keyword expansion strategy (e.g., using broader terms or synonyms)."
            )
        )
        config.name = "PubmedAgent"
        super().__init__(config)

    def step(self, hypothesis: str) -> str:
        if hasattr(hypothesis, 'content'):
            hypothesis = hypothesis.content
        keyword_extractor = KeywordExtractorAgent()
        extracted_keywords = keyword_extractor.extract(hypothesis)
        if not extracted_keywords:
            extracted_keywords = " ".join(hypothesis.split()[:2]).split()
        print(f"[PubMed] For hypothesis, extracted keywords: {extracted_keywords}")
        evidence = call_pubmed_search(extracted_keywords, retmax=10)
        return evidence
    
class CriticAgent(ChatAgent):
    def __init__(self):
        config = ChatAgentConfig(
            llm=ensure_specific_llm_config(clean_llm_config(gpt4o_mini_config_graph)),
            system_message=(
                "CriticAgent:\nTask: Evaluate the hypothesis using the following dimensions:\n"
                "1. Scientific Plausibility (alignment with known biological principles)\n"
                "2. Novelty (innovation compared to current knowledge)\n"
                "3. Testability (specificity for experimental validation)\n"
                "4. Clinical/Biological Relevance (potential diagnostic/therapeutic implications)\n"
                "5. Confidence & Reliability (strength of supporting evidence)\n"
                "6. Technical Clarity & Completeness (logical clarity and context)\n\n"
                "For each hypothesis, provide an overall score on a separate line in the format:\n"
                "Overall Score: X\n"
                "Then add your feedback."
            )
        )
        config.name = "CriticAgent"
        super().__init__(config)
    
    def step(self, literature_info: str, hypothesis: str) -> str:
        if hasattr(hypothesis, 'content'):
            hypothesis = hypothesis.content
        prompt = (
            f"{self.config.system_message}\n"
            f"Hypothesis:\n{hypothesis}\n\n"
            f"Literature Support:\n{literature_info}\n\n"
            "Please evaluate and output your evaluation, ending with a line 'Overall Score: X' where X is the score."
        )
        response = self.llm_response(prompt)
        if hasattr(response, 'content'):
            response = response.content
        print(f"[Critic Output]\n{response}\n")
        return response

class RevisionAgent(ChatAgent):
    def __init__(self):
        config = ChatAgentConfig(
            llm=ensure_specific_llm_config(clean_llm_config(gpt4turbo_mini_config)),
            system_message=(
                "RevisionAgent:\nTask: Based on the CriticAgent's feedback for this hypothesis, decide whether additional external information is needed. "
                "If the feedback indicates insufficient mechanistic details (e.g., mechanism too generic or lack of pathway details), output 'neo4j:<new keywords>' "
                "with the new keywords separated by commas (e.g., 'neo4j:DDT,BRCA1'). "
                "If further literature support is required, output 'pubmed:<new keywords>'. "
                "If the hypothesis is acceptable, output 'terminate'."
            )
        )
        config.name = "RevisionAgent"
        super().__init__(config)

    def step(self, critic_feedback: str, hypothesis: str) -> Tuple[str, str]:
        prompt = (
            f"{self.config.system_message}\n"
            f"Critic Feedback (text):\n{critic_feedback}\n\n"
            f"Hypothesis:\n{hypothesis}\n\n"
            "Please decide and output in the format '<option>:<new keywords>' where <option> is either 'neo4j' or 'pubmed', "
            "or output 'terminate' if no further external information is needed."
        )
        response = self.llm_response(prompt)
        if hasattr(response, 'content'):
            response = response.content
        print(f"[Revision Decision Output]\n{response}\n")
        parts = response.split(":", 1)
        if len(parts) == 2:
            option = parts[0].strip().lower()
            new_keywords = parts[1].strip()
        else:
            option = "terminate"
            new_keywords = ""
        if option == "neo4j":
            # 将 new_keywords 按逗号分割，得到关键词列表
            keywords_list = [kw.strip() for kw in new_keywords.split(",") if kw.strip()]
            if len(keywords_list) > 1:
                # 使用多个关键词进行查询（调用 Neo4j 的多关键词查询接口）
                new_info = neo4j_graph.get_subgraph(keywords=keywords_list, max_level=2, limit=100)
            else:
                new_info = call_neo4j_subgraph(new_keywords)
        elif option == "pubmed":
            keywords_list = [kw.strip() for kw in new_keywords.split(",") if kw.strip()]
            new_info = call_pubmed_search(keywords_list, retmax=10)
        else:
            option = "terminate"
            new_info = ""
        return option, new_info


class DecisionAgent(ChatAgent):
    def __init__(self):
        config = ChatAgentConfig(
            llm=ensure_specific_llm_config(clean_llm_config(gpt4turbo_mini_config_graph)),
            system_message="DecisionAgent:\nTask: Based on the final refined hypotheses and supporting evidence, output the final set of high-quality hypotheses and recommendations."
        )
        config.name = "DecisionAgent"
        super().__init__(config)

    def step(self, final_feedback: str, hypotheses: str) -> str:
        if hasattr(hypotheses, 'content'):
            hypotheses = hypotheses.content
        prompt = (
            f"{self.config.system_message}\n"
            f"Final Feedback:\n{final_feedback}\n"
            f"Final Hypotheses:\n{hypotheses}\n"
            "Please output the final decision including refined hypotheses and recommendations."
        )
        response = self.llm_response(prompt)
        if hasattr(response, 'content'):
            response = response.content
        print(f"[Decision Output]\n{response}\n")
        return response

# ---------------------------
# 8. Full Pipeline Function (Per-Hypothesis Iterative Refinement)
# ---------------------------

def run_full_pipeline(user_input: str) -> str:
    """
    Full pipeline:
    User Input -> Planner -> DiseaseExplorer -> Scientist ->
    For each hypothesis (in structured "Entity–Relation–Entity" form):
        Iterative loop (up to 3 iterations per hypothesis):
            KGAgent, PubMedAgent (only in first iteration, then use cached info), 
            CriticAgent, RevisionAgent, RefineAgent.
            If CriticAgent's evaluation overall score < 5, discard the hypothesis.
            If evaluation reaches high score (>=9) or CriticAgent outputs "TERMINATE", accept the hypothesis.
    -> Decision.
    """
    # Stage 1: Planner generates a plan.
    planner = PlannerAgent()
    plan = planner.step(user_input)
    
    # Stage 2: DiseaseExplorer retrieves KG summary via Neo4j.
    disease_explorer = DiseaseExplorerAgent()
    kg_summary = disease_explorer.step(user_input)
    
    # Stage 3: Scientist generates 3 initial hypotheses based on the KG summary.
    scientist = ScientistAgent()
    initial_hypotheses_str = scientist.step(kg_summary)
    hypothesis_list = [h.strip() for h in initial_hypotheses_str.split("\n") if h.strip()]
    
    refined_hypotheses = []
    # Instantiate agents for iterative refinement.
    kg_agent = KGAgent()
    pubmed_agent = PubmedAgent()
    critic_agent = CriticAgent()
    revision_agent = RevisionAgent()
    refine_agent = RefineAgent()
    
    for hypo in hypothesis_list:
        print(f"--- Processing Hypothesis: {hypo} ---")
        current_hypo = hypo
        iteration = 0
        crit_feedback = ""
        accepted = False
        # 缓存第一次调用的 KG 和 PubMed 信息
        cached_kg_info = None
        cached_pubmed_evidence = None
        while iteration < 3:
            if iteration == 0:
                cached_kg_info = kg_agent.step(current_hypo)
                cached_pubmed_evidence = pubmed_agent.step(current_hypo)
            # 合并缓存信息，传递给 CriticAgent 进行评价
            combined_info = f"KG Info:\n{cached_kg_info}\n\nLiterature Evidence:\n{cached_pubmed_evidence}"
            crit_feedback = critic_agent.step(combined_info, current_hypo)
            overall_score = extract_overall_score(crit_feedback)
            print(f"[Critic] Extracted Overall Score: {overall_score}")
            # 如果整体评分低于阈值，则丢弃该假设
            if overall_score < 3:
                print(f"[Critic] Overall score {overall_score} is below threshold. Discarding hypothesis.")
                current_hypo = None
                break
            # 如果整体评分高于9或反馈中包含"TERMINATE"，则接受该假设
            if overall_score >= 9 or "TERMINATE" in crit_feedback.upper():
                print(f"[Critic] Hypothesis accepted: {current_hypo}")
                accepted = True
                break
            # RevisionAgent 根据 CriticAgent 的反馈决定是否需要额外外部信息
            option, new_info = revision_agent.step(crit_feedback, current_hypo)
            if option == "terminate":
                break
            # 若 RevisionAgent 指示调用额外查询，则更新缓存信息
            if option == "neo4j":
                additional_kg_info = call_neo4j_subgraph(new_info)
                cached_kg_info += "\n" + additional_kg_info
            elif option == "pubmed":
                keywords_list = [kw.strip() for kw in new_info.split(",") if kw.strip()]
                additional_pubmed = call_pubmed_search(keywords_list, retmax=10)
                cached_pubmed_evidence += "\n" + additional_pubmed
            # 使用 RevisionAgent 返回的新关键词进行改进
            current_hypo = refine_agent.step(current_hypo, new_info)
            iteration += 1
        if current_hypo:
            refined_hypotheses.append(current_hypo)
    
    final_hypotheses = "\n".join(refined_hypotheses)
    # Stage 4: DecisionAgent produces the final output.
    decision_agent = DecisionAgent()
    final_decision = decision_agent.step(crit_feedback, final_hypotheses)
    return final_decision

# ---------------------------
# 9. External Interface
# ---------------------------
def run_chat(user_input: str) -> str:
    """
    External interface: Receives user input, runs the full pipeline, and returns the final decision.
    """
    return run_full_pipeline(user_input)

# ---------------------------
# 10. Testing Entry Point
# ---------------------------
if __name__ == "__main__":
    test_query = "Generate new hypotheses about 'Parkinson disease' please."
    result = run_chat(test_query)
    print("=== FINAL RESULT ===")
    print(result)
