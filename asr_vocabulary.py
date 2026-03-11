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
# Format: {"word": weight, ...} where weight is in [-6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5]
# Positive values (1-5): Boost recognition (higher = more priority)
# Negative values (-1 to -6): Suppress recognition (more negative = suppress more)
DEFAULT_HOT_WORDS = {
    # Core ordering terms (highest priority - 5)
    "点餐": 5,       # Order food (avoid recognizing as 点赞)
    "点单": 5,       # Place order
    "菜单": 4,       # Menu
    "推荐": 4,       # Recommend
    "下单": 4,       # Place order
    "结账": 4,       # Pay bill
    "买单": 4,       # Pay bill (alternative)
    "刷卡": 4,       # Pay by card
    "支付宝": 4,     # Alipay
    "微信": 4,       # WeChat Pay

    # Common dish names (high priority - 3 to 4)
    "宫保鸡丁": 3,     # Kung Pao Chicken
    "麻婆豆腐": 3,     # Mapo Tofu
    "担担面": 3,       # Dan Dan Noodles
    "炒饭": 3,         # Fried rice
    "炒面": 3,         # Fried noodles
    "饺子": 3,         # Dumplings
    "春卷": 3,         # Spring rolls
    "火锅": 3,         # Hot pot
    "拉面": 3,         # Ramen
    "小笼包": 3,       # Soup dumplings
    "叉烧": 3,         # Char siu
    "烧鸭": 3,         # Roast duck
    "白切鸡": 3,       # White cut chicken

    # Quantities and modifications (high priority - 3 to 4)
    "一份": 4,         # One portion
    "两份": 4,         # Two portions
    "三份": 4,         # Three portions
    "四份": 4,         # Four portions
    "五份": 4,         # Five portions
    "一人份": 3,       # Single portion
    "两人份": 3,       # Two person portion
    "大份": 3,         # Large portion
    "小份": 3,         # Small portion
    "不要辣": 4,       # No spicy
    "少辣": 4,         # Less spicy
    "微辣": 3,         # Mild spicy
    "中辣": 3,         # Medium spicy
    "重辣": 3,         # Extra spicy
    "少盐": 3,         # Less salt
    "少油": 3,         # Less oil
    "不加葱": 3,       # No scallions
    "不加蒜": 3,       # No garlic
    "不加香菜": 3,     # No cilantro
    "打包": 4,         # Takeout
    "带走": 4,         # To go
    "堂食": 4,         # Dine in

    # Drinks (medium priority - 2)
    "可乐": 2,         # Cola
    "雪碧": 2,         # Sprite
    "豆浆": 2,         # Soy milk
    "茶水": 2,         # Tea
    "啤酒": 2,         # Beer
    "橙汁": 2,         # Orange juice
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
