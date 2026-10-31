import asyncio
import json
import time
import aiohttp

# Target IPTV / HLS stream candidates
# In production, these can be aggregated from open IPTV repositories (e.g. iptv-org) or external sources.
M3U8_LINKS = [
    {
        "name": "Mux Sports Demo (HLS)",
        "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
    },
    {
        "name": "Akamai Live HLS Stream",
        "url": "https://cph-p2p-msl.akamaized.net/hls/live/2000341/test/master.m3u8"
    },
    {
        "name": "Unified Streaming HLS Test",
        "url": "https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8"
    },
    {
        "name": "Bitmovin Sintel Multi-Bitrate",
        "url": "https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8"
    },
    {
        "name": "Offline Stream Demo (Should Fail)",
        "url": "https://example.com/dead-stream.m3u8"
    },
    {
        "name": "Invalid Host Test (Should Fail)",
        "url": "https://fake-invalid-stream-domain-404.org/live.m3u8"
    }
]

async def check_stream_health(session: aiohttp.ClientSession, item: dict, semaphore: asyncio.Semaphore) -> tuple[dict, bool]:
    """
    Fetches the stream URL with a 5-second timeout and validates that
    it responds with HTTP 200 and contains the #EXTM3U manifest header.
    """
    url = item["url"]
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*"
    }

    async with semaphore:
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with session.get(url, headers=headers, timeout=timeout, allow_redirects=True) as response:
                if response.status == 200:
                    # Read the first 100 bytes to check for the required HLS tag
                    chunk = await response.content.read(100)
                    text = chunk.decode("utf-8", errors="ignore")
                    if "#EXTM3U" in text:
                        return item, True
                return item, False
        except (aiohttp.ClientError, asyncio.TimeoutError, Exception):
            return item, False

async def main():
    print(f"Testing {len(M3U8_LINKS)} streams concurrently...")
    start_time = time.time()

    # Semaphore limits concurrent connections to avoid flooding/rate-limits
    semaphore = asyncio.Semaphore(10)

    # Establish a single persistent ClientSession for connection pooling
    async with aiohttp.ClientSession() as session:
        tasks = [check_stream_health(session, stream, semaphore) for stream in M3U8_LINKS]
        results = await asyncio.gather(*tasks)

    # Filter for verified live streams
    working_streams = [item for item, is_online in results if is_online]

    # 1. Export working_streams.json (for frontend ingestion)
    json_output = [
        {
            "id": index + 1,
            "name": item["name"],
            "url": item["url"]
        }
        for index, item in enumerate(working_streams)
    ]

    with open("working_streams.json", "w", encoding="utf-8") as jf:
        json.dump(json_output, jf, indent=2)

    # 2. Export working_streams.m3u (standard IPTV playlist format)
    with open("working_streams.m3u", "w", encoding="utf-8") as mf:
        mf.write("#EXTM3U\n")
        for stream in json_output:
            mf.write(f"#EXTINF:-1 tvg-id=\"{stream['id']}\",{stream['name']}\n")
            mf.write(f"{stream['url']}\n")

    elapsed = round(time.time() - start_time, 2)
    print(f"\n--- Health Check Complete in {elapsed}s ---")
    print(f"Verified working streams: {len(working_streams)} / {len(M3U8_LINKS)}")
    for stream in json_output:
        print(f" [ONLINE] #{stream['id']}: {stream['name']} -> {stream['url']}")

    print("\nSaved output to working_streams.json and working_streams.m3u")

if __name__ == "__main__":
    asyncio.run(main())
