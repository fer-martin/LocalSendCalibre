from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog


class LocalSendAction(InterfaceAction):
    name = 'Send via LocalSend'
    action_spec = ('Send via LocalSend', None, 'Envía libro por LocalSend', None)
    action_type = 'current'

    def genesis(self):
        self.qaction.triggered.connect(self.send_books)

    def send_books(self):
        from calibre_plugins.localsend_plugin.localsend import send_to_localsend

        # IP del Kobo — cámbiala por la tuya
        TARGET_IP = '192.168.68.114'

        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            return error_dialog(self.gui, 'LocalSend',
                                'Selecciona al menos un libro.', show=True)

        db = self.gui.current_db.new_api
        sent = []
        errors = []

        for row in rows:
            book_id = self.gui.library_view.model().id(row)
            title = db.field_for('title', book_id)

            # Preferir KEPUB, luego EPUB
            fmt = None
            for candidate in ('KEPUB', 'EPUB'):
                if db.has_format(book_id, candidate):
                    fmt = candidate
                    break

            if not fmt:
                errors.append(f"{title}: sin formato EPUB/KEPUB")
                continue

            path = db.format_abspath(book_id, fmt)
            try:
                send_to_localsend(path, TARGET_IP)
                sent.append(title)
            except Exception as e:
                errors.append(f"{title}: {e}")

        msg = ''
        if sent:
            msg += "Enviados:\n" + "\n".join(sent)
        if errors:
            msg += "\n\nErrores:\n" + "\n".join(errors)

        info_dialog(self.gui, 'LocalSend', msg or 'Nada que enviar.',
                    show=True)