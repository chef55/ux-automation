# -*- coding: utf-8 -*-
"""
Интеллектуальный модуль сценарного тестирования пригодности использования.

Архитектурные решения:
  - ModelCoefficients — все обучаемые параметры в одном объекте (RL-точка входа)
  - TF-IDF косинус через sklearn для Information Scent
  - Байесовский сюрприз D_KL(P_prior || P_posterior)
  - Нормальное распределение с корреляционной матрицей для популяции
  - KLM/MHP масштабируются линейно внутри физиологических диапазонов из таблиц РПЗ
  - Пошаговый лог траектории (StepRecord) для будущего RL-цикла
  - Воспроизводимость через изолированный rng на сессию
  - FullState — единый объект состояния сессии (MDP-совместимость)
  - ActionType + backtracking — агент может возвращаться назад
  - Вероятностный backtracking: p = base_p * (1 − best_scent)
  - Краткосрочная память агента: visited set в FullState, предотвращение циклов
  - ERROR_RECOVERY hub-bias: узлы с высокой навигационной значимостью получают бонус Q

Выходной формат:
[{
    'age':     int,
    'clicks':  [id, id, ...],
    'time':    [float, ...],   # мс от начала сессии
    'success': int | -1
}, ...]
"""

from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# =============================================================================
# 0. КОНСТАНТЫ
# =============================================================================

# Нормализация времени в Q(s,a): делитель, чтобы T ∈ [0, 1]
STEP_TIME_NORM_MS: float = 12_000.0

# Бонус Information Scent для элемента, совпадающего с target_id
TARGET_SCENT_BONUS: float = 0.8

# Минимально возможное время одного шага (мс)
MIN_STEP_MS: float = 80.0

# Верхняя граница tau_p (мс) — защита при малых weight
TAU_P_CAP_MS: float = 1_200.0

# Ограничение краткосрочной памяти агента: Miller's Law (7 ± 2)
# Агент помнит только последние WM_MEMORY_SPAN посещённых узлов
WM_MEMORY_SPAN: int = 7


class MHP:
    """Диапазоны Model Human Processor (мс)."""
    TAU_P_MIN: ClassVar[float] = 50.0
    TAU_P_MAX: ClassVar[float] = 200.0
    TAU_C_MIN: ClassVar[float] = 25.0
    TAU_C_MAX: ClassVar[float] = 170.0
    TAU_M_MIN: ClassVar[float] = 30.0
    TAU_M_MAX: ClassVar[float] = 100.0
    WM_MIN:    ClassVar[int]   = 5
    WM_MAX:    ClassVar[int]   = 9


class KLM:
    """Временные операторы KLM (мс, таблица 2 РПЗ)."""
    KEY_PRESS_MIN:    ClassVar[float] = 80.0
    KEY_PRESS_MAX:    ClassVar[float] = 1_200.0
    POINT:            ClassVar[float] = 1_100.0
    HAND_MOVE:        ClassVar[float] =   400.0
    MENTAL_PREP:      ClassVar[float] = 1_350.0
    MOUSE_CLICK:      ClassVar[float] =   100.0
    LINK_CLICK:       ClassVar[float] = 3_730.0
    DROPDOWN_NO_LOAD: ClassVar[float] = 3_040.0
    DROPDOWN_LOAD:    ClassVar[float] = 3_960.0
    SCROLL:           ClassVar[float] = 3_960.0
    TEXT_INPUT:       ClassVar[float] = 2_320.0

    TAG_TO_KLM: ClassVar[Dict[str, float]] = {
        "a":        3_730.0,
        "button":   3_730.0,
        "input":    2_320.0,
        "select":   3_040.0,
        "textarea": 2_320.0,
        "div":      100.0 + 1_350.0,
        "span":     100.0 + 1_350.0,
        "li":       3_730.0,
        "nav":      100.0 + 1_350.0,
        "section":  3_960.0,
        "header":   100.0,
        "footer":   3_960.0,
    }

    @classmethod
    def for_tag(cls, tag: str) -> float:
        return cls.TAG_TO_KLM.get(tag.lower(), cls.MOUSE_CLICK + cls.MENTAL_PREP)


# =============================================================================
# 1. ОБУЧАЕМЫЕ КОЭФФИЦИЕНТЫ (RL-точка входа)
# =============================================================================

@dataclass
class ModelCoefficients:
    """
    Все параметры, подбираемые через RL.

    Для RL-агента этот объект — action space:
    агент меняет значения, прогоняет симуляцию, получает скаляр метрики
    (например, расхождение с реальными пользователями) и обновляет коэффициенты.

    Три группы параметров:
      - reward_weights : веса Q(s,a) = w1·G − w2·T − w3·C
      - timing_fitts   : коэффициенты закона Фиттса (a, b)
      - timing_hick    : коэффициент закона Хика-Хаймана (b)
    """
    # Q(s,a) = w_scent·G − w_time·T − w_surprise·C
    w_scent:    float = 1.00
    w_time:     float = 0.25
    w_surprise: float = 0.35

    # Закон Фиттса: tau_m_fitts = fitts_a + fitts_b · log2(1 + D/W)
    fitts_a: float = 50.0
    fitts_b: float = 120.0

    # Закон Хика-Хаймана: добавка к tau_c = hick_b · log2(n+1)
    hick_b: float = 150.0

    # Гауссов шум: σ как доля от базового времени
    noise_sigma: float = 0.12

    # Вероятность отказа при переполнении рабочей памяти
    wm_overload_p_abandon: float = 0.45

    # Вероятность backtracking при плохом scent (для SEARCH / ERROR_RECOVERY)
    p_backtrack: float = 0.15

    # Штраф за backtracking в reward
    backtrack_penalty: float = 0.40

    # Вес hub-bias в Q при ERROR_RECOVERY: Q += w_hub * hub_score(node)
    w_hub_bias: float = 0.30

    def as_vector(self) -> np.ndarray:
        """Сериализация в вектор для RL-агента."""
        return np.array([
            self.w_scent, self.w_time, self.w_surprise,
            self.fitts_a, self.fitts_b, self.hick_b,
            self.noise_sigma, self.wm_overload_p_abandon,
            self.p_backtrack, self.backtrack_penalty,
            self.w_hub_bias,
        ], dtype=float)

    @classmethod
    def from_vector(cls, v: np.ndarray) -> "ModelCoefficients":
        """Десериализация из вектора RL-агента."""
        return cls(
            w_scent               = float(v[0]),
            w_time                = float(v[1]),
            w_surprise            = float(v[2]),
            fitts_a               = float(v[3]),
            fitts_b               = float(v[4]),
            hick_b                = float(v[5]),
            noise_sigma           = float(v[6]),
            wm_overload_p_abandon = float(v[7]),
            p_backtrack           = float(v[8]) if len(v) > 8 else 0.15,
            backtrack_penalty     = float(v[9]) if len(v) > 9 else 0.40,
            w_hub_bias            = float(v[10]) if len(v) > 10 else 0.30,
        )

    def clamp(self) -> "ModelCoefficients":
        """
        Ограничивает параметры физически разумными границами.
        Вызывать после каждого шага RL, чтобы не выйти в нефизичную область.
        """
        return ModelCoefficients(
            w_scent               = max(0.0, self.w_scent),
            w_time                = max(0.0, self.w_time),
            w_surprise            = max(0.0, self.w_surprise),
            fitts_a               = float(np.clip(self.fitts_a,               0.0, 500.0)),
            fitts_b               = float(np.clip(self.fitts_b,               0.0, 500.0)),
            hick_b                = float(np.clip(self.hick_b,                0.0, 500.0)),
            noise_sigma           = float(np.clip(self.noise_sigma,           0.0,   0.5)),
            wm_overload_p_abandon = float(np.clip(self.wm_overload_p_abandon, 0.0,   1.0)),
            p_backtrack           = float(np.clip(self.p_backtrack,           0.0,   0.5)),
            backtrack_penalty     = float(np.clip(self.backtrack_penalty,     0.0,   2.0)),
            w_hub_bias            = float(np.clip(self.w_hub_bias,            0.0,   2.0)),
        )


# =============================================================================
# 2. КОНТРАКТЫ ДАННЫХ
# =============================================================================

class TaskType(Enum):
    NAVIGATION     = "navigation"
    SEARCH         = "search"
    CONVERSION     = "conversion"
    ERROR_RECOVERY = "error_recovery"


class ActionType(Enum):
    """
    Типы действий агента в MDP.
    FORWARD — переход к выбранному элементу (основное действие).
    BACK    — возврат к предыдущему узлу (backtracking при ошибке).
    """
    FORWARD = "forward"
    BACK    = "back"


@dataclass
class FullState:
    """
    Единый объект состояния сессии (MDP-совместимость).

    Объединяет позицию в интерфейсе и внутреннее состояние агента.
    Передаётся в StepRecord как снимок перед действием — это даёт
    полный кортеж (s, a, r, s') для RL без дополнительных усилий.
    """
    current_node_id: int
    fatigue:         float
    wm_load:         int
    steps:           int
    prev_node_id:     Optional[int]  = None                               # для backtracking
    last_k_visited:   Tuple[int, ...] = field(default_factory=tuple)       # краткосрочная память (Miller: 7±2)

    @property
    def visited(self) -> frozenset:
        """Множество посещённых узлов из last_k_visited (для backward compat)."""
        return frozenset(self.last_k_visited)


@dataclass
class DOMElement:
    id:            int
    parent_id:     int
    tag:           str
    weight:        float   # визуальная заметность V ∈ [0, 1]
    text:          str     # агрегированный текст (после bubbling) — для scent/TF-IDF
    original_text: str = field(default='')  # исходный текст из DOM — для _is_success


@dataclass
class TaskConfig:
    task_type:       TaskType
    target_id:       Optional[int] = None
    target_keywords: List[str]     = field(default_factory=list)
    max_steps:       int           = 50


@dataclass
class AgentProfile:
    """
    Финальные параметры агента (мс / безразмерные).
    Все значения лежат строго внутри физиологических диапазонов MHP/KLM.
    """
    age: int
    skill: float          # уровень навыка пользователя ∈ [0.5, 1.5], из generate_population
    # MHP (мс)
    tau_p: float
    tau_c: float
    tau_m: float
    # KLM
    key_speed:    float
    # Поведенческие
    wm_max:       int
    p_detect:     float
    temperature:  float
    fatigue_rate: float
    alpha:        float   # коэффициент обучаемости (закон практики)


@dataclass
class QComponents:
    """
    Именованные компоненты Q(s,a) = w_scent·G − w_time·T − w_surprise·C [+ w_hub·H].

    Хранятся в StepRecord для интерпретируемости траектории и диплома.
    Позволяют разложить каждое решение агента на вклады отдельных факторов.
    """
    g:          float   # Information Scent ∈ [0, 1]
    time_cost:  float   # T = τ_step / STEP_TIME_NORM ∈ [0, ~1]
    surprise:   float   # C = D_KL / 5.0 ∈ [0, 1]
    hub_bias:   float   # H = hub_score ∈ [0, 1]; 0 если не ERROR_RECOVERY
    q_raw:      float   # итоговое Q до штрафа backtrack

    def to_reward(self, backtrack_penalty: float, is_back: bool) -> float:
        """R(s,a) = Q_raw − backtrack_penalty·I[BACK]."""
        return self.q_raw - (backtrack_penalty if is_back else 0.0)


@dataclass
class StepRecord:
    """
    Запись одного шага взаимодействия.

    Содержит всё необходимое для формирования кортежа (s, a, r, s') в RL:
      - state_before : FullState до действия (S)
      - action_type  : ActionType (FORWARD / BACK)
      - visible_ids  : id элементов, видимых агенту
      - chosen_id    : id выбранного элемента (A)
      - q_values     : Q(s,a) для всех кандидатов (для policy gradient)
      - scent        : G-компонента вознаграждения
      - surprise     : C-компонента вознаграждения
      - step_time_ms : τ_step (T-компонента)
      - reward       : скалярное R(s,a) этого шага
      - elapsed_ms   : накопленное время от начала сессии
    """
    step:         int
    state_before: FullState
    action_type:  ActionType
    visible_ids:  List[int]
    chosen_id:    int
    q_values:     List[float]
    q_components: QComponents   # именованные компоненты выбранного действия (§6.2)
    step_time_ms: float
    reward:       float
    elapsed_ms:   float

    # Shortcut-свойства для обратной совместимости с аналитикой
    @property
    def scent(self) -> float:
        return self.q_components.g

    @property
    def surprise(self) -> float:
        return self.q_components.surprise


@dataclass
class SessionResult:
    """
    Расширенный результат одной сессии.
    `to_output()` возвращает строго требуемый формат ТЗ.
    """
    age:        int
    skill:      float            # уровень навыка агента ∈ [0.5, 1.5]
    clicks:     List[int]
    time:       List[float]
    success:    int              # id успешного элемента или -1
    trajectory: List[StepRecord]

    def to_output(self) -> Dict[str, Any]:
        """Контракт ТЗ."""
        return {
            "age":     self.age,
            "skill":   round(self.skill, 4),
            "clicks":  self.clicks,
            "time":    self.time,
            "success": self.success,
        }


# =============================================================================
# 3. ГЕНЕРАТОР ПОПУЛЯЦИИ
# =============================================================================

class AgentFactory:
    """
    Многомерное нормальное распределение с корреляционной матрицей.

    Латентные переменные: [age, skill, motor]
    Корреляции:
        age  ↑  →  skill ↓ (−0.4),  motor ↓ (−0.3)
        skill ↑ →  motor ↑ (+0.2)

    Параметры MHP/KLM масштабируются линейно внутри физиологических
    диапазонов таблиц РПЗ через _lerp(lo, hi, t).
    """
    _CORR = np.array([
        [ 1.00, -0.40, -0.30],
        [-0.40,  1.00,  0.20],
        [-0.30,  0.20,  1.00],
    ])
    _L = np.linalg.cholesky(_CORR)

    def generate_population(
        self,
        count:      int,
        mean_age:   float = 35.0,
        std_age:    float = 10.0,
        mean_skill: float = 1.0,
        std_skill:  float = 0.1,
        seed:       Optional[int] = None,
    ) -> List[AgentProfile]:
        rng    = np.random.default_rng(seed)
        z_raw  = rng.standard_normal((3, count))
        z_corr = (self._L @ z_raw).T                        # [N, 3]

        ages   = np.clip(z_corr[:, 0] * std_age  + mean_age,   18, 90).astype(int)
        skills = np.clip(z_corr[:, 1] * std_skill + mean_skill, 0.5, 1.5)
        motors = np.clip(z_corr[:, 2] * 0.30     + 1.0,         0.5, 1.5)

        return [
            self._build(int(ages[i]), float(skills[i]), float(motors[i]))
            for i in range(count)
        ]



    @staticmethod
    def _lerp(lo: float, hi: float, t: float) -> float:
        return lo + (hi - lo) * float(np.clip(t, 0.0, 1.0))

    @staticmethod
    def _age_t(age: int) -> float:
        return (age - 18) / 72.0

    @staticmethod
    def _skill_t(skill: float) -> float:
        return 1.0 - (skill - 0.5) / 1.0

    def _build(self, age: int, skill: float, motor: float) -> AgentProfile:
        at = self._age_t(age)
        st = self._skill_t(skill)
        mt = self._skill_t(motor)
        return AgentProfile(
            age          = age,
            skill        = skill,
            tau_p        = self._lerp(MHP.TAU_P_MIN, MHP.TAU_P_MAX, 0.6 * at + 0.4 * st),
            tau_c        = self._lerp(MHP.TAU_C_MIN, MHP.TAU_C_MAX, 0.5 * at + 0.5 * st),
            tau_m        = self._lerp(MHP.TAU_M_MIN, MHP.TAU_M_MAX, 0.7 * at + 0.3 * mt),
            key_speed    = self._lerp(KLM.KEY_PRESS_MIN, KLM.KEY_PRESS_MAX, 0.4 * at + 0.6 * mt),
            wm_max       = int(round(self._lerp(MHP.WM_MAX, MHP.WM_MIN, at))),
            p_detect     = self._lerp(0.95, 0.45, 0.5 * at + 0.5 * st),
            temperature  = self._lerp(0.3,  3.0,  0.4 * at + 0.6 * st),
            fatigue_rate = self._lerp(0.003, 0.02, 0.5 * at + 0.5 * st),
            alpha        = self._lerp(0.25, 0.05, st),
        )


# =============================================================================
# 4. МЕНЕДЖЕР СРЕДЫ
# =============================================================================

_UNREACHABLE_DIST: int = 8


class EnvironmentManager:
    """DOM-дерево как двунаправленный граф с валидацией на входе."""

    def __init__(self, raw_dom_list: List[Dict]) -> None:
        self.nodes:    Dict[int, DOMElement]    = {}
        self.children: Dict[int, List[int]]     = defaultdict(list)
        self.parent:   Dict[int, Optional[int]] = {}
        self._build(raw_dom_list)
        self._bubble_text()
        self._validate_no_cycles()
        self._validate_connected()

    def _build(self, raw: List[Dict]) -> None:
        all_ids = {item["id"] for item in raw}
        for item in raw:
            _text = item.get("text", "")
            node = DOMElement(
                id            = item["id"],
                parent_id     = item["parent_id"],
                tag           = item.get("tag", "div"),
                weight        = float(item.get("weight", 0.5)),
                text          = _text,
                original_text = _text,
            )
            self.nodes[node.id] = node
            self.children[node.parent_id].append(node.id)
            self.parent[node.id] = node.parent_id if node.parent_id in all_ids else None

    def _bubble_text(self) -> None:
        """
        Проброс текста листьев вверх по дереву (text bubbling).

        Реальный пользователь видит текст кнопки/ссылки и ориентируется по нему,
        даже находясь в родительском узле. Без этого шага у всех промежуточных
        узлов (button, li, nav, header) text='' → scent=0 → агент не получает
        семантического сигнала и не может проложить путь к нужному элементу.

        Алгоритм: обход снизу вверх (post-order), каждый узел наследует
        агрегированный текст своих прямых детей, если своего текста нет.
        Тексты разделяются пробелом; дубли не убираются (TF-IDF сам взвесит).
        Исходный DOM не изменяется — меняются только объекты DOMElement в памяти.
        """
        # Топологический порядок: листья раньше родителей
        # BFS от корня даёт порядок сверху вниз → reverse = снизу вверх
        root = self.get_root_id()
        order: List[int] = []
        queue: deque = deque([root])
        while queue:
            nid = queue.popleft()
            order.append(nid)
            for child_id in self.children.get(nid, []):
                queue.append(child_id)

        for nid in reversed(order):
            node = self.nodes[nid]
            if node.text.strip():
                continue  # у узла уже есть свой текст — не перезаписываем
            child_texts = [
                self.nodes[cid].text
                for cid in self.children.get(nid, [])
                if self.nodes[cid].text.strip()
            ]
            if child_texts:
                node.text = " ".join(child_texts)

    def _validate_no_cycles(self) -> None:
        visited: set = set()
        stack = [self.get_root_id()]
        while stack:
            nid = stack.pop()
            if nid in visited:
                raise ValueError(f"DOM-граф содержит цикл у узла id={nid}")
            visited.add(nid)
            stack.extend(self.children.get(nid, []))

    def _validate_connected(self) -> None:
        root = self.get_root_id()
        visited: set = set()
        queue = deque([root])
        while queue:
            nid = queue.popleft()
            if nid in visited:
                continue
            visited.add(nid)
            for child in self.children.get(nid, []):
                queue.append(child)
        unreachable = set(self.nodes) - visited
        if unreachable:
            raise ValueError(
                f"DOM-граф несвязный: узлы {sorted(unreachable)} недостижимы из корня id={root}"
            )

    def get_root_id(self) -> int:
        for nid in self.nodes:
            if self.parent.get(nid) is None:
                return nid
        return next(iter(self.nodes))

    # Теги, которые реальный пользователь замечает при первичном сканировании
    # страницы (F-pattern, визуальные якоря) — всегда добавляются в visible.
    _LANDMARK_TAGS: ClassVar[frozenset] = frozenset({
        "header", "nav", "main", "footer", "aside", "form",
    })

    def get_visible_elements(self, current_id: int, depth: int = 15) -> List[DOMElement]:
        """
        BFS вниз на depth + siblings + родитель + landmark-узлы.

        Landmark-проброс моделирует визуальное сканирование страницы:
        реальный пользователь замечает header/nav даже не находясь рядом,
        поскольку они выделены визуально и семантически (позиция, размер, контраст).
        Без этого агент застревает в тяжёлых по weight, но пустых div-контейнерах
        и никогда не получает сигнала от навигационных зон с низким DOM-весом.

        ВАЖНО (исправление v9): landmark-проброс ограничен только теми landmark-узлами,
        которые являются предками текущего узла или их прямыми детьми (siblings на уровне
        предков). Это предотвращает смешение header и footer: находясь в header,
        агент не видит footer как опцию, и наоборот. Логика соответствует реальному
        поведению пользователя — он не перескакивает взглядом через весь интерфейс.
        """
        visited, result = {current_id}, []
        queue = deque([(current_id, 0)])
        while queue:
            nid, d = queue.popleft()
            for child_id in self.children.get(nid, []):
                if child_id not in visited and child_id in self.nodes:
                    visited.add(child_id)
                    result.append(self.nodes[child_id])
                    if d + 1 < depth:
                        queue.append((child_id, d + 1))
        par = self.parent.get(current_id)
        if par is not None and par in self.nodes:
            if par not in visited:
                result.append(self.nodes[par])
                visited.add(par)
            # Siblings: добавляем братьев текущего узла, но исключаем landmark-узлы
            # противоположной или несовместимой семантической зоны.
            #
            # Правило v9 (уточнено):
            #  - В header/nav → footer исключается
            #  - В footer → header/nav исключаются
            #  - В основном контенте (div/section/main/…) → header И footer
            #    исключаются как siblings, т.к. они представляют фиксированный
            #    chrome интерфейса (fixed/sticky), а не контентные блоки.
            #    Пользователь в теле страницы не «перепрыгивает» взглядом
            #    на header/footer — они вне его текущего контекста прокрутки.
            _CHROME_TAGS: frozenset = frozenset({"header", "footer"})  # fixed UI chrome
            _OPPOSITE_ZONES: Dict[str, frozenset] = {
                "header": frozenset({"footer"}),
                "footer": frozenset({"header", "nav"}),
                "nav":    frozenset({"footer"}),
            }
            # Зона текущего узла: идём вверх до первого landmark/chrome предка
            _zone_tags_to_exclude: frozenset = _CHROME_TAGS  # default: content → hide chrome siblings
            _nid_check = current_id
            while _nid_check in self.nodes:
                _t = self.nodes[_nid_check].tag.lower()
                if _t in _OPPOSITE_ZONES:
                    # Мы внутри header/nav/footer — применяем точечное исключение
                    _zone_tags_to_exclude = _OPPOSITE_ZONES[_t]
                    break
                _p_check = self.parent.get(_nid_check)
                if _p_check is None or _p_check not in self.nodes:
                    break
                _nid_check = _p_check

            for sib in self.children.get(par, []):
                if sib != current_id and sib not in visited and sib in self.nodes:
                    sib_tag = self.nodes[sib].tag.lower()
                    if sib_tag in _zone_tags_to_exclude:
                        continue  # не показываем семантически несовместимых соседей
                    result.append(self.nodes[sib])
                    visited.add(sib)

        # Landmark-проброс v9: только предки текущего узла и их прямые дети,
        # с фильтрацией семантически несовместимых зон.
        #
        # Единый источник истины об исключаемых зонах — _zone_tags_to_exclude,
        # вычисленный выше в sibling-блоке. Используем его и здесь, чтобы
        # ancestor broadcast не добавлял header/footer когда мы в основном контенте.
        ancestor_ids: set = set()
        nid = current_id
        while True:
            p = self.parent.get(nid)
            if p is None or p not in self.nodes:
                break
            ancestor_ids.add(p)
            nid = p

        for anc_id in ancestor_ids:
            # Сам предок-landmark (только если не в исключённой зоне)
            anc_node = self.nodes[anc_id]
            anc_tag = anc_node.tag.lower()
            if anc_tag in self._LANDMARK_TAGS and anc_id not in visited:
                if anc_tag not in _zone_tags_to_exclude:
                    result.append(anc_node)
                    visited.add(anc_id)
            # Прямые дети предка: только совместимые с текущей зоной landmark-узлы
            for child_id in self.children.get(anc_id, []):
                if child_id not in visited and child_id in self.nodes:
                    child_node = self.nodes[child_id]
                    child_tag = child_node.tag.lower()
                    if child_tag in self._LANDMARK_TAGS and child_tag not in _zone_tags_to_exclude:
                        result.append(child_node)
                        visited.add(child_id)

        return result if result else list(self.nodes.values())[:5]

    def hub_score(self, node_id: int) -> float:
        """
        Навигационная значимость узла ∈ [0, 1] для ERROR_RECOVERY bias.

        Критерии:
          - количество прямых детей (широта охвата)
          - навигационный тег (nav, header, main — опорные точки интерфейса)
          - визуальный вес (weight)

        Используется в CognitiveMotorEngine._q() при TaskType.ERROR_RECOVERY.
        """
        _HUB_TAGS = {"nav", "header", "main", "body", "section"}
        node = self.nodes.get(node_id)
        if node is None:
            return 0.0
        n_children   = len(self.children.get(node_id, []))
        max_children = max((len(v) for v in self.children.values()), default=1)
        child_score  = n_children / max(max_children, 1)
        tag_score    = 1.0 if node.tag.lower() in _HUB_TAGS else 0.0
        return float(np.clip(0.5 * child_score + 0.3 * tag_score + 0.2 * node.weight, 0.0, 1.0))

    def logical_distance(self, id_from: int, id_to: int) -> int:
        if id_from == id_to:
            return 0

        def neighbours(nid: int) -> List[int]:
            res = list(self.children.get(nid, []))
            p = self.parent.get(nid)
            if p is not None:
                res.append(p)
            return res

        visited = {id_from}
        queue: deque = deque([(id_from, 0)])
        while queue:
            cur, d = queue.popleft()
            for nb in neighbours(cur):
                if nb == id_to:
                    return d + 1
                if nb not in visited:
                    visited.add(nb)
                    queue.append((nb, d + 1))
        return _UNREACHABLE_DIST


# =============================================================================
# 5. INFORMATION SCENT (TF-IDF косинус)
# =============================================================================

class ScentVectorizer:
    """
    Обёртка над TfidfVectorizer из sklearn.

    Обучается один раз на всех текстах DOM + текст цели.
    Вычисляет косинусное сходство элемента с целью:
        G = cosine_similarity(v_elem, v_goal)

    Замена на sentence-transformers требует только переопределения
    fit() и scent() — интерфейс для движка остаётся прежним.
    """

    def __init__(self) -> None:
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._goal_vec = None

    def fit(self, dom_texts: List[str], goal_text: str) -> None:
        corpus = dom_texts + [goal_text]
        self._vectorizer = TfidfVectorizer(
            analyzer="word",
            token_pattern=r"(?u)\b[a-zA-Zа-яёА-ЯЁ]+\b",
            min_df=1,
            sublinear_tf=True,
        )
        self._vectorizer.fit(corpus)
        self._goal_vec = self._vectorizer.transform([goal_text])

    def scent(self, elem_text: str) -> float:
        """G ∈ [0, 1]: косинусное сходство текста элемента с целью."""
        if self._vectorizer is None or not elem_text.strip():
            return 0.0
        elem_vec = self._vectorizer.transform([elem_text])
        score = cosine_similarity(elem_vec, self._goal_vec)[0, 0]
        return float(np.clip(score, 0.0, 1.0))


# =============================================================================
# 6. БАЙЕСОВСКИЙ СЮРПРИЗ
# =============================================================================

def bayesian_surprise(prior_q: List[float], posterior_q: List[float]) -> float:
    """
    C = D_KL(P_prior ‖ P_posterior), формула 11 РПЗ.

    P строится через softmax(Q) с нейтральной температурой.
    Эпсилон добавляется до нормировки — сумма остаётся корректным
    вероятностным распределением.
    """
    def _softmax(q: List[float]) -> np.ndarray:
        a = np.array(q, dtype=float)
        a -= a.max()
        e = np.exp(a) + 1e-12   # ε до деления → нормировка корректна
        return e / e.sum()

    if len(prior_q) < 2 or len(posterior_q) < 2:
        return 0.0
    p = _softmax(prior_q)
    q = _softmax(posterior_q)
    n = min(len(p), len(q))
    return float(np.clip(np.sum(p[:n] * np.log(p[:n] / q[:n])), 0.0, 5.0))


# =============================================================================
# 7. КОГНИТИВНО-МОТОРНЫЙ ДВИЖОК
# =============================================================================

class CognitiveMotorEngine:
    """
    Вычисляет Q(s,a), выбирает действие через Softmax, считает τ_step.

    Принимает ModelCoefficients снаружи — RL-агент меняет коэффициенты,
    не трогая логику движка.
    """

    def __init__(
        self,
        agent:      AgentProfile,
        task:       TaskConfig,
        coeff:      ModelCoefficients,
        vectorizer: ScentVectorizer,
        rng:        np.random.Generator,
    ) -> None:
        self.agent      = agent
        self.task       = task
        self.coeff      = coeff
        self.vectorizer = vectorizer
        self.rng        = rng
        self._prev_q:   List[float] = []

    def _scent(self, elem: DOMElement) -> float:
        g = self.vectorizer.scent(elem.text)
        if self.task.target_id is not None and elem.id == self.task.target_id:
            g = min(1.0, g + TARGET_SCENT_BONUS)
        g += elem.weight * 0.05
        return float(np.clip(g, 0.0, 1.0))

    def _surprise(self, current_q: List[float]) -> float:
        return bayesian_surprise(self._prev_q, current_q) if self._prev_q else 0.0

    def _t_norm(self, elem: DOMElement, distance: int, n: int, step: int) -> float:
        return self._timing_base(elem, distance, n, step) / STEP_TIME_NORM_MS

    def _q(
        self,
        elem:     DOMElement,
        distance: int,
        n:        int,
        step:     int,
        surprise: float,
        env:      Optional["EnvironmentManager"] = None,
    ) -> QComponents:
        """
        Вычисляет Q(s,a) и возвращает именованные компоненты.

        Согласованность Q и R:
            Q_raw = w_scent·G − w_time·T − w_surprise·C [+ w_hub·H]
            R(s,a) = Q_raw − backtrack_penalty·I[BACK]

            Q используется для softmax-выбора действия.
            R — для логирования и RL-обучения.
            Единственное отличие: backtrack_penalty добавляется только в R,
            поскольку он не влияет на выбор между FORWARD-кандидатами.
        """
        g    = self._scent(elem)
        t    = self._t_norm(elem, distance, n, step)
        c    = surprise / 5.0
        h    = 0.0
        if self.task.task_type == TaskType.ERROR_RECOVERY and env is not None:
            h = env.hub_score(elem.id)
        q_raw = (
            self.coeff.w_scent    * g
            - self.coeff.w_time   * t
            - self.coeff.w_surprise * c
            + self.coeff.w_hub_bias * h
        )
        return QComponents(g=g, time_cost=t, surprise=c, hub_bias=h, q_raw=q_raw)

    def _task_temperature_scale(self, best_scent: float = 0.0) -> float:
        """
        Адаптивный масштаб температуры softmax.

        Базовые значения отражают тип задачи (SEARCH — исследование,
        NAVIGATION — целенаправленное движение). Но ключевой принцип:
        температура обратно пропорциональна лучшему scent в поле зрения.

        Когда агент видит элемент с высоким scent (он его «узнал»),
        выбор становится почти детерминированным — независимо от типа задачи.
        Это соответствует психологической модели: человек, заметивший нужную
        надпись, немедленно на неё кликает, не блуждает дальше.

        scale = base * (1 − confidence)
        где confidence = best_scent ** 0.5  ∈ [0, 1]
        """
        base = {
            TaskType.NAVIGATION:     0.7,
            TaskType.SEARCH:         1.3,
            TaskType.CONVERSION:     1.0,
            TaskType.ERROR_RECOVERY: 1.5,
        }.get(self.task.task_type, 1.0)
        # При best_scent=1.0 → confidence=1.0 → scale≈0 (почти жёсткий выбор)
        # При best_scent=0.0 → confidence=0.0 → scale=base (полное исследование)
        confidence = float(np.sqrt(np.clip(best_scent, 0.0, 1.0)))
        return float(np.clip(base * (1.0 - 0.85 * confidence), 0.05, base))

    def _p_backtrack(self) -> float:
        """Базовая вероятность backtracking по типу задачи."""
        base = self.coeff.p_backtrack
        return {
            TaskType.NAVIGATION:     base * 0.5,
            TaskType.SEARCH:         base * 1.0,
            TaskType.CONVERSION:     base * 0.7,
            TaskType.ERROR_RECOVERY: base * 2.0,
        }.get(self.task.task_type, base)

    def choose_action(
        self,
        perceived:  List[DOMElement],
        env:        "EnvironmentManager",
        state:      "FullState",
    ) -> Tuple[Optional[DOMElement], ActionType, List[float], List[float], float, QComponents]:
        """
        Возвращает (выбранный_элемент, action_type, q_values, scents, surprise).

        Surprise вычисляется здесь единожды и передаётся наружу —
        _session() использует его напрямую без повторного расчёта.

        Backtracking вероятностный:
            p_back = base_p * task_scale * (1 − best_scent)
        Нет жесткого порога — вероятность плавно растёт по мере
        снижения уверенности агента.

        Visited-фильтр:
            при FORWARD предпочитаем непосещённые узлы;
            уже посещённые получают штраф Q *= 0.5.
        """
        current_id = state.current_node_id
        step       = state.steps
        fatigue    = state.fatigue

        if not perceived:
            return None, ActionType.FORWARD, [], [], 0.0, QComponents(0.0, 0.0, 0.0, 0.0, 0.0)

        n         = len(perceived)
        distances = [env.logical_distance(current_id, e.id) for e in perceived]
        scents    = [self._scent(e) for e in perceived]

        # --- Единый источник surprise (§4 ТЗ) ---
        prior_q_proxy = [self.coeff.w_scent * s for s in scents]
        surprise      = self._surprise(prior_q_proxy)

        # Вычисляем компоненты Q для каждого кандидата
        qc_list: List[QComponents] = [
            self._q(e, d, n, step, surprise, env)
            for e, d in zip(perceived, distances)
        ]

        # q_raw — скаляр для softmax; штраф за повторное посещение (§4.2 ТЗ)
        q_values: List[float] = [
            qc.q_raw * 0.5 if e.id in state.visited else qc.q_raw
            for qc, e in zip(qc_list, perceived)
        ]

        self._prev_q = q_values.copy()

        # --- Вероятностный backtracking (§5.1 ТЗ) ---
        best_scent  = max(scents) if scents else 0.0
        p_back      = self._p_backtrack() * (1.0 - best_scent)
        if (
            state.prev_node_id is not None
            and float(self.rng.random()) < p_back
        ):
            prev_elem = env.nodes.get(state.prev_node_id)
            if prev_elem is not None:
                # Для backtrack-элемента считаем компоненты Q
                back_dist = env.logical_distance(current_id, prev_elem.id)
                back_qc   = self._q(prev_elem, back_dist, n, step, surprise, env)
                return prev_elem, ActionType.BACK, q_values, scents, surprise, back_qc

        # --- Forward: softmax с масштабом по задаче ---
        task_scale = self._task_temperature_scale(best_scent=best_scent)
        tau        = max(0.05, self.agent.temperature * (1.0 + fatigue) * task_scale)
        q_arr      = np.array(q_values, dtype=float)
        q_arr     -= q_arr.max()
        probs      = np.exp(q_arr / tau)
        probs     /= probs.sum()

        idx = int(self.rng.choice(n, p=probs))
        return perceived[idx], ActionType.FORWARD, q_values, scents, surprise, qc_list[idx]

    # Landmark-теги не срезаются перцептивным фильтром: реальный пользователь
    # всегда замечает header/nav при сканировании, независимо от их DOM-веса.
    _LANDMARK_TAGS: ClassVar[frozenset] = frozenset({
        "header", "nav", "main", "footer", "aside", "form",
    })

    # Теги, которые замечаются при сканировании меню навигации.
    # Когда пользователь смотрит на nav/header, он читает все пункты подряд.
    _MENU_TAGS: ClassVar[frozenset] = frozenset({
        "a", "button", "li", "span", "label",
    })

    def perceive(self, elements: List[DOMElement], fatigue: float) -> List[DOMElement]:
        """
        Стохастический перцептивный фильтр (формула 7) с landmark-исключением
        и усилением видимости элементов меню.

        Три режима:
        1. Landmark (header, nav, …) — p=1.0, всегда видим.
        2. Элементы меню (a, button, li, span, …) — p = max(weight-base, scent-boost).
           Ключевое изменение v9: weight НЕ является жёстким нижним ограничителем.
           Элемент с weight≈0 (например, span глубоко в DOM) всё равно замечается,
           если его текст семантически близок к цели (scent > порог).
           Это соответствует реальному поведению: пользователь читает текст ссылки,
           а не оценивает её CSS-вес. Формула:
               p = max(weight_p, scent_p)
               weight_p = weight * p_detect * (1 − fatigue_pen)   [мин. 0.05]
               scent_p  = 0.9 * p_detect * scent * (1 − fatigue_pen)
        3. Остальные элементы — стандартный стохастический фильтр по weight.
        """
        pen    = min(0.6, fatigue * 2.0)
        result = []
        for e in elements:
            tag = e.tag.lower()
            if tag in self._LANDMARK_TAGS:
                # Landmark: высокий приоритет, но не абсолютный (p ≥ 0.85).
                # Это позволяет scent-сигналу из глубоко вложенных элементов
                # конкурировать с навигационными зонами при softmax-выборе.
                # В v8 landmark'ы получали p=1.0 → агент всегда их замечал
                # и никогда не «заглядывал вглубь» в scent-rich ветки.
                p_landmark = float(np.clip(0.92 * (1.0 - 0.3 * pen), 0.85, 0.99))
                if float(self.rng.random()) < p_landmark:
                    result.append(e)
            elif tag in self._MENU_TAGS:
                # p = max(weight-based, scent-based) — оба сигнала конкурируют
                scent_val  = self.vectorizer.scent(e.text)
                weight_p   = float(np.clip(
                    e.weight * self.agent.p_detect * (1.0 - pen), 0.05, 0.99
                ))
                scent_p    = float(np.clip(
                    0.9 * self.agent.p_detect * scent_val * (1.0 - pen), 0.0, 0.99
                ))
                p_detect_eff = max(weight_p, scent_p)
                if float(self.rng.random()) < p_detect_eff:
                    result.append(e)
            elif float(self.rng.random()) < float(np.clip(
                e.weight * self.agent.p_detect * (1.0 - pen), 0.05, 0.99
            )):
                result.append(e)
        return result if result else [max(elements, key=lambda e: e.weight)]

    def step_time(
        self, elem: DOMElement, distance: int, n: int, step: int, fatigue: float
    ) -> float:
        """τ_step с множителем усталости и гауссовым шумом."""
        base   = self._timing_base(elem, distance, n, step)
        f_mult = 1.0 + self.agent.fatigue_rate * step
        noise  = float(self.rng.normal(1.0, self.coeff.noise_sigma))
        return max(MIN_STEP_MS, base * f_mult * noise)

    def _timing_base(self, elem: DOMElement, distance: int, n: int, step: int) -> float:
        a = self.agent

        # τ_p (формула 6)
        tau_p = a.tau_p * math.log2(max(1, n) + 1) / max(elem.weight, 0.01)
        tau_p = min(tau_p, TAU_P_CAP_MS)

        # τ_c (формулы 8, 10)
        hick  = self.coeff.hick_b * math.log2(n + 1)
        learn = a.tau_c * (max(1, step) ** -a.alpha)
        tau_c = learn + hick

        # τ_m (формула 12 + KLM)
        W_proxy = max(0.01, elem.weight) * 80.0
        fitts   = self.coeff.fitts_a + self.coeff.fitts_b * math.log2(1.0 + distance / W_proxy)
        klm     = KLM.for_tag(elem.tag) + a.key_speed
        if step == 0:
            klm += KLM.HAND_MOVE
        tau_m = fitts + klm

        return tau_p + tau_c + tau_m


# =============================================================================
# 8. МЕНЕДЖЕР СИМУЛЯЦИИ
# =============================================================================

class SimulationRunner:

    def __init__(self, env: EnvironmentManager, coeff: Optional[ModelCoefficients] = None) -> None:
        self.env   = env
        self.coeff = coeff or ModelCoefficients()
        self._vectorizer: Optional[ScentVectorizer] = None

    def run_batch(
        self,
        agents: List[AgentProfile],
        task:   TaskConfig,
        seed:   Optional[int] = None,
    ) -> List[SessionResult]:
        """
        Прогоняет сессии для всех агентов.

        ScentVectorizer обучается один раз на весь батч —
        DOM не меняется между агентами (исправлено относительно v2).
        Каждая сессия получает свой изолированный rng = Generator(seed + i).
        """
        self._vectorizer = self._build_vectorizer(task)
        results = []
        for i, agent in enumerate(agents):
            session_seed = (seed + i) if seed is not None else None
            rng = np.random.default_rng(session_seed)
            results.append(self._session(agent, task, rng))
        return results

    def _build_vectorizer(self, task: TaskConfig) -> ScentVectorizer:
        dom_texts  = [n.text for n in self.env.nodes.values()]
        goal_parts = list(task.target_keywords)
        if task.target_id is not None and task.target_id in self.env.nodes:
            goal_parts.append(self.env.nodes[task.target_id].text)
        goal_text = " ".join(goal_parts) or "target"
        vec = ScentVectorizer()
        vec.fit(dom_texts, goal_text)
        return vec

    # -------------------------------------------------------------------------
    # MDP-декомпозиция: три явных этапа шага (§1, §6 ТЗ)
    # -------------------------------------------------------------------------

    @staticmethod
    def _decide(
        engine:    CognitiveMotorEngine,
        env:       EnvironmentManager,
        perceived: List[DOMElement],
        state:     FullState,
    ) -> Tuple[Optional[DOMElement], ActionType, List[float], List[float], float, QComponents]:
        """π(a | s) — политика выбора действия."""
        return engine.choose_action(perceived, env, state)

    @staticmethod
    def _transition(
        state:       FullState,
        target:      DOMElement,
        action_type: ActionType,
        agent:       AgentProfile,
        dist:        int,
        step:        int,
        rng:         np.random.Generator,
        coeff:       ModelCoefficients,
    ) -> Tuple[FullState, bool]:
        """
        s' = T(s, a) — переход состояния.

        Возвращает (new_state, abandon):
          abandon=True означает, что WM-перегрузка вызвала отказ агента.
        """
        # Обновление краткосрочной памяти (Miller's Law: last WM_MEMORY_SPAN узлов)
        # Агент «забывает» давно посещённые узлы
        new_k = (state.last_k_visited + (state.current_node_id,))[-WM_MEMORY_SPAN:]
        # Landmark-узлы (header, nav, …) замечаются визуально — переход к ним
        # не увеличивает когнитивную нагрузку так же, как навигация по DOM-дереву.
        _LANDMARK_TAGS = frozenset({"header", "nav", "main", "footer", "aside", "form"})
        wm_delta = (
            0 if target.tag.lower() in _LANDMARK_TAGS
            else max(0, dist - 1)
        )
        new_wm = (
            max(0, state.wm_load - 2)
            if action_type == ActionType.BACK
            else state.wm_load + wm_delta
        )
        new_state = FullState(
            current_node_id = target.id,
            fatigue         = state.fatigue + agent.fatigue_rate,
            wm_load         = new_wm,
            steps           = step + 1,
            prev_node_id    = state.current_node_id,
            last_k_visited  = new_k,
        )
        # WM-перегрузка.
        # Вероятность бросить задачу масштабируется обратно к навыку агента:
        # крутой пользователь (высокий wm_max) справляется с когнитивной нагрузкой.
        # p_abandon = base * (wm_load − wm_max) / wm_max  — растёт с глубиной перегрузки
        if new_state.wm_load > agent.wm_max:
            overload_depth = (new_state.wm_load - agent.wm_max) / max(agent.wm_max, 1)
            p_abandon = float(np.clip(
                coeff.wm_overload_p_abandon * overload_depth / 2.0,
                0.01, coeff.wm_overload_p_abandon
            ))
            if float(rng.random()) < p_abandon:
                return new_state, True
            new_state = FullState(
                current_node_id = new_state.current_node_id,
                fatigue         = new_state.fatigue,
                wm_load         = max(0, new_state.wm_load - 3),
                steps           = new_state.steps,
                prev_node_id    = new_state.prev_node_id,
                last_k_visited  = new_state.last_k_visited,
            )
        return new_state, False

    @staticmethod
    def _compute_reward(
        qc:          QComponents,
        action_type: ActionType,
        coeff:       ModelCoefficients,
    ) -> float:
        """
        R(s, a) — функция вознаграждения.

        R = Q_raw − backtrack_penalty·I[BACK]

        Использует QComponents.to_reward() для явной согласованности Q и R:
        единственное отличие reward от Q — штраф за BACK-действие.
        """
        return qc.to_reward(coeff.backtrack_penalty, action_type == ActionType.BACK)

    # -------------------------------------------------------------------------

    def _session(
        self,
        agent: AgentProfile,
        task:  TaskConfig,
        rng:   np.random.Generator,
    ) -> SessionResult:
        assert self._vectorizer is not None

        engine = CognitiveMotorEngine(agent, task, self.coeff, self._vectorizer, rng)

        state = FullState(
            current_node_id = self.env.get_root_id(),
            fatigue         = 0.0,
            wm_load         = 0,
            steps           = 0,
            prev_node_id    = None,
            last_k_visited  = (),
        )

        clicks:     List[int]        = []
        times:      List[float]      = []
        trajectory: List[StepRecord] = []
        elapsed:    float            = 0.0
        success:    int              = -1

        for step in range(task.max_steps):
            # Адаптивная глубина BFS (исправление v9).
            # Для SEARCH: всегда используем depth=4, т.к. целевые элементы
            # могут быть глубоко вложены (например span#275, weight=0.0002).
            # Для NAVIGATION/CONVERSION: depth=2 по умолчанию, расширяем до 4
            # если лучший scent в окне ниже порога (агент «слеп» в текущей позиции).
            _use_depth = 15
            if task.task_type == TaskType.SEARCH:
                _use_depth = 15  # SEARCH всегда сканирует глубже
            else:
                raw_visible_probe = self.env.get_visible_elements(state.current_node_id, depth=15)
                _best_quick = max(
                    (engine.vectorizer.scent(e.text) for e in raw_visible_probe),
                    default=0.0,
                )
                if _best_quick < 0.05:
                    _use_depth = 15
                else:
                    raw_visible = raw_visible_probe  # переиспользуем, не пересчитываем
            raw_visible = self.env.get_visible_elements(state.current_node_id, depth=_use_depth)
            perceived   = engine.perceive(raw_visible, state.fatigue)

            # 1. π(a | s) — решение
            target, action_type, q_values, scents, surprise, chosen_qc = self._decide(
                engine, self.env, perceived, state
            )
            if target is None:
                break

            dist = self.env.logical_distance(state.current_node_id, target.id)

            # 2. τ_step — время шага
            t        = engine.step_time(target, dist, len(perceived), step, state.fatigue)
            elapsed += t

            # 3. R(s, a) = Q_raw − backtrack_penalty·I[BACK]  (§2.2 ТЗ: Q согласован с R)
            reward = self._compute_reward(chosen_qc, action_type, self.coeff)

            # Логирование до перехода (снимок s)
            clicks.append(target.id)
            times.append(round(elapsed, 2))
            trajectory.append(StepRecord(
                step         = step,
                state_before = FullState(
                    current_node_id = state.current_node_id,
                    fatigue         = state.fatigue,
                    wm_load         = state.wm_load,
                    steps           = state.steps,
                    prev_node_id    = state.prev_node_id,
                    last_k_visited  = state.last_k_visited,
                ),
                action_type  = action_type,
                visible_ids  = [e.id for e in perceived],
                chosen_id    = target.id,
                q_values     = q_values,
                q_components = chosen_qc,
                step_time_ms = t,
                reward       = reward,
                elapsed_ms   = elapsed,
            ))

            # 4. T(s, a) → s' — переход состояния
            state, abandon = self._transition(
                state, target, action_type, agent, dist, step, rng, self.coeff
            )
            if abandon:
                break

            if self._is_success(target, task):
                success = target.id
                state = FullState(
                    current_node_id = state.current_node_id,
                    fatigue         = state.fatigue,
                    wm_load         = 0,
                    steps           = state.steps,
                    prev_node_id    = state.prev_node_id,
                    last_k_visited  = state.last_k_visited,
                )
                break

        return SessionResult(
            age=agent.age, skill=agent.skill, clicks=clicks, time=times,
            success=success, trajectory=trajectory,
        )

    @staticmethod
    def _is_success(elem: DOMElement, task: TaskConfig) -> bool:
        if task.task_type in (TaskType.NAVIGATION, TaskType.CONVERSION):
            return elem.id == task.target_id
        if task.task_type == TaskType.SEARCH:
            # Проверяем только исходный текст элемента (до bubbling),
            # иначе любой предок с агрегированным текстом ложно засчитается как успех.
            tl = elem.original_text.lower()
            return any(kw.lower() in tl for kw in task.target_keywords)
        if task.task_type == TaskType.ERROR_RECOVERY:
            if task.target_id is not None and elem.id == task.target_id:
                return True
            if task.target_keywords:
                tl = elem.original_text.lower()
                return any(kw.lower() in tl for kw in task.target_keywords)
        return False


# =============================================================================
# 9. АНАЛИТИКА
# =============================================================================

class UsabilityMetrics:
    @staticmethod
    def compute(results: List[SessionResult]) -> Dict[str, Any]:
        n = len(results)
        if not n:
            return {}
        succ   = [r.success != -1 for r in results]
        n_succ = sum(succ)
        times  = [r.time[-1] if r.time else 0.0 for r in results]
        steps  = [len(r.clicks) for r in results]
        t_ok   = [t for t, s in zip(times, succ) if s]
        return {
            "n_simulations":        n,
            "p_success":            round(n_succ / n, 4),
            "p_error":              round(1 - n_succ / n, 4),
            "mean_task_time_ms":    round(float(np.mean(times)), 1),
            "std_task_time_ms":     round(float(np.std(times)), 1),
            "mean_time_success_ms": round(float(np.mean(t_ok)), 1) if t_ok else None,
            "mean_steps":           round(float(np.mean(steps)), 2),
            "std_steps":            round(float(np.std(steps)), 2),
            "min_steps":            int(np.min(steps)),
            "max_steps":            int(np.max(steps)),
        }


# =============================================================================
# 10. ПУБЛИЧНЫЙ API
# =============================================================================

def run_simulation(
    dom_list:    List[Dict],
    task_config: TaskConfig,
    n_agents:    int   = 30,
    mean_age:    float = 35.0,
    std_age:     float = 10.0,
    mean_skill:  float = 1.0,
    std_skill:   float = 0.1,
    coeff:       Optional[ModelCoefficients] = None,
    seed:        Optional[int] = 42,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Точка входа для внешнего использования.

    Для RL-цикла:
        coeff_vec = coeff.as_vector()
        # ... RL-агент меняет coeff_vec ...
        new_coeff = ModelCoefficients.from_vector(coeff_vec).clamp()
        output, metrics = run_simulation(..., coeff=new_coeff)
        loss = abs(metrics['p_success'] - target_p_success)

    Возвращает (output, metrics):
        output  — список сессий в жёстком формате ТЗ
        metrics — агрегированные метрики ТПИ
    """
    factory = AgentFactory()
    agents  = factory.generate_population(
        count=n_agents, mean_age=mean_age, std_age=std_age,
        mean_skill=mean_skill, std_skill=std_skill, seed=seed,
    )
    env     = EnvironmentManager(dom_list)
    runner  = SimulationRunner(env, coeff=coeff or ModelCoefficients())
    results = runner.run_batch(agents, task_config, seed=seed)

    output  = [r.to_output() for r in results]
    metrics = UsabilityMetrics.compute(results)
    return output, metrics


# =============================================================================
# 11. ДЕМО
# =============================================================================

if __name__ == "__main__":
    import json
    with open("result.json", "r", encoding="utf-8") as f:
        sample_dom = json.load(f)
    """
    sample_dom = [
        {"id": 1,  "parent_id": 0,  "tag": "body",    "weight": 1.00, "text": ""},
        {"id": 2,  "parent_id": 1,  "tag": "header",  "weight": 0.80, "text": "My App"},
        {"id": 3,  "parent_id": 1,  "tag": "nav",     "weight": 0.70, "text": "Navigation"},
        {"id": 4,  "parent_id": 3,  "tag": "a",       "weight": 0.60, "text": "Home"},
        {"id": 5,  "parent_id": 3,  "tag": "a",       "weight": 0.55, "text": "Products catalogue"},
        {"id": 6,  "parent_id": 3,  "tag": "a",       "weight": 0.50, "text": "Contact Us"},
        {"id": 7,  "parent_id": 1,  "tag": "main",    "weight": 0.90, "text": ""},
        {"id": 8,  "parent_id": 7,  "tag": "section", "weight": 0.40, "text": "Featured products"},
        {"id": 9,  "parent_id": 8,  "tag": "div",     "weight": 0.30, "text": "Product A - Buy now"},
        {"id": 10, "parent_id": 8,  "tag": "div",     "weight": 0.30, "text": "Product B details"},
        {"id": 11, "parent_id": 7,  "tag": "section", "weight": 0.35, "text": "Search section"},
        {"id": 12, "parent_id": 11, "tag": "input",   "weight": 0.50, "text": "Enter what you want to calculate or know about"},
        {"id": 13, "parent_id": 11, "tag": "button",  "weight": 0.60, "text": "Search submit"},
        {"id": 14, "parent_id": 7,  "tag": "section", "weight": 0.25, "text": "Contact form"},
        {"id": 15, "parent_id": 14, "tag": "button",  "weight": 0.45, "text": "Submit contact request"},
    ]
    """

    def _sep(title: str) -> None:
        print("\n" + "=" * 60)
        print(title)
        print("=" * 60)

    # --- Сценарий 1: NAVIGATION ---
    _sep("NAVIGATION → target_id=9  |  25 агентов, age~35, skill~1.0")
    out, m = run_simulation(
        dom_list=sample_dom,
        task_config=TaskConfig(TaskType.NAVIGATION, target_id=275, max_steps=30),
        n_agents=25, mean_age=35, std_age=8, mean_skill=1.0, seed=42,
    )
    print(json.dumps(m, ensure_ascii=False, indent=2))
    print("\nПримеры сессий:")
    for s in out[:4]:
        print(f"  age={s['age']:2d}  skill={s['skill']:.2f}  steps={len(s['clicks']):2d}"
              f"  success={s['success']}  total_ms={s['time'][-1] if s['time'] else 0:.0f}")

    # --- Сценарий 2: SEARCH, пожилая аудитория ---
    _sep("SEARCH → ['calculate','know']  |  25 агентов, age~62, skill~0.7")
    out2, m2 = run_simulation(
        dom_list=sample_dom,
        task_config=TaskConfig(TaskType.SEARCH, target_keywords=["Personal Health"], max_steps=500),
        n_agents=25, mean_age=20, std_age=2, mean_skill=1.3, std_skill=0.15, seed=7,
    )
    print(json.dumps(m2, ensure_ascii=False, indent=2))

    # --- Демо RL-интерфейса ---
    _sep("Демо RL-интерфейса: изменение коэффициентов → другие метрики")
    default_coeff = ModelCoefficients()
    v = default_coeff.as_vector()
    print("Вектор по умолчанию:", v)

    v2 = v.copy()
    v2[0] = 1.5   # w_scent ↑
    v2[1] = 0.1   # w_time  ↓
    new_coeff = ModelCoefficients.from_vector(v2).clamp()
    _, m3 = run_simulation(
        dom_list=sample_dom,
        task_config=TaskConfig(TaskType.NAVIGATION, target_id=9, max_steps=30),
        n_agents=25, mean_age=35, coeff=new_coeff, seed=42,
    )
    print(f"\nДефолтные коэфф.:    p_success={m['p_success']}  mean_steps={m['mean_steps']}")
    print(f"Изменённые (RL-шаг): p_success={m3['p_success']}  mean_steps={m3['mean_steps']}")

    # --- Сценарий 3: ERROR_RECOVERY с hub-bias ---
    _sep("ERROR_RECOVERY → target_id=4 (Home)  |  25 агентов, age~40, skill~0.9")
    out3, m_er = run_simulation(
        dom_list=sample_dom,
        task_config=TaskConfig(TaskType.ERROR_RECOVERY, target_id=4, max_steps=30),
        n_agents=25, mean_age=40, std_age=10, mean_skill=1.3, seed=42,
    )
    print(json.dumps(m_er, ensure_ascii=False, indent=2))
    print("(backtracking активен, hub-bias направляет к nav/header)")

    # --- Разброс параметров популяции ---
    _sep("Разброс параметров популяции (первые 6 агентов, seed=99):")
    factory = AgentFactory()
    pop = factory.generate_population(6, mean_age=40, std_age=12, seed=99)
    print(f"{'age':>4} {'skill':>6} {'tau_p':>6} {'tau_c':>6} {'tau_m':>6} {'p_det':>6} {'temp':>5} {'wm':>3}")
    for a in pop:
        print(f"{a.age:>4} {a.skill:>6.3f} {a.tau_p:>6.1f} {a.tau_c:>6.1f} {a.tau_m:>6.1f}"
              f" {a.p_detect:>6.2f} {a.temperature:>5.2f} {a.wm_max:>3}")
