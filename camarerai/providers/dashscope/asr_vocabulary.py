"""
ASR Hot Words / Vocabulary Management for DashScope Paraformer

This module manages hot words (热词) for the speech recognition system
to improve accuracy for restaurant-specific terms.

Usage:
    from camarerai.providers.dashscope.asr_vocabulary import get_or_create_phrases
    vocabulary_id = get_or_create_phrases()

Then pass vocabulary_id to Recognition():
    recognition = Recognition(
        model="paraformer-realtime-v2",
        vocabulary_id=vocabulary_id,
        ...
    )
"""

import os
from dashscope.audio.asr import VocabularyService

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

# Cache the vocabulary ID so we don't recreate it every time
_vocabulary_cache = None


def create_phrases(hot_words=None, model="paraformer-realtime-v2"):
    """
    Create a hot word vocabulary for ASR.

    Args:
        hot_words: Dict of {word: weight} where weight is 1-100
        model: The ASR model to create vocabulary for

    Returns:
        vocabulary_id: str - ID to pass to Recognition(vocabulary_id=...)
    """
    if hot_words is None:
        hot_words = DEFAULT_HOT_WORDS

    # Convert hot_words dict to vocabulary format
    vocabulary = []
    for word, weight in hot_words.items():
        vocabulary.append({
            "text": word,
            "weight": weight,
            "lang": "zh"  # Default to Chinese, could be made configurable
        })

    try:
        service = VocabularyService()
        response = service.create_vocabulary(
            target_model=model,
            vocabulary=vocabulary
        )

        if response.status_code == 200:
            # Get the vocabulary_id from the response
            vocabulary_id = response.output.get("vocabulary_id")
            print(f"[ASR Phrases] Created hot words: {vocabulary_id}")
            print(f"[ASR Phrases] Total words: {len(hot_words)}")
            return vocabulary_id
        else:
            print(f"[ASR Phrases] Failed to create: {response.message}")
            return None

    except Exception as e:
        print(f"[ASR Phrases] Error creating phrases: {e}")
        return None


def get_or_create_phrases(hot_words=None):
    """
    Get cached vocabulary ID or create new one.

    Note: In production, you might want to persist the vocabulary_id
    to avoid creating new vocabulary on each restart.

    Returns:
        vocabulary_id: str or None if creation fails
    """
    global _vocabulary_cache

    if _vocabulary_cache:
        return _vocabulary_cache

    vocabulary_id = create_phrases(hot_words)
    if vocabulary_id:
        _vocabulary_cache = vocabulary_id
    return vocabulary_id


def list_vocabularies(page=1, page_size=10):
    """List all existing vocabulary sets."""
    try:
        service = VocabularyService()
        response = service.list_vocabularies(page=page, page_size=page_size)
        return response
    except Exception as e:
        print(f"[ASR Phrases] Error listing vocabularies: {e}")
        return None


def query_vocabulary(vocabulary_id):
    """Query details of a specific vocabulary."""
    try:
        service = VocabularyService()
        response = service.query_vocabulary(vocabulary_id=vocabulary_id)
        return response
    except Exception as e:
        print(f"[ASR Phrases] Error querying vocabulary: {e}")
        return None


if __name__ == "__main__":
    # Test creating vocabulary
    print("Creating ASR hot words vocabulary...")
    vocabulary_id = get_or_create_phrases()
    if vocabulary_id:
        print(f"\nSuccess! Vocabulary ID: {vocabulary_id}")
        print(f"\nHot words included:")
        for word, weight in DEFAULT_HOT_WORDS.items():
            print(f"  - {word} (weight: {weight})")
    else:
        print("Failed to create vocabulary")
