# Football Stream Validator Backend

Asynchronous Python backend and scheduled GitHub Actions workflow that tests and validates live HLS (`.m3u8`) stream manifests.

## Features
- **Asynchronous Concurrent Validation**: Uses `aiohttp` and `asyncio.Semaphore` to test multiple streams simultaneously with connection pooling.
- **Header Verification**: Ensures responses return HTTP 200 and the required `#EXTM3U` manifest header.
- **Dual Export**: Automatically generates:
  - `working_streams.json`: Structured array of working channels for frontend consumption.
  - `working_streams.m3u`: Standard IPTV playlist format.
- **Scheduled CI/CD Automation**: GitHub Action runs daily at midnight UTC to verify active feeds and auto-commit updated lists.

## Setup & Local Execution

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run stream health check:
   ```bash
   python check_streams.py
   ```
