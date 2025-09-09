from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp
import os

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        if not url:
            return render_template("index.html", error="Please enter a URL")

        try:
            ydl_opts = {
                "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
                "nocheckcertificate": True,
                "noplaylist": True   # only download one video
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if not filename.endswith(".mp4"):
                    filename = os.path.splitext(filename)[0] + ".mp4"

            # delete after sending
            @after_this_request
            def remove_file(response):
                try:
                    os.remove(filename)
                except Exception as e:
                    print(f"Error deleting file: {e}")
                return response

            return send_file(filename, as_attachment=True)

        except Exception as e:
            return render_template("index.html", error=f"Error: {str(e)}")

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
