class RankingConfig:
    # Configurable weights for combining scores
    ALPHA_WEIGHT = 0.4  # Weight for initial behaviour/AIS score
    BETA_WEIGHT = 0.6   # Weight for physical consistency score

ranking_config = RankingConfig()
