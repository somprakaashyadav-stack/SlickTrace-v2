def estimate_volume_loss(hours_elapsed: float, wind_speed_knots: float, sea_temp_c: float) -> float:
    """
    Placeholder for oil weathering model (e.g. ADIOS or OpenOil).
    Estimates the percentage of volume lost to evaporation and natural dispersion.
    """
    # Highly simplified empirical decay curve for demo purposes
    # E.g., light crude might lose 30% in first 24h at 20C and 10 knots.
    
    base_loss_rate = 0.01 # 1% per hour
    
    # Wind increases evaporation/dispersion
    wind_factor = max(1.0, wind_speed_knots / 10.0)
    
    # Temp increases evaporation
    temp_factor = max(0.5, sea_temp_c / 20.0)
    
    hourly_loss_rate = base_loss_rate * wind_factor * temp_factor
    
    total_loss_fraction = min(0.9, hours_elapsed * hourly_loss_rate)
    return round(total_loss_fraction, 3)
