"""InternLink — Development entry point."""

from app import create_app

app = create_app()

if __name__ == '__main__':
    # threaded=True: dev server melayani banyak request paralel (HTML, CSS,
    # font, JS). Tanpa ini server single-threaded -> aset antre berurutan
    # dan LCP membengkak beberapa detik walau waktu server kecil.
    app.run(debug=True, port=5000, threaded=True)
