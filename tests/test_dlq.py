import pytest
from celery.exceptions import Retry
from pipeline.tasks import process_raw_file_task, app

def test_dlq_routing_on_max_retries(mocker):
    """
    Tests that a task failing 3 times is correctly routed 
    to the dead_letter queue instead of disappearing.
    """
    # 1. Mock file existence to pass the initial safety check
    mocker.patch("os.path.exists", return_value=True)
    
    # 2. Force the normalizer to crash to trigger the `except` block
    mocker.patch("pipeline.tasks.normalize", side_effect=Exception("Simulated Data Crash"))
    
    # 3. Spy on Celery's send_task function to intercept the DLQ hand-off
    mock_send_task = mocker.patch.object(app, "send_task")
    
    # 4. Mock the task's internal request context to pretend we are on attempt #3
    mocker.patch.object(process_raw_file_task.request, "retries", 3)
    
    # 5. Execute the task directly (synchronously)
    result = process_raw_file_task("data/raw_scrapes/broken_file.json", "test_source")
    
    # 6. Verify the task returned the correct failure string
    assert "FAILED: Sent to DLQ" in result
    
    # 7. Verify the message was specifically routed to the 'dead_letter' queue
    mock_send_task.assert_called_once_with(
        "pipeline.tasks.process_raw_file_task",
        args=["data/raw_scrapes/broken_file.json", "test_source"],
        queue="dead_letter"
    )

def test_task_retries_on_initial_failure(mocker):
    """
    Tests that a failure on attempt 1 or 2 triggers a standard retry 
    and DOES NOT go to the DLQ.
    """
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("pipeline.tasks.normalize", side_effect=Exception("Simulated Database Timeout"))
    mock_send_task = mocker.patch.object(app, "send_task")
    
    # NEW: Intercept Celery's retry mechanism so it plays nicely with Pytest
    mock_retry = mocker.patch.object(process_raw_file_task, "retry", side_effect=Retry)
    
    # Pretend we are only on attempt #1
    mocker.patch.object(process_raw_file_task.request, "retries", 1)
    
    with pytest.raises(Retry):
        process_raw_file_task("data/raw_scrapes/timeout_file.json", "test_source")
        
    # VERIFY: It triggered a retry, but DID NOT send anything to the DLQ
    mock_retry.assert_called_once()
    mock_send_task.assert_not_called()