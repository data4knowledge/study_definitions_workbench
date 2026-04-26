import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.imports.import_processors import (
    ImportProcessorBase,
    ImportExcel,
    ImportM11,
    ImportCPT,
    ImportLegacy,
    ImportFhirPRISM2,
    ImportFhirPRISM3,
    ImportUSDM3,
    ImportUSDM4,
)


@pytest.fixture
def mock_usdm_db():
    """Mock the USDMDb class."""
    with patch("app.imports.import_processors.USDMDb") as mock:
        instance = mock.return_value
        instance.from_excel.return_value = None
        instance.from_json.return_value = None
        instance.to_json.return_value = '{"study": {"name": "test-study"}}'
        instance.wrapper.return_value = MagicMock()
        yield mock


@pytest.fixture
def mock_m11_protocol():
    """Mock the M11Protocol class."""
    with patch("app.imports.import_processors.USDM4M11") as mock:
        instance = mock.return_value
        mock_wrapper = MagicMock()
        mock_wrapper.to_json.return_value = '{"study": {"name": "test-study"}}'
        instance.from_docx.return_value = mock_wrapper
        instance.extra = {
            "title_page": {},
            "amendment": {},
            "miscellaneous": {},
        }
        instance.errors.to_dict.return_value = {"errors": []}
        instance.errors.dump.return_value = "No errors"
        yield mock


@pytest.fixture
def mock_from_fhir_v1():
    """Mock the M11 class for FHIR imports."""
    with patch("app.imports.import_processors.M11") as mock:
        instance = mock.return_value
        mock_wrapper = MagicMock()
        mock_wrapper.to_json.return_value = '{"study": {"name": "test-study"}}'
        instance.from_message = AsyncMock(return_value=mock_wrapper)
        instance.extra = {
            "title_page": {},
            "amendment": {},
            "miscellaneous": {},
        }
        instance.errors.to_dict.return_value = {"errors": []}
        instance.errors.dump.return_value = "No errors"
        yield mock


@pytest.fixture
def mock_usdm3():
    """Mock the USDM3 class."""
    with patch("app.imports.import_processors.USDM3") as mock:
        instance = mock.return_value
        instance.convert.return_value = MagicMock()
        instance.convert.return_value.to_json.return_value = (
            '{"study": {"name": "test-study"}}'
        )
        instance.validate.return_value = MagicMock()
        instance.validate.return_value.to_dict.return_value = {"errors": []}
        yield mock


@pytest.fixture
def mock_usdm4():
    """Mock the USDM4 class."""
    with patch("app.imports.import_processors.USDM4") as mock:
        instance = mock.return_value
        instance.convert.return_value = MagicMock()
        instance.convert.return_value.to_json.return_value = (
            '{"study": {"name": "test-study"}}'
        )
        instance.validate.return_value = MagicMock()
        instance.validate.return_value.to_dict.return_value = {"errors": []}
        yield mock


@pytest.fixture
def mock_object_path():
    """Mock the ObjectPath class."""
    with patch("app.imports.import_processors.ObjectPath") as mock:
        instance = mock.return_value
        instance.get.side_effect = lambda path: {
            "study/name": "test-study",
            "study/versions[0]/studyPhase/standardCode/decode": "Phase 1",
        }.get(path, "")
        yield mock


@pytest.fixture
def mock_data_files():
    """Mock the DataFiles class."""
    with patch("app.imports.import_processors.DataFiles") as mock:
        instance = mock.return_value
        instance.path.return_value = ("/path/to/file", "filename.ext", True)
        instance.save.return_value = ("/path/to/file", "filename.ext")
        instance.read.return_value = '{"study": {"name": "test-study"}}'
        yield mock


@pytest.fixture
def mock_logger():
    """Mock the application_logger."""
    with patch("app.imports.import_processors.application_logger") as mock:
        yield mock


class TestImportProcessorBase:
    """Tests for the ImportProcessorBase class."""

    def test_init(self):
        """Test initialization of ImportProcessorBase."""
        processor = ImportProcessorBase("TEST_TYPE", "test-uuid", "/path/to/file")
        assert processor.usdm is None
        assert processor.errors is None
        assert processor.type == "TEST_TYPE"
        assert processor.uuid == "test-uuid"
        assert processor.full_path == "/path/to/file"
        assert processor.extra == processor._blank_extra()

    @pytest.mark.asyncio
    async def test_process(self):
        """Test process method."""
        processor = ImportProcessorBase("TEST_TYPE", "test-uuid", "/path/to/file")
        result = await processor.process()
        assert not result

    def test_blank_extra(self):
        """Test _blank_extra method."""
        processor = ImportProcessorBase("TEST_TYPE", "test-uuid", "/path/to/file")
        extra = processor._blank_extra()
        assert "amendment" in extra
        assert "miscellaneous" in extra
        assert "title_page" in extra

    def test_study_parameters(self):
        """Test _study_parameters method."""
        # Setup
        processor = ImportProcessorBase("TEST_TYPE", "test-uuid", "/path/to/file")
        processor.usdm = '{"study": {"name": "test-study"}, "usdmVersion": "1.0"}'

        # Patch the _study_parameters method to return a known dictionary
        with patch.object(
            ImportProcessorBase,
            "_study_parameters",
            return_value={
                "name": "test-study-TEST_TYPE",
                "phase": "X, Y",
                "full_title": "Test Study Title",
                "sponsor_identifier": "TEST-123",
                "nct_identifier": "NCT12345678",
                "sponsor": "Test Sponsor",
            },
        ):
            # Execute
            result = processor._study_parameters()
            print(f"RESULT: {result}")

            # Assert
            assert result["name"] == "test-study-TEST_TYPE"
            assert result["phase"] == "X, Y"
            assert result["full_title"] == "Test Study Title"
            assert result["sponsor_identifier"] == "TEST-123"
            assert result["nct_identifier"] == "NCT12345678"
            assert result["sponsor"] == "Test Sponsor"

    def test_study_parameters_exception(self, mock_usdm_db, mock_logger):
        """Test _study_parameters method with exception."""
        # Setup
        processor = ImportProcessorBase("TEST_TYPE", "test-uuid", "/path/to/file")
        processor.usdm = '{"study": {"name": "test-study"}}'
        mock_usdm_db.return_value.from_json.side_effect = Exception("Test exception")

        # Execute
        result = processor._study_parameters()

        # Assert
        assert result is None
        mock_logger.exception.assert_called_once()

    def test_get_parameter(self, mock_object_path):
        """Test _get_parameter method."""
        # Setup
        processor = ImportProcessorBase("TEST_TYPE", "test-uuid", "/path/to/file")

        # Execute
        result = processor._get_parameter(mock_object_path.return_value, "study/name")

        # Assert
        assert result == "test-study"
        mock_object_path.return_value.get.assert_called_once_with("study/name")

    def test_get_parameter_not_found(self, mock_object_path):
        """Test _get_parameter method with not found path."""
        # Setup
        processor = ImportProcessorBase("TEST_TYPE", "test-uuid", "/path/to/file")
        mock_object_path.return_value.get.return_value = None

        # Execute
        result = processor._get_parameter(
            mock_object_path.return_value, "not/found/path"
        )

        # Assert
        assert result == ""
        mock_object_path.return_value.get.assert_called_once_with("not/found/path")


class TestImportExcel:
    """Tests for the ImportExcel class."""

    @pytest.mark.asyncio
    async def test_process(self, mock_usdm_db):
        """Test process method."""
        # Setup
        processor = ImportExcel("USDM_EXCEL", "test-uuid", "/path/to/file")
        processor.file_import = MagicMock()
        processor.session = MagicMock()

        # Execute
        result = await processor.process()

        # Assert
        assert result
        # USDMDb is called multiple times: once in process() and again in _study_parameters()
        assert mock_usdm_db.call_count >= 1
        mock_usdm_db.return_value.from_excel.assert_called_once_with("/path/to/file")
        mock_usdm_db.return_value.to_json.assert_called_once()
        assert processor.usdm == mock_usdm_db.return_value.to_json.return_value
        assert processor.errors == mock_usdm_db.return_value.from_excel.return_value


class TestImportM11:
    """Tests for the ImportM11 class."""

    @pytest.mark.asyncio
    async def test_process(self, mock_m11_protocol):
        """Test process method — happy path. Validation runs before
        USDM extraction, findings are projected and persisted via the
        ``m11_validation`` media type, and the USDM extraction proceeds
        independently."""
        # Setup
        processor = ImportM11("M11_DOCX", "test-uuid", "/path/to/file")
        sample_findings = [
            {
                "rule_id": "M11_001",
                "severity": "error",
                "section": "1",
                "element": "Full Title",
                "message": "Required element 'Full Title' is missing.",
                "rule_text": "",
                "path": "",
            }
        ]

        # Mock the _study_parameters method to avoid the error with version.phases()
        with (
            patch.object(
                processor,
                "_study_parameters",
                return_value={"name": "test-study-M11_DOCX"},
            ),
            patch("app.imports.import_processors.M11Validator") as mock_validator,
            patch(
                "app.imports.import_processors.project_m11_result",
                return_value=sample_findings,
            ) as mock_project,
            patch("app.imports.import_processors.DataFiles") as mock_data_files,
        ):
            mock_validator.return_value.validate.return_value = MagicMock()
            # Execute
            result = await processor.process()

        # Assert — import succeeded
        assert result
        mock_m11_protocol.assert_called_once()
        mock_m11_protocol.return_value.from_docx.assert_called_once()
        assert (
            processor.usdm
            == mock_m11_protocol.return_value.from_docx.return_value.to_json.return_value
        )
        assert processor.extra == processor._blank_extra()
        assert (
            processor.errors
            == mock_m11_protocol.return_value.errors.to_dict.return_value
        )

        # Assert — validation ran, was projected, and was persisted
        mock_validator.assert_called_once()
        call_args = mock_validator.call_args
        assert call_args.args[0] == "/path/to/file"
        mock_project.assert_called_once()
        mock_data_files.assert_called_once_with("test-uuid")
        save_call = mock_data_files.return_value.save.call_args
        assert save_call.args[0] == "m11_validation"
        import json as _json

        assert _json.loads(save_call.args[1]) == sample_findings
        assert processor.m11_validation == sample_findings

    @pytest.mark.asyncio
    async def test_process_validation_exception_does_not_stop_import(
        self, mock_m11_protocol, mock_logger
    ):
        """A crash in the M11 validation step must not abort the
        import — validator output is advisory, not a gate."""
        processor = ImportM11("M11_DOCX", "test-uuid", "/path/to/file")
        with (
            patch.object(processor, "_study_parameters", return_value={"name": "test"}),
            patch(
                "app.imports.import_processors.M11Validator",
                side_effect=RuntimeError("boom"),
            ),
            patch("app.imports.import_processors.DataFiles"),
        ):
            result = await processor.process()

        # Import still completes and USDM extraction still runs
        assert result
        mock_m11_protocol.return_value.from_docx.assert_called_once()
        # Findings attribute is present and empty; exception was logged
        assert processor.m11_validation == []
        mock_logger.exception.assert_called()


class TestImportCPT:
    """Tests for the ImportCPT class."""

    @pytest.mark.asyncio
    async def test_process(self):
        mock_wrapper = MagicMock()
        mock_wrapper.to_json.return_value = '{"study": {"name": "test-study"}}'
        with patch("app.imports.import_processors.USDM4CPT") as mock_cpt:
            instance = mock_cpt.return_value
            instance.from_docx.return_value = mock_wrapper
            instance.extra = {"title_page": {}, "amendment": {}, "miscellaneous": {}}
            instance.errors.to_dict.return_value = {"errors": []}
            instance.errors.dump.return_value = "No errors"
            processor = ImportCPT("CPT_DOCX", "test-uuid", "/path/to/file")
            with patch.object(
                processor, "_study_parameters", return_value={"name": "test"}
            ):
                result = await processor.process()
        assert result
        assert processor.usdm == '{"study": {"name": "test-study"}}'
        assert processor.extra == instance.extra

    @pytest.mark.asyncio
    async def test_process_no_wrapper(self):
        with patch("app.imports.import_processors.USDM4CPT") as mock_cpt:
            instance = mock_cpt.return_value
            instance.from_docx.return_value = None
            instance.errors.to_dict.return_value = {"errors": []}
            instance.errors.dump.return_value = "No errors"
            processor = ImportCPT("CPT_DOCX", "test-uuid", "/path/to/file")
            result = await processor.process()
        assert result
        assert processor.usdm is None


class TestImportLegacy:
    """Tests for the ImportLegacy class."""

    @pytest.mark.asyncio
    async def test_process(self):
        processor = ImportLegacy("LEGACY_PDF", "test-uuid", "/path/to/file")
        result = await processor.process()
        assert result


class TestImportFhirPRISM2:
    """Tests for the ImportFhirPRISM2 class."""

    @pytest.mark.asyncio
    async def test_process_success(self, mock_from_fhir_v1):
        processor = ImportFhirPRISM2("FHIR_PRISM2_JSON", "test-uuid", "/path/to/file")
        with patch.object(
            processor, "_study_parameters", return_value={"name": "test"}
        ):
            result = await processor.process()
        assert result
        assert processor.success
        assert (
            processor.usdm
            == mock_from_fhir_v1.return_value.from_message.return_value.to_json.return_value
        )

    @pytest.mark.asyncio
    async def test_process_failure(self):
        with patch("app.imports.import_processors.M11") as mock_m11:
            instance = mock_m11.return_value
            instance.from_message = AsyncMock(return_value=None)
            instance.errors.to_dict.return_value = {"errors": ["fail"]}
            instance.errors.dump.return_value = "Error"
            processor = ImportFhirPRISM2(
                "FHIR_PRISM2_JSON", "test-uuid", "/path/to/file"
            )
            result = await processor.process()
        assert not result
        assert not processor.success
        assert "PRISM2" in processor.fatal_error


class TestImportFhirPRISM3:
    """Tests for the ImportFhirPRISM3 class."""

    @pytest.mark.asyncio
    async def test_process_success(self):
        mock_wrapper = MagicMock()
        mock_wrapper.to_json.return_value = '{"study": {"name": "test-study"}}'
        with patch("app.imports.import_processors.M11") as mock_m11:
            instance = mock_m11.return_value
            instance.from_message = AsyncMock(return_value=mock_wrapper)
            instance.errors.to_dict.return_value = {"errors": []}
            instance.errors.dump.return_value = "No errors"
            processor = ImportFhirPRISM3(
                "FHIR_PRISM3_JSON", "test-uuid", "/path/to/file"
            )
            with patch.object(
                processor, "_study_parameters", return_value={"name": "test"}
            ):
                result = await processor.process()
        assert result
        assert processor.success

    @pytest.mark.asyncio
    async def test_process_failure(self):
        with patch("app.imports.import_processors.M11") as mock_m11:
            instance = mock_m11.return_value
            instance.from_message = AsyncMock(return_value=None)
            instance.errors.to_dict.return_value = {"errors": ["fail"]}
            instance.errors.dump.return_value = "Error"
            processor = ImportFhirPRISM3(
                "FHIR_PRISM3_JSON", "test-uuid", "/path/to/file"
            )
            result = await processor.process()
        assert not result
        assert not processor.success
        assert "PRISM3" in processor.fatal_error


# class TestImportFhirPRISM2:
#     """Tests for the ImportFhirPRISM2 class."""

#     @pytest.mark.asyncio
#     async def test_process(self, mock_from_fhir_v1):
#         """Test process method."""
#         # Setup
#         processor = ImportFhirPRISM2("FHIR_PRISM2_JSON", "test-uuid", "/path/to/file")

#         # Execute
#         result = await processor.process()

#         # Assert
#         assert result
#         mock_from_fhir_v1.assert_called_once_with("test-uuid")
#         mock_from_fhir_v1.return_value.to_usdm.assert_called_once()
#         # The to_usdm method is mocked to return a string directly, not a coroutine
#         assert processor.usdm == mock_from_fhir_v1.return_value.to_usdm.return_value


class TestImportUSDM3:
    """Tests for the ImportUSDM3 class.

    The import contract for v3 is: always run v3 validation, always
    convert to v4, always run v4 validation, always extract parameters.
    Validation findings are captured in ``processor.errors`` (sourced
    from the v4 results — that's the file we keep) but are advisory:
    they do not fail the import. The only blocking failures are a
    conversion crash and a missing study-parameter dict.
    """

    @pytest.mark.asyncio
    async def test_process(self, mock_data_files, mock_usdm3, mock_usdm4):
        """Happy path — both validations clean, conversion succeeds."""
        # Setup
        processor = ImportUSDM3("USDM3_JSON", "test-uuid", "/path/to/file")

        # Execute
        result = await processor.process()

        # Assert
        assert result
        mock_data_files.assert_called_once_with("test-uuid")
        mock_data_files.return_value.path.assert_called_with("usdm")
        mock_usdm3.assert_called_once()
        mock_usdm3.return_value.validate.assert_called_once_with("/path/to/file")
        mock_usdm4.call_count == 2
        mock_usdm4.return_value.convert.assert_called_once_with("/path/to/file")
        mock_usdm4.return_value.validate.assert_called_once_with("/path/to/file")
        # Use assert_any_call instead of assert_called_with to check that the method was called with these parameters
        # regardless of the order
        mock_data_files.return_value.save.assert_any_call("usdm", processor.usdm)
        assert (
            processor.usdm
            == mock_usdm3.return_value.convert.return_value.to_json.return_value
        )
        # Errors come from the v4 validation pass — that's the file
        # that's stored, so its rule output is what users will be
        # working from.
        assert (
            processor.errors
            == mock_usdm4.return_value.validate.return_value.to_dict.return_value
        )
        assert processor.success
        assert processor.fatal_error is None

    @pytest.mark.asyncio
    async def test_process_v3_validation_failure_does_not_block(
        self, mock_data_files, mock_usdm3, mock_usdm4
    ):
        """v3 rule failures used to block; they're now advisory. The
        import proceeds through conversion and v4 validation regardless
        of what the v3 engine reports."""
        instance = mock_usdm3.return_value
        instance.validate.return_value.passed_or_not_implemented = lambda: False
        instance.validate.return_value.to_dict.return_value = {
            "errors": [{"status": "Failure"}]
        }

        processor = ImportUSDM3("USDM3_JSON", "test-uuid", "/path/to/file")
        result = await processor.process()

        assert result
        assert processor.success
        assert processor.fatal_error is None
        # Conversion and v4 validation must still run on a v3 failure —
        # that's the whole point of the gate being lifted.
        mock_usdm4.return_value.convert.assert_called_once_with("/path/to/file")
        mock_usdm4.return_value.validate.assert_called_once_with("/path/to/file")

    @pytest.mark.asyncio
    async def test_process_v4_validation_failure_does_not_block(
        self, mock_data_files, mock_usdm3, mock_usdm4
    ):
        """Same contract as v3: v4 rule failures are persisted but do
        not fail the import."""
        instance = mock_usdm4.return_value
        instance.validate.return_value.passed_or_not_implemented = lambda: False
        instance.validate.return_value.to_dict.return_value = {
            "errors": [{"status": "Failure"}]
        }

        processor = ImportUSDM3("USDM3_JSON", "test-uuid", "/path/to/file")
        result = await processor.process()

        assert result
        assert processor.success
        assert processor.fatal_error is None
        assert processor.errors == {"errors": [{"status": "Failure"}]}

    @pytest.mark.asyncio
    async def test_process_conversion_crash_blocks(
        self, mock_data_files, mock_usdm3, mock_usdm4
    ):
        """A v3→v4 conversion crash is a structural failure — without a
        v4 file we have nothing to anchor a study record to, so the
        import does fail. The diagnostic falls back to the v3 rule
        output so the user has something to act on."""
        mock_usdm3.return_value.validate.return_value.to_dict.return_value = {
            "errors": [{"status": "v3 issue"}]
        }
        mock_usdm4.return_value.convert.side_effect = ValueError("bad input")

        processor = ImportUSDM3("USDM3_JSON", "test-uuid", "/path/to/file")
        result = await processor.process()

        assert not result
        assert not processor.success
        assert processor.fatal_error is not None
        assert "conversion failed" in processor.fatal_error
        # v3 findings are surfaced when conversion blows up.
        assert processor.errors == {"errors": [{"status": "v3 issue"}]}


class TestImportUSDM:
    """Tests for the ImportUSDM class.

    The v4 import contract: validate, persist findings to
    ``processor.errors``, extract parameters (with a fallback to
    placeholder values when extraction raises), succeed. The processor
    never sets ``success = False`` — validation findings are advisory
    and even a structurally non-conforming file lands so the user can
    review it via the study view + Errors File download.
    """

    @pytest.mark.asyncio
    async def test_process(self, mock_data_files, mock_usdm4):
        """Happy path."""
        # Setup
        processor = ImportUSDM4("USDM4_JSON", "test-uuid", "/path/to/file")

        # Execute
        result = await processor.process()

        # Assert
        assert result
        mock_data_files.assert_called_once_with("test-uuid")
        mock_data_files.return_value.path.assert_called_with("usdm")
        mock_data_files.return_value.read.assert_called_once_with("usdm")
        mock_usdm4.call_count == 2
        mock_usdm4.return_value.validate.assert_called_once_with("/path/to/file")
        assert processor.usdm == mock_data_files.return_value.read.return_value
        assert (
            processor.errors
            == mock_usdm4.return_value.validate.return_value.to_dict.return_value
        )

    @pytest.mark.asyncio
    async def test_process_validation_failure_does_not_block(
        self, mock_data_files, mock_usdm4
    ):
        """Validation findings are persisted but don't fail the
        import. Users review the imported study and remediate from
        there — the gate lifted to support exactly this workflow."""
        instance = mock_usdm4.return_value
        instance.validate.return_value.passed_or_not_implemented = lambda: False
        instance.validate.return_value.to_dict.return_value = {
            "errors": [{"status": "Failure"}]
        }

        processor = ImportUSDM4("USDM4_JSON", "test-uuid", "/path/to/file")
        result = await processor.process()

        assert result
        assert processor.success
        assert processor.fatal_error is None
        # Findings are still persisted on the processor so the import
        # manager can write them to the errors file.
        assert processor.errors == {"errors": [{"status": "Failure"}]}

    @pytest.mark.asyncio
    async def test_process_missing_parameters_falls_back(
        self, mock_data_files, mock_usdm4
    ):
        """When ``_study_parameters`` returns ``None`` (the wrapper /
        accessors raised on a structurally non-conforming file), the
        processor falls back to a placeholder parameters dict so the
        import still lands. ``Study.study_and_version`` synthesises a
        name from the file_import when the placeholder leaves it
        empty, so downstream consumers cope."""
        processor = ImportUSDM4("USDM4_JSON", "test-uuid", "/path/to/file")

        with patch.object(ImportUSDM4, "_study_parameters", return_value=None):
            result = await processor.process()

        assert result
        assert processor.success
        assert processor.fatal_error is None
        # Fallback parameters are a dict with the canonical keys
        # populated to empty strings — that's the contract
        # ``Study.study_and_version`` reads against.
        assert processor.study_parameters == {
            "name": "",
            "phase": "",
            "full_title": "",
            "sponsor_identifier": "",
            "nct_identifier": "",
            "sponsor": "",
        }
