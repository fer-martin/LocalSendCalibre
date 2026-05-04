import os
import re
import shutil
import tempfile

from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog


def _safe_name(s):
    return re.sub(r'[<>:"/\\|?*\0]', '_', s).strip() or 'book'


class LocalSendAction(InterfaceAction):
    name = 'Send via LocalSend'
    action_spec = ('Send via LocalSend', None, 'Envía libro por LocalSend', None)
    action_type = 'current'

    def genesis(self):
        self.qaction.triggered.connect(self.send_books)

    def send_books(self):
        from qt.core import QDialog
        from calibre_plugins.localsend_plugin.localsend import send_to_localsend
        from calibre_plugins.localsend_plugin.device_dialog import DeviceDialog
        from calibre_plugins.localsend_plugin.kepub import convert_epub_to_kepub
        from calibre_plugins.localsend_plugin.config import prefs

        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            return error_dialog(self.gui, 'LocalSend',
                                'Selecciona al menos un libro.', show=True)

        dlg = DeviceDialog(self.gui)
        if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.selected_ip:
            return
        target_ip = dlg.selected_ip

        kepubify = bool(prefs['kepubify'])
        db = self.gui.current_db.new_api

        sent, errors = [], []
        temp_files = []

        try:
            for row in rows:
                book_id = self.gui.library_view.model().id(row)
                title = db.field_for('title', book_id) or 'untitled'
                authors = db.field_for('authors', book_id) or ()
                author_str = ' & '.join(authors) if authors else 'Unknown'
                base_name = _safe_name(f'{title} - {author_str}')

                send_path = None
                send_filename = None

                # 1. Si ya hay KEPUB en la biblioteca, usarlo
                if db.has_format(book_id, 'KEPUB'):
                    send_path = db.format_abspath(book_id, 'KEPUB')
                    send_filename = f'{base_name}.kepub.epub'

                # 2. Si hay EPUB, kepubificar (o no) según preferencia
                elif db.has_format(book_id, 'EPUB'):
                    epub_path = db.format_abspath(book_id, 'EPUB')
                    if kepubify:
                        try:
                            tmp_path, method = convert_epub_to_kepub(epub_path)
                            temp_files.append(tmp_path)
                            send_path = tmp_path
                            send_filename = f'{base_name}.kepub.epub'
                        except Exception as e:
                            errors.append(f'{title}: error kepubificando: {e}')
                            continue
                    else:
                        send_path = epub_path
                        send_filename = f'{base_name}.epub'
                else:
                    errors.append(f'{title}: sin formato EPUB/KEPUB')
                    continue

                try:
                    send_to_localsend(send_path, target_ip,
                                      filename=send_filename)
                    sent.append(title)
                except Exception as e:
                    errors.append(f'{title}: {e}')
        finally:
            for p in temp_files:
                try:
                    os.remove(p)
                except Exception:
                    pass

        msg = ''
        if sent:
            msg += 'Enviados:\n• ' + '\n• '.join(sent)
        if errors:
            msg += '\n\nErrores:\n• ' + '\n• '.join(errors)
        info_dialog(self.gui, 'LocalSend',
                    msg or 'Nada que enviar.', show=True)