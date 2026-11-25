import asyncio
from src.db import init_db, close_client
from src.models import LoanApplication, Applicant

async def test_model_init():
    await init_db([LoanApplication])
    # Create in-memory model instance
    app = LoanApplication(current_state="submitted", applicant=Applicant(name="T", ssn_last4="0000", credit_score=700))
    assert app.current_state == "submitted"
    await close_client()

if __name__ == '__main__':
    asyncio.run(test_model_init())
