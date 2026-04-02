from node import *
from schema import CheckState
from langgraph.graph import START, END, StateGraph

# SubGraph
subgraph_builder = StateGraph(CheckState)

for node in SUBGRAPH_NODE:
    subgraph_builder.add_node(node.__name__, node)

subgraph_builder.add_edge(START, "extract_title")
subgraph_builder.add_edge("extract_title", "get_info")
subgraph_builder.add_conditional_edges("get_info", router)
subgraph_builder.add_edge("check_info", "write_report")
subgraph_builder.add_edge("write_report", END)

sub_graph = subgraph_builder.compile()

# MainGraph
def run_sub_graph(state: CheckState):
    res = sub_graph.invoke(state)
    return {"results": [res]}

main_builder = StateGraph(ParentState)

main_builder.add_node("extract_citations", extract_citations)
main_builder.add_node("process_citation", run_sub_graph)



main_builder.add_edge(START, "extract_citations")
# 使用 conditional edges 触发动态并行
main_builder.add_conditional_edges("extract_citations", map_to_subgraphs, ["process_citation"])
main_builder.add_edge("process_citation", END)

main_graph = main_builder.compile()
