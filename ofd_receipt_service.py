#! /usr/bin/env python3

# coding utf-8
# ᛝ

import json
from datetime import datetime
from pathlib import Path
import signal
import sys
from threading import Event

import common.constants as constants
from database import DatabaseSession, Transaction, ReceiptStatus
from logger.logger import setup_logger


class Service:
    """
        Orchestrates receipt ingestion and processing.
    
        URL files are used only as an input source. Every URL is first persisted
        into receipt_identity and only then processed.
    
        Database transactions must remain short:
            - no HTTP requests inside transactions;
            - no retry delays inside transactions;
            - no parsing inside transactions.
    """
    
    def __init__(
            self, 
            database_session,
            url_lists_path,
            parser, 
            fetcher, 
            logger,
            config_path,
            shutdown_event: Event | None = None
    ):
        self.__database = database_session
        self.__parser = parser
        self.__fetcher = fetcher
        self.logger = logger
        self.__config_path = Path(config_path)
        self.__url_lists_path = Path(url_lists_path)
        self.__shutdown_event = (
            shutdown_event
            if shutdown_event is not None
            else Event()
        )
        self.__last_file = None
        self.__last_uri = None

    def request_shutdown(self) -> None:
        self.__shutdown_event.set()
    
    # ----------------------------------------------------------------------------------------
    # State & Config
    #-----------------------------------------------------------------------------------------
    def __load_config(self) -> bool:
        if not self.__config_path.exists():
            self.logger.info(
                "Config file does not exist:  %s", 
                self.__config_path
            )
            return False
        
        try: # @todo make config as other class
            with open(
                self.__config_path,
                "r",
                encoding="utf-8",
            ) as config_file:
                config = json.load(config_file)
        except(OSError, json.JSONDecodeError):
            self.logger.exception(
                "Failed to load state file: %s",
                self.__config_path
            )
            raise
        
        if not isinstance(config, dict):
            raise ValueError(
                f"Invalid state file format: {self.__config_path}"
            )
        
        self.__last_file = config.get("last_file")
        self.__last_uri = config.get("last_url")
        
        self.logger.info(
            "State loaded: last_file:%s, last_url=%s",
            self.__last_file,
            self.__last_uri
        )
        return True
    
    def __save_state(self) -> None:
        self.__config_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )
        
        state = {
            "last_file": self.__last_file,
            "last_url": self.__last_uri
        }
        
        config_file_path = self.__config_path.with_suffix(".tmp")
        
        try:
            with config_file_path.open(
                "w",
                encoding="utf-8",
            ) as config_file:
                json.dump(
                    state,
                    config_file,
                    ensure_ascii=False,
                    indent=4,
                )
                
            config_file_path.replace(self.__config_path)
        except OSError:
            self.logger.exception(
                "Failed to save state file: %s",
                self.__config_path
            )
    
    def __update_state(self, processed_filename: str, uri: str) -> None:
        self.__last_file = processed_filename
        self.__last_uri = uri
        self.__save_state()
    
    # ----------------------------------------------------------------------------------------
    # Input \ Output
    # ----------------------------------------------------------------------------------------
    def __get_receipt_files(self) -> list[Path]:
        if not self.__url_lists_path.exists():
            self.logger.warning(
                "URI directory not exist: %s",
                self.__url_lists_path
            )
            return []
        
        files = sorted(
            path
            for path in self.__url_lists_path.iterdir()
            if path.is_file()
        )

        valid_files = []
        for file_path in files:
            file_date = file_path.stem[:8]
            try:
                if len(file_date) != 8:
                    raise ValueError("file name must start with YYYYMMDD")
                if len(file_path.stem) > 8 and file_path.stem[8] not in "_-":
                    raise ValueError("file date must be followed by '_' or '-'")
                datetime.strptime(file_date, constants.URI_FILE_DATE_FORMAT)
            except ValueError:
                self.logger.warning(
                    "Skipping URL file with invalid date prefix (expected YYYYMMDD): %s",
                    file_path.name
                )
                continue
            valid_files.append(file_path)

        files = valid_files
        
        self.logger.info(
            "Found %d URL files",
            len(files)
        )
        
        return files
    
    # ----------------------------------------------------------------------------------------
    # URL ingestion
    # ----------------------------------------------------------------------------------------
    def __store_url(self, url: str):
        """
        Parse URL and persist its identity

        This method perform only DB work. The Transaction is intentionally
        short and contains no network operations.
        """

        identity = self.__fetcher.parse_url(url)

        with Transaction(self.__database) as t:
            if t.receipt_identity.exist(
                identity.fiscal_number,
                identity.fiscal_sign,
            ):
                self.logger.debug(
                    "Recept identity already exist: "
                    "fiscal_number: %s, fiscal_sign: %s",
                    identity.fiscal_number,
                    identity.fiscal_sign
                )
                return

            t.receipt_identity.create(identity)

        self.logger.info(
            "Receipt identity added: fiscal_number: %s, fiscal_sign: %s",
            identity.fiscal_number,
            identity.fiscal_sign
        )
        return identity

    def __ingest_file(self, file_path: Path) -> None:
        """
        Read URLs by batches and persist each batch into receipt_identity.
        
        The checkpoint is updated after each batch has been persisted and processed.
        """
        
        self.logger.info(
            "Start ingesting file: %s",
            file_path,
        )
        
        resume = (
            self.__last_file == file_path.name and
            self.__last_uri is not None
        )
        checkpoint_resume = resume
        
        processed = 0
        url_batch = []

        def process_batch(batch: list[str]) -> bool:
            last_completed_url = None
            for url in batch:
                if self.__shutdown_event.is_set():
                    break
                try:
                    identity = self.__store_url(url)
                except Exception:
                    self.logger.exception(
                        "Failed to register URL: %s",
                        url
                    )
                    raise

                if identity is not None:
                    self.__process_identity(identity, None)
                last_completed_url = url

            queues_processed = True
            if not self.__shutdown_event.is_set():
                queues_processed = self.__process_status(ReceiptStatus.FETCHED)
                if queues_processed:
                    queues_processed = self.__process_status(ReceiptStatus.PENDING)

            if last_completed_url is not None:
                self.__update_state(file_path.name, last_completed_url)
            return (
                last_completed_url == batch[-1] and
                queues_processed and
                not self.__shutdown_event.is_set()
            )
        
        try:
            if resume:
                with file_path.open(
                    "r",
                    encoding="utf-8",
                ) as uri_file:
                    checkpoint_found = False
                    for raw_uri in uri_file:
                        if self.__shutdown_event.is_set():
                            return
                        if raw_uri.strip() == self.__last_uri:
                            checkpoint_found = True
                            break
                if not checkpoint_found:
                    self.logger.warning(
                        "Saved URL checkpoint was not found in file; "
                        "skipping the file: %s",
                        file_path
                    )
                    return

            with file_path.open(
                "r",
                encoding="utf-8",
            ) as uri_file:
                for raw_uri in uri_file:
                    if self.__shutdown_event.is_set():
                        break

                    url = raw_uri.strip()
                    
                    if not url:
                        continue
                    
                    if resume:
                        if url == self.__last_uri:
                            resume = False
                        
                        continue
                    url_batch.append(url)
                    if len(url_batch) >= constants.URL_BATCH_SIZE:
                        if not process_batch(url_batch):
                            return
                        processed += len(url_batch)
                        url_batch = []

                if url_batch:
                    if not process_batch(url_batch):
                        processed += len(url_batch)
                        return
                    processed += len(url_batch)
                elif processed == 0 and not checkpoint_resume:
                    self.__update_state(file_path.name, None)
        except OSError:
            self.logger.exception(
                "Failed to read URL file: %s",
                file_path,
            )
            raise

        self.logger.info(
            "Finished ingesting file: %s; processed: %s",
            file_path,
            processed
        )

    def __process_identity(self, identity, receipt_html: str | None) -> None:
        try:
            if receipt_html is None:
                receipt_html = self.__fetcher.get_receipt(identity.url)
                with Transaction(self.__database) as t:
                    t.receipt_identity.update_receipt_html(
                        identity.fiscal_number,
                        identity.fiscal_sign,
                        receipt_html
                    )
                    t.receipt_identity.update_status(
                        identity.fiscal_number,
                        identity.fiscal_sign,
                        ReceiptStatus.FETCHED
                    )

            receipt = self.__parser.parse(receipt_html, identity)

            with Transaction(self.__database) as t:
                seller_id, cash_register_id = t.seller.get_or_create(
                    receipt.store,
                    receipt.cash_register
                )
                t.receipt.create(
                    receipt,
                    {
                        "receipt_identity_id": t.receipt_identity.id(
                            identity.fiscal_number,
                            identity.fiscal_sign
                        ),
                        "seller_id": seller_id,
                        "cash_register_id": cash_register_id
                    }
                )
                t.receipt_identity.update_status(
                    identity.fiscal_number,
                    identity.fiscal_sign,
                    ReceiptStatus.PARSED
                )
                identity_duration = t.receipt_identity.created_updated_difference(
                    identity.fiscal_number,
                    identity.fiscal_sign
                )

            self.logger.info(
                "Receipt parsed: fiscal_number=%s fiscal_sign=%s; "
                "created-to-updated: %.3f seconds",
                identity.fiscal_number,
                identity.fiscal_sign,
                identity_duration.total_seconds() if identity_duration else 0
            )
        except Exception:
            self.logger.exception(
                "Failed to process receipt: fiscal_number=%s fiscal_sign=%s",
                identity.fiscal_number,
                identity.fiscal_sign
            )
            with Transaction(self.__database) as t:
                t.receipt_identity.update_status(
                    identity.fiscal_number,
                    identity.fiscal_sign,
                    ReceiptStatus.ERROR
                )

    def __process_status(self, status: ReceiptStatus) -> bool:
        last_id = 0

        while True:
            if self.__shutdown_event.is_set():
                return False

            with Transaction(self.__database) as t:
                identities = t.receipt_identity.get_by_status(
                    status,
                    constants.IDENTITY_BATCH_SIZE,
                    last_id
                )

            if not identities:
                return True

            for identity_id, identity, receipt_html in identities:
                if self.__shutdown_event.is_set():
                    return False
                last_id = identity_id
                self.__process_identity(identity, receipt_html)

            self.logger.info(
                "Processed %d identities with status %s",
                len(identities),
                status.name
            )

    def __get_status_ids(self, status: ReceiptStatus) -> list[int]:
        identity_ids = []
        last_id = 0

        while True:
            if self.__shutdown_event.is_set():
                return identity_ids

            with Transaction(self.__database) as t:
                batch_ids = t.receipt_identity.get_ids_by_status(
                    status,
                    constants.IDENTITY_BATCH_SIZE,
                    last_id
                )

            if not batch_ids:
                return identity_ids

            identity_ids.extend(batch_ids)
            last_id = batch_ids[-1]

    def __process_status_ids(
            self,
            identity_ids: list[int],
            status: ReceiptStatus
    ) -> bool:
        for batch_start in range(0, len(identity_ids), constants.IDENTITY_BATCH_SIZE):
            if self.__shutdown_event.is_set():
                return False

            batch_ids = identity_ids[
                batch_start:batch_start + constants.IDENTITY_BATCH_SIZE
            ]
            with Transaction(self.__database) as t:
                identities = t.receipt_identity.get_by_ids(batch_ids, status)

            for identity_id, identity, receipt_html in identities:
                if self.__shutdown_event.is_set():
                    return False
                self.__process_identity(identity, receipt_html)

        return True

    def run(self) -> None:
        """
        Database session lifecycle is managed by the caller.
        """
        self.logger.info("Service started")
        
        try:
            self.__load_config()
            if self.__shutdown_event.is_set():
                return

            error_ids = self.__get_status_ids(ReceiptStatus.ERROR)
            files = self.__get_receipt_files()

            if self.__last_file:
                files = [
                    file_path
                    for file_path in files
                    if file_path.name >= self.__last_file
                ]
            
            for file_path in files:
                if self.__shutdown_event.is_set():
                    break

                self.logger.info(
                    "Current URL file: %s",
                    file_path
                )

                try:
                    self.__ingest_file(file_path)
                except Exception:
                    self.logger.exception(
                        "Failed to ingest URL file; stopping file ingestion: %s",
                        file_path
                    )
                    break

                if self.__shutdown_event.is_set():
                    break

            if not self.__shutdown_event.is_set():
                self.__process_status(ReceiptStatus.FETCHED)
                self.__process_status(ReceiptStatus.PENDING)

            for attempt in range(constants.ERROR_RETRY_LIMIT):
                if self.__shutdown_event.is_set():
                    break
                self.logger.info(
                    "Retrying ERROR queue: attempt %d of %d",
                    attempt + 1,
                    constants.ERROR_RETRY_LIMIT
                )
                if not self.__process_status_ids(error_ids, ReceiptStatus.ERROR):
                    break

            if self.__shutdown_event.is_set():
                self.logger.info("Service stopped after graceful shutdown request")
                return

            with Transaction(self.__database) as t:
                error_count = t.receipt_identity.count_by_status(ReceiptStatus.ERROR)

            if error_count:
                self.logger.warning(
                    "%d receipt identities remain in ERROR after retry",
                    error_count
                )
            else:
                self.logger.info("No receipt identities remain in ERROR")
        except Exception:
            self.logger.exception("Service run failed; stopping this run")
        finally:
            self.logger.info("OFD receipt service stopped")

    #def write_receipt_as_json(self, receipt):
    #    with open('resource/out/expected_{}.json'.format(receipt.receipt_meta.fiscal_number), mode='w', encoding='utf-8') as f:
    #        f.write(json.dumps(asdict(receipt), ensure_ascii=False, indent=4, default=str))


def main() -> int:
    from network import OFDFetcher
    from parsing import OFDSoliqParser

    logger = setup_logger(
        "ofd_service",
        Path(constants.DEFAULT_LOGS_PATH) / "ofd_service.log"
    )
    database = DatabaseSession(
        Path(constants.DEFAULT_DATABASE_PATH),
        Path(constants.DEFAULT_DATABASE_SCHEMA_PATH),
        logger
    )
    shutdown_event = Event()

    def request_shutdown(signum, frame):
        logger.info("Shutdown requested: signal=%s", signum)
        shutdown_event.set()

    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)

    try:
        database.open()
        service = Service(
            database_session = database,
            url_lists_path = constants.DEFAULT_URI_LISTS_PATH,
            parser = OFDSoliqParser(logger),
            fetcher = OFDFetcher(logger),
            logger = logger,
            config_path = constants.DEFAULT_CONFIG_PATH,
            shutdown_event = shutdown_event
        )
        service.run()
    except KeyboardInterrupt:
        logger.info("Service interrupted; shutting down")
        shutdown_event.set()
    except Exception as error:
        logger.exception(
            "Service terminated with error: %s",
            error
        )
        return 1
    finally:
        try:
            database.close()
        except Exception:
            logger.exception("Failed to close database session")

    return 0


if __name__ == '__main__':
    sys.exit(main())
