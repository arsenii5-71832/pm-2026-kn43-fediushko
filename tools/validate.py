#!/usr/bin/env python3
import sys
import os
import csv
import re
from datetime import datetime

def validate_case(target_dir):
    errors = []
    warnings = []
    successes = []

    if not os.path.isdir(target_dir):
        print(f"ERROR: Директорія '{target_dir}' не знайдена.")
        return 1

    readme_path = os.path.join(target_dir, "README.md")
    sources_path = os.path.join(target_dir, "sources.csv")

    # 1. Перевірка наявності файлів
    if not os.path.isfile(readme_path):
        errors.append(f"Файл {readme_path} не знайдено.")
    else:
        successes.append(f"Файл README.md знайдено в {target_dir}")

    if not os.path.isfile(sources_path):
        errors.append(f"Файл {sources_path} не знайдено.")
    else:
        successes.append(f"Файл sources.csv знайдено в {target_dir}")

    # 2. Перевірка sources.csv
    valid_source_ids = set()
    if os.path.isfile(sources_path):
        try:
            with open(sources_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = ["source_id", "claim", "source_title", "publisher", "url", "pub_date", "accessed"]
                if header != expected_header:
                    errors.append(f"sources.csv: Неправильний заголовок. Очікується: {expected_header}, отримано: {header}")
                else:
                    successes.append("sources.csv: Заголовок валідний.")

                rows = list(reader)
                if len(rows) < 3:
                    errors.append(f"sources.csv: Має містити щонайменше 3 джерела (знайдено {len(rows)}).")
                else:
                    successes.append(f"sources.csv: Знайдено {len(rows)} джерел (>= 3).")

                publishers = set()
                urls = set()
                has_non_wiki = False

                date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")

                for i, row in enumerate(rows, start=2):
                    if len(row) != 7:
                        errors.append(f"sources.csv рядок {i}: очікується 7 колонок, отримано {len(row)}.")
                        continue
                    sid, claim, title, pub, url, pub_date, accessed = row
                    valid_source_ids.add(sid.strip())
                    publishers.add(pub.strip())
                    urls.add(url.strip())

                    if "wikipedia.org" not in url.lower():
                        has_non_wiki = True

                    if not sid.strip().startswith("SRC-"):
                        warnings.append(f"sources.csv рядок {i}: source_id '{sid}' бажано у форматі SRC-XX.")

                    if not date_regex.match(pub_date.strip()):
                        errors.append(f"sources.csv рядок {i}: pub_date '{pub_date}' не у форматі YYYY-MM-DD.")
                    if not date_regex.match(accessed.strip()):
                        errors.append(f"sources.csv рядок {i}: accessed '{accessed}' не у форматі YYYY-MM-DD.")

                    if not (url.startswith("http://") or url.startswith("https://")):
                        errors.append(f"sources.csv рядок {i}: некоректний URL '{url}'.")

                if len(publishers) < 2:
                    errors.append(f"sources.csv: Потрібно щонайменше 2 різних видавці (знайдено {len(publishers)}).")
                else:
                    successes.append(f"sources.csv: Знайдено {len(publishers)} унікальних видавців (>= 2).")

                if len(urls) < 3:
                    errors.append(f"sources.csv: Потрібно щонайменше 3 різні URL (знайдено {len(urls)}).")
                else:
                    successes.append(f"sources.csv: Знайдено {len(urls)} унікальних URL (>= 3).")

                if not has_non_wiki:
                    errors.append("sources.csv: Потрібно щонайменше 1 джерело не з wikipedia.org.")
                else:
                    successes.append("sources.csv: Присутні джерела не з wikipedia.org.")

        except Exception as e:
            errors.append(f"Помилка при читанні sources.csv: {e}")

    # 3. Перевірка README.md
    if os.path.isfile(readme_path):
        try:
            with open(readme_path, mode="r", encoding="utf-8") as f:
                content = f.read()

            required_sections = [
                "1. Кейс і контекст",
                "2. Таймлайн",
                "3. Патерни провалу і кореневі причини",
                "4. Рішення PM",
                "5. Перенесення на власний проєкт",
                "6. Робочий журнал"
            ]

            last_pos = -1
            order_ok = True
            for sec in required_sections:
                pos = content.find(sec)
                if pos == -1:
                    errors.append(f"README.md: Відсутній обов'язковий розділ '{sec}'.")
                else:
                    if pos < last_pos:
                        order_ok = False
                    last_pos = pos

            if order_ok:
                successes.append("README.md: Усі 6 розділів присутні у правильному порядку.")
            else:
                errors.append("README.md: Розділи розташовані не у правильному порядку.")

            # Перевірка кількості слів у Розділі 1
            sec1_match = re.search(r"## 1\. Кейс і контекст\s*\n(.*?)(?=\n## 2\.|\Z)", content, re.DOTALL)
            if sec1_match:
                sec1_text = sec1_match.group(1).strip()
                words = [w for w in sec1_text.split() if w not in ["-", "—", "–"]]
                word_count = len(words)
                if word_count > 150:
                    errors.append(f"README.md Розділ 1: перевищено ліміт слів ({word_count} слів > 150 слів).")
                else:
                    successes.append(f"README.md Розділ 1: обсяг {word_count} слів (<= 150 слів).")

            # Перевірка таймлайну (мінімум 5 подій)
            timeline_matches = re.findall(r"\|\s*(\d{4}-\d{2})\s*\|(.*?)\|\s*(\[SRC-\d+\])\s*\|", content)
            if len(timeline_matches) < 5:
                warnings.append(f"README.md Розділ 2: виявлено {len(timeline_matches)} рядків таймлайну (рекомендовано 5-8).")
            else:
                successes.append(f"README.md Розділ 2: виявлено {len(timeline_matches)} подій у таймлайні (формат РРРР-ММ та [SRC-XX]).")

            # Перевірка 3 рівнів (Процес, Люди, Технології)
            has_process = "процес" in content.lower()
            has_people = "люди" in content.lower()
            has_tech = "технології" in content.lower()
            if has_process and has_people and has_tech:
                successes.append("README.md Розділ 3: покриває три рівні (Процес, Люди, Технології).")
            else:
                errors.append("README.md Розділ 3: має покривати три рівні (Процес, Люди, Технології).")

            # Перевірка посилань на джерела
            found_refs = set(re.findall(r"\[(SRC-\d+)\]", content))
            if valid_source_ids:
                missing_refs = found_refs - valid_source_ids
                if missing_refs:
                    errors.append(f"README.md: посилання {missing_refs} відсутні у sources.csv.")
                else:
                    successes.append(f"README.md: Усі посилання {found_refs} відповідають sources.csv.")

        except Exception as e:
            errors.append(f"Помилка при читанні README.md: {e}")

    # Вивід результатів
    print("=" * 60)
    print(f"РЕЗУЛЬТАТ ВАЛІДАЦІЇ ДЛЯ '{target_dir}':")
    print("=" * 60)

    for s in successes:
        print(f"  [OK] {s}")

    for w in warnings:
        print(f"  [WARN] {w}")

    if errors:
        print("-" * 60)
        print(f"ЗНАЙДЕНО ПОМИЛОК: {len(errors)}")
        for e in errors:
            print(f"  [ERROR] {e}")
        print("=" * 60)
        return 1
    else:
        print("-" * 60)
        print(" УСІ ПЕРЕВІРКИ УСПІШНО ПРОЙДЕНО! Помилок не виявлено.")
        print("=" * 60)
        return 0

def validate_charter(target_dir):
    errors = []
    warnings = []
    successes = []

    if not os.path.isdir(target_dir):
        print(f"ERROR: Директорія '{target_dir}' не знайдена.")
        return 1

    readme_path = os.path.join(target_dir, "README.md")
    stakeholders_path = os.path.join(target_dir, "stakeholders.csv")
    criteria_path = os.path.join(target_dir, "success_criteria.csv")

    # 1. Перевірка наявності файлів
    for p, name in [(readme_path, "README.md"), (stakeholders_path, "stakeholders.csv"), (criteria_path, "success_criteria.csv")]:
        if not os.path.isfile(p):
            errors.append(f"Файл {p} не знайдено.")
        else:
            successes.append(f"Файл {name} знайдено в {target_dir}")

    # 2. Перевірка stakeholders.csv
    valid_stakeholder_ids = set()
    if os.path.isfile(stakeholders_path):
        try:
            with open(stakeholders_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = ["stakeholder_id", "name_or_role", "organization", "interest", "influence", "attitude", "strategy", "owner"]
                if header != expected_header:
                    errors.append(f"stakeholders.csv: Неправильний заголовок. Очікується: {expected_header}, отримано: {header}")
                else:
                    successes.append("stakeholders.csv: Заголовок валідний.")

                rows = list(reader)
                if len(rows) < 5:
                    errors.append(f"stakeholders.csv: Має містити щонайменше 5 стейкхолдерів (знайдено {len(rows)}).")
                else:
                    successes.append(f"stakeholders.csv: Знайдено {len(rows)} стейкхолдерів (>= 5).")

                has_manage_closely = False
                has_non_supporter = False
                quadrant_rules = {
                    ("high", "high"): "manage_closely",
                    ("low", "high"): "keep_satisfied",
                    ("high", "low"): "keep_informed",
                    ("low", "low"): "monitor"
                }

                for i, row in enumerate(rows, start=2):
                    if len(row) != 8:
                        errors.append(f"stakeholders.csv рядок {i}: очікується 8 колонок, отримано {len(row)}.")
                        continue
                    sid, role, org, interest, influence, attitude, strategy, owner = [c.strip() for c in row]
                    valid_stakeholder_ids.add(sid)

                    if not sid.startswith("ST-"):
                        warnings.append(f"stakeholders.csv рядок {i}: stakeholder_id '{sid}' бажано у форматі ST-XX.")

                    interest_low = interest.lower()
                    influence_low = influence.lower()
                    attitude_low = attitude.lower()
                    strategy_low = strategy.lower()

                    if interest_low not in ["high", "low"]:
                        errors.append(f"stakeholders.csv рядок {i}: interest має бути 'high' або 'low' (отримано '{interest}').")
                    if influence_low not in ["high", "low"]:
                        errors.append(f"stakeholders.csv рядок {i}: influence має бути 'high' або 'low' (отримано '{influence}').")

                    # ST-1: Перевірка стратегії відповідно до квадранту
                    expected_strategy = quadrant_rules.get((interest_low, influence_low))
                    if expected_strategy and strategy_low != expected_strategy:
                        errors.append(f"stakeholders.csv рядок {i} ({sid}): для interest={interest}, influence={influence} стратегія має бути '{expected_strategy}', отримано '{strategy}'.")

                    if strategy_low == "manage_closely":
                        has_manage_closely = True

                    if attitude_low in ["neutral", "blocker", "opponent", "resistant"]:
                        has_non_supporter = True

                # ST-2
                if not has_manage_closely:
                    errors.append("stakeholders.csv: Потрібен щонайменше один стейкхолдер зі стратегією 'manage_closely' (ST-2).")
                else:
                    successes.append("stakeholders.csv: Присутній стейкхолдер зі стратегією 'manage_closely' (ST-2).")

                # ST-3
                if not has_non_supporter:
                    errors.append("stakeholders.csv: Потрібні стейкхолдери з attitude != 'supporter' (нейтральні або блокери) (ST-3).")
                else:
                    successes.append("stakeholders.csv: Присутні стейкхолдери з attitude != 'supporter' (ST-3).")

        except Exception as e:
            errors.append(f"Помилка при читанні stakeholders.csv: {e}")

    # 3. Перевірка success_criteria.csv
    if os.path.isfile(criteria_path):
        try:
            with open(criteria_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = ["criterion_id", "criterion", "metric", "baseline", "target", "measure_how", "accepted_by"]
                if header != expected_header:
                    errors.append(f"success_criteria.csv: Неправильний заголовок. Очікується: {expected_header}, отримано: {header}")
                else:
                    successes.append("success_criteria.csv: Заголовок валідний.")

                rows = list(reader)
                if len(rows) < 3:
                    errors.append(f"success_criteria.csv: Має містити щонайменше 3 критерії (знайдено {len(rows)}).")
                else:
                    successes.append(f"success_criteria.csv: Знайдено {len(rows)} критеріїв (>= 3).")

                accepted_by_set = set()
                for i, row in enumerate(rows, start=2):
                    if len(row) != 7:
                        errors.append(f"success_criteria.csv рядок {i}: очікується 7 колонок, отримано {len(row)}.")
                        continue
                    cid, crit, metric, base, target, mhow, acc = [c.strip() for c in row]
                    accepted_by_set.add(acc)

                    if not cid.startswith("SC-"):
                        warnings.append(f"success_criteria.csv рядок {i}: criterion_id '{cid}' бажано у форматі SC-XX.")

                    if not re.search(r"\d+", target):
                        errors.append(f"success_criteria.csv рядок {i} ({cid}): target повинен містити конкретні числа/показники (отримано '{target}').")

                if len(accepted_by_set) < 2:
                    errors.append(f"success_criteria.csv: Повинно бути щонайменше 2 різних стейкхолдери в 'accepted_by' (знайдено {len(accepted_by_set)}).")
                else:
                    successes.append(f"success_criteria.csv: Знайдено {len(accepted_by_set)} різних стейкхолдерів в accepted_by (>= 2).")

        except Exception as e:
            errors.append(f"Помилка при читанні success_criteria.csv: {e}")

    # 4. Перевірка README.md
    if os.path.isfile(readme_path):
        try:
            with open(readme_path, mode="r", encoding="utf-8") as f:
                content = f.read()

            required_sections = [
                "1. Навіщо цей проєкт",
                "2. Business case: чому саме це рішення",
                "3. Обсяг",
                "4. Обмеження з мого варіанта",
                "5. Критерії успіху",
                "6. Стейкхолдери",
                "7. Робочий журнал"
            ]

            last_pos = -1
            order_ok = True
            for sec in required_sections:
                pos = content.find(sec)
                if pos == -1:
                    errors.append(f"README.md: Відсутній обов'язковий розділ '{sec}'.")
                else:
                    if pos < last_pos:
                        order_ok = False
                    last_pos = pos

            if order_ok:
                successes.append("README.md: Усі 7 розділів присутні у правильному порядку.")
            else:
                errors.append("README.md: Розділи розташовані не у правильному порядку.")

            # Перевірка на кутові дужки-плейсхолдери <...>
            placeholders = re.findall(r"<[^>\n]{2,}>", content)
            # Фільтруємо можливі HTML-теги або дозволені символи, якщо такі є
            real_placeholders = [p for p in placeholders if not re.match(r"^<(https?://|!--|/?[a-z1-6]+>?)", p, re.IGNORECASE)]
            if real_placeholders:
                errors.append(f"README.md: Виявлено невидалені плейсхолдери шаблону у кутових дужках: {real_placeholders[:3]}")
            else:
                successes.append("README.md: Плейсхолдери у кутових дужках відсутні.")

        except Exception as e:
            errors.append(f"Помилка при читанні README.md: {e}")

    # Вивід результатів
    print("=" * 60)
    print(f"РЕЗУЛЬТАТ ВАЛІДАЦІЇ ДЛЯ '{target_dir}':")
    print("=" * 60)

    for s in successes:
        print(f"  [OK] {s}")

    for w in warnings:
        print(f"  [WARN] {w}")

    if errors:
        print("-" * 60)
        print(f"ЗНАЙДЕНО ПОМИЛОК: {len(errors)}")
        for e in errors:
            print(f"  [ERROR] {e}")
        print("=" * 60)
        return 1
    else:
        print("-" * 60)
        print(" УСІ ПЕРЕВІРКИ УСПІШНО ПРОЙДЕНО! Помилок не виявлено.")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "lr01_case"
    if "charter" in target or "lr05" in target:
        sys.exit(validate_charter(target))
    else:
        sys.exit(validate_case(target))
