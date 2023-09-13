import os
from typing import Tuple, List, Set
from functools import wraps
from threading import Thread
import logging

from PyQt5.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QWidget,
    QMessageBox,
    QPlainTextEdit,
)
from PyQt5.QtGui import (
    QValidator,
    QStandardItemModel,
    QStandardItem,
)
from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
)

from ah import config
from ah.ui.main_view import Ui_MainWindow
from ah.tsm_exporter import TSMExporter
from ah.db import AuctionDB
from ah.cache import Cache
from ah.models.base import StrEnum_
from ah.models.blizzard import (
    RegionEnum,
    GameVersionEnum,
    Namespace,
    NameSpaceCategoriesEnum,
)
from ah.api import GHAPI
from ah.storage import TextFile


def threaded(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()

    return wrapper


class LoggingLevel(StrEnum_):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TextEditLoggerHandler(logging.Handler):
    def __init__(self, editor: QPlainTextEdit):
        super().__init__()
        self._editor = editor

    def emit(self, record):
        msg = self.format(record)
        self._editor.appendPlainText(msg)


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


class RealmsModel(QStandardItemModel):
    def __init__(self, data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._data = data

    @classmethod
    def from_data(cls, data: List[Tuple[str, int]]) -> None:
        model = cls(data)
        for realm, crid in data:
            item = QStandardItem(f"{realm}\t{crid}")
            item.setCheckable(True)
            item.setEditable(False)
            model.appendRow(item)

        return model

    def get_selected_realms(self) -> Set[str]:
        realms = set()
        for row in range(self.rowCount()):
            item = self.item(row)
            if item.checkState() == Qt.Checked:
                realm = self._data[row][0]
                realms.add(realm)

        return realms


class Window(QMainWindow, Ui_MainWindow):
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        # widgets that need to be disabled when updating or exporting
        lock_on_export_or_update = [
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
        self._lock_on_export.extend(lock_on_export_or_update)
        # widgets that need to be disabled when updating
        self._lock_on_update = [
            self.lineEdit_updater_id,
            self.lineEdit_updater_secret,
            self.checkBox_updater_remote,
            self.pushButton_updater_update,
            self.pushButton_exporter_export,
        ]
        self._lock_on_update.extend(lock_on_export_or_update)

        # tee log on a textedit
        self._log_handler = None
        self.set_up()

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
        log_handler = TextEditLoggerHandler(self.plainTextEdit_log_log)
        log_handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
        logging.getLogger().addHandler(log_handler)
        self._log_handler = log_handler

        # set default logging level
        self.comboBox_log_log_level.setCurrentText(LoggingLevel.INFO)

        """Settings Tab"""
        # db path select
        self.toolButton_settings_db_path.clicked.connect(
            lambda: self.lineEdit_settings_db_path.setText(
                self.get_existing_directory(self, "Select DB Path")
            )
        )

        # game path init
        text_warcraft_base = TSMExporter.find_warcraft_base() or ""
        self.lineEdit_settings_game_path.setText(text_warcraft_base)

        # game path select
        self.toolButton_settings_game_path.clicked.connect(
            lambda: self.lineEdit_settings_game_path.setText(
                self.get_existing_directory(self, "Select Warcraft Base Path")
            )
        )

        # game path validator
        self.lineEdit_settings_game_path.setValidator(
            self.WarCraftBaseValidator(self.lineEdit_settings_game_path)
        )
        self.lineEdit_settings_game_path.hasAcceptableInput()

        # repo validator
        self.lineEdit_settings_repo.setValidator(
            self.RepoValidator(self.lineEdit_settings_repo)
        )
        self.lineEdit_settings_repo.hasAcceptableInput()

        # gh proxy validator
        self.lineEdit_settings_gh_proxy.setValidator(
            self.GHProxyValidator(self.lineEdit_settings_gh_proxy)
        )
        self.lineEdit_settings_gh_proxy.hasAcceptableInput()

        """Exporter Tab"""
        # populate regions
        self.comboBox_exporter_region.addItems(region.name for region in RegionEnum)

        # populate game versions
        self.comboBox_exporter_game_version.addItems(
            version.name for version in GameVersionEnum
        )

        # on dropdown change (region, game version), update realm list
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

        """Dropdown select TW and Retail"""
        self.comboBox_exporter_region.setCurrentText(RegionEnum.TW.name)
        self.comboBox_exporter_game_version.setCurrentText(GameVersionEnum.RETAIL.name)

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

    def on_exporter_dropdown_change(self) -> None:
        try:
            db = self.get_auction_db()
        except ConfigError as e:
            self.popup_error("Config Error", str(e))
            return

        namespace = self.get_namespace()
        # ioerror gets ignored by `load_meta`, returns empty dict.
        meta = db.load_meta(namespace)
        connected_reamls = meta.get("connected_realms", {})
        tups_realm_crid = []
        for crid, realms in connected_reamls.items():
            for realm in realms:
                tups_realm_crid.append((realm, crid))

        self.populate_exporter_realms(tups_realm_crid)

    @threaded
    def on_exporter_export(self, *args, **kwargs) -> None:
        # lock widgets
        for widget in self._lock_on_export:
            widget.setEnabled(False)

        # export
        try:
            realms = self.listView_exporter_realms.model().get_selected_realms()
            namespace = self.get_namespace()
            exporter = self.get_exporter()
            exporter.export_region(namespace, realms)

        except ConfigError as e:
            self.popup_error("Config Error", str(e))
            return

        # unlock widgets
        for widget in self._lock_on_export:
            widget.setEnabled(True)

    def populate_exporter_realms(self, tups_realm_crid: List[Tuple[str, int]]) -> None:
        model = RealmsModel.from_data(tups_realm_crid)
        self.listView_exporter_realms.setModel(model)

    def popup_error(self, type: str, message: str) -> None:
        QMessageBox.critical(self, type, message)

    def get_cache(self) -> Cache:
        return Cache(config.DEFAULT_CACHE_PATH)

    def get_gh_api(self) -> GHAPI:
        if self.checkBox_settings_gh_proxy.isChecked():
            self.lineEdit_settings_gh_proxy.validator().raise_invalid()
            gh_proxy = self.lineEdit_settings_gh_proxy.text()

        else:
            gh_proxy = None

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

    def get_auction_db(self) -> AuctionDB:
        gh_api = self.get_gh_api()
        data_path = self.lineEdit_settings_db_path.text()
        data_path = os.path.normpath(data_path)
        data_path = os.path.abspath(data_path)

        # if we're in exporter tab (current tab name 'tab_exporter'):
        if self.tabWidget.currentWidget() == self.tab_exporter:
            if self.checkBox_exporter_remote.isChecked():
                mode = AuctionDB.MODE_REMOTE_R
            else:
                mode = AuctionDB.MODE_LOCAL_RW

        # if we're in updater tab (current tab name 'tab_updater'):
        elif self.tabWidget.currentWidget() == self.tab_updater:
            if self.checkBox_updater_remote.isChecked():
                mode = AuctionDB.MODE_LOCAL_REMOTE_RW
            else:
                mode = AuctionDB.MODE_LOCAL_RW

        else:
            raise RuntimeError(
                f"Invalid selected tab {self.tabWidget.currentWidget()!r}"
                f" for function 'get_auction_db'"
            )

        # need repo if we're in remote mode
        if mode in (AuctionDB.MODE_LOCAL_REMOTE_RW, AuctionDB.MODE_REMOTE_R):
            self.lineEdit_settings_repo.validator().raise_invalid()
            repo = self.lineEdit_settings_repo.text()
        else:
            repo = None

        return AuctionDB(
            data_path,
            config.MARKET_VALUE_RECORD_EXPIRES,
            use_compression=config.DEFAULT_DB_COMPRESS,
            mode=mode,
            fork_repo=repo,
            gh_api=gh_api,
        )

    def get_exporter(self) -> TSMExporter:
        self.lineEdit_settings_game_path.validator().raise_invalid()
        warcraft_base = self.lineEdit_settings_game_path.text()
        warcraft_base = os.path.normpath(warcraft_base)
        warcraft_base = os.path.abspath(warcraft_base)
        game_version = GameVersionEnum[
            self.comboBox_exporter_game_version.currentText()
        ]
        export_path = TSMExporter.get_tsm_appdata_path(warcraft_base, game_version)
        export_file = TextFile(export_path)
        auction_db = self.get_auction_db()
        return TSMExporter(auction_db, export_file)
