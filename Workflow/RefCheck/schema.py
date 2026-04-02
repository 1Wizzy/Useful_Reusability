from typing import TypedDict, Literal, Annotated
from pydantic import BaseModel, Field
from operator import add


# State Schema
class CheckState(TypedDict):
    text_to_check: str
    old_ref: str
    new_ref: str
    ref_format: Literal["IEEE", "GB/T 7714", "MLA", "APA"]
    url: str
    title: str
    abstract: str
    check_result: str
    check_reason: str

class State(TypedDict):
    context: str

# Model Ouput Schema
class TitleSchema(BaseModel):
    title: str = Field(description="paper title")

class CheckResultSchema(BaseModel):
    check_result: str = Field(description="Check Result")
    check_reason: str = Field(description="Check Reason")


# Tool Input Schema
class GetPaperInfoSchema(BaseModel):
    title: str = Field(description="paper title")
    ref_format: Literal["IEEE", "GB/T 7714", "MLA", "APA"] = Field(
        description="Reference Format", default="IEEE"
    )



### Main Graph

class CitationPair(BaseModel):
    text_to_check: str = Field(description="引用的具体贡献描述内容")
    old_ref: str = Field(description="对应的完整参考文献条目文本")

class ExtractionResult(BaseModel):
    pairs: list[CitationPair] = Field(description="提取的引文与参考文献对列表")

class ParentState(TypedDict):
    context: str          
    ref_format: Literal["IEEE", "GB/T 7714", "MLA", "APA"]
    pairs: list[CitationPair] # 提取后存放的列表
    results: Annotated[list[CheckState], add]
