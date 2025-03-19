# from transformers import AutoTokenizer, AutoModel
# import networkx as nx
# import os
# import pickle
# from ScienceDiscovery.utils import *
# import os

# data_dir_source = 'D:/DFKI/data/PrimeKG/'
# graph_name = 'brca1_limited_2hop_related_kg.graphml'
# embeddings_name = 'brca1_limited_2hop_related_kg_embeddings.pkl'
# tokenizer_model = "BAAI/bge-large-en-v1.5"

# embedding_tokenizer = AutoTokenizer.from_pretrained(tokenizer_model) 
# embedding_model = AutoModel.from_pretrained(tokenizer_model,  ) 

# G = load_graph_with_text_as_JSON (data_dir=data_dir_source, graph_name=graph_name)
# G = return_giant_component_of_graph  (G)
# G = nx.Graph(G)
# try:
#     node_embeddings = generate_node_embeddings(G, embedding_tokenizer, embedding_model, )
# except:
#     print ("Node embeddings not loaded, need to regenerate.")
#     node_embeddings = generate_node_embeddings(G, embedding_tokenizer, embedding_model, )
