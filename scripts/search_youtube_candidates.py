import yt_dlp

queries = {
    'workshop': 'ytsearch4:workshop assembly line workers mechanic cctv',
    'warehouse': 'ytsearch4:warehouse forklift loading dock cctv security camera',
    'retail_queue': 'ytsearch4:supermarket checkout queue cctv footage',
    'cafe': 'ytsearch4:restaurant dining tables cctv footage surveillance',
    'bottling': 'ytsearch4:bottling plant conveyor belt industrial packaging',
    'barcode': 'ytsearch4:conveyor belt barcode scanner logistics packaging',
    'pedestrian': 'ytsearch4:pedestrian street crossing cctv surveillance footage',
    'safety_k3': 'ytsearch4:construction workers safety vest helmet cctv',
    'gym': 'ytsearch4:gym squat exercise side view workout fitness',
    'dashcam': 'ytsearch4:truck driver cabin dashcam blind spot highway'
}

ydl = yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'extract_flat': True})
for cat, q in queries.items():
    print(f"=== {cat} ===")
    try:
        res = ydl.extract_info(q, download=False)
        for entry in res.get('entries', []):
            eid = entry.get('id')
            title = entry.get('title')
            dur = entry.get('duration')
            print(f"https://www.youtube.com/watch?v={eid} | {dur}s | {title}")
    except Exception as e:
        print(f"Error {cat}: {e}")
