"""
Tải artifact articles_cache.json từ workflow fetch_news sang workflow send_news.
Dùng GitHub REST API với GITHUB_TOKEN tự động có sẵn trong Actions.
"""
import os
import json
import zipfile
import io
import urllib.request
import urllib.error

HEADERS = {
    "Authorization": f"Bearer {os.environ.get('GITHUB_TOKEN', '')}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
REPO = os.environ.get("GITHUB_REPOSITORY", "")


def _get(url: str):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def download_cache(artifact_name: str) -> bool:
    """
    Tải artifact_name từ lần chạy thành công mới nhất của fetch_news.yml.
    Trả về True nếu tải được, False nếu không.
    """
    if not REPO or not os.environ.get("GITHUB_TOKEN"):
        print("  [cache] Không có GITHUB_TOKEN/REPO – bỏ qua.")
        return False

    try:
        # Tìm các lần chạy thành công gần nhất của fetch_news.yml
        runs_url = (
            f"https://api.github.com/repos/{REPO}/actions/workflows/"
            f"fetch_news.yml/runs?status=success&per_page=5"
        )
        runs = _get(runs_url).get("workflow_runs", [])
        if not runs:
            print("  [cache] Chưa có lần chạy fetch_news nào thành công.")
            return False

        for run in runs:
            run_id = run["id"]
            arts = _get(
                f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/artifacts"
            ).get("artifacts", [])

            for art in arts:
                if art["name"] == artifact_name and not art.get("expired", False):
                    dl_url = art["archive_download_url"]
                    req = urllib.request.Request(dl_url, headers=HEADERS)
                    with urllib.request.urlopen(req) as resp:
                        raw = resp.read()

                    zf = zipfile.ZipFile(io.BytesIO(raw))
                    with zf.open("articles_cache.json") as f:
                        articles = json.load(f)

                    with open("articles_cache.json", "w", encoding="utf-8") as out:
                        json.dump(articles, out, ensure_ascii=False, indent=2)

                    print(f"  [cache] Tải thành công '{artifact_name}' ({len(articles)} bài, run {run_id})")
                    return True

        print(f"  [cache] Không tìm thấy artifact '{artifact_name}'.")
        return False

    except Exception as e:
        print(f"  [cache] Lỗi khi tải artifact: {e}")
        return False
