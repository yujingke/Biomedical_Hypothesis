from neo4j import GraphDatabase
from typing import List, Dict, Optional
import numpy as np

############################################################
# (Optional) Simple embedding & similarity functions for demonstration
############################################################
def simulate_embedding(text: str) -> List[float]:
    vec = [0.0, 0.0, 0.0]
    for i, char in enumerate(text[:3]):
        vec[i] = (ord(char) % 10) / 10.0
    return vec

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))

relationship_embeddings = {
    "disease_protein": [0.9, 0.1, 0.0],
    "disease_disease": [0.8, 0.2, 0.0],
    "disease_phenotype_positive": [0.85, 0.15, 0.0],
    "drug_effect": [0.2, 0.8, 0.0],
    "contraindication": [0.1, 0.9, 0.0],
    # ... add additional relationship types as needed
}

############################################################
# Detailed summarization function for biomedical KG
############################################################
def summarize_subgraph_aggregated(
    nodes_data: List[Dict], 
    rels_data: List[Dict],
    max_display: int = 50
) -> str:
    """
    Aggregate the subgraph summary to reduce token usage.
    Group relationships by source node, relationship type, and display_relation (if available),
    and list the target node names in one line.
    """
    # Build a lookup dictionary for node names using their IDs.
    node_lookup = {node["id"]: node.get("name", "Unknown") for node in nodes_data}
    
    # Group relationships by (start_node, relationship type, display_relation)
    grouped = {}
    for rel in rels_data:
        # Note: Use 'element_id' if available to avoid deprecation warnings.
        start_id = rel.get(":START_ID") or rel.get("start_node_id")
        end_id = rel.get(":END_ID") or rel.get("end_node_id")
        start_name = node_lookup.get(start_id, "Unknown")
        end_name = node_lookup.get(end_id, "Unknown")
        rtype = rel.get(":TYPE") or rel.get("rel_type", "Unknown")
        disp = rel.get("display_relation", "").strip()
        key = (start_name, rtype, disp)
        if key not in grouped:
            grouped[key] = set()
        grouped[key].add(end_name)
    
    # Build the summary lines by aggregating target names.
    lines = []
    for (start_name, rtype, disp), targets in grouped.items():
        targets_list = sorted(list(targets))
        targets_str = ", ".join(targets_list)
        if disp:
            lines.append(f"{start_name} --[{rtype} | {disp}]--> {targets_str}")
        else:
            lines.append(f"{start_name} --[{rtype}]--> {targets_str}")
    
    return "\n".join(lines)



############################################################
# Main Neo4j interface class
############################################################
class Neo4jGraph:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()

    def get_subgraph_multiple_keywords(
        self,
        keywords: List[str],
        max_level: int = 2,
        limit: int = 100
    ) -> str:
        """
        Multiple-keyword scenario using apoc.path.subgraphAll.
        """
        with self.driver.session() as session:
            cypher = """
            MATCH (n)
            WHERE n.name IN $keywords
            WITH collect(n) AS startNodes
            CALL apoc.path.subgraphAll(startNodes, {maxLevel:$max_level, limit:$limit})
            YIELD nodes, relationships
            RETURN nodes, relationships
            """
            result = session.run(cypher, keywords=keywords, max_level=max_level, limit=limit)
            record = result.single()
            if not record:
                return "No subgraph found for the given keywords."
            
            nodes_data = []
            rels_data = []
            nodes_list = record["nodes"]
            rels_list  = record["relationships"]

            for node in nodes_list:
                nodes_data.append({
                    "id": node.id,
                    "name": node.get("name", ""),
                    "source": node.get("source", ""),
                    ":LABEL": list(node.labels)[0] if node.labels else "Unknown"
                })
            for rel in rels_list:
                rels_data.append({
                    ":TYPE": rel.type,
                    ":START_ID": rel.start_node.id,
                    ":END_ID": rel.end_node.id,
                    "display_relation": rel.get("display_relation", "")
                })
            
            summary = summarize_subgraph_aggregated(nodes_data, rels_data, max_display=50)
            return summary

    def get_subgraph_single_keyword_multiple_reltypes(
        self,
        keyword: str,
        relationship_types: List[str],
        each_rel_limit: int = 50
    ) -> str:
        """
        Single keyword with specified relationship types.
        For each provided relationship type, query up to each_rel_limit results.
        """
        with self.driver.session() as session:
            all_nodes_data = {}
            all_rels_data = []
            for rtype in relationship_types:
                cypher = f"""
                MATCH (n {{name: $keyword}})-[r:`{rtype}`]-(m)
                RETURN n, r, m
                LIMIT {each_rel_limit}
                """
                results = session.run(cypher, keyword=keyword)
                for record in results:
                    n = record["n"]
                    m = record["m"]
                    if n.id not in all_nodes_data:
                        all_nodes_data[n.id] = {
                            "id": n.id,
                            "name": n.get("name", ""),
                            "source": n.get("source", ""),
                            ":LABEL": list(n.labels)[0] if n.labels else "Unknown"
                        }
                    if m.id not in all_nodes_data:
                        all_nodes_data[m.id] = {
                            "id": m.id,
                            "name": m.get("name", ""),
                            "source": m.get("source", ""),
                            ":LABEL": list(m.labels)[0] if m.labels else "Unknown"
                        }
                    r_obj = record["r"]
                    all_rels_data.append({
                        ":TYPE": r_obj.type,
                        ":START_ID": r_obj.start_node.id,
                        ":END_ID": r_obj.end_node.id,
                        "display_relation": r_obj.get("display_relation", "")
                    })
            
            summary = summarize_subgraph_aggregated(list(all_nodes_data.values()), all_rels_data)
            return summary

    def get_subgraph_single_keyword_all_reltypes(
        self,
        keyword: str,
        each_rel_limit: int = 20
    ) -> str:
        """
        Single keyword query with no relationship types provided.
        Automatically retrieves all distinct relationship types for the node,
        and for each type, limits the results to each_rel_limit.
        """
        with self.driver.session() as session:
            distinct_query = """
            MATCH (n {name: $keyword})-[r]-()
            RETURN DISTINCT type(r) AS rtype
            """
            result = session.run(distinct_query, keyword=keyword)
            rel_types = [record["rtype"] for record in result]

            all_nodes_data = {}
            all_rels_data = []
            for rtype in rel_types:
                cypher = f"""
                MATCH (n {{name: $keyword}})-[r:`{rtype}`]-(m)
                RETURN n, r, m
                LIMIT {each_rel_limit}
                """
                results = session.run(cypher, keyword=keyword)
                for record in results:
                    n = record["n"]
                    m = record["m"]
                    if n.id not in all_nodes_data:
                        all_nodes_data[n.id] = {
                            "id": n.id,
                            "name": n.get("name", ""),
                            "source": n.get("source", ""),
                            ":LABEL": list(n.labels)[0] if n.labels else "Unknown"
                        }
                    if m.id not in all_nodes_data:
                        all_nodes_data[m.id] = {
                            "id": m.id,
                            "name": m.get("name", ""),
                            "source": m.get("source", ""),
                            ":LABEL": list(m.labels)[0] if m.labels else "Unknown"
                        }
                    r_obj = record["r"]
                    all_rels_data.append({
                        ":TYPE": r_obj.type,
                        ":START_ID": r_obj.start_node.id,
                        ":END_ID": r_obj.end_node.id,
                        "display_relation": r_obj.get("display_relation", "")
                    })
            
            summary = summarize_subgraph_aggregated(list(all_nodes_data.values()), all_rels_data)
            return summary

    def get_subgraph(
        self,
        keywords: List[str],
        relationship_types: Optional[List[str]] = None,
        max_level: int = 2,
        limit: int = 100
    ) -> str:
        """
        Unified interface:
          - If multiple keywords, use get_subgraph_multiple_keywords.
          - If a single keyword:
              - If relationship_types is provided, use get_subgraph_single_keyword_multiple_reltypes.
              - Otherwise, use get_subgraph_single_keyword_all_reltypes.
        """
        if len(keywords) > 1:
            return self.get_subgraph_multiple_keywords(
                keywords=keywords,
                max_level=max_level,
                limit=limit
            )
        else:
            if not keywords:
                return "No keyword provided."
            single_kw = keywords[0]
            if relationship_types:
                return self.get_subgraph_single_keyword_multiple_reltypes(
                    keyword=single_kw,
                    relationship_types=relationship_types,
                    each_rel_limit=50
                )
            else:
                return self.get_subgraph_single_keyword_all_reltypes(
                    keyword=single_kw,
                    each_rel_limit=20
                )

############################################################
# Example usage in a main guard
############################################################
if __name__ == "__main__":
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "12345678"
    
    graph = Neo4jGraph(uri, user, password)

    # Example 1: Multiple keywords query
    keywords_multi = ["TP53", "BRCA1", "PARP1"]
    result_multi = graph.get_subgraph(keywords_multi)
    print("=== Multiple Keywords Subgraph ===")
    print(result_multi)
    print()

    # # Example 2: Single keyword with specified relationship types
    # single_keyword = ["Parkinson disease"]
    # rel_types = ["disease_protein", "disease_phenotype_positive"]
    # result_single_multi_rel = graph.get_subgraph(
    #     single_keyword, 
    #     relationship_types=rel_types
    # )
    # print("=== Single Keyword + Multiple Relationship Types ===")
    # print(result_single_multi_rel)
    # print()

    # # Example 3: Single keyword with no relationship types provided
    # single_keyword_all = ["Parkinson disease"]
    # result_single_all = graph.get_subgraph(single_keyword_all)
    # print("=== Single Keyword + All Relationship Types ===")
    # print(result_single_all)
    # print()

    graph.close()
