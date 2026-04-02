import requests
from typing import Literal, Any
from tenacity import retry, stop_after_attempt, wait_exponential

def _format_reference(paper_data: dict, ref_format: str) -> str:
    """内部辅助函数：根据论文数据和指定格式生成参考文献字符串"""
    
    # 提取基础字段并设置默认值
    title = paper_data.get("title", "")
    year = paper_data.get("year", "")
    doi = paper_data.get("externalIds", {}).get("DOI", "")
    
    # 提取期刊/会议名称 (优先使用 venue，如果没有则尝试从 journal 对象获取)
    venue = paper_data.get("venue", "")
    if not venue and paper_data.get("journal"):
        venue = paper_data.get("journal", {}).get("name", "")
        
    # 提取作者列表
    authors = paper_data.get("authors", [])
    author_names = [a.get("name", "").strip() for a in authors if a.get("name")]
    
    if not author_names:
        author_names = ["Unknown Author"]

    # --- 开始根据格式拼装 ---
    
    if ref_format == "IEEE":
        # IEEE: J. K. Author, "Title of paper," Abbrev. Title of Periodical, year, doi: xxx.
        ieee_authors = []
        for name in author_names:
            parts = name.split()
            if len(parts) > 1:
                # 提取名首字母 + 姓 (e.g., John Doe -> J. Doe)
                ieee_authors.append(f"{parts[0][0]}. {' '.join(parts[1:])}")
            else:
                ieee_authors.append(name)
        
        author_str = ", ".join(ieee_authors)
        ref = f"{author_str}, \"{title},\" in {venue}, {year}."
        if doi: 
            ref += f" doi: {doi}."
        return ref

    elif ref_format == "GB/T":
        # GB/T 7714: 姓 名首字母, 姓 名首字母, et al. 标题[J/C]. 期刊名, 年份.
        gbt_authors = []
        for name in author_names:
            parts = name.split()
            if len(parts) > 1:
                # Doe J
                gbt_authors.append(f"{parts[-1]} {''.join([p[0] for p in parts[:-1]])}")
            else:
                gbt_authors.append(name)
                
        if len(gbt_authors) > 3:
            author_str = ", ".join(gbt_authors[:3]) + ", et al"
        else:
            author_str = ", ".join(gbt_authors)
            
        # 简单用 [J] 代表期刊文献，严格实现需要根据 publicationTypes 判断
        ref = f"{author_str}. {title}[J]. {venue}, {year}." 
        return ref

    elif ref_format == "MLA":
        # MLA: Last Name, First Name, et al. "Title." Venue, Year. DOI.
        if len(author_names) >= 3:
            parts = author_names[0].split()
            author_str = f"{parts[-1]}, {' '.join(parts[:-1])}, et al" if len(parts) > 1 else f"{author_names[0]}, et al"
        elif len(author_names) == 2:
            author_str = f"{author_names[0]} and {author_names[1]}"
        else:
            parts = author_names[0].split()
            author_str = f"{parts[-1]}, {' '.join(parts[:-1])}" if len(parts) > 1 else author_names[0]

        ref = f"{author_str}. \"{title}.\" {venue} ({year})."
        if doi:
            ref += f" https://doi.org/{doi}"
        return ref

    elif ref_format == "AMA":
        # AMA: Author Last Name First Initial. Title. Venue. Year. doi: ...
        ama_authors = []
        for name in author_names:
            parts = name.split()
            if len(parts) > 1:
                ama_authors.append(f"{parts[-1]} {''.join([p[0] for p in parts[:-1]])}")
            else:
                ama_authors.append(name)
                
        if len(ama_authors) > 6:
            author_str = ", ".join(ama_authors[:3]) + " et al"
        else:
            author_str = ", ".join(ama_authors)
            
        ref = f"{author_str}. {title}. {venue}. {year}."
        if doi: 
            ref += f" doi:{doi}"
        return ref

    # 默认 fallback
    return f"{', '.join(author_names)}. {title}. {year}."


@retry(stop=stop_after_attempt(10), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_paper_info(title: str, ref_format: Literal['IEEE', 'GB/T', 'MLA', 'AMA'] = 'IEEE') -> dict[str, Any]:
    """
    使用 Semantic Scholar 检索论文，并返回指定格式的 Reference 字符串。
    """
    if not title or not title.strip():
        return {}

    print(f"🔍 正在检索并生成 {ref_format} 格式引用: {title}")
    
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    # 【注意】这里新增了 venue 和 journal 字段，这对生成引用至关重要
    params = {
        "query": title,
        "limit": 1,
        "fields": "title,abstract,authors,url,year,venue,journal,externalIds"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("data") and len(data["data"]) > 0:
            paper = data["data"][0]
            
            # 动态生成指定格式的 reference 字符串
            generated_ref = _format_reference(paper, ref_format)
            
            return {
                "title": paper.get("title", ""),
                "abstract": paper.get("abstract") or "NOT FOUND", 
                "url": paper.get("url", ""),
                "doi": paper.get("externalIds", {}).get("DOI", ""),
                "reference": generated_ref, # <--- 新增字段：格式化好的引用
                "ref_format_used": ref_format
            }
        else:
            return {}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API 请求异常: {e}")
        raise
