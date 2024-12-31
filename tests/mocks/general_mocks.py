def mock_called(mock, count=1):
  return mock.call_count == count

def mock_parameters_correct(mock, params):
  result = mock.assert_has_calls(params)
  return result

def error_logged(caplog, text):
  correct_level = caplog.records[-1].levelname == "ERROR"
  return text in caplog.records[-1].message and correct_level
