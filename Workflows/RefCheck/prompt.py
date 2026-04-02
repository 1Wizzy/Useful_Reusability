EXTRACT_MESSAGE = """
Please extract the citation description (text_to_check) and the corresponding complete reference entry (old_ref) from the following text.
Please ensure that the extraction is accurate and match the two one by one.
text:
```
{text}
```
"""

EXTRACT_TITLE_MESSAGE = "Please extract paper title from the reference: {ref}"

CHECK_INFO_MESSAGE = """You are a rigorous academic reviewer.
Please check whether the opinions in the quoted paper are consistent with those in the original paper
Quoted Paper Content:
```
{text_to_check}
```

Original Paper Abstrat:
```
{abstract}
```
Task:
Judge whether the [quoted text] accurately reflects the core proposition in the [original paper abstract].
1. ignore minor wording differences.
2. if the quoted text fabricates non-existent data, methods or exaggerates the conclusion, please judge it as "inconsistent".
3. please give your detailed reason first, and then give the final result.

"""
