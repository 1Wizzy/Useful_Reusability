from schema import *
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from langgraph.constants import Send
from tool import get_paper_info
from typing import Any
from prompt import *


load_dotenv()
model = init_chat_model("google_genai:gemini-3-flash-preview")

def extract_citations(state: ParentState) -> dict:
    model_schema = model.with_structured_output(ExtractionResult)
    res = model_schema.invoke(
        [HumanMessage(EXTRACT_MESSAGE.format(text=state["context"]))]
    )
    return {"pairs": res.pairs} # type: ignore

# 并行映射逻辑：将提取出的多个 pairs 映射为多个并行的 sub_graph 任务
def map_to_subgraphs(state: ParentState):
    sends = []
    for pair in state.get("pairs", []):
        # 为每个子任务组装初始 CheckState
        sub_state = {
            "text_to_check": pair.text_to_check,
            "old_ref": pair.old_ref,
            "ref_format": state.get("ref_format", "IEEE") # 继承主图的设定
        }
        # 发送并行指令: Send(目标节点名, 初始State)
        sends.append(Send("process_citation", sub_state))
    return sends




def extract_title(state: CheckState) -> CheckState:
    model_schema = model.with_structured_output(TitleSchema)
    res = model_schema.invoke(
        [HumanMessage(EXTRACT_TITLE_MESSAGE.format(ref=state["old_ref"]))]
    )
    return {"title": res.title}  # type: ignore # Reducer will merge TypeDict


def get_info(state: CheckState) -> CheckState:
    res = get_paper_info(state["title"], state["ref_format"]) # type: ignore
    return {"abstract": res["abstract"], "new_ref": res["reference"]}  # type: ignore


def router(state: CheckState) -> Literal["write_report", "check_info"]:
    if state["abstract"] == "NOT FOUND":
        return "write_report"
    return "check_info"


def check_info(state: CheckState) -> dict[str, Any]:
    model_schema = model.with_structured_output(CheckResultSchema)
    res = model_schema.invoke(
        [HumanMessage(CHECK_INFO_MESSAGE.format(text_to_check=state["text_to_check"], abstract=state["abstract"])),]
    )
    return {'check_reason': res.check_reason, 'check_result': res.check_result} # type: ignore


def write_report(state: CheckState):
    print('=' * 60)
    print('TITLE:\n', state['title'])
    print('RESULT:\n',state['check_result'])
    print('REASON:\n',state['check_reason'])
    print('=' * 60)


SUBGRAPH_NODE = [extract_title, get_info, check_info, write_report]
