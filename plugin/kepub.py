import os
import shutil
import tempfile


def has_kepub_output_plugin():
    """True si hay un plugin con salida 'kepub' (KEPUB Output integrado
    en Calibre 7+, o KoboTouchExtended)."""
    try:
        from calibre.customize.ui import output_format_plugins
        for p in output_format_plugins():
            if getattr(p, 'file_type', '').lower() == 'kepub':
                return True
    except Exception:
        pass
    return False


def convert_epub_to_kepub(epub_path, log=None):
    """Convierte EPUB a KEPUB usando la pipeline de Calibre.

    Devuelve (ruta_temporal, metodo) con metodo en {'converted', 'renamed'}.
    El llamador debe borrar la ruta cuando termine.
    """
    if has_kepub_output_plugin():
        # OJO: Plumber detecta el formato por la extensión.
        # Necesita .kepub (no .kepub.epub), o usaría EPUB Output.
        plumber_dir = tempfile.mkdtemp(prefix='localsend_kepub_')
        plumber_out = os.path.join(plumber_dir, 'output.kepub')
        try:
            from calibre.ebooks.conversion.plumber import Plumber
            from calibre.utils.logging import default_log
            actual_log = log or default_log

            plumber = Plumber(epub_path, plumber_out, actual_log)
            plumber.run()

            if os.path.exists(plumber_out) and os.path.getsize(plumber_out) > 0:
                # Mover a un archivo final con extensión .kepub.epub
                # (Kobo lo reconoce así por LocalSend)
                fd, final_path = tempfile.mkstemp(suffix='.kepub.epub')
                os.close(fd)
                shutil.move(plumber_out, final_path)
                shutil.rmtree(plumber_dir, ignore_errors=True)
                return final_path, 'converted'
        except Exception as e:
            if log:
                try:
                    log.error(f'Conversión KEPUB falló, fallback a rename: {e}')
                except Exception:
                    pass
        finally:
            shutil.rmtree(plumber_dir, ignore_errors=True)

    # Fallback: copia con extensión .kepub.epub
    fd, out_path = tempfile.mkstemp(suffix='.kepub.epub')
    os.close(fd)
    shutil.copy2(epub_path, out_path)
    return out_path, 'renamed'