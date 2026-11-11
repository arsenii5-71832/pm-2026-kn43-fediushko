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


def validate_backlog(target_dir):
    errors = []
    warnings = []
    successes = []

    if not os.path.isdir(target_dir):
        print(f"ERROR: Директорія '{target_dir}' не знайдена.")
        return 1

    readme_path = os.path.join(target_dir, "README.md")
    dor_path = os.path.join(target_dir, "dor.md")
    backlog_path = os.path.join(target_dir, "backlog.csv")

    # BL-1. Перевірка наявності файлів
    for p, name in [(readme_path, "README.md"), (dor_path, "dor.md"), (backlog_path, "backlog.csv")]:
        if not os.path.isfile(p):
            errors.append(f"BL-1: Файл {p} не знайдено.")
        else:
            successes.append(f"BL-1: Файл {name} знайдено в {target_dir}")

    # BL-2 .. BL-9. Перевірка backlog.csv
    if os.path.isfile(backlog_path):
        try:
            with open(backlog_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = [
                    "story_id", "epic", "title", "as_a", "i_want", "so_that",
                    "acceptance_criteria", "priority_method", "priority_score",
                    "priority_inputs", "rank", "release", "success_criterion"
                ]
                if header != expected_header:
                    errors.append(f"BL-2: Неправильний заголовок backlog.csv. Очікується:\n{expected_header}\nОтримано:\n{header}")
                else:
                    successes.append("BL-2: Заголовок backlog.csv валідний.")

                rows = list(reader)
                if len(rows) < 15:
                    errors.append(f"BL-3: Має містити щонайменше 15 історій (знайдено {len(rows)}).")
                else:
                    successes.append(f"BL-3: Знайдено {len(rows)} історій (>= 15).")

                # Перевірка наявності S-01 .. S-13
                story_ids = [r[0].strip() for r in rows if len(r) > 0]
                missing_base = [f"S-{i:02d}" for i in range(1, 14) if f"S-{i:02d}" not in story_ids]
                if missing_base:
                    errors.append(f"BL-3: Відсутні базові історії зі стартового беклогу: {missing_base}")
                else:
                    successes.append("BL-3: Усі базові історії S-01..S-13 присутні.")

                # BL-4. Епіки
                epics = set(r[1].strip() for r in rows if len(r) > 1 and r[1].strip())
                if len(epics) < 3:
                    errors.append(f"BL-4: Потрібно щонайменше 3 різні епіки (знайдено {len(epics)}: {epics}).")
                else:
                    successes.append(f"BL-4: Знайдено {len(epics)} епіків (>= 3).")

                # BL-5. Реліз REL-1
                rel1_rows = [r for r in rows if len(r) > 11 and r[11].strip() == "REL-1"]
                if len(rel1_rows) < 8:
                    errors.append(f"BL-5: Реліз REL-1 повинен містити щонайменше 8 історій (знайдено {len(rel1_rows)}).")
                else:
                    successes.append(f"BL-5: У релізі REL-1 знайдено {len(rel1_rows)} історій (>= 8).")

                # BL-6. Acceptance criteria
                negative_criteria_count = 0
                negative_keywords = ["невірн", "відхил", "помилк", "немає", "відсутн", "збій", "офлайн", "літак", "недоступн", "заблоков"]
                vague_words = ["зручно", "швидко", "гарно", "просто", "легко"]

                for i, r in enumerate(rows, start=2):
                    if len(r) != 13:
                        errors.append(f"backlog.csv рядок {i}: очікується 13 колонок, отримано {len(r)}.")
                        continue
                    sid, epic, title, as_a, i_want, so_that, ac, pm, pscore, pinputs, rank, rel, sc = [c.strip() for c in r]

                    if rel == "REL-1":
                        if not ac:
                            errors.append(f"BL-6: Історія {sid} в REL-1 повинна мати acceptance_criteria.")
                        else:
                            parts = [p.strip() for p in ac.split(";") if p.strip()]
                            if len(parts) < 2:
                                errors.append(f"BL-6: Історія {sid} повинна мати щонайменше 2 критерії приймання через ';' (отримано {len(parts)}).")
                            for p in parts:
                                for vw in vague_words:
                                    if vw in p.lower():
                                        warnings.append(f"BL-6: Критерій в {sid} містить суб'єктивне слово '{vw}': \"{p}\"")
                            has_neg = any(any(kw in p.lower() for kw in negative_keywords) for p in parts)
                            if has_neg:
                                negative_criteria_count += 1
                    else:
                        if ac:
                            warnings.append(f"BL-6: Історія {sid} поза REL-1 бажано повинна мати порожнє поле acceptance_criteria.")

                if negative_criteria_count < 3:
                    errors.append(f"BL-6: Потрібно щонайменше 3 історії з явним негативним сценарієм (знайдено {negative_criteria_count}).")
                else:
                    successes.append(f"BL-6: Знайдено {negative_criteria_count} історій з негативними сценаріями (>= 3).")

                # BL-7. Метод пріоритезації
                methods = set(r[7].strip().lower() for r in rows if len(r) > 7)
                if len(methods) != 1 or ("rice" not in methods and "moscow" not in methods):
                    errors.append(f"BL-7: Очікується єдиний метод пріоритезації для всього файлу ('rice' або 'moscow', отримано {methods}).")
                else:
                    method_name = list(methods)[0]
                    successes.append(f"BL-7: Використано єдиний метод пріоритезації '{method_name}'.")

                if "rice" in methods:
                    for i, r in enumerate(rows, start=2):
                        if len(r) != 13:
                            continue
                        sid, epic, title, as_a, i_want, so_that, ac, pm, pscore, pinputs, rank, rel, sc = [c.strip() for c in r]
                        if rel == "REL-1":
                            if not pinputs:
                                errors.append(f"BL-7: Для {sid} в REL-1 має бути заповнено priority_inputs у форматі reach=X;impact=Y;confidence=Z;effort=W.")
                            else:
                                params = {}
                                for token in pinputs.split(";"):
                                    if "=" in token:
                                        k, v = token.split("=", 1)
                                        try:
                                            params[k.strip().lower()] = float(v.strip())
                                        except ValueError:
                                            pass
                                if not all(k in params for k in ["reach", "impact", "confidence", "effort"]):
                                    errors.append(f"BL-7: {sid} priority_inputs '{pinputs}' не містить усіх 4 компонентів reach, impact, confidence, effort.")
                                else:
                                    reach = params["reach"]
                                    impact = params["impact"]
                                    confidence = params["confidence"]
                                    effort = params["effort"]
                                    if effort == 0:
                                        errors.append(f"BL-7: {sid} effort не може бути 0.")
                                    else:
                                        expected_score = round((reach * impact * confidence) / effort, 1)
                                        try:
                                            actual_score = float(pscore)
                                            if abs(actual_score - expected_score) > 0.15:
                                                errors.append(f"BL-7: {sid} priority_score {actual_score} не відповідає розрахунку RICE {expected_score}.")
                                        except ValueError:
                                            errors.append(f"BL-7: {sid} priority_score '{pscore}' не є числом.")

                # BL-8. Rank
                try:
                    ranks = [int(r[10].strip()) for r in rows if len(r) > 10]
                    expected_ranks = list(range(1, len(ranks) + 1))
                    if sorted(ranks) != expected_ranks:
                        errors.append(f"BL-8: Поле 'rank' має містити суцільний ряд цілих чисел від 1 до {len(ranks)} без пропусків.")
                    else:
                        successes.append("BL-8: Поле 'rank' містить суцільний числовий ряд від 1 до N.")

                    # Перевірка що REL-1 розташовані вгорі (ранги 1..len(rel1_rows))
                    rel1_ranks = [int(r[10].strip()) for r in rel1_rows]
                    if set(rel1_ranks) != set(range(1, len(rel1_rows) + 1)):
                        warnings.append(f"BL-8: Історії REL-1 мають ранги {sorted(rel1_ranks)}, рекомендовано розташовувати їх на початку (1..{len(rel1_rows)}).")
                    else:
                        successes.append("BL-8: Усі історії REL-1 розташовані на початку списку (найвищі ранги).")
                except ValueError:
                    errors.append("BL-8: Не всі значення в колонці 'rank' є цілими числами.")

                # BL-9. Success criteria
                valid_sc = {"SC-01", "SC-02", "SC-03"}
                used_sc = set()
                for i, r in enumerate(rows, start=2):
                    if len(r) != 13:
                        continue
                    sid, rel, sc = r[0].strip(), r[11].strip(), r[12].strip()
                    if rel == "REL-1":
                        if not sc:
                            errors.append(f"BL-9: Історія {sid} в REL-1 повинна містити success_criterion.")
                        elif sc not in valid_sc:
                            errors.append(f"BL-9: Історія {sid} містить невідомий success_criterion '{sc}' (очікується SC-01, SC-02, або SC-03).")
                        else:
                            used_sc.add(sc)
                if valid_sc - used_sc:
                    errors.append(f"BL-9: Не всі обов'язкові критерії успіху покриті історіями REL-1 (відсутні: {valid_sc - used_sc}).")
                else:
                    successes.append("BL-9: Усі критерії успіху SC-01, SC-02, SC-03 покриті історіями REL-1.")

        except Exception as e:
            errors.append(f"Помилка при читанні backlog.csv: {e}")

    # BL-10. Перевірка dor.md
    if os.path.isfile(dor_path):
        try:
            with open(dor_path, mode="r", encoding="utf-8") as f:
                dor_content = f.read()

            required_dor_sections = [
                "1. Умови взяття історії у спринт",
                "2. Чого DoR свідомо не вимагає",
                "3. Що робити з історією, яка не пройшла DoR",
                "4. Перевірка на власному беклозі"
            ]

            last_pos = -1
            order_ok = True
            for sec in required_dor_sections:
                pos = dor_content.find(sec)
                if pos == -1:
                    errors.append(f"BL-10 dor.md: Відсутній обов'язковий розділ '{sec}'.")
                else:
                    if pos < last_pos:
                        order_ok = False
                    last_pos = pos

            if order_ok:
                successes.append("BL-10 dor.md: Усі 4 розділи присутні у правильному порядку.")
            else:
                errors.append("BL-10 dor.md: Розділи розташовані не у правильному порядку.")

            placeholders = re.findall(r"<[^>\n]{2,}>", dor_content)
            real_placeholders = [p for p in placeholders if not re.match(r"^<(https?://|!--|/?[a-z1-6]+>?)", p, re.IGNORECASE)]
            if real_placeholders:
                errors.append(f"BL-10 dor.md: Виявлено невидалені плейсхолдери у кутових дужках: {real_placeholders[:3]}")
            else:
                successes.append("BL-10 dor.md: Плейсхолдери у кутових дужках відсутні.")
        except Exception as e:
            errors.append(f"Помилка при читанні dor.md: {e}")

    # BL-10. Перевірка README.md
    if os.path.isfile(readme_path):
        try:
            with open(readme_path, mode="r", encoding="utf-8") as f:
                readme_content = f.read()

            required_readme_sections = [
                "1. Трекер",
                "2. Метод пріоритезації і чому саме він",
                "3. Звідки взялися числа",
                "4. Перший реліз",
                "5. Що змінила перевірка за INVEST",
                "6. Історії і критерії успіху",
                "7. Робочий журнал"
            ]

            last_pos = -1
            order_ok = True
            for sec in required_readme_sections:
                pos = readme_content.find(sec)
                if pos == -1:
                    errors.append(f"BL-10 README.md: Відсутній обов'язковий розділ '{sec}'.")
                else:
                    if pos < last_pos:
                        order_ok = False
                    last_pos = pos

            if order_ok:
                successes.append("BL-10 README.md: Усі 7 розділів присутні у правильному порядку.")
            else:
                errors.append("BL-10 README.md: Розділи розташовані не у правильному порядку.")

            placeholders = re.findall(r"<[^>\n]{2,}>", readme_content)
            real_placeholders = [p for p in placeholders if not re.match(r"^<(https?://|!--|/?[a-z1-6]+>?)", p, re.IGNORECASE)]
            if real_placeholders:
                errors.append(f"BL-10 README.md: Виявлено невидалені плейсхолдери у кутових дужках: {real_placeholders[:3]}")
            else:
                successes.append("BL-10 README.md: Плейсхолдери у кутових дужках відсутні.")
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


def validate_wbs(target_dir):
    errors = []
    warnings = []
    successes = []

    if not os.path.isdir(target_dir):
        print(f"ERROR: Директорія '{target_dir}' не знайдена.")
        return 1

    readme_path = os.path.join(target_dir, "README.md")
    wbs_path = os.path.join(target_dir, "wbs.csv")
    schedule_path = os.path.join(target_dir, "schedule.csv")
    roadmap_path = os.path.join(target_dir, "roadmap.csv")

    # 1. Наявність файлів
    for p, name in [(readme_path, "README.md"), (wbs_path, "wbs.csv"), (schedule_path, "schedule.csv"), (roadmap_path, "roadmap.csv")]:
        if not os.path.isfile(p):
            errors.append(f"Файл {p} не знайдено.")
        else:
            successes.append(f"Файл {name} знайдено в {target_dir}")

    wbs_leaf_ids = set()
    wbs_nodes = {}
    wbs_children = {}

    # 2. Перевірка wbs.csv
    if os.path.isfile(wbs_path):
        try:
            with open(wbs_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = ["wbs_id", "parent_id", "name", "level", "deliverable", "owner", "estimate_hours"]
                if header != expected_header:
                    errors.append(f"WBS-1: Неправильний заголовок wbs.csv. Очікується:\n{expected_header}\nОтримано:\n{header}")
                else:
                    successes.append("WBS-1: Заголовок wbs.csv валідний.")

                rows = list(reader)
                if len(rows) < 12:
                    errors.append(f"WBS-2: WBS має містити щонайменше 12 вузлів (знайдено {len(rows)}).")
                else:
                    successes.append(f"WBS-2: Знайдено {len(rows)} вузлів у WBS (>= 12).")

                levels_found = set()
                parent_map = {}
                hours_map = {}
                owner_map = {}
                deliverable_map = {}

                for i, r in enumerate(rows, start=2):
                    if len(r) != 7:
                        errors.append(f"wbs.csv рядок {i}: очікується 7 колонок, отримано {len(r)}.")
                        continue
                    wid, pid, name, lvl, deliv, owner, hours = [c.strip() for c in r]
                    try:
                        lvl_int = int(lvl)
                        levels_found.add(lvl_int)
                    except ValueError:
                        errors.append(f"wbs.csv рядок {i}: level '{lvl}' не є цілим числом.")
                        lvl_int = 0

                    try:
                        h_val = float(hours)
                    except ValueError:
                        errors.append(f"wbs.csv рядок {i}: estimate_hours '{hours}' не є числом.")
                        h_val = 0.0

                    wbs_nodes[wid] = {"name": name, "level": lvl_int, "deliverable": deliv, "owner": owner, "hours": h_val, "parent": pid}
                    hours_map[wid] = h_val
                    owner_map[wid] = owner
                    deliverable_map[wid] = deliv
                    parent_map[wid] = pid
                    wbs_children.setdefault(pid, []).append(wid)

                if levels_found != {1, 2, 3}:
                    errors.append(f"WBS-2: WBS повинен мати рівно 3 рівні ієрархії (знайдено рівні: {sorted(levels_found)}).")
                else:
                    successes.append("WBS-2: WBS має рівно 3 рівні ієрархії (корінь, рівень 2, листки).")

                # Перевірка обов'язкових гілок 2-го рівня: 1.1 ... 1.5
                expected_lvl2 = {"1.1", "1.2", "1.3", "1.4", "1.5"}
                found_lvl2 = {wid for wid, d in wbs_nodes.items() if d["level"] == 2}
                if not expected_lvl2.issubset(found_lvl2):
                    errors.append(f"WBS-2: Відсутні обов'язкові гілки 2-го рівня (1.1..1.5). Знайдено: {found_lvl2}")
                else:
                    successes.append("WBS-2: Усі гілки другого рівня (1.1..1.5) присутні.")

                # Визначення листових вузлів (вузли, які не є батьками для жодного іншого вузла)
                all_parents = set(parent_map.values())
                for wid, d in wbs_nodes.items():
                    if wid not in all_parents and d["level"] == 3:
                        wbs_leaf_ids.add(wid)

                # WBS-3. Правило 100%
                rule100_ok = True
                for wid, children in wbs_children.items():
                    if wid and wid in hours_map:
                        children_sum = sum(hours_map[c] for c in children)
                        parent_hours = hours_map[wid]
                        if abs(children_sum - parent_hours) > 0.01:
                            errors.append(f"WBS-3 (Правило 100%): Вузол {wid} ({parent_hours} год) != сумі дочірніх вузлів {children} ({children_sum} год).")
                            rule100_ok = False
                if rule100_ok:
                    successes.append("WBS-3: Правило 100% виконано: години кожного вузла точно дорівнюють сумі дочірніх.")

                # WBS-4: Стеля годин за варіантом V08 (12 тижнів = 60 днів)
                # PM: 0.5 * 60 * 8 = 240
                # Dev: 2.0 * 60 * 8 = 960
                # QA: 1.0 * 60 * 8 = 480
                # DevOps: 0.25 * 60 * 8 = 120
                # Total: 1800
                root_node = next((wid for wid, d in wbs_nodes.items() if d["level"] == 1), None)
                if root_node:
                    root_hours = hours_map[root_node]
                    ceiling = 1800.0
                    min_allowed = 0.70 * ceiling
                    max_allowed = 1.00 * ceiling
                    if root_hours < min_allowed or root_hours > max_allowed:
                        errors.append(f"WBS-4: Загальний обсяг проєкту ({root_hours} год) має бути в межах 70–100% стелі варіанта V08 ({min_allowed:.0f}–{max_allowed:.0f} год).")
                    else:
                        successes.append(f"WBS-4: Обсяг проєкту {root_hours:.0f} год відповідає 70-100% стелі ({min_allowed:.0f}–{max_allowed:.0f} год, {root_hours/ceiling*100:.1f}%).")

                # Перевірка годин за ролями для листових вузлів
                role_hours = {}
                for wid in wbs_leaf_ids:
                    own = owner_map[wid]
                    role_hours[own] = role_hours.get(own, 0.0) + hours_map[wid]

                role_ceilings = {"PM": 240.0, "Dev": 960.0, "QA": 480.0, "DevOps": 120.0}
                for role, limit in role_ceilings.items():
                    actual = role_hours.get(role, 0.0)
                    if actual > limit:
                        errors.append(f"WBS-4: Роль {role} перевищує стелю годин варіанта ({actual:.0f} > {limit:.0f} год).")
                    else:
                        successes.append(f"WBS-4: Роль {role} у межах ліміту ({actual:.0f} <= {limit:.0f} год).")

                # Deliverables: Тільки іменникові фрази (перевірка на типові дієслова на початку)
                verb_starts = ["розробити", "створити", "дослідити", "провести", "реалізувати", "написати", "налаштувати", "підготувати", "виконати", "тестувати"]
                verb_errors = 0
                for wid, deliv in deliverable_map.items():
                    first_word = deliv.lower().split()[0] if deliv.strip() else ""
                    if any(first_word.startswith(vb) for vb in verb_starts):
                        errors.append(f"WBS deliverable ({wid}): результат має бути іменником/іменниковою фразою, а не дієсловом ('{deliv}').")
                        verb_errors += 1
                if verb_errors == 0:
                    successes.append("WBS deliverable: Усі результати сформульовані як іменникові фрази (без дієслів).")

        except Exception as e:
            errors.append(f"Помилка при читанні wbs.csv: {e}")

    # 3. Перевірка schedule.csv
    schedule_tasks = {}
    if os.path.isfile(schedule_path):
        try:
            with open(schedule_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = ["task_id", "wbs_id", "name", "duration_days", "predecessors", "milestone", "float_days", "is_critical"]
                if header != expected_header:
                    errors.append(f"SCH-1: Неправильний заголовок schedule.csv. Очікується:\n{expected_header}\nОтримано:\n{header}")
                else:
                    successes.append("SCH-1: Заголовок schedule.csv валідний.")

                rows = list(reader)
                if len(rows) < 10:
                    errors.append(f"SCH-5: Графік має містити щонайменше 10 робіт (знайдено {len(rows)}).")
                else:
                    successes.append(f"SCH-5: Знайдено {len(rows)} робіт у графіку (>= 10).")

                covered_wbs_leaves = set()
                start_tasks_count = 0
                milestone_count = 0

                graph = {}
                durations = {}
                recorded_floats = {}
                recorded_criticals = {}

                for i, r in enumerate(rows, start=2):
                    if len(r) != 8:
                        errors.append(f"schedule.csv рядок {i}: очікується 8 колонок, отримано {len(r)}.")
                        continue
                    tid, wid, name, dur, preds, ms, fl, crit = [c.strip() for c in r]

                    try:
                        dur_val = float(dur)
                    except ValueError:
                        errors.append(f"schedule.csv рядок {i}: duration_days '{dur}' не є числом.")
                        dur_val = 0.0

                    try:
                        fl_val = float(fl)
                    except ValueError:
                        errors.append(f"schedule.csv рядок {i}: float_days '{fl}' не є числом.")
                        fl_val = 0.0

                    pred_list = [p.strip() for p in preds.split(",") if p.strip()]
                    if not pred_list:
                        start_tasks_count += 1

                    if ms.lower() == "yes":
                        milestone_count += 1
                        if dur_val != 0:
                            errors.append(f"SCH-4: Віха {tid} повинна мати duration_days = 0 (отримано {dur_val}).")

                    # X-11: посилання на листовий вузол
                    if wid not in wbs_leaf_ids:
                        errors.append(f"X-11: Робота {tid} посилається на нелистовий або неіснуючий вузол WBS '{wid}'.")
                    else:
                        covered_wbs_leaves.add(wid)

                    schedule_tasks[tid] = {"wbs_id": wid, "name": name, "duration": dur_val, "preds": pred_list, "milestone": ms.lower(), "float": fl_val, "critical": crit.lower()}
                    durations[tid] = dur_val
                    graph[tid] = pred_list
                    recorded_floats[tid] = fl_val
                    recorded_criticals[tid] = crit.lower()

                # X-12: покриття листових вузлів WBS
                uncovered_leaves = wbs_leaf_ids - covered_wbs_leaves
                if uncovered_leaves:
                    errors.append(f"X-12: Листові вузли WBS {uncovered_leaves} не мають жодної роботи в календарному плані.")
                else:
                    successes.append("X-12: Усі листові вузли WBS покриті роботами графіка.")

                # Стартові роботи
                if start_tasks_count < 2:
                    errors.append(f"SCH-5: Потрібно щонайменше 2 стартові роботи без попередників (знайдено {start_tasks_count}).")
                else:
                    successes.append(f"SCH-5: Знайдено {start_tasks_count} стартових робіт без попередників (>= 2).")

                # Віхи
                if milestone_count < 2:
                    errors.append(f"SCH-4: Потрібно щонайменше 2 віхи з milestone=yes (знайдено {milestone_count}).")
                else:
                    successes.append(f"SCH-4: Знайдено {milestone_count} віх (>= 2).")

                # Розрахунок критичного шляху: перевірка на цикли та обчислення ES, EF, LS, LF, Float
                in_degree = {u: len(preds) for u, preds in graph.items()}
                succ_graph = {u: [] for u in graph}
                for u, preds in graph.items():
                    for p in preds:
                        if p in succ_graph:
                            succ_graph[p].append(u)
                        else:
                            errors.append(f"SCH-1: Робота {u} посилається на неіснуючого попередника '{p}'.")

                # Топологічне сортування
                topo_order = []
                queue = [u for u, deg in in_degree.items() if deg == 0]
                temp_in_degree = in_degree.copy()
                while queue:
                    u = queue.pop(0)
                    topo_order.append(u)
                    for s in succ_graph.get(u, []):
                        temp_in_degree[s] -= 1
                        if temp_in_degree[s] == 0:
                            queue.append(s)

                if len(topo_order) != len(graph):
                    errors.append("SCH-1: Виявлено цикл у графі залежностей графіка!")
                else:
                    successes.append("SCH-1: Граф робіт ациклічний (циклів не виявлено).")

                    # Прямий прохід
                    es = {}
                    ef = {}
                    for u in topo_order:
                        preds = graph[u]
                        es[u] = max([ef[p] for p in preds], default=0.0)
                        ef[u] = es[u] + durations[u]

                    project_duration = max(ef.values(), default=0.0)

                    # Зворотний прохід
                    lf = {}
                    ls = {}
                    for u in reversed(topo_order):
                        succs = succ_graph.get(u, [])
                        lf[u] = min([ls[s] for s in succs], default=project_duration)
                        ls[u] = lf[u] - durations[u]

                    # Перевірка float_days та is_critical
                    float_mismatch = 0
                    crit_mismatch = 0
                    for u in graph:
                        calc_float = ls[u] - es[u]
                        rec_float = recorded_floats[u]
                        if abs(calc_float - rec_float) > 0.01:
                            errors.append(f"SCH-2: Робота {u}: розрахунковий float={calc_float:.0f}, зазначено float_days={rec_float:.0f}.")
                            float_mismatch += 1

                        expected_crit = "yes" if abs(calc_float) < 0.01 else "no"
                        rec_crit = recorded_criticals[u]
                        if expected_crit != rec_crit:
                            errors.append(f"SCH-3: Робота {u}: is_critical має бути '{expected_crit}', зазначено '{rec_crit}'.")
                            crit_mismatch += 1

                    if float_mismatch == 0:
                        successes.append(f"SCH-2: Усі значення float_days математично точні (довжина критичного шляху: {project_duration:.0f} дн).")
                    if crit_mismatch == 0:
                        successes.append("SCH-3: Поле is_critical позначено як 'yes' виключно для робіт із float=0.")

        except Exception as e:
            errors.append(f"Помилка при читанні schedule.csv: {e}")

    # 4. Перевірка roadmap.csv
    roadmap_releases = set()
    if os.path.isfile(roadmap_path):
        try:
            with open(roadmap_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = ["release_id", "name", "target_date", "goal"]
                if header != expected_header:
                    errors.append(f"RM-1: Неправильний заголовок roadmap.csv. Очікується:\n{expected_header}\nОтримано:\n{header}")
                else:
                    successes.append("RM-1: Заголовок roadmap.csv валідний.")

                rows = list(reader)
                if len(rows) < 2:
                    errors.append(f"RM-1: Дорожня карта повинна містити щонайменше 2 релізи (знайдено {len(rows)}).")
                else:
                    successes.append(f"RM-1: Знайдено {len(rows)} релізи у roadmap.csv (>= 2).")

                date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
                dates = {}
                for i, r in enumerate(rows, start=2):
                    if len(r) != 4:
                        errors.append(f"roadmap.csv рядок {i}: очікується 4 колонки, отримано {len(r)}.")
                        continue
                    rel_id, name, tdate, goal = [c.strip() for c in r]
                    roadmap_releases.add(rel_id)
                    dates[rel_id] = tdate
                    if not date_regex.match(tdate):
                        errors.append(f"roadmap.csv рядок {i}: target_date '{tdate}' не у форматі YYYY-MM-DD.")

                if "REL-1" in dates and "REL-2" in dates:
                    if dates["REL-2"] <= dates["REL-1"]:
                        errors.append(f"RM-1: Дата REL-2 ({dates['REL-2']}) повинна бути пізнішою за REL-1 ({dates['REL-1']}).")
                    else:
                        successes.append(f"RM-1: Дати релізів хронологічно послідовні ({dates['REL-1']} -> {dates['REL-2']}).")

        except Exception as e:
            errors.append(f"Помилка при читанні roadmap.csv: {e}")

    # X-13: Синхронізація з lr06_backlog/backlog.csv
    backlog_path = os.path.join("lr06_backlog", "backlog.csv")
    if os.path.isfile(backlog_path):
        try:
            with open(backlog_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                backlog_releases = set()
                if header and "release" in header:
                    rel_idx = header.index("release")
                    for r in reader:
                        if len(r) > rel_idx and r[rel_idx].strip():
                            backlog_releases.add(r[rel_idx].strip())

                if not roadmap_releases.issubset(backlog_releases):
                    errors.append(f"X-13 / RM-1: Релізи з дорожньої карти {roadmap_releases} відсутні у беклозі (у беклозі є: {backlog_releases}).")
                else:
                    successes.append(f"X-13 / RM-1: Усі релізи дорожньої карти {roadmap_releases} присутні у беклозі.")
        except Exception as e:
            errors.append(f"Помилка при читанні lr06_backlog/backlog.csv: {e}")

    # 5. Перевірка README.md
    if os.path.isfile(readme_path):
        try:
            with open(readme_path, mode="r", encoding="utf-8") as f:
                content = f.read()

            required_sections = [
                "1. Стеля годин мого варіанта",
                "2. Правило 100%: як перевіряли",
                "3. Тривалості: звідки взялися числа",
                "4. Критичний шлях",
                "5. Віхи",
                "6. Дорожня карта",
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

            placeholders = re.findall(r"<[^>\n]{2,}>", content)
            real_placeholders = [p for p in placeholders if not re.match(r"^<(https?://|!--|/?[a-z1-6]+>?)", p, re.IGNORECASE)]
            if real_placeholders:
                errors.append(f"README.md: Виявлено невидалені плейсхолдери у кутових дужках: {real_placeholders[:3]}")
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


def validate_poker(target_dir):
    errors = []
    warnings = []
    successes = []

    if not os.path.isdir(target_dir):
        print(f"ERROR: Директорія '{target_dir}' не знайдена.")
        return 1

    readme_path = os.path.join(target_dir, "README.md")
    votes_path = os.path.join(target_dir, "votes.csv")
    estimates_path = os.path.join(target_dir, "estimates.csv")

    for p, name in [(readme_path, "README.md"), (votes_path, "votes.csv"), (estimates_path, "estimates.csv")]:
        if not os.path.isfile(p):
            errors.append(f"PK-1: Файл {p} не знайдено.")
        else:
            successes.append(f"PK-1: Файл {name} знайдено в {target_dir}")

    # Отримання списку історій REL-1 з lr06_backlog/backlog.csv
    rel1_stories = set()
    backlog_path = os.path.join("lr06_backlog", "backlog.csv")
    if os.path.isfile(backlog_path):
        try:
            with open(backlog_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header and "release" in header and "story_id" in header:
                    s_idx = header.index("story_id")
                    r_idx = header.index("release")
                    for r in reader:
                        if len(r) > max(s_idx, r_idx) and r[r_idx].strip() == "REL-1":
                            rel1_stories.add(r[s_idx].strip())
        except Exception as e:
            errors.append(f"Помилка при читанні backlog.csv: {e}")

    fib_scale = [0, 1, 2, 3, 5, 8, 13, 21]
    fib_set = {str(x) for x in fib_scale} | {"?"}

    def round_to_fib(val):
        best_card = None
        best_diff = 999.0
        for card in fib_scale:
            diff = abs(card - val)
            if diff < best_diff:
                best_diff = diff
                best_card = card
            elif abs(diff - best_diff) < 1e-6:
                # Якщо посередині — беремо більшу
                if card > best_card:
                    best_card = card
        return best_card

    story_rounds = {}
    votes_data = {}

    # 2. Перевірка votes.csv
    if os.path.isfile(votes_path):
        try:
            with open(votes_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = ["story_id", "round", "voter", "vote"]
                if header != expected_header:
                    errors.append(f"PK-1: Неправильний заголовок votes.csv. Очікується:\n{expected_header}\nОтримано:\n{header}")
                else:
                    successes.append("PK-1: Заголовок votes.csv валідний.")

                rows = list(reader)
                for i, r in enumerate(rows, start=2):
                    if len(r) != 4:
                        errors.append(f"votes.csv рядок {i}: очікується 4 колонки, отримано {len(r)}.")
                        continue
                    sid, rnd_str, voter, vote_str = [c.strip() for c in r]
                    try:
                        rnd = int(rnd_str)
                    except ValueError:
                        errors.append(f"votes.csv рядок {i}: round '{rnd_str}' не є цілим числом.")
                        rnd = 1

                    if vote_str not in fib_set:
                        errors.append(f"PK-3: votes.csv рядок {i}: оцінка '{vote_str}' не входить до шкали Фібоначчі (0, 1, 2, 3, 5, 8, 13, 21, ?).")

                    story_rounds.setdefault(sid, set()).add(rnd)
                    votes_data.setdefault(sid, {}).setdefault(rnd, {})[voter.lower()] = vote_str

                # X-1 / PK-2: всі історії REL-1 оцінені
                evaluated_stories = set(story_rounds.keys())
                missing_stories = rel1_stories - evaluated_stories
                if missing_stories:
                    errors.append(f"X-1 / PK-2: У votes.csv відсутні історії релізу REL-1: {missing_stories}")
                else:
                    successes.append(f"X-1 / PK-2: Усі {len(rel1_stories)} історій REL-1 присутні у votes.csv.")

                # PK-4: раунд 1 містить рівно 3 голоси (optimistic <= likely <= pessimistic)
                expected_voters = {"optimistic", "likely", "pessimistic"}
                for sid, r_dict in votes_data.items():
                    if 1 not in r_dict:
                        errors.append(f"PK-4: Для історії {sid} відсутній раунд 1.")
                        continue
                    r1 = r_dict[1]
                    if set(r1.keys()) != expected_voters:
                        errors.append(f"PK-4: Історія {sid} (раунд 1) повинна мати рівно 3 виборців: optimistic, likely, pessimistic (отримано: {list(r1.keys())}).")
                    else:
                        try:
                            o = int(r1["optimistic"])
                            m = int(r1["likely"])
                            p = int(r1["pessimistic"])
                            if not (o <= m <= p):
                                errors.append(f"PK-4: Історія {sid} (раунд 1) порушує монотонність: optimistic ({o}) <= likely ({m}) <= pessimistic ({p}).")
                        except ValueError:
                            pass

                # PK-5: наявність історії з раундом 2 (Конверт 1)
                has_round_2 = any(len(r_dict) >= 2 for r_dict in votes_data.values())
                if not has_round_2:
                    errors.append("PK-5: Відсутня історія з round=2 (переоцінка за Конвертом 1).")
                else:
                    successes.append("PK-5: Присутня історія з round=2 за Конвертом 1.")

        except Exception as e:
            errors.append(f"Помилка при читанні votes.csv: {e}")

    # 3. Перевірка estimates.csv
    if os.path.isfile(estimates_path):
        try:
            with open(estimates_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = ["story_id", "final_estimate", "rounds", "spread_note"]
                if header != expected_header:
                    errors.append(f"ES-1: Неправильний заголовок estimates.csv. Очікується:\n{expected_header}\nОтримано:\n{header}")
                else:
                    successes.append("ES-1: Заголовок estimates.csv валідний.")

                rows = list(reader)
                est_stories = set()
                for i, r in enumerate(rows, start=2):
                    if len(r) != 4:
                        errors.append(f"estimates.csv рядок {i}: очікується 4 колонки, отримано {len(r)}.")
                        continue
                    sid, fest_str, rnds_str, note = [c.strip() for c in r]
                    est_stories.add(sid)

                    try:
                        fest = int(fest_str)
                    except ValueError:
                        errors.append(f"ES-5: estimates.csv рядок {i}: final_estimate '{fest_str}' не є цілим числом.")
                        fest = None

                    try:
                        rnds = int(rnds_str)
                    except ValueError:
                        errors.append(f"ES-1: estimates.csv рядок {i}: rounds '{rnds_str}' не є цілим числом.")
                        rnds = 1

                    if sid in votes_data:
                        actual_max_round = max(votes_data[sid].keys())
                        if rnds != actual_max_round:
                            errors.append(f"ES-1: Для {sid} значення rounds={rnds} не відповідає максимальному раунду з votes.csv ({actual_max_round}).")

                        # Розрахунок PERT за останнім раундом
                        last_r = votes_data[sid][actual_max_round]
                        if all(k in last_r and last_r[k] in fib_set and last_r[k] != "?" for k in ["optimistic", "likely", "pessimistic"]):
                            o = int(last_r["optimistic"])
                            m = int(last_r["likely"])
                            p = int(last_r["pessimistic"])
                            pert = (o + 4.0 * m + p) / 6.0
                            expected_fib = round_to_fib(pert)

                            if fest is not None and fest != expected_fib:
                                errors.append(f"ES-4: Для {sid} final_estimate={fest} не відповідає PERT-округленню до шкали Фібоначчі {expected_fib} (PERT={pert:.3f}).")

                            # Перевірка ширини розкиду
                            if o in fib_scale and p in fib_scale:
                                idx_o = fib_scale.index(o)
                                idx_p = fib_scale.index(p)
                                # 2 або більше проміжних карток означає різницю індексів >= 3
                                if (idx_p - idx_o >= 3 or actual_max_round >= 2) and not note:
                                    errors.append(f"ES-6: Для історії {sid} обов'язково має бути заповнено spread_note (широкий розкид або переоцінка Конверта 1).")

                # ES-3: рівно по одному рядку на кожну історію з votes.csv
                if est_stories != set(votes_data.keys()):
                    errors.append(f"ES-3: Історії в estimates.csv {est_stories} не збігаються з історіями у votes.csv {set(votes_data.keys())}.")
                else:
                    successes.append(f"ES-3: estimates.csv містить рівно по одному рядку на кожну історію з votes.csv ({len(est_stories)} історій).")

        except Exception as e:
            errors.append(f"Помилка при читанні estimates.csv: {e}")

    # 4. Перевірка README.md
    if os.path.isfile(readme_path):
        try:
            with open(readme_path, mode="r", encoding="utf-8") as f:
                content = f.read()

            required_sections = [
                "1. Формат і масштаб",
                "2. Історії з найбільшим розкидом",
                "3. Конверт 1: переоцінка після нової інформації",
                "4. Сума першого релізу проти ємності варіанта",
                "5. Конверт 2: відповідь замовнику про години",
                "6. Історії з карткою «не розумію»",
                "7. Що я зрозумів про свій беклог"
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

            placeholders = re.findall(r"<[^>\n]{2,}>", content)
            real_placeholders = [p for p in placeholders if not re.match(r"^<(https?://|!--|/?[a-z1-6]+>?)", p, re.IGNORECASE)]
            if real_placeholders:
                errors.append(f"README.md: Виявлено невидалені плейсхолдери у кутових дужках: {real_placeholders[:3]}")
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


def validate_forecast(target_dir):
    errors = []
    warnings = []
    successes = []

    if not os.path.isdir(target_dir):
        print(f"ERROR: Директорія '{target_dir}' не знайдена.")
        return 1

    readme_path = os.path.join(target_dir, "README.md")
    velocity_path = os.path.join(target_dir, "velocity.csv")
    forecast_path = os.path.join(target_dir, "forecast.csv")
    simulate_path = os.path.join(target_dir, "simulate.py")

    for p, name in [(readme_path, "README.md"), (velocity_path, "velocity.csv"), (forecast_path, "forecast.csv"), (simulate_path, "simulate.py")]:
        if not os.path.isfile(p):
            errors.append(f"Файл {p} не знайдено.")
        else:
            successes.append(f"Файл {name} знайдено в {target_dir}")

    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    # 1. Перевірка velocity.csv
    sprints_info = []
    if os.path.isfile(velocity_path):
        try:
            with open(velocity_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = ["sprint", "start_date", "end_date", "points_committed", "points_done"]
                if header != expected_header:
                    errors.append(f"VL-1: Неправильний заголовок velocity.csv. Очікується:\n{expected_header}\nОтримано:\n{header}")
                else:
                    successes.append("VL-1: Заголовок velocity.csv валідний.")

                rows = list(reader)
                if len(rows) != 2:
                    errors.append(f"VL-2: velocity.csv повинен містити рівно 2 рядки (знайдено {len(rows)}).")
                else:
                    successes.append("VL-2: velocity.csv містить рівно 2 спринти.")

                for i, r in enumerate(rows, start=2):
                    if len(r) != 5:
                        errors.append(f"velocity.csv рядок {i}: очікується 5 колонок, отримано {len(r)}.")
                        continue
                    sp_str, sdate_str, edate_str, comm_str, done_str = [c.strip() for c in r]
                    if not (date_regex.match(sdate_str) and date_regex.match(edate_str)):
                        errors.append(f"VL-1 рядок {i}: дати мають бути у форматі YYYY-MM-DD ({sdate_str}, {edate_str}).")
                        continue

                    sdate = datetime.strptime(sdate_str, "%Y-%m-%d").date()
                    edate = datetime.strptime(edate_str, "%Y-%m-%d").date()

                    if edate <= sdate:
                        errors.append(f"VL-1 рядок {i}: end_date ({edate}) має бути пізнішою за start_date ({sdate}).")
                    else:
                        successes.append(f"VL-1 рядок {i}: end_date > start_date ({sdate} -> {edate}).")

                    diff_days = (edate - sdate).days
                    if diff_days not in [11, 12, 13, 14]:
                        warnings.append(f"VL-4 рядок {i}: тривалість спринта становить {diff_days} днів (очікується 11–14 днів для 2-тижневого спринта).")
                    else:
                        successes.append(f"VL-4 рядок {i}: тривалість спринта коректна ({diff_days} дн).")

                    try:
                        comm = int(comm_str)
                        done = int(done_str)
                        if comm <= 0 or done <= 0:
                            errors.append(f"velocity.csv рядок {i}: points_committed та points_done мають бути додатними числами.")
                    except ValueError:
                        errors.append(f"velocity.csv рядок {i}: points_committed або points_done не є цілим числом.")

                    sprints_info.append({"sprint": sp_str, "start": sdate, "end": edate, "committed": comm_str, "done": done_str})

                if len(sprints_info) == 2:
                    if sprints_info[1]["start"] < sprints_info[0]["end"]:
                        errors.append(f"VL-3: Спринти перекриваються: початок спринта 2 ({sprints_info[1]['start']}) раніше за кінець спринта 1 ({sprints_info[0]['end']}).")
                    else:
                        successes.append("VL-3: Спринти хронологічно послідовні і не перекриваються.")

        except Exception as e:
            errors.append(f"Помилка при читанні velocity.csv: {e}")

    # Отримання суми final_estimate для REL-1 з lr08_poker/estimates.csv
    rel1_sum_estimates = None
    estimates_path = os.path.join("lr08_poker", "estimates.csv")
    if os.path.isfile(estimates_path):
        try:
            with open(estimates_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header and "story_id" in header and "final_estimate" in header:
                    f_idx = header.index("final_estimate")
                    s_idx = header.index("story_id")
                    pts_sum = 0
                    for r in reader:
                        if len(r) > f_idx:
                            try:
                                pts_sum += int(r[f_idx].strip())
                            except ValueError:
                                pass
                    rel1_sum_estimates = pts_sum
        except Exception as e:
            errors.append(f"Помилка при читанні estimates.csv: {e}")

    # 2. Перевірка forecast.csv
    if os.path.isfile(forecast_path):
        try:
            with open(forecast_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = ["scenario", "remaining_points", "simulations", "p50_sprints", "p85_sprints", "p50_date", "p85_date"]
                if header != expected_header:
                    errors.append(f"FC-1: Неправильний заголовок forecast.csv. Очікується:\n{expected_header}\nОтримано:\n{header}")
                else:
                    successes.append("FC-1: Заголовок forecast.csv валідний.")

                rows = list(reader)
                if len(rows) < 2:
                    errors.append(f"forecast.csv: має містити щонайменше 2 сценарії (знайдено {len(rows)}).")
                else:
                    successes.append(f"forecast.csv: знайдено {len(rows)} сценарії (>= 2).")

                for i, r in enumerate(rows, start=2):
                    if len(r) != 7:
                        errors.append(f"forecast.csv рядок {i}: очікується 7 колонок, отримано {len(r)}.")
                        continue
                    scen, rem_str, sim_str, p50_s_str, p85_s_str, p50_d_str, p85_d_str = [c.strip() for c in r]

                    try:
                        rem = int(rem_str)
                    except ValueError:
                        errors.append(f"forecast.csv рядок {i}: remaining_points '{rem_str}' не є цілим числом.")
                        rem = 0

                    try:
                        sims = int(sim_str)
                        if sims < 10000:
                            warnings.append(f"forecast.csv рядок {i}: кількість симуляцій {sims} < 10000 (рекомендовано >= 10000).")
                    except ValueError:
                        errors.append(f"forecast.csv рядок {i}: simulations '{sim_str}' не є числом.")

                    try:
                        p50_s = int(p50_s_str)
                        p85_s = int(p85_s_str)
                        if p85_s < p50_s:
                            errors.append(f"FC-1 рядок {i}: p85_sprints ({p85_s}) має бути >= p50_sprints ({p50_s}).")
                        else:
                            successes.append(f"FC-1 рядок {i}: p85_sprints ({p85_s}) >= p50_sprints ({p50_s}).")
                    except ValueError:
                        errors.append(f"forecast.csv рядок {i}: p50_sprints або p85_sprints не є цілим числом.")
                        p50_s, p85_s = 0, 0

                    if not (date_regex.match(p50_d_str) and date_regex.match(p85_d_str)):
                        errors.append(f"FC-3 рядок {i}: дати прогнозу мають бути у форматі YYYY-MM-DD ({p50_d_str}, {p85_d_str}).")
                    else:
                        p50_d = datetime.strptime(p50_d_str, "%Y-%m-%d").date()
                        p85_d = datetime.strptime(p85_d_str, "%Y-%m-%d").date()

                        # FC-3: різниця дат точно дорівнює (p85_sprints - p50_sprints) * 14 днів
                        expected_diff_days = (p85_s - p50_s) * 14
                        actual_diff_days = (p85_d - p50_d).days
                        if actual_diff_days != expected_diff_days:
                            errors.append(f"FC-3 рядок {i}: різниця між p85_date та p50_date ({actual_diff_days} дн) != (p85_sprints - p50_sprints) * 14 ({expected_diff_days} дн).")
                        else:
                            successes.append(f"FC-3 рядок {i}: дати точно відповідають формулі сплайну спринтів (різниця: {actual_diff_days} дн).")

                    # FC-2 / X-3: для сценарію 'Весь перший реліз' remaining_points = сума з estimates.csv
                    if "весь" in scen.lower() or "перший" in scen.lower():
                        if rel1_sum_estimates is not None and rem != rel1_sum_estimates:
                            errors.append(f"FC-2 / X-3: Для сценарію '{scen}' remaining_points ({rem}) != сумі estimates.csv для REL-1 ({rel1_sum_estimates}).")
                        else:
                            successes.append(f"FC-2 / X-3: remaining_points першого сценарію ({rem}) точно відповідає сумі estimates.csv.")

        except Exception as e:
            errors.append(f"Помилка при читанні forecast.csv: {e}")

    # 3. Перевірка README.md
    if os.path.isfile(readme_path):
        try:
            with open(readme_path, mode="r", encoding="utf-8") as f:
                content = f.read()

            required_sections = [
                "1. Звідки взялася velocity",
                "2. Як рахувалася симуляція",
                "3. Дві дати першого релізу",
                "4. Прогноз проти критичного шляху з ЛР7",
                "5. Чого вартий прогноз на моїх даних",
                "6. Що я кажу замовнику"
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

            placeholders = re.findall(r"<[^>\n]{2,}>", content)
            real_placeholders = [p for p in placeholders if not re.match(r"^<(https?://|!--|/?[a-z1-6]+>?)", p, re.IGNORECASE)]
            if real_placeholders:
                errors.append(f"README.md: Виявлено невидалені плейсхолдери у кутових дужках: {real_placeholders[:3]}")
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


def validate_review(target_dir):
    errors = []
    warnings = []
    successes = []

    if not os.path.isdir(target_dir):
        print(f"ERROR: Директорія '{target_dir}' не знайдена.")
        return 1

    review_path = os.path.join(target_dir, "review.md")
    readme_path = os.path.join(target_dir, "README.md")

    # 1. Перевірка наявності файлів
    if not os.path.isfile(review_path):
        errors.append(f"Файл {review_path} не знайдено.")
    else:
        successes.append(f"Файл review.md знайдено в {target_dir}")

    if not os.path.isfile(readme_path):
        errors.append(f"Файл {readme_path} не знайдено.")
    else:
        successes.append(f"Файл README.md знайдено в {target_dir}")

    # 2. Перевірка review.md
    if os.path.isfile(review_path):
        try:
            with open(review_path, mode="r", encoding="utf-8") as f:
                r_content = f.read()

            required_sections = [
                "## 1. Механіка",
                "## 2. Наскрізність",
                "## 3. Три зауваження",
                "## 4. Знахідка",
                "## 5. Чого в портфелі ще немає"
            ]

            last_pos = -1
            order_ok = True
            for sec in required_sections:
                pos = r_content.find(sec)
                if pos == -1:
                    errors.append(f"review.md: Відсутній обов'язковий розділ '{sec}'.")
                else:
                    if pos < last_pos:
                        order_ok = False
                    last_pos = pos

            if order_ok:
                successes.append("review.md: Усі 5 обов'язкових розділів присутні у правильному порядку.")
            else:
                errors.append("review.md: Розділи розташовані не у правильному порядку.")

            if "рецензент" not in r_content.lower() or "arsenii" not in r_content.lower():
                errors.append("review.md: Метадані не містять посилання на рецензента (GitHub логін).")
            else:
                successes.append("review.md: Метадані містять рецензента.")

            if "student-" not in r_content and "next" not in r_content:
                warnings.append("review.md: Бажано зазначити GitHub логін автора (n+1) у метаданих.")
            else:
                successes.append("review.md: Метадані містять логін автора.")

            rem_count = len(re.findall(r"###\s*Зауваження\s*\d+", r_content, re.IGNORECASE))
            if rem_count < 3:
                rem_count_alt = len(re.findall(r"(?:REM-\d+|Зауваження\s*\d+)", r_content, re.IGNORECASE))
                if rem_count_alt >= 3:
                    successes.append(f"review.md: Знайдено щонайменше 3 зауваження ({rem_count_alt}).")
                else:
                    errors.append(f"review.md: Розділ 3 повинен містити щонайменше 3 зауваження (знайдено {rem_count}).")
            else:
                successes.append(f"review.md: Знайдено {rem_count} окремих зауважень (>= 3).")

            if "рядок" not in r_content.lower() and "line" not in r_content.lower():
                warnings.append("review.md: Рекомендується вказувати точні номери рядків у зауваженнях.")
            else:
                successes.append("review.md: Зауваження містять посилання на рядки артефактів.")

            placeholders = re.findall(r"<[^>\n]{2,}>", r_content)
            real_placeholders = [p for p in placeholders if not re.match(r"^<(https?://|!--|/?[a-z1-6]+>?)", p, re.IGNORECASE)]
            if real_placeholders:
                errors.append(f"review.md: Виявлено невидалені плейсхолдери у кутових дужках: {real_placeholders[:3]}")
            else:
                successes.append("review.md: Плейсхолдери у кутових дужках відсутні.")

        except Exception as e:
            errors.append(f"Помилка при читанні review.md: {e}")

    # 3. Перевірка README.md
    if os.path.isfile(readme_path):
        try:
            with open(readme_path, mode="r", encoding="utf-8") as f:
                rm_content = f.read()

            required_readme_sections = [
                "Рішення по зауваженнях",
                "Що я забрав із чужого портфеля",
                "Що я перевірю сам перед захистом"
            ]

            for sec in required_readme_sections:
                if sec not in rm_content:
                    errors.append(f"README.md: Відсутній обов'язковий розділ '{sec}'.")
                else:
                    successes.append(f"README.md: Знайдено обов'язковий розділ '{sec}'.")

            if "REM-" not in rm_content and "Accept" not in rm_content and "Reject" not in rm_content:
                warnings.append("README.md: Таблиця рішень бажано має містити вердикти Accept / Reject / Modify.")
            else:
                successes.append("README.md: Таблиця рішень містить вердикти.")

            placeholders = re.findall(r"<[^>\n]{2,}>", rm_content)
            real_placeholders = [p for p in placeholders if not re.match(r"^<(https?://|!--|/?[a-z1-6]+>?)", p, re.IGNORECASE)]
            if real_placeholders:
                errors.append(f"README.md: Виявлено невидалені плейсхолдери у кутових дужках: {real_placeholders[:3]}")
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


def validate_risks_quality(target_dir):
    errors = []
    warnings = []
    successes = []

    if not os.path.isdir(target_dir):
        print(f"ERROR: Директорія '{target_dir}' не знайдена.")
        return 1

    risks_path = os.path.join(target_dir, "risks.csv")
    techdebt_path = os.path.join(target_dir, "techdebt.csv")
    changelog_path = os.path.join(target_dir, "changelog.csv")
    dod_path = os.path.join(target_dir, "dod.md")
    readme_path = os.path.join(target_dir, "README.md")

    # 1. Перевірка наявності файлів
    for p, name in [
        (risks_path, "risks.csv"),
        (techdebt_path, "techdebt.csv"),
        (changelog_path, "changelog.csv"),
        (dod_path, "dod.md"),
        (readme_path, "README.md")
    ]:
        if not os.path.isfile(p):
            errors.append(f"Файл {p} не знайдено.")
        else:
            successes.append(f"Файл {name} знайдено в {target_dir}")

    # Отримання списку історій із беклогу для перевірки X-1
    existing_story_ids = set()
    backlog_path = os.path.join("lr06_backlog", "backlog.csv")
    if os.path.isfile(backlog_path):
        try:
            with open(backlog_path, mode="r", encoding="utf-8") as f:
                r = csv.reader(f)
                next(r, None)
                for row in r:
                    if row:
                        existing_story_ids.add(row[0].strip())
        except Exception:
            pass

    # 2. Перевірка risks.csv
    if os.path.isfile(risks_path):
        try:
            with open(risks_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = [
                    "risk_id", "category", "cause", "event", "consequence",
                    "probability", "impact", "score", "strategy", "owner",
                    "trigger", "response_plan", "status", "review_date",
                    "previous_score", "review_note", "related_story_ids"
                ]
                if header != expected_header:
                    errors.append(f"RK-1: Неправильний заголовок risks.csv. Очікується:\n{expected_header}\nОтримано:\n{header}")
                else:
                    successes.append("RK-1: Заголовок risks.csv валідний.")

                rows = list(reader)
                if len(rows) < 6:
                    errors.append(f"RK-1: risks.csv має містити щонайменше 6 ризиків (знайдено {len(rows)}).")
                else:
                    successes.append(f"RK-1: Знайдено {len(rows)} ризиків (>= 6).")

                categories = set()
                changed_scores_count = 0
                has_course_event_risk = False
                valid_strategies = {"avoid", "mitigate", "transfer", "accept", "escalate"}

                for i, r in enumerate(rows, start=2):
                    if len(r) != 17:
                        errors.append(f"risks.csv рядок {i}: очікується 17 колонок, отримано {len(r)}.")
                        continue

                    (rid, cat, cause, event, cons, prob_s, imp_s, score_s,
                     strat, owner, trig, resp_plan, status, rdate, prev_score_s,
                     rnote, rel_stories) = [c.strip() for c in r]

                    categories.add(cat)

                    # RK-1: probability, impact, score
                    try:
                        p_val = int(prob_s)
                        i_val = int(imp_s)
                        s_val = int(score_s)
                        if not (1 <= p_val <= 5) or not (1 <= i_val <= 5):
                            errors.append(f"RK-1 рядок {i}: probability ({p_val}) та impact ({i_val}) мають бути в діапазоні 1..5.")
                        if s_val != p_val * i_val:
                            errors.append(f"RK-1 рядок {i}: score ({s_val}) != probability * impact ({p_val * i_val}).")
                    except ValueError:
                        errors.append(f"RK-1 рядок {i}: probability, impact або score не є цілими числами.")
                        s_val = 0

                    # RK-3: owner
                    if owner.lower() in ["команда", "всі", "all", "team"]:
                        errors.append(f"RK-3 рядок {i}: owner не може бути абстрактним ('{owner}').")

                    # strategy
                    if strat.lower() not in valid_strategies:
                        errors.append(f"RK-1 рядок {i}: невідома стратегія '{strat}' (очікується {valid_strategies}).")

                    # RK-4: план для червоної зони (score >= 15)
                    if s_val >= 15:
                        resp_lower = resp_plan.lower()
                        if "крок 1" not in resp_lower and "step 1" not in resp_lower:
                            errors.append(f"RK-4 рядок {i} ({rid}): для ризику червоної зони (score={s_val}) план має бути покроковим ('Крок 1 ...').")

                    # RK-5, RK-6, X-15: review_date, previous_score, review_note
                    if rdate != "2026-11-12":
                        errors.append(f"X-15 рядок {i}: review_date '{rdate}' має бути '2026-11-12'.")

                    if prev_score_s:
                        try:
                            prev_val = int(prev_score_s)
                            if prev_val != s_val:
                                if not rnote:
                                    errors.append(f"RK-6 рядок {i} ({rid}): змінено оцінку (було {prev_val}, стало {s_val}), але review_note порожній.")
                                else:
                                    changed_scores_count += 1
                        except ValueError:
                            errors.append(f"risks.csv рядок {i}: previous_score '{prev_score_s}' не є числом.")

                    # X-1: зв'язок з беклогом
                    story_refs = [s.strip() for s in rel_stories.split(";") if s.strip()]
                    if not story_refs:
                        warnings.append(f"risks.csv рядок {i} ({rid}): бажано вказати related_story_ids.")
                    else:
                        for sref in story_refs:
                            if existing_story_ids and sref not in existing_story_ids:
                                errors.append(f"X-1 рядок {i} ({rid}): історія '{sref}' відсутня у беклозі.")

                    if rid == "R-01" or "безпек" in cause.lower() or "oauth" in event.lower() or "персональн" in cause.lower():
                        has_course_event_risk = True

                expected_cats = {"technical", "external", "organizational", "project_management"}
                if not expected_cats.issubset(categories):
                    errors.append(f"RK-2: Мають бути представлені всі 4 категорії ризиків. Відсутні: {expected_cats - categories}")
                else:
                    successes.append("RK-2: Усі 4 обов'язкові категорії ризиків присутні.")

                if changed_scores_count < 2:
                    errors.append(f"RK-5: Щонайменше для 2 ризиків має бути зафіксована зміна score (знайдено {changed_scores_count}).")
                else:
                    successes.append(f"RK-5: Знайдено {changed_scores_count} ризиків зі зміненими оцінками та заповненими review_note (>= 2).")

                if not has_course_event_risk:
                    warnings.append("RK-1: Бажано явно вказати ризик, породжений подією курсу (R-01 про вимоги безпеки).")
                else:
                    successes.append("RK-1: Присутній ризик, породжений подією курсу.")

        except Exception as e:
            errors.append(f"Помилка при читанні risks.csv: {e}")

    # 3. Перевірка techdebt.csv
    if os.path.isfile(techdebt_path):
        try:
            with open(techdebt_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = [
                    "debt_id", "area", "description", "type", "origin",
                    "impact", "effort_hours", "decision", "plan", "owner", "due_sprint"
                ]
                if header != expected_header:
                    errors.append(f"TD-1: Неправильний заголовок techdebt.csv. Очікується:\n{expected_header}\nОтримано:\n{header}")
                else:
                    successes.append("TD-1: Заголовок techdebt.csv валідний.")

                rows = list(reader)
                if len(rows) < 3:
                    errors.append(f"TD-1: techdebt.csv має містити щонайменше 3 записи (знайдено {len(rows)}).")
                else:
                    successes.append(f"TD-1: Знайдено {len(rows)} записів технічного боргу (>= 3).")

                has_deliberate_prudent = False
                for i, r in enumerate(rows, start=2):
                    if len(r) != 11:
                        errors.append(f"techdebt.csv рядок {i}: очікується 11 колонок, отримано {len(r)}.")
                        continue
                    did, area, desc, dtype, origin, impact, effort_s, decision, plan, owner, due_sprint = [c.strip() for c in r]

                    if dtype == "deliberate_prudent":
                        has_deliberate_prudent = True

                    try:
                        eff_val = float(effort_s)
                        if eff_val <= 0:
                            errors.append(f"techdebt.csv рядок {i}: effort_hours має бути > 0 (отримано {eff_val}).")
                    except ValueError:
                        errors.append(f"techdebt.csv рядок {i}: effort_hours '{effort_s}' не є числом.")

                    # TD-2: для pay_now та pay_later обов'язковий due_sprint, для accept - суворо порожній
                    dec_lower = decision.lower()
                    if dec_lower in ["pay_now", "pay_later"]:
                        if not due_sprint:
                            errors.append(f"TD-2 рядок {i} ({did}): для рішення '{decision}' поле due_sprint має містити номер спринта.")
                    elif dec_lower == "accept":
                        if due_sprint:
                            errors.append(f"TD-2 рядок {i} ({did}): для рішення 'accept' поле due_sprint має бути порожнім (знайдено '{due_sprint}').")

                if not has_deliberate_prudent:
                    errors.append("TD-1: Потрібен щонайменше один запис типу 'deliberate_prudent'.")
                else:
                    successes.append("TD-1: Присутній запис технічного боргу типу 'deliberate_prudent'.")

        except Exception as e:
            errors.append(f"Помилка при читанні techdebt.csv: {e}")

    # 4. Перевірка changelog.csv
    if os.path.isfile(changelog_path):
        try:
            with open(changelog_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = [
                    "change_id", "date", "source", "description",
                    "story_ids", "points_delta", "decision", "rationale", "affected_files"
                ]
                if header != expected_header:
                    errors.append(f"CH-1: Неправильний заголовок changelog.csv. Очікується:\n{expected_header}\nОтримано:\n{header}")
                else:
                    successes.append("CH-1: Заголовок changelog.csv валідний.")

                rows = list(reader)
                has_course_event_row = False
                for i, r in enumerate(rows, start=2):
                    if len(r) != 9:
                        errors.append(f"changelog.csv рядок {i}: очікується 9 колонок, отримано {len(r)}.")
                        continue
                    cid, cdate, source, desc, sids, pdelta_s, decision, rationale, aff_files = [c.strip() for c in r]

                    if source == "course_event" or cid == "CH-01":
                        has_course_event_row = True

                    try:
                        int(pdelta_s)
                    except ValueError:
                        errors.append(f"CH-2 рядок {i}: points_delta '{pdelta_s}' не є цілим числом.")

                    if not aff_files:
                        errors.append(f"CH-3 рядок {i}: affected_files не може бути порожнім.")

                if not has_course_event_row:
                    errors.append("CH-1: Відсутній обов'язковий рядок події курсу (source='course_event' або change_id='CH-01').")
                else:
                    successes.append("CH-1: Присутній обов'язковий рядок події курсу (CH-01).")

        except Exception as e:
            errors.append(f"Помилка при читанні changelog.csv: {e}")

    # 5. Перевірка dod.md
    if os.path.isfile(dod_path):
        try:
            with open(dod_path, mode="r", encoding="utf-8") as f:
                dod_content = f.read()

            required_dod_sections = [
                "1. Умови, за яких історія вважається завершеною",
                "2. Чого DoD свідомо не вимагає",
                "3. Як це працює на практиці",
                "4. Хто ухвалює відхилення від DoD"
            ]

            last_pos = -1
            order_ok = True
            for sec in required_dod_sections:
                pos = dod_content.find(sec)
                if pos == -1:
                    errors.append(f"dod.md: Відсутній обов'язковий розділ '{sec}'.")
                else:
                    if pos < last_pos:
                        order_ok = False
                    last_pos = pos

            if order_ok:
                successes.append("dod.md: Усі 4 обов'язкові розділи присутні у правильному порядку.")
            else:
                errors.append("dod.md: Розділи розташовані не у правильному порядку.")

            placeholders = re.findall(r"<[^>\n]{2,}>", dod_content)
            real_placeholders = [p for p in placeholders if not re.match(r"^<(https?://|!--|/?[a-z1-6]+>?)", p, re.IGNORECASE)]
            if real_placeholders:
                errors.append(f"dod.md: Виявлено невидалені плейсхолдери у кутових дужках: {real_placeholders[:3]}")
            else:
                successes.append("dod.md: Плейсхолдери у кутових дужках відсутні.")

        except Exception as e:
            errors.append(f"Помилка при читанні dod.md: {e}")

    # 6. Перевірка README.md
    if os.path.isfile(readme_path):
        try:
            with open(readme_path, mode="r", encoding="utf-8") as f:
                rm_content = f.read()

            required_rm_sections = [
                "1. Звідки взялися ризики",
                "2. Перегляд реєстру",
                "3. Definition of Done",
                "4. Технічний борг",
                "5. Подія курсу",
                "6. Журнал змін"
            ]

            last_pos = -1
            order_ok = True
            for sec in required_rm_sections:
                pos = rm_content.find(sec)
                if pos == -1:
                    errors.append(f"README.md: Відсутній обов'язковий розділ '{sec}'.")
                else:
                    if pos < last_pos:
                        order_ok = False
                    last_pos = pos

            if order_ok:
                successes.append("README.md: Усі 6 обов'язкових розділів присутні у правильному порядку.")
            else:
                errors.append("README.md: Розділи розташовані не у правильному порядку.")

            placeholders = re.findall(r"<[^>\n]{2,}>", rm_content)
            real_placeholders = [p for p in placeholders if not re.match(r"^<(https?://|!--|/?[a-z1-6]+>?)", p, re.IGNORECASE)]
            if real_placeholders:
                errors.append(f"README.md: Виявлено невидалені плейсхолдери у кутових дужках: {real_placeholders[:3]}")
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


def validate_communication(target_dir):
    errors = []
    warnings = []
    successes = []

    if not os.path.isdir(target_dir):
        print(f"ERROR: Директорія '{target_dir}' не знайдена.")
        return 1

    raci_path = os.path.join(target_dir, "raci.csv")
    comm_path = os.path.join(target_dir, "communication.csv")
    readme_path = os.path.join(target_dir, "README.md")

    # 1. Наявність файлів
    for p, name in [(raci_path, "raci.csv"), (comm_path, "communication.csv"), (readme_path, "README.md")]:
        if not os.path.isfile(p):
            errors.append(f"Файл {p} не знайдено.")
        else:
            successes.append(f"Файл {name} знайдено в {target_dir}")

    # Завантаження стейкхолдерів (X-2, CM-1)
    valid_stakeholders = set()
    important_stakeholders = set()
    stakeholders_path = os.path.join("lr05_charter", "stakeholders.csv")
    if os.path.isfile(stakeholders_path):
        try:
            with open(stakeholders_path, mode="r", encoding="utf-8") as f:
                r = csv.reader(f)
                next(r, None)
                for row in r:
                    if len(row) >= 7:
                        sid = row[0].strip()
                        strat = row[6].strip().lower()
                        valid_stakeholders.add(sid)
                        if strat in ["manage_closely", "keep_satisfied"]:
                            important_stakeholders.add(sid)
        except Exception:
            pass

    # Завантаження WBS вузлів (RC-7)
    valid_wbs_ids = set()
    wbs_path = os.path.join("lr07_wbs", "wbs.csv")
    if os.path.isfile(wbs_path):
        try:
            with open(wbs_path, mode="r", encoding="utf-8") as f:
                r = csv.reader(f)
                next(r, None)
                for row in r:
                    if row:
                        valid_wbs_ids.add(row[0].strip())
        except Exception:
            pass

    # 2. Перевірка raci.csv
    if os.path.isfile(raci_path):
        try:
            with open(raci_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = ["activity_id", "activity", "wbs_id", "stakeholder_id", "role"]
                if header != expected_header:
                    errors.append(f"RC-1: Неправильний заголовок raci.csv. Очікується:\n{expected_header}\nОтримано:\n{header}")
                else:
                    successes.append("RC-1: Заголовок raci.csv валідний.")

                rows = list(reader)
                if len(rows) < 18:
                    errors.append(f"RC-1: raci.csv має містити щонайменше 18 рядків (знайдено {len(rows)}).")
                else:
                    successes.append(f"RC-1: Знайдено {len(rows)} рядків у raci.csv (>= 18).")

                allowed_roles = {"R", "A", "AR", "C", "I"}
                activities = {}

                for i, r in enumerate(rows, start=2):
                    if len(r) != 5:
                        errors.append(f"raci.csv рядок {i}: очікується 5 колонок, отримано {len(r)}.")
                        continue
                    aid, act_name, wid, sid, role = [c.strip() for c in r]

                    if role not in allowed_roles:
                        errors.append(f"RC-1 рядок {i}: невідома роль '{role}' (допустимо {allowed_roles}).")

                    if valid_stakeholders and sid not in valid_stakeholders:
                        errors.append(f"X-2 рядок {i}: stakeholder_id '{sid}' відсутній у lr05_charter/stakeholders.csv.")

                    activities.setdefault(aid, []).append({
                        "row": i, "activity": act_name, "wbs_id": wid, "sid": sid, "role": role
                    })

                if len(activities) < 6:
                    errors.append(f"RC-1: Потрібно щонайменше 6 активностей у RACI (знайдено {len(activities)}).")
                else:
                    successes.append(f"RC-1: Знайдено {len(activities)} активностей (>= 6).")

                wbs_activities_count = 0
                non_wbs_activities_count = 0
                accountable_owners = set()

                for aid, items in activities.items():
                    act_texts = {it["activity"] for it in items}
                    wbs_vals = {it["wbs_id"] for it in items}

                    # RC-4, RC-6
                    if len(act_texts) > 1:
                        errors.append(f"RC-4 ({aid}): текст activity має бути однаковим в усіх рядках активності.")
                    if len(wbs_vals) > 1:
                        errors.append(f"RC-6 ({aid}): значення wbs_id має бути однаковим в усіх рядках активності.")

                    wid = next(iter(wbs_vals))
                    if wid:
                        wbs_activities_count += 1
                        if valid_wbs_ids and wid not in valid_wbs_ids:
                            errors.append(f"RC-7 ({aid}): wbs_id '{wid}' не існує у lr07_wbs/wbs.csv.")
                    else:
                        non_wbs_activities_count += 1

                    # RC-2, RC-3
                    a_count = sum(1 for it in items if it["role"] in ("A", "AR"))
                    r_count = sum(1 for it in items if it["role"] in ("R", "AR"))

                    if a_count != 1:
                        errors.append(f"RC-2 ({aid}): має бути рівно 1 роль A/AR (знайдено {a_count}).")
                    if r_count < 1:
                        errors.append(f"RC-3 ({aid}): має бути щонайменше 1 роль R/AR (знайдено {r_count}).")

                    for it in items:
                        if it["role"] in ("A", "AR"):
                            accountable_owners.add(it["sid"])

                if wbs_activities_count < 4:
                    errors.append(f"RC-7: Щонайменше 4 активності мають посилатися на WBS (знайдено {wbs_activities_count}).")
                else:
                    successes.append(f"RC-7: {wbs_activities_count} активностей пов'язано з вузлами WBS (>= 4).")

                if non_wbs_activities_count < 2:
                    errors.append(f"RC-9: Щонайменше 2 активності мають бути рішеннями поза WBS із порожнім wbs_id (знайдено {non_wbs_activities_count}).")
                else:
                    successes.append(f"RC-9: {non_wbs_activities_count} управлінські активності поза WBS (>= 2).")

                if len(accountable_owners) < 2:
                    errors.append(f"RC-8: Роль A/AR має належати щонайменше 2 різним стейкхолдерам (знайдено {accountable_owners}).")
                else:
                    successes.append(f"RC-8: Роль A/AR розподілена між {len(accountable_owners)} різними сторонами ({sorted(accountable_owners)}).")

        except Exception as e:
            errors.append(f"Помилка при читанні raci.csv: {e}")

    # 3. Перевірка communication.csv
    if os.path.isfile(comm_path):
        try:
            with open(comm_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = ["item_id", "stakeholder_id", "message", "channel", "frequency", "format", "owner"]
                if header != expected_header:
                    errors.append(f"CM-1: Неправильний заголовок communication.csv. Очікується:\n{expected_header}\nОтримано:\n{header}")
                else:
                    successes.append("CM-1: Заголовок communication.csv валідний.")

                rows = list(reader)
                if len(rows) < 5:
                    errors.append(f"CM-1: communication.csv має містити щонайменше 5 рядків (знайдено {len(rows)}).")
                else:
                    successes.append(f"CM-1: Знайдено {len(rows)} записів у communication.csv (>= 5).")

                allowed_channels = {"email", "meeting", "chat", "report", "demo", "call"}
                allowed_freqs = {"daily", "weekly", "biweekly", "monthly", "on_event"}
                allowed_formats = {"written", "verbal", "dashboard", "presentation"}

                covered_stakeholders = set()
                has_on_event = False
                has_regular = False

                for i, r in enumerate(rows, start=2):
                    if len(r) != 7:
                        errors.append(f"communication.csv рядок {i}: очікується 7 колонок, отримано {len(r)}.")
                        continue
                    cid, sid, msg, ch, freq, fmt, owner = [c.strip() for c in r]

                    if valid_stakeholders and sid not in valid_stakeholders:
                        errors.append(f"X-2 рядок {i}: stakeholder_id '{sid}' відсутній у lr05_charter/stakeholders.csv.")
                    covered_stakeholders.add(sid)

                    if ch not in allowed_channels:
                        errors.append(f"communication.csv рядок {i}: невідомий channel '{ch}'.")
                    if freq not in allowed_freqs:
                        errors.append(f"communication.csv рядок {i}: невідома frequency '{freq}'.")
                    if fmt not in allowed_formats:
                        errors.append(f"communication.csv рядок {i}: невідомий format '{fmt}'.")

                    if freq == "on_event":
                        has_on_event = True
                    if freq in ("weekly", "biweekly"):
                        has_regular = True

                missing_imp = important_stakeholders - covered_stakeholders
                if missing_imp:
                    errors.append(f"CM-1: Важливі стейкхолдери (manage_closely / keep_satisfied) без запису в communication.csv: {missing_imp}")
                else:
                    successes.append(f"CM-1: Усі важливі стейкхолдери {sorted(important_stakeholders)} покриті планом комунікацій.")

                if not has_on_event:
                    errors.append("CM-2: Відсутній щонайменше один запис із frequency='on_event'.")
                else:
                    successes.append("CM-2: Присутні подієві комунікації (on_event).")

                if not has_regular:
                    errors.append("CM-3: Відсутній регулярний ритм комунікацій (weekly або biweekly).")
                else:
                    successes.append("CM-3: Присутній регулярний ритм комунікацій (weekly/biweekly).")

        except Exception as e:
            errors.append(f"Помилка при читанні communication.csv: {e}")

    # 4. Перевірка README.md
    if os.path.isfile(readme_path):
        try:
            with open(readme_path, mode="r", encoding="utf-8") as f:
                rm_content = f.read()

            required_rm_sections = [
                "1. Ролі матриці",
                "2. Матриця RACI",
                "3. Спірні призначення A",
                "4. Скільки коштує погодження",
                "5. План комунікацій",
                "6. Ризики і комунікації"
            ]

            last_pos = -1
            order_ok = True
            for sec in required_rm_sections:
                pos = rm_content.find(sec)
                if pos == -1:
                    errors.append(f"README.md: Відсутній обов'язковий розділ '{sec}'.")
                else:
                    if pos < last_pos:
                        order_ok = False
                    last_pos = pos

            if order_ok:
                successes.append("README.md: Усі 6 обов'язкових розділів присутні у правильному порядку.")
            else:
                errors.append("README.md: Розділи розташовані не у правильному порядку.")

            placeholders = re.findall(r"<[^>\n]{2,}>", rm_content)
            real_placeholders = [p for p in placeholders if not re.match(r"^<(https?://|!--|/?[a-z1-6]+>?)", p, re.IGNORECASE)]
            if real_placeholders:
                errors.append(f"README.md: Виявлено невидалені плейсхолдери у кутових дужках: {real_placeholders[:3]}")
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


def validate_status_report(target_dir):
    errors = []
    warnings = []
    successes = []

    if not os.path.isdir(target_dir):
        print(f"ERROR: Директорія '{target_dir}' не знайдена.")
        return 1

    impact_path = os.path.join(target_dir, "impact.csv")
    readme_path = os.path.join(target_dir, "README.md")
    cr_path = os.path.join(target_dir, "change_request.md")

    # 1. Перевірка наявності файлів
    for p, name in [(impact_path, "impact.csv"), (readme_path, "README.md"), (cr_path, "change_request.md")]:
        if not os.path.isfile(p):
            errors.append(f"Файл {p} не знайдено.")
        else:
            successes.append(f"Файл {name} знайдено в {target_dir}")

    # Завантаження суміжних файлів для наскрізної перевірки (IM-2, X-16, X-17, X-18)
    valid_risks = set()
    risks_path = os.path.join("lr11_risks_quality", "risks.csv")
    if os.path.isfile(risks_path):
        try:
            with open(risks_path, mode="r", encoding="utf-8") as f:
                r = csv.reader(f)
                next(r, None)
                for row in r:
                    if row:
                        valid_risks.add(row[0].strip())
        except Exception:
            pass

    ch01_decision = None
    ch01_points_delta = None
    changelog_path = os.path.join("lr11_risks_quality", "changelog.csv")
    if os.path.isfile(changelog_path):
        try:
            with open(changelog_path, mode="r", encoding="utf-8") as f:
                r = csv.reader(f)
                next(r, None)
                for row in r:
                    if len(row) >= 7 and row[0].strip() == "CH-01":
                        ch01_points_delta = row[5].strip()
                        ch01_decision = row[6].strip().lower()
        except Exception:
            pass

    target_date_rel1 = None
    roadmap_path = os.path.join("lr07_wbs", "roadmap.csv")
    if os.path.isfile(roadmap_path):
        try:
            with open(roadmap_path, mode="r", encoding="utf-8") as f:
                r = csv.reader(f)
                next(r, None)
                for row in r:
                    if len(row) >= 3 and row[0].strip() == "REL-1":
                        target_date_rel1 = row[2].strip()
        except Exception:
            pass

    p85_date_rel1 = None
    forecast_path = os.path.join("lr09_forecast", "forecast.csv")
    if os.path.isfile(forecast_path):
        try:
            with open(forecast_path, mode="r", encoding="utf-8") as f:
                r = csv.reader(f)
                next(r, None)
                row = next(r, None)
                if row and len(row) >= 7:
                    p85_date_rel1 = row[6].strip()
        except Exception:
            pass

    # 2. Перевірка impact.csv
    if os.path.isfile(impact_path):
        try:
            with open(impact_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = ["dimension", "before", "after", "delta", "risk_ids", "source_file", "note"]
                if header != expected_header:
                    errors.append(f"IM-1: Неправильний заголовок impact.csv. Очікується:\n{expected_header}\nОтримано:\n{header}")
                else:
                    successes.append("IM-1: Заголовок impact.csv валідний.")

                rows = list(reader)
                expected_dims = {"scope", "schedule", "budget", "quality", "risk"}
                found_dims = set()
                changed_count = 0

                for i, r in enumerate(rows, start=2):
                    if len(r) != 7:
                        errors.append(f"impact.csv рядок {i}: очікується 7 колонок, отримано {len(r)}.")
                        continue
                    dim, before, after, delta, risk_ids, src_file, note = [c.strip() for c in r]
                    found_dims.add(dim)

                    if before != after:
                        changed_count += 1

                    # IM-1 & IM-4: наявність чисел
                    if dim in ("scope", "schedule", "budget", "risk"):
                        for col_name, col_val in [("before", before), ("after", after), ("delta", delta)]:
                            if not re.search(r"\d", col_val):
                                errors.append(f"IM-1 / IM-4 рядок {i} ({dim}): колонка '{col_name}' повинна містити числове значення (отримано '{col_val}').")

                    if not re.search(r"\d", delta):
                        errors.append(f"IM-4 рядок {i} ({dim}): поле delta не може бути описовим без чисел ('{delta}').")

                    # IM-2: risk_ids для risk
                    if dim == "risk":
                        if not risk_ids:
                            errors.append("IM-2: Рядок 'risk' повинен мати заповнене поле risk_ids.")
                        else:
                            rlist = [rk.strip() for rk in risk_ids.split(";") if rk.strip()]
                            for rk in rlist:
                                if valid_risks and rk not in valid_risks:
                                    errors.append(f"IM-2: Ризик '{rk}' відсутній у lr11_risks_quality/risks.csv.")
                            if rlist:
                                successes.append(f"IM-2: Рядок risk посилається на валідні ризики {rlist}.")

                    # X-16: існування source_file
                    if not src_file or not os.path.isfile(src_file) or os.path.getsize(src_file) == 0:
                        errors.append(f"X-16 рядок {i} ({dim}): файл джерела '{src_file}' не існує або порожній.")

                    # Звірка points_delta з CH-01
                    if dim == "scope" and ch01_points_delta is not None:
                        if ch01_points_delta not in delta:
                            warnings.append(f"IM-1: У полі scope.delta бажано явно зазначити нетто {ch01_points_delta} (як у CH-01).")

                if found_dims != expected_dims:
                    errors.append(f"IM-1: Мають бути рівно 5 вимірів {expected_dims} (отримано {found_dims}).")
                else:
                    successes.append("IM-1: Усі 5 вимірів (scope, schedule, budget, quality, risk) присутні.")

                if changed_count < 3:
                    errors.append(f"IM-3: Щонайменше 3 виміри мають мати before != after (знайдено {changed_count}).")
                else:
                    successes.append(f"IM-3: У {changed_count} вимірах значення before != after (>= 3).")

                if not any("X-16" in e for e in errors):
                    successes.append("X-16: Усі файли джерел у source_file існують та непорожні.")

        except Exception as e:
            errors.append(f"Помилка при читанні impact.csv: {e}")

    # 3. Перевірка README.md (статус-звіт)
    if os.path.isfile(readme_path):
        try:
            with open(readme_path, mode="r", encoding="utf-8") as f:
                rm_content = f.read()

            required_rm_sections = [
                "1. Головне трьома реченнями",
                "2. Топ-3 ризики",
                "3. Три числа",
                "4. Чого я прошу"
            ]

            last_pos = -1
            order_ok = True
            for sec in required_rm_sections:
                pos = rm_content.find(sec)
                if pos == -1:
                    errors.append(f"README.md: Відсутній обов'язковий розділ '{sec}'.")
                else:
                    if pos < last_pos:
                        order_ok = False
                    last_pos = pos

            if order_ok:
                successes.append("README.md: Усі обов'язкові розділи статус-звіту присутні у правильному порядку.")
            else:
                errors.append("README.md: Розділи розташовані не у правильному порядку.")

            # X-17: перевірка дат
            if target_date_rel1 and target_date_rel1 not in rm_content:
                errors.append(f"X-17: У статус-звіті відсутня планова дата REL-1 '{target_date_rel1}' із roadmap.csv.")
            if p85_date_rel1 and p85_date_rel1 not in rm_content:
                errors.append(f"X-17: У статус-звіті відсутня прогнозна дата P85 '{p85_date_rel1}' із forecast.csv.")
            if target_date_rel1 and p85_date_rel1 and target_date_rel1 in rm_content and p85_date_rel1 in rm_content:
                successes.append(f"X-17: Дати першого релізу ({p85_date_rel1} проти {target_date_rel1}) коректно звірені.")

            if "прийняти до відома" in rm_content.lower():
                errors.append("README.md Розділ 4: Заборонено формулювання 'прийняти до відома', потрібне конкретне управлінське рішення.")

            placeholders = re.findall(r"<[^>\n]{2,}>", rm_content)
            real_placeholders = [p for p in placeholders if not re.match(r"^<(https?://|!--|/?[a-z1-6]+>?)", p, re.IGNORECASE)]
            if real_placeholders:
                errors.append(f"README.md: Виявлено невидалені плейсхолдери у кутових дужках: {real_placeholders[:3]}")
            else:
                successes.append("README.md: Плейсхолдери у кутових дужках відсутні.")

        except Exception as e:
            errors.append(f"Помилка при читанні README.md: {e}")

    # 4. Перевірка change_request.md
    if os.path.isfile(cr_path):
        try:
            with open(cr_path, mode="r", encoding="utf-8") as f:
                cr_content = f.read()

            required_cr_sections = [
                "1. Чого просять",
                "2. Ціна зміни",
                "3. Варіанти дій",
                "4. Рішення",
                "5. Що сказати замовнику"
            ]

            last_pos = -1
            order_ok = True
            for sec in required_cr_sections:
                pos = cr_content.find(sec)
                if pos == -1:
                    errors.append(f"change_request.md: Відсутній обов'язковий розділ '{sec}'.")
                else:
                    if pos < last_pos:
                        order_ok = False
                    last_pos = pos

            if order_ok:
                successes.append("change_request.md: Усі 5 обов'язкових розділів присутні у правильному порядку.")
            else:
                errors.append("change_request.md: Розділи розташовані не у правильному порядку.")

            # X-18: сувора відповідність рішення в change_request.md та changelog.csv
            if ch01_decision == "accepted":
                if not re.search(r"\*\*Рішення\*\*\s*\|\s*`?approve`?", cr_content):
                    errors.append("X-18: У change_request.md рішення має бути суворо 'approve' (відповідно до accepted у CH-01).")
                else:
                    successes.append("X-18: Рішення 'approve' у change_request.md точно узгоджується з 'accepted' у changelog.csv.")

            if "ST-01" not in cr_content:
                errors.append("X-18: У change_request.md відсутнє посилання на сторону ухвалення рішення (ST-01 з RACI).")
            else:
                successes.append("X-18: Сторона ухвалення рішення (ST-01) вказана коректно.")

            placeholders = re.findall(r"<[^>\n]{2,}>", cr_content)
            real_placeholders = [p for p in placeholders if not re.match(r"^<(https?://|!--|/?[a-z1-6]+>?)", p, re.IGNORECASE)]
            if real_placeholders:
                errors.append(f"change_request.md: Виявлено невидалені плейсхолдери у кутових дужках: {real_placeholders[:3]}")
            else:
                successes.append("change_request.md: Плейсхолдери у кутових дужках відсутні.")

        except Exception as e:
            errors.append(f"Помилка при читанні change_request.md: {e}")

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


def validate_metrics(target_dir):
    errors = []
    warnings = []
    successes = []

    if not os.path.isdir(target_dir):
        print(f"ERROR: Директорія '{target_dir}' не знайдена.")
        return 1

    findings_path = os.path.join(target_dir, "findings.csv")
    flow_path = os.path.join(target_dir, "flow.csv")
    dash_path = os.path.join(target_dir, "dashboard.csv")
    readme_path = os.path.join(target_dir, "README.md")

    # 1. Наявність файлів
    for p, name in [
        (findings_path, "findings.csv"),
        (flow_path, "flow.csv"),
        (dash_path, "dashboard.csv"),
        (readme_path, "README.md")
    ]:
        if not os.path.isfile(p):
            errors.append(f"Файл {p} не знайдено.")
        else:
            successes.append(f"Файл {name} знайдено в {target_dir}")

    # Суміжні файли для X-1, X-2
    valid_stories = set()
    backlog_path = os.path.join("lr06_backlog", "backlog.csv")
    if os.path.isfile(backlog_path):
        try:
            with open(backlog_path, mode="r", encoding="utf-8") as f:
                r = csv.reader(f)
                next(r, None)
                for row in r:
                    if row:
                        valid_stories.add(row[0].strip())
        except Exception:
            pass

    valid_stakeholders = set()
    stakeholders_path = os.path.join("lr05_charter", "stakeholders.csv")
    if os.path.isfile(stakeholders_path):
        try:
            with open(stakeholders_path, mode="r", encoding="utf-8") as f:
                r = csv.reader(f)
                next(r, None)
                for row in r:
                    if row:
                        valid_stakeholders.add(row[0].strip())
        except Exception:
            pass

    forbidden_actions = ["стежити", "моніторити", "аналізувати"]

    # 2. Перевірка findings.csv
    if os.path.isfile(findings_path):
        try:
            with open(findings_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = ["finding_id", "dataset", "where_seen", "evidence", "diagnosis", "action"]
                if header != expected_header:
                    errors.append(f"FD-1: Неправильний заголовок findings.csv. Очікується:\n{expected_header}\nОтримано:\n{header}")
                else:
                    successes.append("FD-1: Заголовок findings.csv валідний.")

                rows = list(reader)
                if len(rows) < 6:
                    errors.append(f"FD-1: findings.csv має містити щонайменше 6 знахідок (знайдено {len(rows)}).")
                else:
                    successes.append(f"FD-1: Знайдено {len(rows)} знахідок у findings.csv (>= 6).")

                ds_counts = {"burndown": 0, "cfd": 0, "dora": 0}
                for i, r in enumerate(rows, start=2):
                    if len(r) != 6:
                        errors.append(f"findings.csv рядок {i}: очікується 6 колонок, отримано {len(r)}.")
                        continue
                    fid, ds, where, ev, diag, act = [c.strip() for c in r]
                    ds_low = ds.lower()
                    if ds_low in ds_counts:
                        ds_counts[ds_low] += 1

                    if not re.search(r"\d", ev):
                        errors.append(f"FD-2 рядок {i} ({fid}): evidence має містити точні цифри (отримано '{ev}').")

                    act_low = act.lower()
                    for fa in forbidden_actions:
                        if fa in act_low:
                            errors.append(f"FD-3 рядок {i} ({fid}): action містить пасивне слово '{fa}' замість конкретної дії PM.")

                for ds_k, cnt in ds_counts.items():
                    if cnt < 2:
                        errors.append(f"FD-1: Для датасету '{ds_k}' потрібно щонайменше 2 знахідки (знайдено {cnt}).")
                if all(cnt >= 2 for cnt in ds_counts.values()):
                    successes.append(f"FD-1: Покрито всі 3 датасети мінімум по 2 знахідки {ds_counts}.")
                if not any("FD-2" in e for e in errors):
                    successes.append("FD-2: Усі докази (evidence) містять точні числові значення.")
                if not any("FD-3" in e for e in errors):
                    successes.append("FD-3: Усі управлінські дії (action) сформульовані активно без пасивних формулювань.")

        except Exception as e:
            errors.append(f"Помилка при читанні findings.csv: {e}")

    # 3. Перевірка flow.csv
    if os.path.isfile(flow_path):
        try:
            with open(flow_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = ["item_id", "story_id", "type", "created_date", "start_date", "done_date", "blocked_days"]
                if header != expected_header:
                    errors.append(f"FL-1: Неправильний заголовок flow.csv. Очікується:\n{expected_header}\nОтримано:\n{header}")
                else:
                    successes.append("FL-1: Заголовок flow.csv валідний.")

                rows = list(reader)
                if len(rows) < 12:
                    errors.append(f"FL-1: flow.csv має містити щонайменше 12 карток (знайдено {len(rows)}).")
                else:
                    successes.append(f"FL-1: Знайдено {len(rows)} завершених карток (>= 12).")

                no_story_count = 0
                with_story_count = 0
                cycle_times = []

                for i, r in enumerate(rows, start=2):
                    if len(r) != 7:
                        errors.append(f"flow.csv рядок {i}: очікується 7 колонок, отримано {len(r)}.")
                        continue
                    iid, sid, ctype, cr_s, st_s, dn_s, blk_s = [c.strip() for c in r]

                    if not sid:
                        no_story_count += 1
                    else:
                        with_story_count += 1
                        if valid_stories and sid not in valid_stories:
                            errors.append(f"X-1 рядок {i} ({iid}): story_id '{sid}' відсутній у lr06_backlog/backlog.csv.")

                    try:
                        cr_dt = datetime.strptime(cr_s, "%Y-%m-%d").date()
                        st_dt = datetime.strptime(st_s, "%Y-%m-%d").date()
                        dn_dt = datetime.strptime(dn_s, "%Y-%m-%d").date()

                        if not (cr_dt <= st_dt <= dn_dt):
                            errors.append(f"FL-1 рядок {i} ({iid}): порушено порядок дат {cr_s} <= {st_s} <= {dn_s}.")

                        ct = (dn_dt - st_dt).days
                        cycle_times.append(ct)

                        blk_val = int(blk_s)
                        if blk_val < 0 or blk_val > ct:
                            errors.append(f"FL-2 рядок {i} ({iid}): blocked_days ({blk_val}) має бути у [0, {ct}].")
                    except ValueError as ve:
                        errors.append(f"flow.csv рядок {i} ({iid}): некоректна дата або blocked_days ({ve}).")

                if no_story_count < 2:
                    errors.append(f"FL-3: Потрібно щонайменше 2 картки без story_id (знайдено {no_story_count}).")
                else:
                    successes.append(f"FL-3: Знайдено {no_story_count} карток без story_id (>= 2).")

                if with_story_count < 2:
                    errors.append(f"FL-4: Потрібно щонайменше 2 картки зі story_id (знайдено {with_story_count}).")
                else:
                    successes.append(f"FL-4: Знайдено {with_story_count} карток зі story_id (>= 2).")

                if cycle_times and (max(cycle_times) - min(cycle_times) >= 3):
                    successes.append(f"FL-5: Присутній реалістичний розкид cycle time ({min(cycle_times)}..{max(cycle_times)} днів).")
                else:
                    errors.append("FL-5: Замалий розкид значень cycle time у flow.csv.")

        except Exception as e:
            errors.append(f"Помилка при читанні flow.csv: {e}")

    # 4. Перевірка dashboard.csv
    if os.path.isfile(dash_path):
        try:
            with open(dash_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                expected_header = ["metric_id", "metric", "value", "source_file", "reader", "threshold", "decision"]
                if header != expected_header:
                    errors.append(f"DB-1: Неправильний заголовок dashboard.csv. Очікується:\n{expected_header}\nОтримано:\n{header}")
                else:
                    successes.append("DB-1: Заголовок dashboard.csv валідний.")

                rows = list(reader)
                if not (3 <= len(rows) <= 6):
                    errors.append(f"DB-1: Дашборд має містити 3–4 метрики (знайдено {len(rows)}).")
                else:
                    successes.append(f"DB-1: Кількість метрик у дашборді валідна ({len(rows)}).")

                has_flow_source = False
                for i, r in enumerate(rows, start=2):
                    if len(r) != 7:
                        errors.append(f"dashboard.csv рядок {i}: очікується 7 колонок, отримано {len(r)}.")
                        continue
                    mid, mname, val, src, reader_id, thresh, dec = [c.strip() for c in r]

                    if not re.search(r"\d", val):
                        errors.append(f"DB-2 рядок {i} ({mid}): value '{val}' повинне містити число або дату.")
                    if "flow.csv" in src:
                        has_flow_source = True
                    if not re.search(r"\d", thresh):
                        errors.append(f"DB-4 рядок {i} ({mid}): threshold '{thresh}' повинен містити число або дату.")

                    dec_low = dec.lower()
                    for fa in forbidden_actions:
                        if fa in dec_low:
                            errors.append(f"DB-5 рядок {i} ({mid}): decision містить пасивне слово '{fa}'.")

                    if valid_stakeholders and reader_id not in valid_stakeholders:
                        errors.append(f"X-2 рядок {i} ({mid}): reader '{reader_id}' відсутній у lr05_charter/stakeholders.csv.")

                    if not src or not os.path.isfile(src) or os.path.getsize(src) == 0:
                        errors.append(f"X-16 рядок {i} ({mid}): файл джерела '{src}' не існує або порожній.")

                if not has_flow_source:
                    errors.append("DB-3: Дашборд повинен містити принаймні одну метрику з lr14_metrics/flow.csv.")
                else:
                    successes.append("DB-3: Присутня метрика на основі flow.csv.")

                if not any("X-16" in e for e in errors):
                    successes.append("X-16: Усі source_file у dashboard.csv існують і непорожні.")
                if not any("X-2" in e for e in errors):
                    successes.append("X-2: Усі reader існують у карті стейкхолдерів.")

        except Exception as e:
            errors.append(f"Помилка при читанні dashboard.csv: {e}")

    # 5. Перевірка README.md
    if os.path.isfile(readme_path):
        try:
            with open(readme_path, mode="r", encoding="utf-8") as f:
                rm_content = f.read()

            required_rm_sections = [
                "1. Еталонні дані курсу",
                "2. Власні числа потоку",
                "3. Дашборд",
                "4. Метрика, яку найлегше накрутити"
            ]

            last_pos = -1
            order_ok = True
            for sec in required_rm_sections:
                pos = rm_content.find(sec)
                if pos == -1:
                    errors.append(f"README.md: Відсутній обов'язковий розділ '{sec}'.")
                else:
                    if pos < last_pos:
                        order_ok = False
                    last_pos = pos

            if order_ok:
                successes.append("README.md: Усі 4 обов'язкові розділи присутні у правильному порядку.")
            else:
                errors.append("README.md: Розділи розташовані не у правильному порядку.")

            placeholders = re.findall(r"<[^>\n]{2,}>", rm_content)
            real_placeholders = [p for p in placeholders if not re.match(r"^<(https?://|!--|/?[a-z1-6]+>?)", p, re.IGNORECASE)]
            if real_placeholders:
                errors.append(f"README.md: Виявлено невидалені плейсхолдери у кутових дужках: {real_placeholders[:3]}")
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


def validate_budget(target_dir):
    print(f"Початок валідації кошторису, резервів та контрактів у '{target_dir}'...")
    errors = []
    warnings = []
    successes = []

    if not os.path.isdir(target_dir):
        print(f"Помилка: Директорія '{target_dir}' не існує.")
        return 1

    rate_card_path = os.path.join(target_dir, "rate_card.csv")
    budget_path = os.path.join(target_dir, "budget.csv")
    plan_fact_path = os.path.join(target_dir, "plan_fact.csv")
    readme_path = os.path.join(target_dir, "README.md")

    for req_file, label in [
        (rate_card_path, "rate_card.csv"),
        (budget_path, "budget.csv"),
        (plan_fact_path, "plan_fact.csv"),
        (readme_path, "README.md"),
    ]:
        if not os.path.isfile(req_file):
            errors.append(f"Відсутній обов'язковий файл '{label}' у {target_dir}.")
        else:
            successes.append(f"Файл {label} знайдено в {target_dir}")

    # X-4: читання варіанта та картки з кореневого README.md і бюджетного ліміту з lr05_charter/README.md
    root_readme_path = "README.md"
    variant_hours_ceiling = 1800.0
    variant_weeks = 12
    variant_direct_limit = 500000.0
    variant_roles = {"PM", "Dev", "QA", "DevOps"}
    root_contingency_pct = None

    if os.path.isfile(root_readme_path):
        try:
            with open(root_readme_path, mode="r", encoding="utf-8") as f:
                root_rm = f.read()
            if "Валюта проєкту:" in root_rm and "[Поки що порожньо]" not in root_rm.split("Валюта проєкту:")[1].splitlines()[0]:
                successes.append("X-4: Поле 'Валюта проєкту' у кореневому README.md заповнене.")
            else:
                errors.append("X-4: Поле 'Валюта проєкту' у кореневому README.md не заповнене.")

            cont_match = re.search(r"Contingency:\*{0,2}\s*([0-9]+(?:[.,][0-9]+)?)\s*%?", root_rm)
            if cont_match and "[Поки що порожньо]" not in cont_match.group(0):
                root_contingency_pct = float(cont_match.group(1).replace(",", "."))
                successes.append(f"X-4: Поле 'Contingency' у кореневому README.md заповнене ({root_contingency_pct:g}%).")
            else:
                errors.append("X-4: Поле 'Contingency' у кореневому README.md не заповнене.")

            if "V04" in root_rm and "V08" not in root_rm:
                variant_hours_ceiling = 720.0
                variant_weeks = 8
                variant_direct_limit = 430000.0
                variant_roles = {"PM", "Dev", "QA"}
        except Exception as e:
            errors.append(f"Помилка читання кореневого README.md: {e}")

    charter_readme_path = os.path.join("lr05_charter", "README.md")
    if os.path.isfile(charter_readme_path):
        try:
            with open(charter_readme_path, mode="r", encoding="utf-8") as f:
                ch_rm = f.read()
            lim_match = re.search(r"Бюджет direct cost:\s*([0-9\s]+)\s*грн", ch_rm)
            if lim_match:
                variant_direct_limit = float(lim_match.group(1).replace(" ", "").strip())
        except Exception:
            pass

    # 1. Валідація rate_card.csv (RT-1..3, X-4, X-20)
    rate_by_role = {}
    rate_card_hours_sum = 0.0
    if os.path.isfile(rate_card_path):
        try:
            with open(rate_card_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                expected_cols = ["role", "fte", "hours", "rate", "source", "note"]
                if reader.fieldnames != expected_cols:
                    errors.append(f"RT-1: Некоректний заголовок rate_card.csv {reader.fieldnames}, очікується {expected_cols}.")
                else:
                    successes.append("RT-1: Заголовок rate_card.csv валідний.")
                    rates_list = []
                    labor_total = 0.0
                    seen_roles = set()
                    for i, row in enumerate(reader, start=2):
                        role = row.get("role", "").strip()
                        fte_s = row.get("fte", "").strip()
                        hrs_s = row.get("hours", "").strip()
                        rate_s = row.get("rate", "").strip()
                        src = row.get("source", "").strip()
                        note = row.get("note", "").strip()
                        if not role or not note:
                            errors.append(f"RT-1 рядок {i}: role та note не можуть бути порожніми.")
                        seen_roles.add(role)
                        try:
                            fte = float(fte_s)
                            hrs = float(hrs_s)
                            rate = float(rate_s)
                            if fte <= 0 or hrs <= 0 or rate <= 0:
                                errors.append(f"RT-1 рядок {i} ({role}): fte, hours і rate мають бути > 0.")
                            expected_hrs = fte * variant_weeks * 40
                            if abs(hrs - expected_hrs) > 0.01:
                                errors.append(f"X-4 рядок {i} ({role}): hours ({hrs}) != fte*weeks*40 ({expected_hrs}).")
                            rate_by_role[role] = rate
                            rates_list.append(rate)
                            rate_card_hours_sum += hrs
                            labor_total += hrs * rate
                        except ValueError:
                            errors.append(f"RT-1 рядок {i} ({role}): некоректне числове значення fte/hours/rate.")

                        if not re.match(r"^https?://\S+", src):
                            errors.append(f"RT-3 рядок {i} ({role}): source '{src}' має містити коректний HTTP(S) URL.")

                    if seen_roles == variant_roles:
                        successes.append(f"X-4: Ролі rate_card.csv {sorted(seen_roles)} точно відповідають варіанту.")
                    else:
                        errors.append(f"X-4: Ролі rate_card.csv {sorted(seen_roles)} не збігаються з ролями варіанта {sorted(variant_roles)}.")

                    if abs(rate_card_hours_sum - variant_hours_ceiling) <= 0.01:
                        successes.append(f"X-4: Сума годин rate_card.csv ({rate_card_hours_sum:g}) точно дорівнює стелі варіанта ({variant_hours_ceiling:g}).")
                    else:
                        errors.append(f"X-4: Сума годин rate_card.csv ({rate_card_hours_sum:g}) != стелі ({variant_hours_ceiling:g}).")

                    if len(set(rates_list)) > 1:
                        successes.append("RT-1: Ставки ролей у rate_card.csv диференційовані (не однакові).")
                    else:
                        errors.append("RT-1: Усі ставки у rate_card.csv однакові.")

                    if rate_card_hours_sum > 0:
                        blended = labor_total / rate_card_hours_sum
                        own_ceiling = variant_direct_limit / variant_hours_ceiling
                        if blended <= own_ceiling + 0.01 and blended >= 150.0:
                            successes.append(f"RT-2: Blended rate ({blended:.2f} грн/год) нижчий за стелю варіанта ({own_ceiling:.2f} грн/год).")
                        else:
                            errors.append(f"RT-2: Blended rate ({blended:.2f}) порушує межі (150..{own_ceiling:.2f} грн/год).")

                    if not any("RT-3" in e for e in errors):
                        successes.append("RT-3: Усі рядки rate_card.csv містять валідне посилання на джерело.")
        except Exception as e:
            errors.append(f"Помилка читання rate_card.csv: {e}")

    # 2. Валідація budget.csv (BG-1..7, X-19, X-20)
    if os.path.isfile(budget_path):
        try:
            with open(budget_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                expected_cols = ["line_id", "category", "role_or_item", "hours", "rate", "amount", "note"]
                if reader.fieldnames != expected_cols:
                    errors.append(f"BG-1: Некоректний заголовок budget.csv {reader.fieldnames}, очікується {expected_cols}.")
                else:
                    successes.append("BG-1: Заголовок budget.csv валідний.")
                    rows = list(reader)
                    if len(rows) >= 6:
                        successes.append(f"BG-5: Знайдено {len(rows)} рядків кошторису (>= 6).")
                    else:
                        errors.append(f"BG-5: Знайдено лише {len(rows)} рядків кошторису (мінімум 6).")

                    direct_sum = 0.0
                    budget_labor_hours = 0.0
                    contingency_rows = []
                    mr_rows = []
                    non_labor_cats = set()

                    for i, row in enumerate(rows, start=2):
                        lid = row.get("line_id", "").strip()
                        cat = row.get("category", "").strip()
                        item = row.get("role_or_item", "").strip()
                        hrs_s = row.get("hours", "").strip()
                        rate_s = row.get("rate", "").strip()
                        amt_s = row.get("amount", "").strip()
                        note = row.get("note", "").strip()

                        if not lid or not cat or not item or not note:
                            errors.append(f"BG-6 рядок {i}: порожнє обов'язкове поле у budget.csv.")

                        try:
                            amt = float(amt_s)
                            if amt <= 0:
                                errors.append(f"BG-6 рядок {i} ({lid}): сума amount ({amt}) має бути > 0.")
                        except ValueError:
                            errors.append(f"BG-6 рядок {i} ({lid}): некоректна сума amount '{amt_s}'.")
                            amt = 0.0

                        if cat == "labor":
                            try:
                                hrs = float(hrs_s)
                                rate = float(rate_s)
                                if abs(hrs * rate - amt) > 0.01:
                                    errors.append(f"BG-1 рядок {i} ({lid}): hours ({hrs}) * rate ({rate}) != amount ({amt}).")
                                if item not in rate_by_role or abs(rate - rate_by_role[item]) > 0.01:
                                    errors.append(f"X-19 рядок {i} ({lid}): ставка {rate} для '{item}' не збігається з rate_card.csv.")
                                budget_labor_hours += hrs
                                direct_sum += amt
                            except ValueError:
                                errors.append(f"BG-1 рядок {i} ({lid}): labor-рядок має містити числові hours та rate.")
                        elif cat == "contingency":
                            contingency_rows.append(amt)
                            if hrs_s or rate_s:
                                errors.append(f"BG-7 рядок {i} ({lid}): резерв contingency не повинен мати заповнені hours/rate.")
                        elif cat == "management_reserve":
                            mr_rows.append(amt)
                            if hrs_s or rate_s:
                                errors.append(f"BG-7 рядок {i} ({lid}): management_reserve не повинен мати заповнені hours/rate.")
                        elif cat in ("tools", "infrastructure", "other"):
                            non_labor_cats.add(cat)
                            direct_sum += amt
                        else:
                            errors.append(f"BG-6 рядок {i} ({lid}): невідома категорія '{cat}'.")

                    if not any("BG-1" in e for e in errors):
                        successes.append("BG-1: Добуток hours * rate == amount для всіх трудових рядків.")
                    if not any("X-19" in e for e in errors):
                        successes.append("X-19: Усі ставки трудових рядків budget.csv строго збігаються з rate_card.csv.")

                    if abs(budget_labor_hours - rate_card_hours_sum) <= 0.01:
                        successes.append(f"X-20: Сума трудових годин budget.csv ({budget_labor_hours:g}) збігається з rate_card.csv ({rate_card_hours_sum:g}).")
                    else:
                        errors.append(f"X-20: Сума трудових годин budget.csv ({budget_labor_hours:g}) != rate_card.csv ({rate_card_hours_sum:g}).")

                    if len(contingency_rows) == 1:
                        successes.append("BG-2: Присутній рівно 1 рядок contingency.")
                    else:
                        errors.append(f"BG-2: Очікується рівно 1 рядок contingency, знайдено {len(contingency_rows)}.")

                    if len(mr_rows) == 1:
                        successes.append("BG-3: Присутній рівно 1 рядок management_reserve.")
                    else:
                        errors.append(f"BG-3: Очікується рівно 1 рядок management_reserve, знайдено {len(mr_rows)}.")

                    if contingency_rows and direct_sum > 0:
                        cont_pct = (contingency_rows[0] / direct_sum) * 100.0
                        if 5.0 <= cont_pct <= 25.0:
                            successes.append(f"BG-4: Contingency становить {cont_pct:.2f}% від прямих витрат ({direct_sum:g} грн).")
                        else:
                            errors.append(f"BG-4: Contingency ({cont_pct:.2f}%) виходить за межі 5%..25% від прямих витрат.")
                        if root_contingency_pct is not None and abs(cont_pct - root_contingency_pct) > 0.5:
                            errors.append(f"X-4: Відсоток contingency у budget.csv ({cont_pct:.2f}%) != картці README.md ({root_contingency_pct:g}%).")

                    if len(non_labor_cats) >= 2:
                        successes.append(f"BG-7: Покрито нетрудові прямі витрати {sorted(non_labor_cats)}.")
                    else:
                        errors.append(f"BG-7: Недостатньо категорій нетрудових прямих витрат: {sorted(non_labor_cats)}.")

                    if direct_sum <= variant_direct_limit + 0.01:
                        successes.append(f"BG-6: Сума прямих витрат ({direct_sum:g} грн) <= ліміту варіанта ({variant_direct_limit:g} грн).")
                    else:
                        errors.append(f"BG-6: Сума прямих витрат ({direct_sum:g} грн) перевищує ліміт варіанта ({variant_direct_limit:g} грн).")
        except Exception as e:
            errors.append(f"Помилка читання budget.csv: {e}")

    # 3. Валідація plan_fact.csv (PF-1..4, X-21)
    velocity_done_by_sprint = {}
    vel_path = os.path.join("lr09_forecast", "velocity.csv")
    if os.path.isfile(vel_path):
        try:
            with open(vel_path, mode="r", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    velocity_done_by_sprint[row.get("sprint", "").strip()] = float(row.get("points_done", "0").strip())
        except Exception:
            pass

    if os.path.isfile(plan_fact_path):
        try:
            with open(plan_fact_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                expected_cols = [
                    "sprint", "planned_points", "actual_points",
                    "planned_cost_per_point", "actual_cost_per_point",
                    "variance_pct", "source_file", "note",
                ]
                if reader.fieldnames != expected_cols:
                    errors.append(f"PF-1: Некоректний заголовок plan_fact.csv {reader.fieldnames}, очікується {expected_cols}.")
                else:
                    successes.append("PF-1: Заголовок plan_fact.csv валідний.")
                    pf_rows = list(reader)
                    if len(pf_rows) >= 2:
                        successes.append(f"PF-1: Знайдено {len(pf_rows)} спринти у plan_fact.csv (>= 2).")
                    else:
                        errors.append(f"PF-1: Знайдено лише {len(pf_rows)} рядків у plan_fact.csv (мінімум 2).")

                    planned_pts_vals = set()
                    planned_cpp_vals = set()
                    for i, row in enumerate(pf_rows, start=2):
                        sp = row.get("sprint", "").strip()
                        src_file = row.get("source_file", "").strip()
                        try:
                            p_pts = float(row.get("planned_points", "").strip())
                            a_pts = float(row.get("actual_points", "").strip())
                            p_cpp = float(row.get("planned_cost_per_point", "").strip())
                            a_cpp = float(row.get("actual_cost_per_point", "").strip())
                            var_pct = float(row.get("variance_pct", "").strip())

                            planned_pts_vals.add(p_pts)
                            planned_cpp_vals.add(round(p_cpp, 2))

                            sprint_plan_cost = p_pts * p_cpp
                            sprint_act_cost = a_pts * a_cpp
                            if abs(sprint_plan_cost - sprint_act_cost) > 1.0:
                                errors.append(
                                    f"PF-1 рядок {i} (Спринт {sp}): вартість спринта плану ({sprint_plan_cost:.2f}) != факту ({sprint_act_cost:.2f})."
                                )

                            expected_var = ((a_cpp - p_cpp) / p_cpp) * 100.0 if p_cpp > 0 else 0.0
                            if abs(var_pct - expected_var) > 0.05:
                                errors.append(
                                    f"PF-2 рядок {i} (Спринт {sp}): variance_pct ({var_pct}) != очікуваного ({expected_var:.2f})."
                                )
                            if sp in velocity_done_by_sprint and abs(a_pts - velocity_done_by_sprint[sp]) > 0.01:
                                errors.append(
                                    f"X-21 рядок {i} (Спринт {sp}): actual_points ({a_pts:g}) != velocity.csv ({velocity_done_by_sprint[sp]:g})."
                                )
                        except ValueError:
                            errors.append(f"PF-1 рядок {i} (Спринт {sp}): некоректні числові поля у plan_fact.csv.")

                        if not src_file or not os.path.isfile(src_file) or os.path.getsize(src_file) == 0:
                            errors.append(f"PF-4 рядок {i} (Спринт {sp}): source_file '{src_file}' не існує або порожній.")

                    if len(planned_pts_vals) == 1 and len(planned_cpp_vals) == 1:
                        successes.append("PF-3: Планова ємність і планова ціна point однакові для всіх спринтів.")
                    else:
                        errors.append("PF-3: planned_points або planned_cost_per_point різняться між спринтами.")

                    if not any("PF-1 рядок" in e for e in errors):
                        successes.append("PF-1: Вартість спринта однакова для плану і факту в межах заокруглення.")
                    if not any("PF-2" in e for e in errors):
                        successes.append("PF-2: Усі variance_pct розраховані математично точно.")
                    if not any("PF-4" in e for e in errors):
                        successes.append("PF-4: Усі source_file у plan_fact.csv існують і непорожні.")
                    if velocity_done_by_sprint and not any("X-21" in e for e in errors):
                        successes.append("X-21: actual_points у plan_fact.csv точно відповідають lr09_forecast/velocity.csv.")
        except Exception as e:
            errors.append(f"Помилка читання plan_fact.csv: {e}")

    # 4. Валідація README.md у lr16_budget
    if os.path.isfile(readme_path):
        try:
            with open(readme_path, mode="r", encoding="utf-8") as f:
                rm_content = f.read()

            required_rm_sections = [
                "0. Числа варіанта",
                "1. Rate card",
                "2. Кошторис і два резерви",
                "3. Fixed Price проти Time and Material",
                "4. Обрана модель",
                "5. Факт проти плану і прогноз до завершення",
                "6. Що я перевірив",
            ]
            last_pos = -1
            order_ok = True
            for sec in required_rm_sections:
                pos = rm_content.find(sec)
                if pos == -1:
                    errors.append(f"README.md: Відсутній обов'язковий розділ '{sec}'.")
                else:
                    if pos < last_pos:
                        order_ok = False
                    last_pos = pos
            if order_ok and not any("Відсутній обов'язковий розділ" in e for e in errors):
                successes.append("README.md: Усі 7 обов'язкових розділів (0..6) присутні у правильному порядку.")

            placeholders = re.findall(r"<[^>\n]{2,}>", rm_content)
            real_placeholders = [p for p in placeholders if not re.match(r"^<(https?://|!--|/?[a-z1-6]+>?)", p, re.IGNORECASE)]
            if real_placeholders:
                errors.append(f"README.md: Виявлено невидалені плейсхолдери у кутових дужках: {real_placeholders[:3]}")
            else:
                successes.append("README.md: Плейсхолдери у кутових дужках відсутні.")

            forecast_path = os.path.join("lr09_forecast", "forecast.csv")
            if os.path.isfile(forecast_path):
                with open(forecast_path, mode="r", encoding="utf-8-sig") as ff:
                    fc_rows = list(csv.DictReader(ff))
                if len(fc_rows) >= 2:
                    rem_pts = fc_rows[-1].get("remaining_points", "").strip()
                    if rem_pts and rem_pts in rm_content:
                        successes.append(f"X-4: Прогноз у README.md використовує актуальний залишок ({rem_pts} points) з forecast.csv.")
                    elif rem_pts:
                        errors.append(f"X-4: У README.md відсутнє посилання на залишок '{rem_pts} points' із forecast.csv.")
        except Exception as e:
            errors.append(f"Помилка читання README.md: {e}")

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


def validate_ai_assistant(target_dir):
    print(f"Початок валідації AI-асистента PM та меж інструмента у '{target_dir}'...")
    errors = []
    warnings = []
    successes = []

    if not os.path.isdir(target_dir):
        print(f"Помилка: Директорія '{target_dir}' не існує.")
        return 1

    notes_path = os.path.join(target_dir, "input_notes.md")
    tasks_path = os.path.join(target_dir, "tasks.csv")
    prompts_path = os.path.join(target_dir, "prompts.csv")
    errors_path = os.path.join(target_dir, "errors.csv")
    time_saved_path = os.path.join(target_dir, "time_saved.csv")
    policy_path = os.path.join(target_dir, "policy.csv")
    readme_path = os.path.join(target_dir, "README.md")

    for req_file, label in [
        (notes_path, "input_notes.md"),
        (tasks_path, "tasks.csv"),
        (prompts_path, "prompts.csv"),
        (errors_path, "errors.csv"),
        (time_saved_path, "time_saved.csv"),
        (policy_path, "policy.csv"),
        (readme_path, "README.md"),
    ]:
        if not os.path.isfile(req_file):
            errors.append(f"Відсутній обов'язковий файл '{label}' у {target_dir}.")
        else:
            successes.append(f"Файл {label} знайдено в {target_dir}")

    # 1. Збір тегів N-NN з input_notes.md
    note_tags = {}
    if os.path.isfile(notes_path):
        try:
            with open(notes_path, mode="r", encoding="utf-8") as f:
                notes_text = f.read()
            for line in notes_text.splitlines():
                m = re.match(r"^\s*-?\s*(N-\d{2}):\s*(.+)$", line)
                if m:
                    note_tags[m.group(1)] = m.group(2).strip()
            if len(note_tags) >= 14:
                successes.append(f"input_notes.md: Виявлено {len(note_tags)} рядків із тегами N-NN (>= 14).")
            else:
                errors.append(f"input_notes.md: Виявлено лише {len(note_tags)} рядків N-NN (очікується >= 14).")
        except Exception as e:
            errors.append(f"Помилка читання input_notes.md: {e}")

    # 2. Валідація tasks.csv (TK-1..5, X-22)
    if os.path.isfile(tasks_path):
        try:
            with open(tasks_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                expected_cols = ["item_id", "source_line", "type", "item", "origin", "owner", "note"]
                if reader.fieldnames != expected_cols:
                    errors.append(f"TK-1: Некоректний заголовок tasks.csv {reader.fieldnames}, очікується {expected_cols}.")
                else:
                    successes.append("TK-1: Заголовок tasks.csv валідний.")
                    rows = list(reader)
                    if len(rows) >= 8:
                        successes.append(f"TK-1: Знайдено {len(rows)} пунктів у tasks.csv (>= 8).")
                    else:
                        errors.append(f"TK-1: Знайдено лише {len(rows)} пунктів у tasks.csv (мінімум 8).")

                    origins = set()
                    type_counts = {"task": 0, "decision": 0, "open_question": 0}
                    for i, row in enumerate(rows, start=2):
                        iid = row.get("item_id", "").strip()
                        sline = row.get("source_line", "").strip()
                        itype = row.get("type", "").strip()
                        item = row.get("item", "").strip()
                        orig = row.get("origin", "").strip()
                        owner = row.get("owner", "").strip()
                        note = row.get("note", "").strip()

                        if not iid or not item:
                            errors.append(f"TK-1 рядок {i}: порожній item_id або item.")
                        if note_tags and sline not in note_tags:
                            errors.append(f"X-22 рядок {i} ({iid}): source_line '{sline}' відсутній у input_notes.md.")
                        if itype not in type_counts:
                            errors.append(f"TK-2 рядок {i} ({iid}): невідомий type '{itype}'.")
                        else:
                            type_counts[itype] += 1
                        if orig not in ("mine", "both", "ai"):
                            errors.append(f"TK-1 рядок {i} ({iid}): некоректне origin '{orig}'.")
                        else:
                            origins.add(orig)
                        if orig in ("mine", "ai") and not note:
                            errors.append(f"TK-5 рядок {i} ({iid}): поле note обов'язкове для origin='{orig}'.")
                        if owner:
                            src_txt = note_tags.get(sline, "").lower()
                            owner_tokens = [t for t in owner.lower().split() if len(t) > 2]
                            if not any(t in src_txt for t in owner_tokens):
                                errors.append(f"TK-4 рядок {i} ({iid}): owner '{owner}' не підтверджений прямо текстом {sline}.")

                    if origins == {"mine", "both", "ai"}:
                        successes.append("TK-1: Присутні всі три значення origin ('mine', 'both', 'ai').")
                    else:
                        errors.append(f"TK-1: Бракує значень origin, наявні лише {sorted(origins)}.")

                    if type_counts["open_question"] >= 2:
                        successes.append(f"TK-2: Знайдено {type_counts['open_question']} open_question (>= 2).")
                    else:
                        errors.append(f"TK-2: Знайдено лише {type_counts['open_question']} open_question (мінімум 2).")

                    if type_counts["task"] >= 2:
                        successes.append(f"TK-3: Знайдено {type_counts['task']} task (>= 2).")
                    else:
                        errors.append(f"TK-3: Знайдено лише {type_counts['task']} task (мінімум 2).")

                    if not any("TK-4" in e for e in errors):
                        successes.append("TK-4: Поле owner вказано лише там, де особа/роль прямо названа у нотатках.")
                    if not any("TK-5" in e for e in errors):
                        successes.append("TK-5: Усі рядки mine/ai містять пояснення відмінностей у note.")
                    if not any("X-22" in e for e in errors):
                        successes.append("X-22: Усі source_line у tasks.csv відповідають тегам input_notes.md.")
        except Exception as e:
            errors.append(f"Помилка читання tasks.csv: {e}")

    # 3. Валідація prompts.csv (PR-1..6, X-23)
    valid_run_ids = set()
    if os.path.isfile(prompts_path):
        try:
            with open(prompts_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                expected_cols = ["run_id", "date", "tool", "goal", "artifact", "has_input", "iterations", "result", "note"]
                if reader.fieldnames != expected_cols:
                    errors.append(f"PR-1: Некоректний заголовок prompts.csv {reader.fieldnames}, очікується {expected_cols}.")
                else:
                    successes.append("PR-1: Заголовок prompts.csv валідний.")
                    rows = list(reader)
                    if len(rows) >= 4:
                        successes.append(f"PR-1: Знайдено {len(rows)} запусків у prompts.csv (>= 4).")
                    else:
                        errors.append(f"PR-1: Знайдено лише {len(rows)} рядків у prompts.csv (мінімум 4).")

                    has_input_yes = 0
                    iter_ge_2 = 0
                    other_portfolio_runs = 0
                    for i, row in enumerate(rows, start=2):
                        rid = row.get("run_id", "").strip()
                        art = row.get("artifact", "").strip()
                        h_in = row.get("has_input", "").strip()
                        it_s = row.get("iterations", "").strip()
                        if rid in valid_run_ids:
                            errors.append(f"PR-1 рядок {i}: дублікат run_id '{rid}'.")
                        valid_run_ids.add(rid)
                        if h_in == "yes":
                            has_input_yes += 1
                        try:
                            if int(it_s) >= 2:
                                iter_ge_2 += 1
                        except ValueError:
                            errors.append(f"PR-2 рядок {i} ({rid}): iterations '{it_s}' має бути цілим числом.")
                        if not art or not (art.endswith(".csv") or art.endswith(".md")) or not os.path.isfile(art) or os.path.getsize(art) == 0:
                            errors.append(f"PR-3 / X-23 рядок {i} ({rid}): artifact '{art}' має існувати, бути непорожнім та мати розширення .csv/.md.")
                        elif not art.startswith(f"{target_dir}/"):
                            other_portfolio_runs += 1

                    if has_input_yes >= 3:
                        successes.append(f"PR-1: У {has_input_yes} запусках has_input=yes (>= 3).")
                    else:
                        errors.append(f"PR-1: Лише {has_input_yes} запусків з has_input=yes (мінімум 3).")
                    if iter_ge_2 >= 1:
                        successes.append(f"PR-2: Знайдено {iter_ge_2} ітеративний запуск(и) з iterations >= 2.")
                    else:
                        errors.append("PR-2: Відсутній жоден запуск з iterations >= 2.")
                    if other_portfolio_runs >= 1:
                        successes.append(f"PR-6 / X-23: Знайдено {other_portfolio_runs} запуски на інших файлах портфеля.")
                    else:
                        errors.append("PR-6 / X-23: Відсутній запуск на іншому файлі портфеля поза lr17_ai_assistant.")
                    if not any("PR-3" in e for e in errors):
                        successes.append("PR-3: Усі посилання artifact у prompts.csv ведуть на реальні непорожні файли.")
        except Exception as e:
            errors.append(f"Помилка читання prompts.csv: {e}")

    # 4. Валідація errors.csv (ER-1..2)
    if os.path.isfile(errors_path):
        try:
            with open(errors_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                expected_cols = ["error_id", "run_id", "error_type", "what_ai_said", "why_wrong", "how_noticed", "fix"]
                if reader.fieldnames != expected_cols:
                    errors.append(f"ER-1: Некоректний заголовок errors.csv {reader.fieldnames}, очікується {expected_cols}.")
                else:
                    successes.append("ER-1: Заголовок errors.csv валідний.")
                    rows = list(reader)
                    if len(rows) >= 3:
                        successes.append(f"ER-1: Знайдено {len(rows)} зафіксовані помилки AI (>= 3).")
                    else:
                        errors.append(f"ER-1: Знайдено лише {len(rows)} помилок (мінімум 3).")
                    seen_eids = set()
                    err_types = set()
                    for i, row in enumerate(rows, start=2):
                        eid = row.get("error_id", "").strip()
                        rid = row.get("run_id", "").strip()
                        etype = row.get("error_type", "").strip()
                        what = row.get("what_ai_said", "").strip()
                        why = row.get("why_wrong", "").strip()
                        how = row.get("how_noticed", "").strip()
                        fix = row.get("fix", "").strip()
                        if eid in seen_eids:
                            errors.append(f"ER-1 рядок {i}: дублікат error_id '{eid}'.")
                        seen_eids.add(eid)
                        if valid_run_ids and rid not in valid_run_ids:
                            errors.append(f"ER-1 рядок {i} ({eid}): run_id '{rid}' відсутній у prompts.csv.")
                        err_types.add(etype)
                        if not what or not why or not how or not fix:
                            errors.append(f"ER-2 рядок {i} ({eid}): порожнє поле опису або способу виявлення помилки.")
                    if len(err_types) >= 2:
                        successes.append(f"ER-1: Покрито різні типи помилок {sorted(err_types)} (>= 2).")
                    else:
                        errors.append(f"ER-1: Недостатньо типів помилок: {sorted(err_types)} (мінімум 2).")
                    if not any("ER-2" in e for e in errors):
                        successes.append("ER-2: Усі помилки містять конкретні формулювання AI та джерело звірки.")
        except Exception as e:
            errors.append(f"Помилка читання errors.csv: {e}")

    # 5. Валідація time_saved.csv (TS-1..4)
    if os.path.isfile(time_saved_path):
        try:
            with open(time_saved_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                expected_cols = ["case_id", "task", "basis", "minutes_manual", "minutes_ai", "minutes_review", "minutes_saved", "how_measured"]
                if reader.fieldnames != expected_cols:
                    errors.append(f"TS-1: Некоректний заголовок time_saved.csv {reader.fieldnames}, очікується {expected_cols}.")
                else:
                    successes.append("TS-1: Заголовок time_saved.csv валідний.")
                    rows = list(reader)
                    if len(rows) >= 3:
                        successes.append(f"TS-1: Знайдено {len(rows)} виміряних/оцінених кейсів (>= 3).")
                    else:
                        errors.append(f"TS-1: Знайдено лише {len(rows)} кейсів (мінімум 3).")
                    measured_cnt = 0
                    negative_cnt = 0
                    for i, row in enumerate(rows, start=2):
                        cid = row.get("case_id", "").strip()
                        basis = row.get("basis", "").strip()
                        if basis == "measured":
                            measured_cnt += 1
                        try:
                            m_man = float(row.get("minutes_manual", "").strip())
                            m_ai = float(row.get("minutes_ai", "").strip())
                            m_rev = float(row.get("minutes_review", "").strip())
                            m_sav = float(row.get("minutes_saved", "").strip())
                            if abs((m_man - m_ai - m_rev) - m_sav) > 0.01:
                                errors.append(f"TS-1 рядок {i} ({cid}): {m_man} - {m_ai} - {m_rev} != {m_sav}.")
                            if m_rev <= 0:
                                errors.append(f"TS-3 рядок {i} ({cid}): minutes_review ({m_rev}) має бути > 0.")
                            if m_sav < 0:
                                negative_cnt += 1
                        except ValueError:
                            errors.append(f"TS-1 рядок {i} ({cid}): некоректні числові поля часу.")
                    if measured_cnt >= 1:
                        successes.append(f"TS-2: Присутній реальний хронометраж (basis=measured: {measured_cnt}).")
                    else:
                        errors.append("TS-2: Відсутній жоден рядок з basis=measured.")
                    if not any("TS-3" in e for e in errors):
                        successes.append("TS-3: Час на перевірку (minutes_review > 0) враховано у кожному кейсі.")
                    if not any("TS-1 рядок" in e for e in errors):
                        successes.append("TS-1: Формула minutes_saved = minutes_manual - minutes_ai - minutes_review точна.")
                    if negative_cnt >= 1:
                        successes.append(f"TS-4: Враховано чесний негативний кейс ({negative_cnt} з від'ємною економією).")
        except Exception as e:
            errors.append(f"Помилка читання time_saved.csv: {e}")

    # 6. Валідація policy.csv (PL-1..4)
    if os.path.isfile(policy_path):
        try:
            with open(policy_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                expected_cols = ["rule_id", "case", "mode", "owner", "check", "why"]
                if reader.fieldnames != expected_cols:
                    errors.append(f"PL-1: Некоректний заголовок policy.csv {reader.fieldnames}, очікується {expected_cols}.")
                else:
                    successes.append("PL-1: Заголовок policy.csv валідний.")
                    rows = list(reader)
                    if len(rows) >= 5:
                        successes.append(f"PL-1: Знайдено {len(rows)} правил автономії AI (>= 5).")
                    else:
                        errors.append(f"PL-1: Знайдено лише {len(rows)} правил (мінімум 5).")
                    modes = {"forbidden": 0, "draft": 0, "autonomous": 0}
                    file_mentions = 0
                    pii_forbidden = False
                    for i, row in enumerate(rows, start=2):
                        rid = row.get("rule_id", "").strip()
                        case = row.get("case", "").strip()
                        mode = row.get("mode", "").strip()
                        check = row.get("check", "").strip()
                        why = row.get("why", "").strip()
                        if mode not in modes:
                            errors.append(f"PL-1 рядок {i} ({rid}): невідомий mode '{mode}'.")
                        else:
                            modes[mode] += 1
                        combined = f"{case} {check} {why}".lower()
                        if ".csv" in combined or ".md" in combined:
                            file_mentions += 1
                        if mode == "forbidden" and any(k in combined for k in ("персональн", "конфіденційн", "парол")):
                            pii_forbidden = True

                    if modes["forbidden"] >= 2 and modes["draft"] >= 2 and modes["autonomous"] >= 1:
                        successes.append(f"PL-1 / PL-4: Баланс режимів дотримано {modes}.")
                    else:
                        errors.append(f"PL-1 / PL-4: Порушено баланс режимів {modes} (потрібно >=2 forbidden, >=2 draft, >=1 autonomous).")
                    if file_mentions >= 1:
                        successes.append(f"PL-2: Названо конкретні файли портфеля у правилах ({file_mentions}).")
                    else:
                        errors.append("PL-2: Жодне правило політики не посилається на файл портфеля.")
                    if pii_forbidden:
                        successes.append("PL-3: Зафіксовано заборону передачі персональних/конфіденційних даних.")
                    else:
                        errors.append("PL-3: Відсутня явна заборона передачі персональних даних.")
        except Exception as e:
            errors.append(f"Помилка читання policy.csv: {e}")

    # 7. Валідація README.md
    if os.path.isfile(readme_path):
        try:
            with open(readme_path, mode="r", encoding="utf-8") as f:
                rm_content = f.read()

            required_rm_sections = [
                "0. Інструмент і вхід",
                "1. Автоматизований крок",
                "2. Дві версії одного переліку",
                "3. Помилки інструмента",
                "4. Заощаджений час",
                "5. Правило роботи з AI на моєму проєкті",
                "6. Промпти",
            ]
            last_pos = -1
            order_ok = True
            for sec in required_rm_sections:
                pos = rm_content.find(sec)
                if pos == -1:
                    errors.append(f"README.md: Відсутній обов'язковий розділ '{sec}'.")
                else:
                    if pos < last_pos:
                        order_ok = False
                    last_pos = pos
            if order_ok and not any("Відсутній обов'язковий розділ" in e for e in errors):
                successes.append("README.md: Усі 7 обов'язкових розділів (0..6) присутні у правильному порядку.")

            placeholders = re.findall(r"<[^>\n]{2,}>", rm_content)
            allowed_marker = "<нотатки N-01 ... N-14>"
            real_placeholders = [
                p for p in placeholders
                if p != allowed_marker and not re.match(r"^<(https?://|!--|/?[a-z1-6]+>?)", p, re.IGNORECASE)
            ]
            if real_placeholders:
                errors.append(f"README.md: Виявлено невидалені плейсхолдери у кутових дужках: {real_placeholders[:3]}")
            else:
                successes.append("README.md: Неприпустимі плейсхолдери у кутових дужках відсутні.")
        except Exception as e:
            errors.append(f"Помилка читання README.md: {e}")

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
    if len(sys.argv) > 1:
        target = sys.argv[1]
        if "charter" in target or "lr05" in target:
            sys.exit(validate_charter(target))
        elif "backlog" in target or "lr06" in target:
            sys.exit(validate_backlog(target))
        elif "wbs" in target or "lr07" in target:
            sys.exit(validate_wbs(target))
        elif "poker" in target or "lr08" in target:
            sys.exit(validate_poker(target))
        elif "forecast" in target or "lr09" in target:
            sys.exit(validate_forecast(target))
        elif "review" in target or "lr10" in target:
            sys.exit(validate_review(target))
        elif "risk" in target or "debt" in target or "quality" in target or "lr11" in target:
            sys.exit(validate_risks_quality(target))
        elif "comm" in target or "raci" in target or "lr12" in target:
            sys.exit(validate_communication(target))
        elif "metric" in target or "flow" in target or "dash" in target or "lr14" in target:
            sys.exit(validate_metrics(target))
        elif "status" in target or "impact" in target or "lr15" in target:
            sys.exit(validate_status_report(target))
        elif "budget" in target or "rate" in target or "lr16" in target:
            sys.exit(validate_budget(target))
        elif "ai" in target or "assist" in target or "lr17" in target:
            sys.exit(validate_ai_assistant(target))
        else:
            sys.exit(validate_case(target))
    else:
        labs = []
        if os.path.isdir("lr01_case"):
            labs.append(("lr01_case", validate_case))
        if os.path.isdir("lr05_charter"):
            labs.append(("lr05_charter", validate_charter))
        if os.path.isdir("lr06_backlog"):
            labs.append(("lr06_backlog", validate_backlog))
        if os.path.isdir("lr07_wbs"):
            labs.append(("lr07_wbs", validate_wbs))
        if os.path.isdir("lr08_poker"):
            labs.append(("lr08_poker", validate_poker))
        if os.path.isdir("lr09_forecast"):
            labs.append(("lr09_forecast", validate_forecast))
        if os.path.isdir("lr10_review"):
            labs.append(("lr10_review", validate_review))
        if os.path.isdir("lr11_risks_quality"):
            labs.append(("lr11_risks_quality", validate_risks_quality))
        if os.path.isdir("lr12_communication"):
            labs.append(("lr12_communication", validate_communication))
        if os.path.isdir("lr14_metrics"):
            labs.append(("lr14_metrics", validate_metrics))
        if os.path.isdir("lr15_status_report"):
            labs.append(("lr15_status_report", validate_status_report))
        if os.path.isdir("lr16_budget"):
            labs.append(("lr16_budget", validate_budget))
        if os.path.isdir("lr17_ai_assistant"):
            labs.append(("lr17_ai_assistant", validate_ai_assistant))

        overall_res = 0
        for ldir, val_fn in labs:
            res = val_fn(ldir)
            if res != 0:
                overall_res = 1
        sys.exit(overall_res)
