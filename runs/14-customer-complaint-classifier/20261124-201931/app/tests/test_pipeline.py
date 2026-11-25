import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import asyncio
from unittest.mock import patch, AsyncMock

import src.app.pipeline as pipeline

@pytest.mark.asyncio
async def test_embed_text_offline_returns_zeros():
    # When OPENAI_API_KEY not set, embed_text should return zeros
    with patch.dict('os.environ', {'OPENAI_API_KEY': ''}):
        vec = await pipeline.embed_text('hello')
        assert isinstance(vec, list)
        assert len(vec) == pipeline.EMBEDDING_DIMS
        assert all(v == 0.0 for v in vec)

@pytest.mark.asyncio
async def test_classify_text_falls_back_on_bad_json(mocker):
    # Patch openai.ChatCompletion.create to return malformed JSON
    fake_resp = AsyncMock()
    fake_resp.choices = [AsyncMock()]
    fake_resp.choices[0].message = {'content': 'not a json'}
    def fake_create(*args, **kwargs):
        return fake_resp
    mocker.patch('src.app.pipeline.openai.ChatCompletion.create', side_effect=fake_create)
    parsed = await pipeline.classify_text_with_llm('I have an issue')
    assert 'product_category' in parsed
    assert 'root_cause' in parsed
    assert 'urgency' in parsed
