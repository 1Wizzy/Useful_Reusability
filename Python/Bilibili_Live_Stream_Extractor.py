# -*- coding: utf-8 -*-
"""
B站直播流链接抓取工具 + 扫码登录
"""

import requests
import re
import time
import qrcode


class BilibiliQRCodeLogin:
    GEN_URL = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
    POLL_URL = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Origin': 'https://www.bilibili.com',
        })

    def login(self, timeout=180, interval=3):
        resp = self.session.get(self.GEN_URL)
        data = resp.json()
        qrcode_key, url = data['data']['qrcode_key'], data['data']['url']

        print("请扫码登录：", url)
        img = qrcode.make(url)
        img.show()

        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = self.session.get(self.POLL_URL, params={'qrcode_key': qrcode_key})
            js = resp.json()
            code = js.get('data', {}).get('code')
            if code == 86101:
                pass
            elif code == 86090:
                print("✅ 已扫码，等待确认…")
            elif code == 0:
                print("🎉 登录成功！")
                return self.session.cookies.get_dict()
            elif code == 86038:
                print("❌ 二维码已失效，请重新生成")
                return None
            time.sleep(interval)
        print("⏰ 登录超时")
        return None


class BilibiliLiveStreamExtractor:
    def __init__(self, cookies=None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://live.bilibili.com/',
            'Origin': 'https://live.bilibili.com'
        })
        if cookies:
            cookie_header = '; '.join(f"{k}={v}" for k, v in cookies.items())
            self.session.headers.update({'Cookie': cookie_header})

        self.quality_map = {
            30000: "杜比",
            20000: "4K",
            10000: "原画",
            400: "蓝光",
            250: "超清",
            150: "高清",
            80: "流畅"
        }

    def extract_room_id(self, url):
        if 'live.bilibili.com' in url:
            room_id = re.search(r'/(\d+)', url)
            if room_id:
                return room_id.group(1)
        return None

    def get_room_info(self, room_id):
        url = f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={room_id}"
        resp = self.session.get(url)
        data = resp.json()
        if data['code'] == 0:
            return data['data']
        return None

    def get_all_stream_urls(self, room_id):
        all_streams = {}
        for qn, quality_name in self.quality_map.items():
            streams = self.get_play_url(room_id, qn)
            if streams:
                all_streams[qn] = {'quality_name': quality_name, 'streams': streams}
        return all_streams

    def get_play_url(self, room_id, qn=10000):
        url = "https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo"
        params = {
            'room_id': room_id,
            'no_playurl': 0,
            'mask': 0,
            'qn': qn,
            'platform': 'web',
            'protocol': '0,1',
            'format': '0,1,2',
            'codec': '0,1,2'
        }
        resp = self.session.get(url, params=params)
        data = resp.json()
        if data['code'] == 0 and 'playurl_info' in data['data']:
            return self.parse_all_streams(data['data']['playurl_info']['playurl'])
        return None

    def parse_all_streams(self, play_info):
        streams = {}
        if 'stream' not in play_info:
            return streams
        for stream in play_info['stream']:
            protocol_name = stream.get('protocol_name', 'unknown')
            for format_info in stream.get('format', []):
                format_name = format_info.get('format_name', 'unknown')
                for codec in format_info.get('codec', []):
                    codec_name = codec.get('codec_name', 'unknown')
                    current_qn = codec.get('current_qn', 0)
                    url_info_list = codec.get('url_info', [])
                    base_url = codec.get('base_url', '')
                    for url_info in url_info_list:
                        full_url = url_info['host'] + base_url + url_info['extra']
                        stream_key = f"{protocol_name}_{format_name}_{codec_name}"
                        streams.setdefault(stream_key, []).append({
                            'url': full_url,
                            'protocol': protocol_name,
                            'format': format_name,
                            'codec': codec_name,
                            'current_qn': current_qn,
                            'quality_name': self.quality_map.get(current_qn, f"未知({current_qn})")
                        })
        return streams

    def print_stream_info(self, all_streams):
        print("\n" + "=" * 80)
        print("B站直播流链接信息")
        print("=" * 80)
        for qn, stream_info in sorted(all_streams.items(), key=lambda x: x[0], reverse=True):
            quality_name = stream_info['quality_name']
            streams = stream_info['streams']
            if not streams:
                continue
            print(f"\n【{quality_name} - {qn}】")
            for stream_key, stream_list in streams.items():
                protocol, fmt, codec = stream_key.split('_', 2)
                print(f"\n  ▶ {protocol.upper()} - {fmt.upper()} - {codec.upper()}")
                for i, stream in enumerate(stream_list):
                    print(f"    [{i+1}] {stream['url']}")

    def get_best_streams(self, all_streams):
        best_streams = {}
        # 优先级：杜比 > 4K > 原画 > 蓝光 > 超清 > 高清 > 流畅
        priority_qn = [30000, 20000, 10000, 400, 250, 150, 80]
        for qn in priority_qn:
            if qn in all_streams and all_streams[qn]['streams']:
                streams = all_streams[qn]['streams']
                quality_name = all_streams[qn]['quality_name']
                preferred_keys = [
                    'http_stream_flv_avc',
                    'http_stream_flv_hevc',
                    'http_hls_ts_avc',
                    'http_hls_ts_hevc'
                ]
                for key in preferred_keys:
                    if key in streams and streams[key]:
                        best_streams[quality_name] = streams[key][0]['url']
                        return best_streams  # 取到最高的就直接返回
        return best_streams


def main(live_url):
    login = BilibiliQRCodeLogin()
    cookies = login.login()
    if not cookies:
        print("未能登录，退出。")
        return

    extractor = BilibiliLiveStreamExtractor(cookies=cookies)
    room_id = extractor.extract_room_id(live_url)
    if not room_id:
        print("无法提取房间号")
        return

    room_info = extractor.get_room_info(room_id)
    if not room_info:
        print("无法获取房间信息")
        return

    print(f"房间号: {room_id}")
    print(f"标题: {room_info.get('title','未知')} 主播: {room_info.get('uname','未知')}")
    if room_info.get('live_status') != 1:
        print("❌ 未开播")
        return

    all_streams = extractor.get_all_stream_urls(room_id)
    extractor.print_stream_info(all_streams)

    best = extractor.get_best_streams(all_streams)
    if best:
        print("\n" + "=" * 80)
        print("推荐的最佳流链接（最高清晰度）")
        print("=" * 80)
        for quality, url in best.items():
            print(f"\n【{quality}】\n{url}")


if __name__ == "__main__":
    main("https://live.bilibili.com/22908869")
