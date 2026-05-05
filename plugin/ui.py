import re

from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog


def _safe_name(s):
    return re.sub(r'[<>:"/\\|?*\0]', '_', s).strip() or 'book'


class LocalSendAction(InterfaceAction):
    name = 'Send via LocalSend'
    action_spec = ('Send via LocalSend', None,
                   'Envía libro por LocalSend', None)
    action_type = 'current'

    # Localizaciones donde queremos que aparezca por defecto
    DEFAULT_LOCATIONS = (
        'action-layout-toolbar',          # barra principal
        'action-layout-context-menu',     # clic derecho en biblioteca
        # 'action-layout-menubar',        # barra de menú clásica
        # 'action-layout-context-menu-cover-browser',
        # 'action-layout-context-menu-split',
    )

    def genesis(self):
        # get_icons es inyectada por Calibre en el namespace del plugin
        icon = get_icons('images/icon.png', 'Send via LocalSend')
        self.qaction.setIcon(icon)
        self.qaction.triggered.connect(self.send_books)

    def _setup_default_placements(self):
        """Añade el plugin a las localizaciones deseadas la primera vez.
        Después respeta cualquier cambio que haga el usuario.
        """
        from calibre_plugins.localsend_plugin.config import prefs
        if prefs.get('placements_initialized', False):
            return

        from calibre.gui2 import gprefs

        changed = False
        for key in self.DEFAULT_LOCATIONS:
            current = list(gprefs.get(key, ()))
            if self.name not in current:
                current.append(self.name)
                gprefs[key] = current
                changed = True

        prefs['placements_initialized'] = True

        # Refrescar barras y menús sin reiniciar
        if changed:
            try:
                self.gui.bars_manager.init_bars()
            except Exception:
                # Si fallara, simplemente se aplicará al siguiente reinicio
                pass

    def initialization_complete(self):
        self._setup_default_placements()
        # Conectar al cambio de selección de la vista de biblioteca
        self.gui.library_view.selectionModel().selectionChanged.connect(
            self._update_enabled)
        self._update_enabled()

    def location_selected(self, loc):
        # Solo activo en la biblioteca (no cuando hay un dispositivo USB
        # seleccionado, etc.)
        self.qaction.setEnabled(loc == 'library' and self._has_selection())

    def _has_selection(self):
        try:
            return bool(
                self.gui.library_view.selectionModel().selectedRows())
        except Exception:
            return False

    def _update_enabled(self, *args):
        self.qaction.setEnabled(self._has_selection())

    # ------------------------------------------------------------------
    def send_books(self):
        from qt.core import QDialog
        from calibre_plugins.localsend_plugin.device_dialog import DeviceDialog
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

        # Preparar lista de libros (todo lo que necesite I/O de la
        # biblioteca lo hacemos aquí, en el hilo de UI)
        db = self.gui.current_db.new_api
        books = []
        skipped = []

        for row in rows:
            book_id = self.gui.library_view.model().id(row)
            title = db.field_for('title', book_id) or 'untitled'
            authors = db.field_for('authors', book_id) or ()
            author_str = ' & '.join(authors) if authors else 'Unknown'
            base_name = _safe_name(f'{title} - {author_str}')

            if db.has_format(book_id, 'KEPUB'):
                fmt = 'KEPUB'
                path = db.format_abspath(book_id, 'KEPUB')
                send_filename = f'{base_name}.kepub.epub'
            elif db.has_format(book_id, 'EPUB'):
                fmt = 'EPUB'
                path = db.format_abspath(book_id, 'EPUB')
                # Si vamos a kepubificar, lo guardamos como .kepub.epub
                send_filename = (f'{base_name}.kepub.epub'
                                 if kepubify else f'{base_name}.epub')
            else:
                skipped.append(f'{title}: sin EPUB/KEPUB')
                continue

            books.append({
                'book_id': book_id,
                'title': title,
                'format': fmt,
                'path': path,
                'send_filename': send_filename,
            })

        if not books:
            return error_dialog(
                self.gui, 'LocalSend',
                'Ninguno de los libros seleccionados tiene formato EPUB/KEPUB.\n\n' +
                '\n'.join(skipped),
                show=True)

        # Lanzar el job en background
        from calibre.gui2.threaded_jobs import ThreadedJob
        from calibre_plugins.localsend_plugin.job import send_books_job

        description = (f'LocalSend → {target_ip}: '
                       f'{len(books)} libro(s)')

        job = ThreadedJob(
            'localsend_send_books',     # tipo
            description,                 # descripción visible
            send_books_job,              # función
            (target_ip, books, kepubify),
            {},
            self._on_send_done,          # callback al terminar
            killable=True,
        )
        self.gui.job_manager.run_threaded_job(job)

        # Pequeño aviso en la status bar
        self.gui.status_bar.show_message(
            f'LocalSend: enviando {len(books)} libro(s)…', 5000)

        # Si hubo libros saltados, avisamos ya
        if skipped:
            info_dialog(
                self.gui, 'LocalSend',
                'Algunos libros no se enviarán:\n• ' + '\n• '.join(skipped),
                show=True)

    # ------------------------------------------------------------------
    def _on_send_done(self, job):
        if job.failed:
            # job.failed True si la función lanzó excepción
            return self.gui.job_exception(
                job, dialog_title='LocalSend: error')

        result = job.result or {'sent': [], 'errors': []}
        sent = result.get('sent', [])
        errors = result.get('errors', [])

        msg = ''
        if sent:
            msg += 'Enviados:\n• ' + '\n• '.join(sent)
        if errors:
            msg += '\n\nErrores:\n• ' + '\n• '.join(errors)
        info_dialog(self.gui, 'LocalSend',
                    msg or 'Nada que enviar.', show=True)