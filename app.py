from flask import Flask, render_template, request, send_file, after_this_request, send_from_directory
import yt_dlp
import os
import base64
import uuid

app = Flask(__name__)

# Use persistent disk if available (Render) else fallback to local "downloads"
DOWNLOAD_FOLDER = os.getenv("DOWNLOAD_FOLDER", "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# --- Cookie setup ---
COOKIE_FILE_PATH = None
COOKIES_B64 = os.environ.get("COOKIES_B64")

if COOKIES_B64:
    try:
        COOKIE_FILE_PATH = os.path.join(DOWNLOAD_FOLDER, "cookies.txt")
        with open(COOKIE_FILE_PATH, "wb") as f:
            f.write(base64.b64decode(COOKIES_B64))
        print(f"[INFO] Cookies file created at {COOKIE_FILE_PATH}")
    except Exception as e:
        print("[ERROR] Could not decode COOKIES_B64:", e)
        COOKIE_FILE_PATH = None
elif os.path.exists("cookies.txt"):
    COOKIE_FILE_PATH = os.path.abspath("cookies.txt")
    print("[INFO] Using local cookies.txt")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        if not url:
            return render_template("index.html", error="Please enter a URL")

        try:
            # Unique filename per request to avoid conflicts
            uid = str(uuid.uuid4())
            outtmpl = os.path.join(DOWNLOAD_FOLDER, f"{uid}_%(title)s.%(ext)s")

            ydl_opts = {
                "outtmpl": outtmpl,
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
                "nocheckcertificate": True,
                "noplaylist": True
            }

            if COOKIE_FILE_PATH:
                ydl_opts["cookiefile"] = COOKIE_FILE_PATH

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            filepath = os.path.abspath(filename)
            print(f"[DEBUG] File ready: {filepath}, exists={os.path.exists(filepath)}")

            # Instead of direct send (may timeout), give user a link
            download_name = os.path.basename(filepath)
            return render_template("index.html", 
                                   message=f"Download complete! Click below:",
                                   download_link=f"/downloads/{download_name}")

        except Exception as e:
            return render_template("index.html", error=f"Error: {str(e)}")

    return render_template("index.html")


@app.route("/downloads/<filename>")
def serve_download(filename):
    """Serve a file from the download folder and delete it after sending."""
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    if not os.path.exists(filepath):
        return f"File not found: {filename}", 404

    @after_this_request
    def cleanup(response):
        try:
            os.remove(filepath)
            print(f"[INFO] Deleted file after send: {filepath}")
        except Exception as e:
            print(f"[ERROR] Failed to delete {filepath}: {e}")
        return response

    # Use send_file instead of send_from_directory (more reliable cleanup)
    return send_file(filepath, as_attachment=True)


if __name__ == "__main__":
    # Bind to 0.0.0.0 for Render
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 3001)), debug=True)
