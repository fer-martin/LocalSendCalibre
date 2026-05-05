import os


def send_books_job(target_ip, books, kepubify,
                   log=None, abort=None, notifications=None):
    """Función que se ejecuta en hilo separado.

    `books` es una lista de dicts con: book_id, title, format, path, send_filename.
    Devuelve {'sent': [...], 'errors': [...]}.
    """
    from calibre_plugins.localsend_plugin.localsend import send_to_localsend
    from calibre_plugins.localsend_plugin.kepub import convert_epub_to_kepub

    sent = []
    errors = []
    temp_files = []
    total = len(books)

    def notify(pct, msg):
        if notifications is not None:
            try:
                notifications.put((pct, msg))
            except Exception:
                pass
        if log is not None:
            try:
                log(msg)
            except Exception:
                pass

    try:
        for idx, book in enumerate(books):
            if abort is not None and abort.is_set():
                notify(idx / total, 'Cancelado')
                break

            title = book['title']
            base = idx / total
            step = 1.0 / total

            send_path = book['path']
            method = 'as-is'

            # Kepubificación si procede
            if book['format'] == 'EPUB' and kepubify:
                notify(base, f'Convirtiendo a KEPUB: {title}')
                try:
                    tmp_path, method = convert_epub_to_kepub(
                        book['path'], log=log)
                    temp_files.append(tmp_path)
                    send_path = tmp_path
                except Exception as e:
                    errors.append(f'{title}: error kepubificando: {e}')
                    notify(base + step, '')
                    continue

            if abort is not None and abort.is_set():
                notify(base, 'Cancelado')
                break

            notify(base + step * 0.5, f'Enviando: {title}')
            try:
                send_to_localsend(send_path, target_ip,
                                  filename=book['send_filename'])
                sent.append(f'{title} [{method}]')
            except Exception as e:
                errors.append(f'{title}: {e}')

            notify(base + step, '')

        notify(1.0, 'Hecho')
    finally:
        for p in temp_files:
            try:
                os.remove(p)
            except Exception:
                pass

    return {'sent': sent, 'errors': errors}