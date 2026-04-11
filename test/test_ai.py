from utils.wesAi import prompt_wes_com
import pytest

@pytest.mark.asyncio
async def test_wesai():
    print("請自我介紹")
    print(await prompt_wes_com("請自我介紹"))
