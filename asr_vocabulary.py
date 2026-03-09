"""
ASR Hot Words / Vocabulary Management for DashScope Paraformer

This module manages hot words (热词) for the speech recognition system
to improve accuracy for restaurant-specific terms.

Usage:
    from asr_vocabulary import get_or_create_phrases
    phrase_id = get_or_create_phrases()

Then pass phrase_id to Recognition.start():
    recognition.start(phrase_id=phrase_id)
"""

import os
from dashscope.audio.asr import AsrPhraseManager

# Hot words for restaurant ordering
# Format: {"word": weight, ...} where weight is 1-100 (higher = more priority)
DEFAULT_HOT_WORDS = {
    # Core ordering terms (high priority - 90-100)
    "点餐": 100,      # Order food (avoid recognizing as 点赞)
    "点单": 100,      # Place order
    "菜单": 90,       # Menu
    "推荐": 90,       # Recommend
    "下单": 90,       # Place order
    "结账": 90,       # Pay bill
    "买单": 90,       # Pay bill (alternative)
    "刷卡": 85,       # Pay by card
    "支付宝": 85,     # Alipay
    "微信": 85,       # WeChat Pay

    # Common dish names (medium-high priority - 70-85)
    "宫保鸡丁": 80,    # Kung Pao Chicken
    "麻婆豆腐": 80,    # Mapo Tofu
    "担担面": 80,      # Dan Dan Noodles
    "炒饭": 75,        # Fried rice
    "炒面": 75,        # Fried noodles
    "饺子": 75,        # Dumplings
    "春卷": 75,        # Spring rolls
    "火锅": 75,        # Hot pot
    "拉面": 75,        # Ramen
    "小笼包": 80,      # Soup dumplings
    "叉烧": 75,        # Char siu
    "烧鸭": 75,        # Roast duck
    "白切鸡": 75,      # White cut chicken

    # Quantities and modifications (high priority - 80-90)
    "一份": 85,        # One portion
    "两份": 85,        # Two portions
    "三份": 85,        # Three portions
    "四份": 85,        # Four portions
    "五份": 85,        # Five portions
    "一人份": 80,      # Single portion
    "两人份": 80,      # Two person portion
    "大份": 80,        # Large portion
    "小份": 80,        # Small portion
    "不要辣": 85,      # No spicy
    "少辣": 85,        # Less spicy
    "微辣": 80,        # Mild spicy
    "中辣": 80,        # Medium spicy
    "重辣": 80,        # Extra spicy
    "少盐": 80,        # Less salt
    "少油": 80,        # Less oil
    "不加葱": 75,      # No scallions
    "不加蒜": 75,      # No garlic
    "不加香菜": 75,    # No cilantro
    "打包": 85,        # Takeout
    "带走": 85,        # To go
    "堂食": 85,        # Dine in

    # Drinks (medium priority - 60-75)
    "可乐": 70,        # Cola
    "雪碧": 70,        # Sprite
    "豆浆": 70,        # Soy milk
    "茶水": 70,        # Tea
    "啤酒": 70,        # Beer
    "橙汁": 70,        # Orange juice
}

# Cache the phrase ID so we don't recreate it every time
_phrase_cache = None


def create_phrases(hot_words=None, model="paraformer-realtime-v2"):
    """
    Create a hot word phrase set for ASR.

    Args:
        hot_words: Dict of {word: weight} where weight is 1-100
        model: The ASR model to create phrases for

    Returns:
        phrase_id: str - ID to pass to Recognition.start(phrase_id=...)
    """
    if hot_words is None:
        hot_words = DEFAULT_HOT_WORDS

    try:
        response = AsrPhraseManager.create_phrases(
            model=model,
            phrases=hot_words
        )

        if response.status_code == 200:
            # Get the phrase_id from the response
            # The response contains a job_id that becomes the phrase_id
            phrase_id = response.output.get("job_id")
            print(f"[ASR Phrases] Created hot words: {phrase_id}")
            print(f"[ASR Phrases] Total words: {len(hot_words)}")
            return phrase_id
        else:
            print(f"[ASR Phrases] Failed to create: {response.message}")
            return None

    except Exception as e:
        print(f"[ASR Phrases] Error creating phrases: {e}")
        return None


def get_or_create_phrases(hot_words=None):
    """
    Get cached phrase ID or create new one.

    Note: In production, you might want to persist the phrase_id
    to avoid creating new phrases on each restart.

    Returns:
        phrase_id: str or None if creation fails
    """
    global _phrase_cache

    if _phrase_cache:
        return _phrase_cache

    phrase_id = create_phrases(hot_words)
    if phrase_id:
        _phrase_cache = phrase_id
    return phrase_id


def list_phrases(page=1, page_size=10):
    """List all existing phrase sets."""
    try:
        response = AsrPhraseManager.list_phrases(page=page, page_size=page_size)
        return response
    except Exception as e:
        print(f"[ASR Phrases] Error listing phrases: {e}")
        return None


def query_phrases(phrase_id):
    """Query details of a specific phrase set."""
    try:
        response = AsrPhraseManager.query_phrases(phrase_id=phrase_id)
        return response
    except Exception as e:
        print(f"[ASR Phrases] Error querying phrases: {e}")
        return None


if __name__ == "__main__":
    # Test creating phrases
    print("Creating ASR hot words...")
    phrase_id = get_or_create_phrases()
    if phrase_id:
        print(f"\nSuccess! Phrase ID: {phrase_id}")
        print(f"\nHot words included:")
        for word, weight in DEFAULT_HOT_WORDS.items():
            print(f"  - {word} (weight: {weight})")
    else:
        print("Failed to create phrases")
