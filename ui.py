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
        from calibre_plugins.localsend_plugin.device_dialog import DeviceDialog

        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            return error_dialog(self.gui, 'LocalSend',
                                'Selecciona al menos un libro.', show=True)

        dlg = DeviceDialog(self.gui)
        if dlg.exec() != QDialog_Accepted() or not dlg.selected_ip:
            return
        target_ip = dlg.selected_ip

        db = self.gui.current_db.new_api
        sent, errors = [], []

        for row in rows:
            book_id = self.gui.library_view.model().id(row)
            title = db.field_for('title', book_id)

            fmt = None
            for candidate in ('KEPUB', 'EPUB'):
                if db.has_format(book_id, candidate):
                    fmt = candidate
                    break
            if not fmt:
                errors.append(f'{title}: sin formato EPUB/KEPUB')
                continue

            path = db.format_abspath(book_id, fmt)
            try:
                send_to_localsend(path, target_ip)
                sent.append(title)
            except Exception as e:
                errors.append(f'{title}: {e}')

        msg = ''
        if sent:
            msg += 'Enviados:\n' + '\n'.join(sent)
        if errors:
            msg += '\n\nErrores:\n' + '\n'.join(errors)
        info_dialog(self.gui, 'LocalSend', msg or 'Nada que enviar.', show=True)


def QDialog_Accepted():
    # Helper compatible PyQt5 / PyQt6
    from qt.core import QDialog
    return QDialog.DialogCode.Accepted