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

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "lr01_case"
    sys.exit(validate_case(target))
