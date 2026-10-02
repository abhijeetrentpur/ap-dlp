import os
import sys
import shutil

# Automatically load bundled static FFmpeg into PATH
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

import yt_dlp

FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None

def print_banner():
    print("\n" + "=" * 55)
    print("      AP-DLP PYTHON DOWNLOADER (BY Abhijeet Pandey | https://github.com/abhijeetrentpur/ap-dlp)")
    print("=" * 55)
    if FFMPEG_AVAILABLE:
        print("[Status] FFmpeg is active! High quality video & audio merging enabled.")
    else:
        print("[Notice] FFmpeg not detected. Pre-merged formats will be used.")
    print("-" * 55)

def select_quality():
    print("\nSelect Video Quality:")
    print("  1. Best Available (Highest Quality)")
    print("  2. 1080p (Full HD)")
    print("  3. 720p (HD)")
    print("  4. 480p (Standard)")
    print("  5. 360p (Low / Data Saver)")
    choice = input("Enter choice (1-5) [Default 1]: ").strip()
    
    res_map = {
        '1': None,
        '2': 1080,
        '3': 720,
        '4': 480,
        '5': 360,
    }
    height = res_map.get(choice, None)
    
    if height is None:
        if FFMPEG_AVAILABLE:
            return 'bestvideo+bestaudio/best', 'Best Available'
        else:
            return 'best[ext=mp4]/best', 'Best Available (Pre-merged)'
    else:
        if FFMPEG_AVAILABLE:
            return f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best', f'{height}p'
        else:
            return f'best[height<={height}][ext=mp4]/best[height<={height}]/best', f'{height}p (Pre-merged)'

def create_progress_hook():
    downloaded_files = []
    
    def hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed')
            eta = d.get('eta')
            
            bar_len = 25
            if total > 0:
                percent = (downloaded / total) * 100
                filled = int(bar_len * downloaded // total)
                bar = '=' * filled + ('>' if filled < bar_len else '')
                bar = bar.ljust(bar_len, '.')
                total_str = f"{total / (1024 * 1024):.1f} MB"
            else:
                percent = 0.0
                bar = '.' * bar_len
                total_str = "Unknown"
                
            dl_str = f"{downloaded / (1024 * 1024):.1f} MB"
            speed_str = f"{speed / (1024 * 1024):.2f} MB/s" if speed else "-- MB/s"
            eta_str = f"{int(eta)}s" if eta is not None else "--s"
            
            sys.stdout.write(
                f"\r  Progress: [{bar}] {percent:5.1f}% | {dl_str}/{total_str} | {speed_str} | ETA: {eta_str}   "
            )
            sys.stdout.flush()
            
        elif d['status'] == 'finished':
            filepath = d.get('filename')
            if filepath and filepath not in downloaded_files:
                downloaded_files.append(filepath)
            sys.stdout.write("\n  [Status] Stream downloaded! Finalizing/merging file...\n")
            sys.stdout.flush()

    return hook, downloaded_files

def get_downloader(ydl_opts, url, download_path):
    print(f"\n[Download Destination Folder]: {os.path.abspath(download_path)}")
    print(f"[Target URL]: {url}")
    print("[Starting download...]")
    
    hook, downloaded_files = create_progress_hook()
    ydl_opts['progress_hooks'] = [hook]
    ydl_opts['noprogress'] = True
    
    final_files = []
    def post_processor_hook(d):
        if d.get('status') == 'finished':
            info = d.get('info_dict', {})
            fp = info.get('filepath') or info.get('_filename')
            if fp and fp not in final_files:
                final_files.append(fp)
                
    ydl_opts['postprocessor_hooks'] = [post_processor_hook]
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            print("\n" + "=" * 55)
            print("[Success] Download completed successfully!")
            
            # Display final merged files that exist on disk
            saved = [f for f in final_files if os.path.exists(f)]
            if not saved:
                saved = [f for f in downloaded_files if os.path.exists(f)]
                
            if saved:
                print("[Saved File(s)]:")
                for f in list(dict.fromkeys(saved)):
                    print(f"  -> {os.path.abspath(f)}")
            else:
                print(f"[Saved in]: {os.path.abspath(download_path)}")
            print("=" * 55)
    except Exception as e:
        print(f"\n[Error] Download failed: {e}")

def show_menu(download_path):
    print_banner()
    print(f"Active Download Directory:\n  -> {os.path.abspath(download_path)}")
    print("-" * 55)
    print("1. Download Video (Select Quality: 1080p, 720p, 480p, 360p, Best)")
    print("2. Download Audio Only (Extract MP3 / Audio)")
    print("3. Download Entire Playlist")
    print("4. Download Video with Subtitles")
    print("5. Change Download Directory")
    print("6. Exit")
    return input("Select an option (1-6): ").strip()

def main():
    download_path = os.path.join(os.getcwd(), 'downloads')
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    while True:
        choice = show_menu(download_path)
        
        if choice == '6':
            print("\nExiting program. Goodbye!")
            break
            
        if choice == '5':
            new_path = input(f"\nEnter new download path [current: {download_path}]: ").strip()
            if new_path:
                if not os.path.exists(new_path):
                    try:
                        os.makedirs(new_path)
                        download_path = new_path
                        print(f"[Success] Directory created: {download_path}")
                    except Exception as err:
                        print(f"[Error] Could not create directory: {err}")
                else:
                    download_path = new_path
                    print(f"[Success] Download directory set to: {download_path}")
            continue

        if choice not in ['1', '2', '3', '4']:
            print("\n[Invalid option] Please choose between 1 and 6.")
            continue

        url = input("\nEnter the Video/Playlist URL: ").strip()
        if not url:
            print("[Error] URL cannot be empty.")
            continue

        base_opts = {
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'js_runtimes': {'node': {}},
        }

        if choice == '1':
            format_str, quality_label = select_quality()
            print(f"[Selected Quality]: {quality_label}")
            base_opts['format'] = format_str
            if FFMPEG_AVAILABLE:
                base_opts['merge_output_format'] = 'mp4'
            
        elif choice == '2':
            if FFMPEG_AVAILABLE:
                base_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
            else:
                print("\n[Notice] FFmpeg is not installed. Downloading native audio (m4a/webm) without re-encoding.")
                base_opts.update({
                    'format': 'bestaudio/best',
                })
            
        elif choice == '3':
            format_str, quality_label = select_quality()
            print(f"[Selected Quality for Playlist]: {quality_label}")
            base_opts.update({
                'format': format_str,
                'noplaylist': False,
                'outtmpl': os.path.join(download_path, '%(playlist_title)s', '%(playlist_index)s - %(title)s.%(ext)s'),
            })
            if FFMPEG_AVAILABLE:
                base_opts['merge_output_format'] = 'mp4'
            
        elif choice == '4':
            format_str, quality_label = select_quality()
            base_opts.update({
                'format': format_str,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
            })
            if FFMPEG_AVAILABLE:
                base_opts['merge_output_format'] = 'mkv'
                base_opts['postprocessors'] = [{
                    'key': 'FFmpegEmbedSubtitle',
                    'already_have_subtitle': False,
                }]

        get_downloader(base_opts, url, download_path)

if __name__ == "__main__":
    main()
