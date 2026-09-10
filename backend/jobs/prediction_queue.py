import asyncio
import uuid
import logging
from typing import Tuple

from backend.persistence.database import SessionLocal
from backend.services.prediction_service import generate_predictions

logger = logging.getLogger(__name__)

# The in-memory asyncio queue
# Holds tuples of (case_id, timepoint)
_queue: asyncio.Queue | None = None

def _get_queue() -> asyncio.Queue:
    global _queue
    if _queue is None:
        _queue = asyncio.Queue()
    return _queue

def reset_queue() -> None:
    global _queue
    _queue = None

async def enqueue_prediction(case_id: uuid.UUID, timepoint: int) -> None:
    """
    Adds a prediction request to the background queue.
    Returns immediately so the API doesn't block.
    """
    q = _get_queue()
    await q.put((case_id, timepoint))
    logger.info(f"Enqueued prediction job for Case: {case_id} at Timepoint: {timepoint}")

async def process_queue() -> None:
    """
    Long-running background worker loop that pulls from the queue
    and executes the Prediction Service synchronously using a fresh DB session.
    """
    logger.info("Prediction Job Queue worker started.")
    q = _get_queue()
    while True:
        try:
            # Block until an item is available
            case_id, timepoint = await q.get()
        except asyncio.CancelledError:
            logger.info("Prediction Job Queue worker shutting down.")
            break
        except Exception as e:
            logger.error(f"Error getting job from queue: {str(e)}")
            await asyncio.sleep(1)
            continue
            
        try:
            logger.info(f"Processing prediction job for Case: {case_id} at Timepoint: {timepoint}")
            
            def _run_prediction():
                db = SessionLocal()
                try:
                    generate_predictions(db, case_id, timepoint)
                finally:
                    db.close()
            
            await asyncio.to_thread(_run_prediction)
            logger.info(f"Completed prediction job for Case: {case_id} at Timepoint: {timepoint}")

        except Exception as e:
            logger.error(f"Error processing prediction job: {str(e)}")
        finally:
            q.task_done()
