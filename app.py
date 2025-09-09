from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp
import os
import base64

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
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
            ydl_opts = {
                "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
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

            # Get absolute path (important for send_file)
            filepath = os.path.abspath(filename)

            # Debug log
            print(f"Preparing to send file: {filepath}, exists={os.path.exists(filepath)}")

            @after_this_request
            def remove_file(response):
                try:
                    os.remove(filepath)
                    print(f"Deleted file: {filepath}")
                except Exception as e:
                    print(f"Error deleting file: {e}")
                return response

            return send_file(filepath, as_attachment=True)

        except Exception as e:
            return render_template("index.html", error=f"Error: {str(e)}")

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
