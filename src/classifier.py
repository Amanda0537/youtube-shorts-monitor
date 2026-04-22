"""
自动分类引擎
基于视频标题、描述、标签、频道信息进行多维度自动分类

分类维度:
1. 内容赛道 (niche)
2. 人物/人设 (character/persona)
3. 标题钩子类型 (hook_type)
4. 内容钩子类型 - 基于描述和标签分析 (content_hook)
5. 语言 (language)
6. 制作方式 (production)
7. AI/动画适配度 (ai_score)
8. 推荐指数 (recommend_score)
"""
import re

# ============================================================
# 赛道关键词库
# ============================================================
NICHE_KEYWORDS = {
    "SAT": {
        "name": "解压/满足感",
        "keywords": ["satisfying", "asmr", "smooth", "oddly", "slime", "cutting", "peeling",
                      "organizing", "cleaning", "soap", "kinetic sand", "relaxing", "soothing"],
        "ai_score": 90,
    },
    "ANI": {
        "name": "动物/宠物",
        "keywords": ["cat", "dog", "puppy", "kitten", "pet", "animal", "bunny", "bird",
                      "hamster", "duck", "fish", "wildlife", "zoo", "猫", "狗", "宠物"],
        "ai_score": 70,
    },
    "FUN": {
        "name": "搞笑/整蛊",
        "keywords": ["funny", "lol", "comedy", "meme", "prank", "fail", "hilarious", "laugh",
                      "humor", "joke", "blooper", "bro ", "bruh", "sus", "搞笑", "整蛊", "恶搞"],
        "ai_score": 65,
    },
    "STR": {
        "name": "故事/剧情",
        "keywords": ["story", "emotional", "heart", "love", "sad", "touching", "life",
                      "family", "mom", "dad", "daughter", "son", "wife", "husband", "感动", "故事"],
        "ai_score": 85,
    },
    "EDU": {
        "name": "科普/知识",
        "keywords": ["learn", "science", "fact", "history", "explain", "how does", "why do",
                      "education", "tutorial", "did you know", "psychology", "知识", "科普"],
        "ai_score": 90,
    },
    "GAM": {
        "name": "游戏",
        "keywords": ["minecraft", "roblox", "fortnite", "game", "gaming", "gamer", "gameplay",
                      "mario", "pokemon", "gta", "fps", "pvp", "boss fight", "游戏"],
        "ai_score": 85,
    },
    "CMP": {
        "name": "对比/排行",
        "keywords": ["vs", "versus", "compare", "comparison", "better", "which one", "ranking",
                      "top 5", "top 10", "tier list", "best", "worst", "对比", "排行"],
        "ai_score": 90,
    },
    "WIF": {
        "name": "脑洞/假设",
        "keywords": ["what if", "imagine", "would you", "hypothetical", "impossible",
                      "unbelievable", "mind blow", "crazy", "insane", "如果"],
        "ai_score": 95,
    },
    "ILL": {
        "name": "视觉错觉/特效",
        "keywords": ["illusion", "magic", "trick", "optical", "visual", "effect", "transform",
                      "morph", "transition", "before after", "glow up", "特效", "魔术", "变身"],
        "ai_score": 90,
    },
    "MUS": {
        "name": "音乐/舞蹈",
        "keywords": ["music", "song", "dance", "sing", "cover", "remix", "beat", "rhythm",
                      "choreography", "kpop", "k-pop", "bts", "concert", "音乐", "舞蹈"],
        "ai_score": 40,
    },
    "FOD": {
        "name": "美食",
        "keywords": ["food", "cook", "recipe", "eat", "mukbang", "taste", "kitchen", "bake",
                      "chef", "meal", "delicious", "yummy", "美食", "吃", "做菜"],
        "ai_score": 60,
    },
    "SPT": {
        "name": "体育/运动",
        "keywords": ["sport", "football", "soccer", "basketball", "cricket", "ipl", "nba",
                      "goal", "workout", "fitness", "gym", "exercise", "体育", "运动"],
        "ai_score": 30,
    },
    "EMO": {
        "name": "情感/治愈",
        "keywords": ["wholesome", "kind", "kindness", "save", "rescue", "help", "charity",
                      "faith", "god", "jesus", "allah", "pray", "bless", "治愈", "暖心"],
        "ai_score": 80,
    },
    "QIZ": {
        "name": "猜谜/互动",
        "keywords": ["guess", "quiz", "test", "challenge", "can you", "find the", "spot the",
                      "which one", "real or fake", "true or false", "猜", "挑战"],
        "ai_score": 90,
    },
    "DIY": {
        "name": "手工/创意",
        "keywords": ["diy", "craft", "handmade", "build", "create", "art", "draw", "paint",
                      "design", "lego", "origami", "手工", "创意"],
        "ai_score": 75,
    },
    "FAS": {
        "name": "时尚/美妆",
        "keywords": ["fashion", "style", "outfit", "makeup", "beauty", "skincare", "model",
                      "grwm", "ootd", "hairstyle", "时尚", "穿搭"],
        "ai_score": 35,
    },
}

# ============================================================
# 钩子类型关键词库
# ============================================================
HOOK_KEYWORDS = {
    "WAIT": {
        "name": "反转/等结尾",
        "patterns": [r"wait\s*(for|till|until)", r"watch\s*till", r"till\s*the\s*end",
                      r"you won'?t\s*believe", r"unexpected", r"plot\s*twist"],
    },
    "GUESS": {
        "name": "猜谜互动",
        "patterns": [r"guess\s*(the|what|who)", r"can\s*you\s*(find|spot|see|guess)",
                      r"test\s*your", r"only\s*\d+%"],
    },
    "VS": {
        "name": "对比对决",
        "patterns": [r"\bvs\.?\b", r"versus", r"or\s*\?", r"which\s*(is|one)",
                      r"compare", r"battle\b"],
    },
    "BRO": {
        "name": "第三人称搞笑",
        "patterns": [r"\bbro\b", r"when\s*(you|your|he|she|they|we)", r"nobody\s*:",
                      r"pov\s*:", r"me\s*when"],
    },
    "HOW": {
        "name": "教程/方法",
        "patterns": [r"how\s*to", r"tutorial", r"diy", r"tips?\b", r"hack\b",
                      r"top\s*\d+", r"simple\s*(way|trick|step)"],
    },
    "SHOCK": {
        "name": "震惊/夸张",
        "patterns": [r"omg", r"oh\s*my\s*god", r"insane", r"crazy", r"unbelievable",
                      r"worst\b", r"best\b", r"most\s*(epic|insane|amazing)"],
    },
    "QSTN": {
        "name": "提问式",
        "patterns": [r"\?$", r"real\s*or\s*fake", r"true\s*or\s*false",
                      r"would\s*you", r"what\s*if", r"did\s*you\s*know"],
    },
    "STORY": {
        "name": "叙事型",
        "patterns": [r"my\s*(mom|dad|sister|brother|friend|daughter|son|wife)",
                      r"i\s*(was|went|found|made|tried)", r"(she|he)\s*(was|found|made|saved)"],
    },
    "EMJ": {
        "name": "纯表情/标签",
        "patterns": [r"^[#\s\U0001F600-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\w]+$"],
    },
}

# ============================================================
# 人设/角色检测
# ============================================================
CHARACTER_PATTERNS = {
    # 动画/虚拟角色
    "Minecraft角色": ["minecraft", "steve", "creeper", "enderman", "villager"],
    "Roblox角色": ["roblox", "noob", "piggy"],
    "Mario角色": ["mario", "luigi", "peach", "bowser", "toad"],
    "Poppy Playtime": ["poppy playtime", "huggy wuggy", "mommy long legs", "catnap"],
    "Skibidi": ["skibidi", "cameraman", "speakerman", "tv man"],
    "Among Us": ["among us", "impostor", "crewmate", "sus"],
    "Sonic角色": ["sonic", "tails", "knuckles", "shadow", "eggman"],
    "Disney角色": ["mickey", "elsa", "frozen", "moana", "encanto"],
    # 动物人设
    "猫咪人设": ["cat", "kitten", "kitty", "neko", "猫"],
    "狗狗人设": ["dog", "puppy", "doggo", "pup", "狗"],
    # 人物类型
    "宝宝/亲子": ["baby", "toddler", "kid", "child", "daughter", "son", "宝宝"],
    "情侣": ["couple", "boyfriend", "girlfriend", "bf", "gf", "relationship", "情侣"],
    "家庭": ["family", "mom", "dad", "parent", "mother", "father", "家人", "妈妈"],
    # 职业人设
    "厨师": ["chef", "cook", "recipe", "kitchen", "厨师"],
    "健身达人": ["fitness", "gym", "workout", "muscle", "gains"],
    "魔术师": ["magic", "magician", "illusion", "trick"],
}

# ============================================================
# 语言检测
# ============================================================
LANGUAGE_PATTERNS = {
    "ZH": re.compile(r'[\u4e00-\u9fff]'),
    "HI": re.compile(r'[\u0900-\u097F]'),
    "AR": re.compile(r'[\u0600-\u06FF]'),
    "JA": re.compile(r'[\u3040-\u309F\u30A0-\u30FF]'),
    "KO": re.compile(r'[\uAC00-\uD7AF]'),
    "RU": re.compile(r'[\u0400-\u04FF]'),
    "TH": re.compile(r'[\u0E00-\u0E7F]'),
    "VI": re.compile(r'[\u00C0-\u1EF9]'),
    "ES": re.compile(r'[ñáéíóúü¿¡]', re.IGNORECASE),
}

# ============================================================
# 制作方式检测
# ============================================================
PRODUCTION_KEYWORDS = {
    "AI-GEN": ["ai generated", "ai art", "midjourney", "stable diffusion", "dall-e",
               "sora", "runway", "gen-2", "ai animation", "ai video"],
    "ANIM": ["animation", "animated", "cartoon", "3d render", "blender", "cgi",
             "motion graphics", "anime", "manga style", "pixar style"],
    "SCREEN": ["gameplay", "screen record", "walkthrough", "playthrough", "speedrun"],
    "EDIT": ["edit", "compilation", "montage", "remix", "mashup", "recap"],
}


def classify_video(video):
    """
    对单个视频进行全维度分类

    Args:
        video: dict, 包含 title, description, tags, channel_name 等字段

    Returns:
        dict, 分类结果
    """
    title = (video.get("title") or "").lower()
    desc = (video.get("description") or "").lower()
    tags = [t.lower() for t in (video.get("tags") or [])]
    channel = (video.get("channel_name") or "").lower()
    all_text = f"{title} {desc} {' '.join(tags)} {channel}"

    result = {}

    # 1. 内容赛道
    result["niche"], result["niche_name"], result["niche_ai_score"] = detect_niche(title, all_text)

    # 2. 人物/人设
    result["character"], result["character_source"] = detect_character(all_text)

    # 3. 标题钩子
    result["title_hook"], result["title_hook_name"] = detect_hook(title)

    # 4. 内容钩子（基于描述和标签）
    result["content_hook"], result["content_hook_name"] = detect_hook(f"{desc} {' '.join(tags)}")

    # 5. 语言
    result["language"] = detect_language(video.get("title", ""))

    # 6. 制作方式
    result["production"] = detect_production(all_text)

    # 7. AI/动画适配度 (0-100)
    result["ai_score"] = calc_ai_score(result)

    # 8. 是否推荐
    result["is_recommended"] = calc_recommend(video, result)

    # 9. 推荐理由
    result["recommend_reasons"] = get_recommend_reasons(video, result)

    return result


def detect_niche(title, all_text):
    """检测内容赛道"""
    scores = {}
    for code, info in NICHE_KEYWORDS.items():
        score = 0
        for kw in info["keywords"]:
            if kw in title:
                score += 3  # 标题权重更高
            elif kw in all_text:
                score += 1
        if score > 0:
            scores[code] = score

    if scores:
        best = max(scores, key=scores.get)
        return best, NICHE_KEYWORDS[best]["name"], NICHE_KEYWORDS[best]["ai_score"]
    return "OTH", "其他", 50


def detect_character(all_text):
    """检测人物/人设"""
    for character, keywords in CHARACTER_PATTERNS.items():
        for kw in keywords:
            if kw in all_text:
                # 判断来源
                source = "原创IP"
                if character in ["Minecraft角色", "Roblox角色", "Mario角色",
                                 "Poppy Playtime", "Skibidi", "Among Us",
                                 "Sonic角色", "Disney角色"]:
                    source = "游戏/动漫IP"
                elif character in ["猫咪人设", "狗狗人设"]:
                    source = "动物"
                elif character in ["宝宝/亲子", "情侣", "家庭"]:
                    source = "生活人设"
                elif character in ["厨师", "健身达人", "魔术师"]:
                    source = "职业人设"
                return character, source
    return "未识别", "N/A"


def detect_hook(text):
    """检测钩子类型"""
    for code, info in HOOK_KEYWORDS.items():
        for pattern in info["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                return code, info["name"]
    return "NONE", "无明显钩子"


def detect_language(title):
    """检测语言"""
    # 检查非拉丁字符
    for lang, pattern in LANGUAGE_PATTERNS.items():
        if pattern.search(title):
            return lang

    # 检查是否以表情和标签为主（无语言）
    cleaned = re.sub(r'[#@\s\U0001F000-\U0001FFFF\u2600-\u27BF]', '', title)
    if len(cleaned) < 5:
        return "NO-LANG"

    # 默认英文
    return "EN"


def detect_production(all_text):
    """检测制作方式"""
    for method, keywords in PRODUCTION_KEYWORDS.items():
        for kw in keywords:
            if kw in all_text:
                return method
    # 默认判断
    return "UNKNOWN"


def calc_ai_score(result):
    """计算 AI/动画适配度"""
    score = result.get("niche_ai_score", 50)

    # 制作方式加分
    prod = result.get("production", "")
    if prod in ("AI-GEN", "ANIM"):
        score = min(100, score + 15)
    elif prod == "SCREEN":
        score = min(100, score + 5)
    elif prod == "REAL":
        score = max(0, score - 20)

    # 语言加分（无语言 = 更适合全球传播）
    if result.get("language") == "NO-LANG":
        score = min(100, score + 10)
    elif result.get("language") == "EN":
        score = min(100, score + 5)

    # 人设来源加分
    if result.get("character_source") == "游戏/动漫IP":
        score = min(100, score + 10)

    return score


def calc_recommend(video, classification):
    """判断是否推荐（重点关注的视频）"""
    reasons = get_recommend_reasons(video, classification)
    return len(reasons) >= 2


def get_recommend_reasons(video, classification):
    """获取推荐理由"""
    reasons = []
    views = video.get("views", 0)
    subs = video.get("subscribers", 0)
    virality = video.get("virality_ratio", 0)
    ai_score = classification.get("ai_score", 0)

    # 小频道大爆款
    if subs > 0 and subs < 100000 and virality > 50:
        reasons.append(f"小频道爆款(粉丝{subs:,}, 爆款系数{virality}x)")

    # 超高爆款系数
    if virality > 100:
        reasons.append(f"超高爆款系数({virality}x)")

    # AI/动画高适配
    if ai_score >= 80:
        reasons.append(f"AI动画适配度高({ai_score}分)")

    # 英文或无语言 + 高播放
    lang = classification.get("language", "")
    if lang in ("EN", "NO-LANG") and views > 50000000:
        reasons.append(f"英文/全球市场 + 高播放({views//1000000}M)")

    # 已有AI/动画制作方式
    if classification.get("production") in ("AI-GEN", "ANIM"):
        reasons.append("已是AI/动画内容，直接参考")

    return reasons


def classify_all(videos):
    """批量分类所有视频"""
    for v in videos:
        classification = classify_video(v)
        v.update(classification)
    return videos


if __name__ == "__main__":
    test = {
        "title": "Guess The Animal",
        "description": "Can you guess all the animals?",
        "tags": ["animals", "quiz", "guess"],
        "channel_name": "MrBeast",
        "views": 76000000,
        "subscribers": 300000000,
    }
    result = classify_video(test)
    for k, v in result.items():
        print(f"  {k}: {v}")
