# -*- coding: utf-8 -*-
"""
B站直播流链接抓取工具
专注于获取不同编码和清晰度的流链接
"""

import requests
import json
import re
from urllib.parse import urlparse


class BilibiliLiveStreamExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://live.bilibili.com/',
            'Origin': 'https://live.bilibili.com'
        })
        
        # 清晰度映射
        self.quality_map = {
            30000: "杜比",
            20000: "4K",
            10000: "原画",
            400: "蓝光",
            250: "超清",
            150: "高清",
            80: "流畅"
        }
        
        # 编码格式映射
        self.codec_map = {
            7: "avc",
            12: "hevc",
            13: "av1"
        }
        
    def extract_room_id(self, url):
        """从URL中提取房间号"""
        try:
            if 'live.bilibili.com' in url:
                room_id = re.search(r'/(\d+)', url)
                if room_id:
                    return room_id.group(1)
            return None
        except Exception as e:
            print(f"提取房间号失败: {e}")
            return None
    
    def get_room_info(self, room_id):
        """获取直播间基本信息"""
        try:
            url = f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={room_id}"
            response = self.session.get(url)
            data = response.json()
            
            if data['code'] == 0:
                return data['data']
            else:
                print(f"获取房间信息失败: {data['message']}")
                return None
        except Exception as e:
            print(f"请求房间信息失败: {e}")
            return None
    
    def get_all_stream_urls(self, room_id):
        """获取所有可用的流链接（不同清晰度和编码）"""
        all_streams = {}
        
        # 遍历所有可能的清晰度
        for qn, quality_name in self.quality_map.items():
            print(f"正在获取 {quality_name}({qn}) 的流信息...")
            streams = self.get_play_url(room_id, qn)
            if streams:
                all_streams[qn] = {
                    'quality_name': quality_name,
                    'streams': streams
                }
        
        return all_streams
    
    def get_play_url(self, room_id, qn=10000):
        """获取指定清晰度的直播流地址"""
        try:
            url = "https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo"
            params = {
                'room_id': room_id,
                'no_playurl': 0,
                'mask': 0,
                'qn': qn,
                'platform': 'web',
                'protocol': '0,1',  # 0=http_stream, 1=http_hls
                'format': '0,1,2',  # 0=flv, 1=ts, 2=fmp4
                'codec': '0,1,2'    # 0=avc, 1=hevc, 2=av1
            }
            
            response = self.session.get(url, params=params)
            data = response.json()
            
            if data['code'] == 0 and 'playurl_info' in data['data']:
                return self.parse_all_streams(data['data']['playurl_info']['playurl'])
            else:
                return None
                
        except Exception as e:
            print(f"请求播放地址失败: {e}")
            return None
    
    def parse_all_streams(self, play_info):
        """解析所有流地址信息"""
        streams = {}
        
        try:
            if 'stream' not in play_info:
                print("警告: 播放信息中没有找到stream数据")
                return streams
                
            for stream in play_info['stream']:
                protocol_name = stream.get('protocol_name', 'unknown')
                
                for format_info in stream.get('format', []):
                    format_name = format_info.get('format_name', 'unknown')
                    
                    for codec in format_info.get('codec', []):
                        codec_name = codec.get('codec_name', 'unknown')
                        current_qn = codec.get('current_qn', 0)
                        accept_qn = codec.get('accept_qn', [])
                        
                        # 构建完整的流URL
                        url_info_list = codec.get('url_info', [])
                        if url_info_list:
                            base_url = codec.get('base_url', '')
                            
                            for url_info in url_info_list:
                                if 'host' in url_info and 'extra' in url_info:
                                    full_url = url_info['host'] + base_url + url_info['extra']
                                    
                                    # 使用更安全的键名构建方式
                                    stream_key = f"{protocol_name}_{format_name}_{codec_name}"
                                    
                                    if stream_key not in streams:
                                        streams[stream_key] = []
                                    
                                    stream_data = {
                                        'url': full_url,
                                        'protocol': protocol_name,
                                        'format': format_name,
                                        'codec': codec_name,
                                        'current_qn': current_qn,
                                        'accept_qn': accept_qn,
                                        'quality_name': self.quality_map.get(current_qn, f"未知({current_qn})"),
                                        'host': url_info.get('host', 'unknown')
                                    }
                                    streams[stream_key].append(stream_data)
            
            return streams
        except Exception as e:
            print(f"解析流地址失败: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def print_stream_info(self, all_streams):
        """格式化打印流信息"""
        if not all_streams:
            print("未获取到任何流信息")
            return
        
        print("\n" + "="*80)
        print("B站直播流链接信息")
        print("="*80)
        
        for qn, stream_info in sorted(all_streams.items(), key=lambda x: x[0], reverse=True):
            quality_name = stream_info['quality_name']
            streams = stream_info['streams']
            
            if not streams:
                continue
                
            print(f"\n【{quality_name} - {qn}】")
            print("-" * 50)
            
            # 按协议和格式分组显示
            for stream_key, stream_list in streams.items():
                parts = stream_key.split('_')
                if len(parts) >= 3:
                    protocol = parts[0]
                    format_name = parts[1]
                    codec = '_'.join(parts[2:])  # 处理编码名可能包含下划线的情况
                else:
                    protocol, format_name, codec = stream_key, "unknown", "unknown"
                print(f"\n  ▶ {protocol.upper()} - {format_name.upper()} - {codec.upper()}")
                
                for i, stream in enumerate(stream_list):
                    print(f"    [{i+1}] {stream['url']}")
                    print(f"        主机: {stream['host']}")
    
    def get_best_streams(self, all_streams):
        """获取推荐的最佳流链接"""
        best_streams = {}
        
        # 优先级: 原画 > 蓝光 > 超清 > 高清
        priority_qn = [10000, 400, 250, 150]
        
        for qn in priority_qn:
            if qn in all_streams and all_streams[qn]['streams']:
                streams = all_streams[qn]['streams']
                quality_name = all_streams[qn]['quality_name']
                
                # 推荐顺序: http_stream + flv + avc
                preferred_keys = [
                    'http_stream_flv_avc',
                    'http_stream_flv_hevc',
                    'http_hls_ts_avc',
                    'http_hls_ts_hevc'
                ]
                
                for key in preferred_keys:
                    if key in streams and streams[key]:
                        best_streams[quality_name] = streams[key][0]['url']
                        break
                
                if len(best_streams) >= 3:  # 获取前3个质量等级即可
                    break
        
        return best_streams


def main(live_url):
    """主函数"""
    # 直播间URL
    extractor = BilibiliLiveStreamExtractor()
    
    # 提取房间号
    room_id = extractor.extract_room_id(live_url)
    if not room_id:
        print("无法提取房间号")
        return
    
    print(f"房间号: {room_id}")
    
    # 获取房间信息
    room_info = extractor.get_room_info(room_id)
    if room_info:
        print(f"直播间标题: {room_info.get('title', '未知')}")
        print(f"主播: {room_info.get('uname', '未知')}")
        print(f"直播状态: {'🔴 直播中' if room_info.get('live_status') == 1 else '⚫ 未开播'}")
        
        if room_info.get('live_status') != 1:
            print("\n❌ 当前未在直播，无法获取流链接")
            return
    else:
        print("无法获取房间信息")
        return
    
    # 获取所有流链接
    print(f"\n正在获取直播间 {room_id} 的所有流链接...")
    all_streams = extractor.get_all_stream_urls(room_id)
    
    # 显示详细信息
    extractor.print_stream_info(all_streams)
    
    # 显示推荐的最佳流链接
    best_streams = extractor.get_best_streams(all_streams)
    if best_streams:
        print(f"\n" + "="*80)
        print("推荐的最佳流链接")
        print("="*80)
        for quality, url in best_streams.items():
            print(f"\n【{quality}】")
            print(f"{url}")


if __name__ == "__main__":
    live_url = "[Put the url here]"
    main(live_url)