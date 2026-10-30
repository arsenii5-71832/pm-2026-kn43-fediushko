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


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "lr01_case"
    if "charter" in target or "lr05" in target:
        sys.exit(validate_charter(target))
    elif "backlog" in target or "lr06" in target:
        sys.exit(validate_backlog(target))
    else:
        sys.exit(validate_case(target))
