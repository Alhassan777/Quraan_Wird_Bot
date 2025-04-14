import pytest
import os
import pytz
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

# Import functions from bot module
from bot import (
    handle_checkmark,
    get_user_datetime,
    is_admin,
    DEFAULT_TIMEZONE,
    user_data,
    group_data
)

# Reset data before each test
@pytest.fixture
def reset_data():
    user_data.clear()
    group_data.clear()
    yield
    user_data.clear()
    group_data.clear()

# Mock Update object
@pytest.fixture
def mock_update():
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_user.first_name = "Test"
    update.effective_user.last_name = "User"
    update.effective_chat.id = 456
    update.effective_chat.type = "private"
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    return update

# Mock Context object
@pytest.fixture
def mock_context():
    context = MagicMock()
    context.args = []
    return context

# Test timezone default
@pytest.mark.asyncio
async def test_default_timezone(reset_data, mock_update):
    user_id = mock_update.effective_user.id
    datetime_obj = await get_user_datetime(user_id)
    assert datetime_obj.tzinfo.zone == DEFAULT_TIMEZONE

# Test user in private chat is admin
@pytest.mark.asyncio
async def test_is_admin_private_chat(reset_data, mock_update):
    mock_update.effective_chat.type = "private"
    result = await is_admin(mock_update)
    assert result is True

# Test checkmark handling with new user
@pytest.mark.asyncio
async def test_handle_checkmark_new_user(reset_data, mock_update, mock_context):
    # Set up checkmark message
    mock_update.message.text = "✅"
    
    # Call the function
    await handle_checkmark(mock_update, mock_context)
    
    # Check if user was added and streak initialized
    assert mock_update.effective_user.id in user_data
    assert user_data[mock_update.effective_user.id]["streak"] == 1
    assert "last_check" in user_data[mock_update.effective_user.id]
    assert user_data[mock_update.effective_user.id]["timezone"] == DEFAULT_TIMEZONE
    
    # Check if reply was sent
    mock_update.message.reply_text.assert_called_once()

# Test anti-spam (duplicate checkmark in same day)
@pytest.mark.asyncio
async def test_handle_checkmark_duplicate(reset_data, mock_update, mock_context):
    # Add user with a check today
    user_id = mock_update.effective_user.id
    user_data[user_id] = {
        "streak": 1,
        "last_check": datetime.now(),
        "timezone": DEFAULT_TIMEZONE
    }
    
    # Set up checkmark message
    mock_update.message.text = "✅"
    
    # Call the function
    await handle_checkmark(mock_update, mock_context)
    
    # Check if streak remained the same (no increment)
    assert user_data[user_id]["streak"] == 1
    
    # Check if duplicate message was sent
    mock_update.message.reply_text.assert_called_once_with("لقد سجلت وردك بالفعل اليوم! 🙏")

# Test streak increment with consecutive days
@pytest.mark.asyncio
async def test_streak_increment(reset_data, mock_update, mock_context):
    # Add user with a check yesterday
    user_id = mock_update.effective_user.id
    yesterday = datetime.now() - timedelta(days=1)
    user_data[user_id] = {
        "streak": 5,
        "last_check": yesterday,
        "timezone": DEFAULT_TIMEZONE
    }
    
    # Set up checkmark message
    mock_update.message.text = "✅"
    
    # Call the function
    await handle_checkmark(mock_update, mock_context)
    
    # Check if streak incremented
    assert user_data[user_id]["streak"] == 6
    
    # Check if success message was sent
    mock_update.message.reply_text.assert_called_once()

# Test streak reset after missing days
@pytest.mark.asyncio
async def test_streak_reset(reset_data, mock_update, mock_context):
    # Add user with a check from several days ago
    user_id = mock_update.effective_user.id
    days_ago = datetime.now() - timedelta(days=3)
    user_data[user_id] = {
        "streak": 10,
        "last_check": days_ago,
        "timezone": DEFAULT_TIMEZONE
    }
    
    # Set up checkmark message
    mock_update.message.text = "✅"
    
    # Call the function
    await handle_checkmark(mock_update, mock_context)
    
    # Check if streak was reset to 1
    assert user_data[user_id]["streak"] == 1
    
    # Check if message was sent
    mock_update.message.reply_text.assert_called_once()

# Test group handling
@pytest.mark.asyncio
async def test_handle_checkmark_in_group(reset_data, mock_update, mock_context):
    # Set up as group chat
    mock_update.effective_chat.type = "group"
    
    # Set up checkmark message
    mock_update.message.text = "✅"
    
    # Call the function
    await handle_checkmark(mock_update, mock_context)
    
    # Check if user was added to user_data
    user_id = mock_update.effective_user.id
    assert user_id in user_data
    assert user_data[user_id]["streak"] == 1
    
    # Check if group data was updated
    chat_id = mock_update.effective_chat.id
    assert chat_id in group_data
    assert user_id in group_data[chat_id]
    assert group_data[chat_id][user_id]["streak"] == 1
    assert group_data[chat_id][user_id]["name"] == "Test User" 