import pytest
from contacts_api.email_utils import send_email
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_send_email_success(mocker):
    mocker.patch("contacts_api.email_utils.logger.info", return_value=None)

    try:
        await send_email("Test Subject", "test@example.com", "<p>Test Body</p>")
    except Exception:
        pytest.fail("send_email raised an exception unexpectedly")


@pytest.mark.asyncio
async def test_send_email_failure(mocker):
    mocker.patch("contacts_api.email_utils.logger.info", side_effect=Exception("Simulated failure"))

    with pytest.raises(HTTPException, match="Failed to send email"):
        await send_email("Test Subject", "test@example.com", "<p>Test Body</p>")
