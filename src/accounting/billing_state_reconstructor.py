import logging

from sqlalchemy.orm import Session

from src.accounting.billing_state_machine import BillingStateMachine
from src.accounting.event_store import EventStore
from src.models import User

logger = logging.getLogger(__name__)


class BillingStateReconstructor:
    @staticmethod
    def reconstruct_billing_fsm_from_history(
        db: Session, user: User
    ) -> BillingStateMachine:
        """
        Reconstructs the BillingAccount FSM by replaying all historical transitions
        and applying ledger entries chronologically.
        This is the source of truth for the user's current billing state.

        Args:
            db: The database session
            user_id: The UUID of the user whose billing state to reconstruct

        Returns:
            BillingAccount: FSM instance with state reconstructed from history

        Raises:
            ValueError: If transition history is invalid or corrupted
        """
        event_store = EventStore(db)
        events = event_store.get_events_for_user(user.id)
        fsm = BillingStateMachine(user_id=user.id)
        fsm.apply_events(events)
        return fsm
