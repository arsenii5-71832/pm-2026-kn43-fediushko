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

        overall_res = 0
        for ldir, val_fn in labs:
            res = val_fn(ldir)
            if res != 0:
                overall_res = 1
        sys.exit(overall_res)
