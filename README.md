# Agent Skills

A collection of agent skills for AI coding agents. Skills are packaged instructions that extend agent capabilities.

Works with Claude Code, Antigravity, Cursor, Codex, Amp, Cline, and [35+ other agents](https://github.com/vercel-labs/skills#supported-agents).

## Installation

```bash
npx skills add Smolevich/agent-skills
```

The CLI auto-detects your installed agents and sets up skills for each one.

Install a specific skill:

```bash
npx skills add Smolevich/agent-skills --skill linkedin-post-optimizer
```

## Available Skills

### linkedin-post-optimizer

Transform raw ideas into authentic LinkedIn posts adapted to the user's profile level, voice, and audience. Includes AI slop detection, voice preservation, and engagement optimization.

**Features:**
- 10-step workflow: idea → stats → topic sharpening → writing → expert review → refinement
- Profile-aware (Beginner / Intermediate / Advanced)
- Anti-AI-slop: actively removes patterns that scream "ChatGPT wrote this"
- Multilingual: RU/EN with language-audience mismatch detection
- Built-in expert review and iterative refinement loop

[View skill →](skills/linkedin-post-optimizer/SKILL.md)

## Usage

Once installed, skills activate automatically when you ask your agent a relevant question.

**Claude Code:**
```bash
/linkedin-post-optimizer drafts/my-post.md
```

**Codex / Antigravity / Cursor / other agents:**
```
"Write a LinkedIn post about switching from Cursor to CLI-first AI workflow"
```

## Skill Structure

Each skill contains:
- `SKILL.md` — Instructions for the agent
- `references/` — Supporting documentation (optional)
- `evals/` — Test cases (optional)

## jev-score — оценка черновика по прошлым постам

CLI, который говорит, насколько черновик LinkedIn-поста сильный на фоне ваших же прошлых
постов: оценка 1–10 и квантиль, сила крючка в первых двух строках, 1–2 самых похожих
залетевших поста с цифрами, 2–3 точечные правки и проверка правил (≤200 слов, личное
начало, один вопрос в CTA). Текст целиком не переписывается.

```bash
uv run jev-score corpus                       # один раз и после каждой новой выгрузки
uv run jev-score drafts/2026-10-12-post.md    # оценка черновика
uv run jev-score drafts/...md --no-edits      # без правок от Claude
uv run jev-score loo                          # leave-one-out по корпусу
```

Запускать из каталога, где лежат `data/` (выгрузки LinkedIn) и `drafts/`.

### Данные — вне репозитория

Репозиторий публичный, поэтому тексты постов, метрики и кэш признаков лежат в
`~/.local/share/jev-score/` (или `$JEV_SCORE_HOME`), а тесты работают на синтетике.

Корпус собирается из того, что LinkedIn отдаёт сам, без браузера:

- `data/*/aggregate_analytics.xlsx`, лист TOP POSTS — топ-50 по показам и по вовлечению;
- `Shares.csv` из полной выгрузки (`~/Downloads/*LinkedInDataExport*.zip`) — тексты постов;
- `drafts/*.md` — тексты постов, вышедших после выгрузки (сопоставляются по словам slug-а
  в URL, а для slug-а из имени вложения — по дате и имени файла; при двух кандидатах пост
  остаётся без текста);
- `data/**/*post-analytics*.xlsx` — выгрузки отдельных постов: комментарии, сохранения, охват;
- `matches.json` в каталоге данных — ручные сопоставления `{"<id поста>": "<файл черновика>" | null}`
  для случаев, которые автоматика честно не решает.

Чего нет в выгрузках (доля показов вне сети, комментарии и сохранения у большинства постов),
то помечается в `jev-score corpus` как отсутствующее и не выдумывается. Посты из `Shares.csv`,
опубликованные в окне выгрузки, но не попавшие в топ-50, идут в корпус как «ниже топа»:
точных показов у них нет, для обучения берётся половина порога топ-50.

### Почему Jev считает признаки, а правки пишет Claude

Jev (System One модель TypeSafe) не генерирует текст и не умеет «оценить по образцам»:
он отвечает вероятностями на узкие вопросы о тексте. Поэтому разделение такое:

1. **Jev** на каждый пост отвечает на 14 вопросов (2 Score: сила крючка, конкретика;
   12 Noul: личное начало, деньги и цены, собственный результат, неожиданный тезис,
   признание промаха, лёгкий вопрос в конце, корпоративный тон и т. д.). Признаки
   корпуса кэшируются по хэшу текста.
2. **Код** добавляет то, что считается точно (длина, число в крючке, один вопрос в CTA, язык),
   и строит композит: вес признака — его корреляция с log показов на прошлых постах. На
   ~50 постах регрессия (и ridge тоже) подгоняется под шум и в leave-one-out была не лучше
   монетки (Spearman −0.01), а композит с весами-корреляциями без подбираемых параметров
   даёт 16 из 25 залетевших выше нижней половины и Spearman 0.19. Сигнал слабый — это
   ориентир, а не прогноз охвата.
3. **Jev** ещё раз — сравнивает черновик с 15 залетевшими постами (один Noul на пару),
   отсюда «похож на».
4. **Claude** (`claude -p --model sonnet`, без инструментов) получает tone-guide, черновик,
   три признака, которые сильнее всего тянут прогноз вниз, и нарушенные правила — и
   формулирует 2–3 правки строкой «было → стало — зачем».

### Ключ

`TYPESAFE_API_KEY` берётся из окружения. Ключ Jev лежит в Vault `secret/find-job/jev`
(поле `api_key`); как достать его на время запуска — `~/pet-projects/docs/secrets.md`.

### Сколько стоит

Один прогон черновика — два запроса к Jev (~10 тыс. входных токенов, около $0.0004)
и один ход Claude sonnet (≈$0.08 по оценке Claude Code, идёт в подписку). Первый сбор
признаков по корпусу — ещё ~50 запросов к Jev, порядка $0.005.

## License

MIT
