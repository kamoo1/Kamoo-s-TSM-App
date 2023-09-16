# TODO:
# - tool tab, clear cache
# - tool tab, install font?
# - tool tab, patch tsm region db
# DONE:
# - "local remote" mode updating
# - save settings on close, load on init
# - make region / game version selection related requests in a thread

import re
import os
from typing import (
    Tuple,
    List,
    Set,
    Dict,
    Callable,
)
from functools import wraps
import logging
import itertools

from PyQt5.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QWidget,
    QMessageBox,
    QLineEdit,
    QCheckBox,
    QComboBox,
)
from PyQt5.QtGui import (
    QValidator,
    QStandardItemModel,
    QStandardItem,
    QTextCursor,
)
from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
    QThread,
    QObject,
    QTimer,
    QSettings,
)

from ah import config
from ah.ui.main_view import Ui_MainWindow
from ah.tsm_exporter import TSMExporter, main as exporter_main
from ah.updater import main as updater_main
from ah.db import AuctionDB
from ah.cache import Cache
from ah.models.base import StrEnum_
from ah.models.blizzard import (
    RegionEnum,
    GameVersionEnum,
    Namespace,
    NameSpaceCategoriesEnum,
)
from ah.api import GHAPI, BNAPI


DEFAULT_SETTINGS = (
    ("settings/db_path", "db", "lineEdit_settings_db_path"),
    (
        "settings/warcraft_base",
        TSMExporter.find_warcraft_base() or "",
        "lineEdit_settings_game_path",
    ),
    (
        "settings/repo",
        "https://github.com/kamoo1/TSM-Backend",
        "lineEdit_settings_repo",
    ),
    (
        "settings/gh_proxy",
        "https://worker.moonglade.site",
        "lineEdit_settings_gh_proxy",
    ),
    ("settings/gh_proxy_enabled", True, "checkBox_settings_gh_proxy"),
    ("exporter/region", RegionEnum.TW.name, "comboBox_exporter_region"),
    (
        "exporter/game_version",
        GameVersionEnum.RETAIL.name,
        "comboBox_exporter_game_version",
    ),
    ("exporter/remote", True, "checkBox_exporter_remote"),
    ("updater/remote", True, "checkBox_updater_remote"),
    ("updater/client_id", "", "lineEdit_updater_id"),
    ("updater/client_secret", "", "lineEdit_updater_secret"),
)


class WorkerThread(QThread):
    _sig_final = pyqtSignal(bool, str)
    _sig_data = None
    logger = logging.getLogger("WorkerThread")

    def __init__(
        self,
        parent: QObject,
        func: Callable,
        *args,
        _on_final: Callable = None,
        **kwargs,
    ):
        # NOTE: make sure child class consumes all their arguments
        # or else they will be passed to the function and probably cause error.

        # NOTE:
        # To pervent error - 'QThread: Destroyed while thread is still running':
        # QThread need to be referenced in order to prevent it from being garbage
        # collected.
        # StackOverflow:
        # https://stackoverflow.com/questions/43647719
        super().__init__(parent=parent)
        self._func = func
        self._args = args
        if _on_final:
            self._sig_final.connect(_on_final)
        self._kwargs = kwargs

    def run(self):
        try:
            ret = self._func(*self._args, **self._kwargs)
        except Exception as e:
            self.logger.exception(e)
            if self._sig_final:
                self._sig_final.emit(False, str(e))

            return

        else:
            if self._sig_final:
                self._sig_final.emit(True, "")

            return ret


class ExporterDropdownWorkerThread(WorkerThread):
    # Dict[str, List[str]]
    _sig_data = pyqtSignal(dict)

    def __init__(self, *args, _on_data: Callable = None, **kwargs):
        super().__init__(*args, **kwargs)
        if _on_data:
            self._sig_data.connect(_on_data)

    def run(self):
        ret = super().run()
        if self._sig_data and ret:
            self._sig_data.emit(ret)


def threaded(parent, worker_cls=WorkerThread, **kwargs):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs_):
            kwargs.update(kwargs_)
            thread = worker_cls(parent, func, *args, **kwargs)
            thread.start()

        return inner

    return wrapper


class LoggingLevel(StrEnum_):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEmitterHandler(logging.Handler):
    def __init__(self, log_signal):
        super().__init__()
        self._log_signal = log_signal

    def emit(self, record):
        msg = self.format(record)
        self._log_signal.emit(msg)


class AppError(Exception):
    pass


class ConfigError(AppError):
    pass


class VisualValidator(QValidator):
    state_signal = pyqtSignal(QValidator.State)

    def __init__(self, obj: QWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._obj = obj
        self._state = None
        self.state_signal.connect(self.on_state_change)

    def on_state_change(self, state: QValidator.State):
        if state == self.State.Invalid:
            style = "border: 2px solid orange"
        elif state == self.State.Intermediate:
            style = "border: 2px solid orange"
        elif state == self.State.Acceptable:
            style = ""
        self._obj.setStyleSheet(style)
        self._state = state

    def get_state(self) -> QValidator.State:
        return self._state


class WarCraftBaseValidator(VisualValidator):
    def validate(self, text: str, pos: int) -> Tuple[QValidator.State, str, int]:
        if TSMExporter.validate_warcraft_base(text):
            state = self.State.Acceptable

        else:
            state = self.State.Intermediate

        self.state_signal.emit(state)
        return self.State.Acceptable, text, pos

    def raise_invalid(self) -> None:
        if self.get_state() != QValidator.Acceptable:
            raise ConfigError("Invalid Warcraft Base Path")


class RepoValidator(VisualValidator):
    def validate(self, text: str, pos: int) -> Tuple[QValidator.State, str, int]:
        if AuctionDB.validate_repo(text):
            state = self.State.Acceptable

        else:
            state = self.State.Intermediate

        self.state_signal.emit(state)
        return self.State.Acceptable, text, pos

    def raise_invalid(self):
        if self.get_state() != QValidator.Acceptable:
            raise ConfigError("Invalid Github Repo")


class GHProxyValidator(VisualValidator):
    def validate(self, text: str, pos: int) -> Tuple[QValidator.State, str, int]:
        if GHAPI.validate_gh_proxy(text):
            state = self.State.Acceptable

        else:
            state = self.State.Intermediate

        self.state_signal.emit(state)
        return self.State.Acceptable, text, pos

    def raise_invalid(self):
        if self.get_state() != QValidator.Acceptable:
            raise ConfigError("Invalid Github Proxy")


class RegexValidator(VisualValidator):
    def __init__(self, obj: QWidget, regex: str, *args, **kwargs):
        super().__init__(obj, *args, **kwargs)
        self._regex = regex

    def validate(self, text: str, pos: int) -> Tuple[QValidator.State, str, int]:
        if re.match(self._regex, text):
            state = self.State.Acceptable

        else:
            state = self.State.Intermediate

        self.state_signal.emit(state)
        return self.State.Acceptable, text, pos

    def raise_invalid(self):
        if self.get_state() != QValidator.Acceptable:
            raise ConfigError("Invalid Input")


class RealmsModel(QStandardItemModel):
    def __init__(self, data: List[Tuple[str, int]], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._data = data
        for realm, crid in data:
            item = QStandardItem(f"{realm}\t{crid}")
            item.setCheckable(True)
            item.setEditable(False)
            self.appendRow(item)

    def get_selected_realms(self) -> Set[str]:
        realms = set()
        for row in range(self.rowCount()):
            item = self.item(row)
            if item.checkState() == Qt.Checked:
                realm = self._data[row][0]
                realms.add(realm)

        return realms


class UpdaterModel(QStandardItemModel):
    def __init__(
        self,
        data: List[Tuple[RegionEnum, GameVersionEnum]],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._data = data
        for region, game_version in data:
            item = QStandardItem(f"{region.name}\t{game_version.name}")
            item.setCheckable(True)
            item.setEditable(False)
            self.appendRow(item)

    def get_selected_combos(self) -> Set[Tuple[RegionEnum, GameVersionEnum]]:
        combos = set()
        for row in range(self.rowCount()):
            item = self.item(row)
            if item.checkState() == Qt.Checked:
                combo = self._data[row]
                combos.add(combo)

        return combos


class Window(QMainWindow, Ui_MainWindow):
    _log_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        # widgets that need to be disabled when updating or exporting
        lock_on_any = [
            self.lineEdit_settings_db_path,
            self.lineEdit_settings_game_path,
            self.toolButton_settings_db_path,
            self.toolButton_settings_game_path,
            self.lineEdit_settings_repo,
            self.lineEdit_settings_gh_proxy,
        ]
        # widgets that need to be disabled when exporting
        self._lock_on_export = [
            self.comboBox_exporter_region,
            self.comboBox_exporter_game_version,
            self.listView_exporter_realms,
            self.checkBox_exporter_remote,
            self.pushButton_exporter_export,
            self.pushButton_updater_update,
        ]
        self._lock_on_export.extend(lock_on_any)
        # widgets that need to be disabled when updating
        self._lock_on_update = [
            self.lineEdit_updater_id,
            self.lineEdit_updater_secret,
            self.checkBox_updater_remote,
            self.pushButton_updater_update,
            self.pushButton_exporter_export,
        ]
        self._lock_on_update.extend(lock_on_any)

        # widgets that need to be disabled when selecting
        # export region / game version
        self._lock_on_export_dropdown = [
            self.comboBox_exporter_region,
            self.comboBox_exporter_game_version,
            self.listView_exporter_realms,
            self.checkBox_exporter_remote,
            self.pushButton_exporter_export,
        ]
        self._lock_on_export_dropdown.extend(lock_on_any)

        self._log_handler = None
        self.settings = QSettings("settings.ini", QSettings.IniFormat)
        self.set_up()
        self.load_settings()

        # timer = QTimer(self)
        # timer.singleShot(100, self.post_init)

    def closeEvent(self, event) -> None:
        self.save_settings()
        event.accept()

    def load_settings(self) -> None:
        for key, value, widget_name in DEFAULT_SETTINGS:
            widget = getattr(self, widget_name)
            if isinstance(widget, QLineEdit):
                widget.setText(self.settings.value(key, value))
            elif isinstance(widget, QCheckBox):
                # NOTE: INI file doesn't perserve bool type, it becomes str when loaded.
                val = self.settings.value(key, value)
                if isinstance(val, str):
                    val = val.lower() == "true"
                widget.setChecked(val)
            elif isinstance(widget, QComboBox):
                widget.setCurrentText(self.settings.value(key, value))
            else:
                raise RuntimeError(f"Unknown widget type for load settings: {widget!r}")

    def save_settings(self) -> None:
        # save settings
        for key, value, widget_name in DEFAULT_SETTINGS:
            widget = getattr(self, widget_name)
            if isinstance(widget, QLineEdit):
                value = widget.text()
            elif isinstance(widget, QCheckBox):
                value = widget.isChecked()
            elif isinstance(widget, QComboBox):
                value = widget.currentText()
            else:
                raise RuntimeError(f"Unknown widget type for save settings: {widget!r}")

            self.settings.setValue(key, value)

    @classmethod
    def get_existing_directory(cls, that, prompt: str) -> str:
        path = QFileDialog.getExistingDirectory(that, prompt)
        # normalize path
        return os.path.normpath(path)

    def set_up(self) -> None:
        """Log Tab"""
        # populate logging level combo box
        self.comboBox_log_log_level.addItems(level for level in LoggingLevel)

        # set up logging level change handler
        self.comboBox_log_log_level.currentTextChanged.connect(
            self.on_logging_level_change
        )

        # set up logging handler
        log_handler = LogEmitterHandler(self._log_signal)
        log_handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
        logging.getLogger().addHandler(log_handler)
        self._log_handler = log_handler
        self._log_signal.connect(self.on_log_recieved)

        # set default logging level
        self.comboBox_log_log_level.setCurrentText(LoggingLevel.INFO)

        """Settings Tab"""
        # db path select
        self.toolButton_settings_db_path.clicked.connect(
            lambda: self.lineEdit_settings_db_path.setText(
                self.get_existing_directory(self, "Select DB Path")
            )
        )

        # game path validator
        self.lineEdit_settings_game_path.setValidator(
            WarCraftBaseValidator(self.lineEdit_settings_game_path)
        )
        self.lineEdit_settings_game_path.hasAcceptableInput()
        # game path select
        self.toolButton_settings_game_path.clicked.connect(
            lambda: self.lineEdit_settings_game_path.setText(
                self.get_existing_directory(self, "Select Warcraft Base Path")
            )
        )

        # repo validator
        self.lineEdit_settings_repo.setValidator(
            RepoValidator(self.lineEdit_settings_repo)
        )
        self.lineEdit_settings_repo.hasAcceptableInput()

        # gh proxy validator
        self.lineEdit_settings_gh_proxy.setValidator(
            GHProxyValidator(self.lineEdit_settings_gh_proxy)
        )
        self.lineEdit_settings_gh_proxy.hasAcceptableInput()

        """Exporter Tab"""
        # regions
        self.comboBox_exporter_region.addItems(region.name for region in RegionEnum)
        # game versions
        self.comboBox_exporter_game_version.addItems(
            version.name for version in GameVersionEnum
        )
        # on region / game version change, update realm list
        self.comboBox_exporter_region.currentTextChanged.connect(
            self.on_exporter_dropdown_change
        )
        self.comboBox_exporter_game_version.currentTextChanged.connect(
            self.on_exporter_dropdown_change
        )

        # on list item double click, toggle check
        self.listView_exporter_realms.doubleClicked.connect(
            self.on_exporter_list_dblclick
        )

        # on export button click, export
        self.pushButton_exporter_export.clicked.connect(self.on_exporter_export)

        """Updater Tab"""
        # client id validator
        self.lineEdit_updater_id.setValidator(
            RegexValidator(self.lineEdit_updater_id, r"^[a-f0-9]{32}$")
        )
        self.lineEdit_updater_id.hasAcceptableInput()

        # client secret validator
        self.lineEdit_updater_secret.setValidator(
            RegexValidator(self.lineEdit_updater_secret, r"^[a-zA-Z0-9]{32}$")
        )
        self.lineEdit_updater_secret.hasAcceptableInput()

        # populate combos
        self.populate_updater_combos()

        # on list item double click, toggle check
        self.listView_updater_combos.doubleClicked.connect(
            self.on_updater_list_dblclick
        )

        # on update button click, update
        self.pushButton_updater_update.clicked.connect(self.on_updater_update)

    def on_log_recieved(self, msg: str) -> None:
        # StackOverflow
        # https://stackoverflow.com/questions/72868417
        text_edit = self.plainTextEdit_log_log
        cursor = text_edit.textCursor()
        if cursor.atEnd():
            # store the current selection
            anchor = cursor.anchor()
            position = cursor.position()

            # change the text
            text_edit.appendPlainText(msg)

            # restore the selection
            cursor.setPosition(anchor)
            cursor.setPosition(position, QTextCursor.KeepAnchor)
            text_edit.setTextCursor(cursor)
        else:
            # just add the text
            text_edit.appendPlainText(msg)

    def on_logging_level_change(self) -> None:
        handler = self._log_handler
        level = self.comboBox_log_log_level.currentText()
        handler.setLevel(level)

    def on_exporter_list_dblclick(self, index) -> None:
        model = self.listView_exporter_realms.model()
        item = model.itemFromIndex(index)
        item.setCheckState(
            Qt.Checked if item.checkState() == Qt.Unchecked else Qt.Unchecked
        )

    def on_updater_list_dblclick(self, index) -> None:
        model = self.listView_updater_combos.model()
        item = model.itemFromIndex(index)
        item.setCheckState(
            Qt.Checked if item.checkState() == Qt.Unchecked else Qt.Unchecked
        )

    def on_exporter_dropdown_change(self) -> None:
        # lock widgets
        for widget in self._lock_on_export_dropdown:
            widget.setEnabled(False)

        try:
            data_path = self.get_db_path()
            namespace = self.get_namespace()

            if self.checkBox_exporter_remote.isChecked():
                mode = AuctionDB.MODE_REMOTE_R
                repo = self.get_repo()
                gh_api = self.get_gh_api()

            else:
                mode = AuctionDB.MODE_LOCAL_RW
                repo = None
                gh_api = None

            db = AuctionDB(
                data_path,
                config.MARKET_VALUE_RECORD_EXPIRES,
                use_compression=config.DEFAULT_DB_COMPRESS,
                mode=mode,
                fork_repo=repo,
                gh_api=gh_api,
            )

        except ConfigError as e:
            self.popup_error("Config Error", str(e))
            return

        def on_data(connected_realms: Dict[str, List[str]]):
            tups_realm_crid = []
            for crid, realms in connected_realms.items():
                for realm in realms:
                    tups_realm_crid.append((realm, crid))

            self.populate_exporter_realms(tups_realm_crid)

        def on_final(success: bool, msg: str) -> None:
            # unlock widgets
            for widget in self._lock_on_export_dropdown:
                widget.setEnabled(True)

            if not success:
                self.popup_error("Export Error", msg)

        @threaded(
            self,
            worker_cls=ExporterDropdownWorkerThread,
            _on_final=on_final,
            _on_data=on_data,
        )
        def task():
            # ioerror gets ignored by `load_meta`, returns empty dict.
            meta = db.load_meta(namespace)
            connected_reamls = meta.get("connected_realms", {})
            return connected_reamls

        task()

    def on_exporter_export(self) -> None:
        # lock widgets
        for widget in self._lock_on_export:
            widget.setEnabled(False)

        try:
            self.lineEdit_settings_game_path.validator().raise_invalid()
            warcraft_base = self.lineEdit_settings_game_path.text()
            warcraft_base = os.path.normpath(warcraft_base)
            warcraft_base = os.path.abspath(warcraft_base)

            game_version = GameVersionEnum[
                self.comboBox_exporter_game_version.currentText()
            ]
            db_path = self.get_db_path()
            realms = self.listView_exporter_realms.model().get_selected_realms()
            region = RegionEnum[self.comboBox_exporter_region.currentText()]
            repo = self.get_repo()
            remote_mode = self.checkBox_exporter_remote.isChecked()
            gh_proxy = self.get_gh_proxy()
            cache = self.get_cache()

        except ConfigError as e:
            self.popup_error("Config Error", str(e))
            return

        def on_final(success: bool, msg: str) -> None:
            # unlock widgets
            for widget in self._lock_on_export:
                widget.setEnabled(True)

            if not success:
                self.popup_error("Export Error", msg)

        @threaded(self, _on_final=on_final)
        def task(*args, **kwargs):
            exporter_main(
                db_path=db_path,
                repo=repo if remote_mode else None,
                gh_proxy=gh_proxy,
                game_version=game_version,
                warcraft_base=warcraft_base,
                export_region=region,
                export_realms=realms,
                cache=cache,
            )

        task()

    def on_updater_update(self) -> None:
        # lock widgets
        for widget in self._lock_on_update:
            widget.setEnabled(False)

        try:
            db_path = self.get_db_path()
            repo = self.get_repo()
            gh_proxy = self.get_gh_proxy()
            client_id = self.lineEdit_updater_id.text()
            client_secret = self.lineEdit_updater_secret.text()
            cache = self.get_cache()
            bn_api = BNAPI(
                client_id=client_id,
                client_secret=client_secret,
                cache=cache,
            )
            combos = self.listView_updater_combos.model().get_selected_combos()

        except ConfigError as e:
            self.popup_error("Config Error", str(e))
            return

        def on_task_done(success: bool, msg: str) -> None:
            # unlock widgets
            for widget in self._lock_on_update:
                widget.setEnabled(True)

            if not success:
                self.popup_error("Update Error", msg)

        @threaded(self, on_final=on_task_done)
        def task(*args, **kwargs):
            for region, game_version in combos:
                updater_main(
                    db_path=db_path,
                    repo=repo,
                    gh_proxy=gh_proxy,
                    game_version=game_version,
                    region=region,
                    cache=cache,
                    bn_api=bn_api,
                )

        task()

    def populate_exporter_realms(self, tups_realm_crid: List[Tuple[str, int]]) -> None:
        model = RealmsModel(tups_realm_crid)
        self.listView_exporter_realms.setModel(model)

    def populate_updater_combos(self) -> None:
        # make combinations (region, game_version)
        combos = []
        for region, game_version in itertools.product(RegionEnum, GameVersionEnum):
            combos.append((region, game_version))

        # populate combos
        model = UpdaterModel(combos)
        self.listView_updater_combos.setModel(model)

    def popup_error(self, type: str, message: str) -> None:
        QMessageBox.critical(self, type, message)

    def get_cache(self) -> Cache:
        return Cache(config.DEFAULT_CACHE_PATH)

    def get_gh_proxy(self) -> str:
        if self.checkBox_settings_gh_proxy.isChecked():
            self.lineEdit_settings_gh_proxy.validator().raise_invalid()
            gh_proxy = self.lineEdit_settings_gh_proxy.text()

        else:
            gh_proxy = None

        return gh_proxy

    def get_gh_api(self) -> GHAPI:
        gh_proxy = self.get_gh_proxy()
        cache = self.get_cache()
        return GHAPI(cache, gh_proxy=gh_proxy)

    def get_namespace(self) -> Namespace:
        # if we're in exporter tab (current tab name 'tab_exporter'):
        if self.tabWidget.currentWidget() == self.tab_exporter:
            region = RegionEnum[self.comboBox_exporter_region.currentText()]
            game_version = GameVersionEnum[
                self.comboBox_exporter_game_version.currentText()
            ]
            return Namespace(
                category=NameSpaceCategoriesEnum.DYNAMIC,
                game_version=game_version,
                region=region,
            )

        else:
            raise RuntimeError(
                f"Invalid selected tab {self.tabWidget.currentWidget()!r}"
                f" for function 'get_namespace'"
            )

    def get_db_path(self) -> str:
        data_path = self.lineEdit_settings_db_path.text()
        data_path = os.path.normpath(data_path)
        data_path = os.path.abspath(data_path)
        return data_path

    def get_repo(self) -> str:
        self.lineEdit_settings_repo.validator().raise_invalid()
        repo = self.lineEdit_settings_repo.text()
        return repo
