import requests
from urllib.parse import urlparse

def test_proxy(proxy_url, test_url="https://myip.ipip.net/json", timeout=5):
    """
    测试代理服务器是否可用（支持多种协议和认证信息）
    
    :param proxy_url: 代理服务器地址（格式：协议://[用户名:密码@]ip:端口）
    :param test_url: 用于测试的URL, 修改测试url需同步修改返回数据逻辑
    :param timeout: 请求超时时间（秒）
    :return: (是否成功, 原始响应文本) 元组
    """
    # 解析代理URL
    parsed = urlparse(proxy_url)
    
    # 验证协议支持
    supported_protocols = ['http', 'https', 'socks4', 'socks5']
    if parsed.scheme not in supported_protocols:
        return False, f"不支持的协议: {parsed.scheme}，支持的协议: {', '.join(supported_protocols)}"
    
    # 构建代理字典（自动处理认证信息）
    proxies = {
        'http': proxy_url,
        'https': proxy_url,
    }
    
    # 显示调试信息
    debug_info = {
        '协议': parsed.scheme,
        '主机': parsed.hostname,
        '端口': parsed.port,
        '认证': '有' if parsed.username else '无'
    }
    print(f"测试代理配置: {debug_info}")
    
    try:
        response = requests.get(
            test_url,
            proxies=proxies,
            timeout=timeout
        )
        
        # 检查状态码
        if response.status_code != 200:
            return False, f"HTTP错误状态码: {response.status_code}"
        
        # 验证返回的IP是否与代理一致
        origin_ip = response.json()['data']['ip']
        origin_ip_location = ' '.join([item for item in response.json()['data']['location'] if item])
        
        if parsed.hostname == origin_ip:
            return True, response.text
        elif origin_ip:
            return True, f"代理可能有效，但返回IP({origin_ip} {origin_ip_location})与代理IP({parsed.hostname})不匹配"
        else:
            return True, "成功连接但未返回IP信息"


    
    except requests.exceptions.ProxyError as e:
        return False, f"代理错误: {str(e)}"
    except requests.exceptions.ConnectTimeout:
        return False, "连接超时"
    except requests.exceptions.ConnectionError:
        return False, "网络连接错误"
    except requests.exceptions.JSONDecodeError:
        return False, "响应解析失败 - 可能不是有效的JSON"
    except Exception as e:
        return False, f"未知错误: {str(e)}"


if __name__ == "__main__":
    # 测试不同类型的代理
    proxies_to_test = [
        'http://127.0.0.1:7890',
        'https://127.0.0.1:7890',
        'socks4://127.0.0.1:7890',
        'socks5://127.0.0.1:7890',
    ]
    
    for proxy in proxies_to_test:
        print(f"\n{'='*50}")
        print(f"测试代理: {proxy}")
        
        success, message = test_proxy(proxy, test_url="https://myip.ipip.net/json")
        
        if success:
            print(f"✅ 代理可用")
            print(f"响应摘要: {message[:100]}...")
        else:
            print(f"❌ 代理不可用")
            print(f"错误信息: {message}")
