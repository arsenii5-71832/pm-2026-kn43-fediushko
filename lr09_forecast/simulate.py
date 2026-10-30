#!/usr/bin/env python3
"""
Скрипт симуляції Monte Carlo для прогнозування термінів релізу
на основі історичної швидкості команди (Velocity).
"""

import random
import math
from datetime import datetime, timedelta

def calculate_percentile(data, p):
    """Обчислення процентиля для масиву значень без зовнішніх бібліотек."""
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return d0 + d1

def simulate_monte_carlo(velocities, remaining_points, simulations=10000, seed=42):
    """
    Прогін симуляції Monte Carlo.
    Повертає P50 та P85 кількості спринтів.
    """
    if seed is not None:
        random.seed(seed)
    
    results = []
    for _ in range(simulations):
        rem = remaining_points
        sprints_count = 0
        while rem > 0:
            sprints_count += 1
            rem -= random.choice(velocities)
        results.append(sprints_count)
    
    p50 = math.ceil(calculate_percentile(results, 50))
    p85 = math.ceil(calculate_percentile(results, 85))
    return p50, p85, results

def main():
    # Фактичні дані перших двох спринтів нашого проєкту
    own_velocities = [11, 13]
    total_rel1_points = 39
    closed_points = 11 + 13  # 24
    remaining_after_two = total_rel1_points - closed_points  # 15
    
    end_sprint_1 = datetime.strptime("2026-10-02", "%Y-%m-%d").date()
    end_sprint_2 = datetime.strptime("2026-10-16", "%Y-%m-%d").date()
    
    print("=" * 65)
    print("СИМУЛЯЦІЯ MONTE CARLO ДЛЯ ВЛАСНОГО ПРОЄКТУ")
    print("=" * 65)
    
    # Сценарій 1: Весь перший реліз (відлік від кінця Спринта 1)
    p50_s1, p85_s1, _ = simulate_monte_carlo(own_velocities, total_rel1_points, simulations=10000)
    p50_date_1 = end_sprint_1 + timedelta(days=(p50_s1 - 1) * 14)
    p85_date_1 = end_sprint_1 + timedelta(days=(p85_s1 - 1) * 14)
    
    print(f"1. Весь перший реліз ({total_rel1_points} points):")
    print(f"   P50 спринтів: {p50_s1} -> Дата: {p50_date_1}")
    print(f"   P85 спринтів: {p85_s1} -> Дата: {p85_date_1}")
    
    # Сценарій 2: Залишок після двох спринтів (відлік від кінця Спринта 2)
    p50_s2, p85_s2, _ = simulate_monte_carlo(own_velocities, remaining_after_two, simulations=10000)
    p50_date_2 = end_sprint_2 + timedelta(days=p50_s2 * 14)
    p85_date_2 = end_sprint_2 + timedelta(days=p85_s2 * 14)
    
    print(f"\n2. Залишок після двох спринтів ({remaining_after_two} points):")
    print(f"   P50 спринтів: {p50_s2} -> Дата: {p50_date_2}")
    print(f"   P85 спринтів: {p85_s2} -> Дата: {p85_date_2}")
    
    print("\n" + "=" * 65)
    print("ПРОГІН НА НАВЧАЛЬНИХ ДАНИХ КУРСУ (220 points):")
    print("=" * 65)
    
    ref_12 = [21, 17, 26, 14, 23, 6, 28, 12, 22, 25, 18, 9]
    ref_1_2 = [21, 17]
    ref_5_6 = [23, 6]
    
    p50_ref12, p85_ref12, _ = simulate_monte_carlo(ref_12, 220, simulations=10000)
    p50_ref12_sub, p85_ref12_sub, _ = simulate_monte_carlo(ref_1_2, 220, simulations=10000)
    p50_ref56_sub, p85_ref56_sub, _ = simulate_monte_carlo(ref_5_6, 220, simulations=10000)
    
    print(f"1. Усі 12 спринтів (12 значень): P50 = {p50_ref12}, P85 = {p85_ref12} (інтервал: {p85_ref12 - p50_ref12})")
    print(f"2. Спринти 1 і 2 (21, 17):       P50 = {p50_ref12_sub}, P85 = {p85_ref12_sub} (інтервал: {p85_ref12_sub - p50_ref12_sub})")
    print(f"3. Спринти 5 і 6 (23, 6):        P50 = {p50_ref56_sub}, P85 = {p85_ref56_sub} (інтервал: {p85_ref56_sub - p50_ref56_sub})")

if __name__ == "__main__":
    main()
