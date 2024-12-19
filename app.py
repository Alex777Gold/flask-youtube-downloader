from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp
import os
import time

app = Flask(__name__)

# Path to save files
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Function to get available formats


def get_available_formats(url):
    try:
        # Options to get formats without downloading
        ydl_opts = {
            'quiet': True,
            'noplaylist': True,
            'extractaudio': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])
            available_formats = []
            for f in formats:
                available_formats.append({
                    'format': f['format_id'],
                    'quality': f.get('quality', 'Unknown'),
                    'ext': f['ext'],
                    'resolution': f.get('height', 'Unknown'),
                    'vcodec': f.get('vcodec', 'Unknown'),
                    'acodec': f.get('acodec', 'Unknown')
                })
            return available_formats
    except Exception as e:
        return str(e)

# Function to download video or audio


def download_video(url, only_audio=False):
    try:
        # Get UNIX timestamp
        unix_timestamp = int(time.time())

        # If only audio, set parameters to download only audio
        if only_audio:
            ydl_opts = {
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'noplaylist': True,  # Don't download playlist
                'format': 'bestaudio/best',  # Select only audio (best)
                'extractaudio': True,  # Extract only audio
                'audioquality': 0,  # Best audio quality
            }
        else:
            # If both video and audio, select the best format for both
            ydl_opts = {
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'noplaylist': True,  # Don't download playlist
                'format': 'bestvideo+bestaudio/best',  # Download best video and audio
                'extractaudio': False,  # Don't extract audio, keep it with the video
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)

            # Add UNIX timestamp to the filename
            file_path_with_timestamp = file_path.replace(
                info_dict['title'], f"{info_dict['title']}_{unix_timestamp}")

            # Rename the file to add the timestamp
            os.rename(file_path, file_path_with_timestamp)

            # Return a message with the saved file name
            return f"'{file_path_with_timestamp}'"
    except Exception as e:
        return f"Error during download: {e}"

# Main page


@app.route('/')
def index():
    return render_template('index.html')

# Get available formats


@app.route('/get_formats', methods=['POST'])
def get_formats():
    url = request.json.get('url')
    formats = get_available_formats(url)

    formats.reverse()
    return jsonify(formats)

# Download video or audio


@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    only_audio = 'audio' in request.form

    message = download_video(url, only_audio)
    return render_template('index.html', message=message)

# Download file


@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)


# Run the application
if __name__ == '__main__':
    app.run(debug=True)
