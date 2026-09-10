import asyncio
import uuid
import pytest
from unittest.mock import patch, MagicMock

from backend.jobs.prediction_queue import enqueue_prediction, process_queue, _get_queue, reset_queue

@pytest.mark.asyncio
async def test_enqueue_prediction():
    reset_queue()
    q = _get_queue()
        
    case_id = uuid.uuid4()
    timepoint = 1
    
    await enqueue_prediction(case_id, timepoint)
    
    assert q.qsize() == 1
    enqueued_case, enqueued_tp = q.get_nowait()
    assert enqueued_case == case_id
    assert enqueued_tp == timepoint

@pytest.mark.asyncio
async def test_process_queue_runs_prediction():
    reset_queue()
    q = _get_queue()

    case_id = uuid.uuid4()
    timepoint = 1
    
    # Enqueue a job
    await enqueue_prediction(case_id, timepoint)
    
    # Mock generate_predictions
    with patch('backend.jobs.prediction_queue.generate_predictions') as mock_gen_pred:
        # Start worker
        worker = asyncio.create_task(process_queue())
        
        # Wait a tiny bit for the worker to process the item
        await asyncio.sleep(0.1)
        
        # Cancel worker
        worker.cancel()
        try:
            await worker
        except asyncio.CancelledError:
            pass
            
        # Verify it processed the item
        mock_gen_pred.assert_called_once()
        args, kwargs = mock_gen_pred.call_args
        # First arg is DB session, second is case_id, third is timepoint
        assert args[1] == case_id
        assert args[2] == timepoint
        
        assert q.empty()
