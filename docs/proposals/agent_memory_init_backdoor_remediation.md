# 提案：關閉記憶本體論初始化後門（Agent Memory Init Back Door）

- 狀態：Phase A 已實作（observe-only，已併入 `agents/memory.py`，9 新測試 + 181 回歸綠）；Phase B DRAFT（**預設行為變更**，待治理升格與獨立驗證）
- 提出來源：cursor-agent（DMN／report 唯讀分析）
- 關聯證據：`replay/reports/false_strategy_report.md`（False Strategy Resistance 0.65）
- 定位：穩定化（stabilization）等級修補，非新文明層
- 約束：遵守 freeze 紀律、append-only、weakest-link 整合分數 ≥ 0.95、不得自我驗證升格、不降低既有閾值

---

## 1. 問題根因

系統有兩套互不相連的記憶機制：

### (a) Agent 本地記憶（有後門）— `agents/memory.py`

- `AgentMemory.remember()` 的 `category` 是自由字串，`confidence` 預設 1.0，直接落盤。
- `MemoryEntry` 沒有 `layer` 欄位，從不呼叫升格閘門。
- 結果：`remember(content, category="strategy")` 等於憑空產生「L4 策略、信心 1.0、零驗證」記憶。這正是 Phase 1E 的 FE-STRAT-001/002。

### (b) 本體論升格／衰減（完整但未接線）— `memory/ontology/*`

- `promotion_rules.py::check_promotion_eligibility` 嚴謹定義 L1→L4 閘門，但 AgentMemory 從不使用。
- `decay_engine.py::DecayEngine.sweep()` 完整，但要求 entry 具備 `.layer/.timestamp/.entry_id/.confidence`；`MemoryEntry` 只有 `created/confidence/uses/last_used`，缺 `layer/entry_id/timestamp`，所以 DecayEngine 永遠碰不到 agent 記憶。
- agent 端僅容量驅逐 `_evict()`，無時間／信心衰減。

### (c) 三重碎片化（加重問題）

策略散在三處：`BaseAgent._strategies`（`base.py`，存 state.json）、`AgentMemory` 的 entries.jsonl、本體論 L4。`execute()` 走 `find_strategy`（讀 `_strategies`），根本不讀 AgentMemory，導致假策略無人交叉驗證。

---

## 2. 目標與量化驗收

| 指標 | 現況 | 目標 |
|---|---|---|
| False Strategy Resistance（Phase 1E） | 0.65 | ≥ 0.85 |
| Promotion chain integrity（1E 子項） | 0.20 | ≥ 0.80 |
| 直接以 conf=1.0 注入 L3/L4 的路徑 | 存在 | 0（被閘門擋下） |
| DecayEngine 覆蓋 agent 記憶 | 否 | 是（先 observe） |

---

## 3. 設計（四個修補點）

### P1：類別→層級映射 + 初始信心上限

- `MemoryEntry` 新增 `layer / entry_id / timestamp / last_accessed`，與本體論對齊。
- `remember()`：建立 category→候選 layer 映射（knowledge/pattern→L1、failure→L2、skill→L3、strategy→L4）；初始一律落 L1 且 `confidence = min(confidence, 0.5)`。
- 新增 `seed_knowledge()` 專供預載：強制 `layer=L1`、`confidence ≤ 0.5`、`metadata.origin="preloaded"`。

### P2：升格閘門上線（擋住 L3/L4 直注）

- 新增 `promote(entry, target_layer)`：呼叫 `check_promotion_eligibility`，未過則拒絕並回傳 blocking_reasons。
- L2→L3、L3→L4 的 `requires_governance / requires_verifier`：接 `guardian_check` 與獨立 verifier；不得由產生記憶的同一 agent 自我驗證。

### P3：接通 DecayEngine（先 observe，後 enforce）

- P1 後可直接餵 `DecayEngine.sweep()`。
- 新增 `AgentMemory.decay_sweep(now)`：先以 recommendations_only 產出 DecayReport（archive/remove 建議）寫 observability，不自動刪；穩定後再開 enforce。
- `_evict()` 改為「容量 + 衰減後信心」綜合排序。

### P4：用後交叉驗證（成果回饋信心）

- `base.py::run_task()` 完成後，對實際採用的策略呼叫 `ConfidenceModel.update_on_success/failure`（失敗用 `DecayEngine.apply_failed_reuse`）。
- 收斂三重碎片化：`execute()` 策略查詢統一改走 AgentMemory，使「被用到才升信心、用壞就降」成立。

---

## 4. 既有資料遷移（不可靜默改寫）

- `scripts/migrate_agent_memory_layers.py`：掃 `state/agents/*/memory/entries.jsonl`，補 `layer`、依 Phase 1E 結論降 FE-STRAT-001/002 為 L2 信心 0.3，修正 FE-KNOW/FAIL。
- 遵守 append-only/稽核：寫新檔 + 審計記錄（`observability/evolution_audit/`），不就地竄改；附 dry-run。

---

## 5. 分期（每期皆為治理閘門）

1. Phase A（observe）✅ 已完成：P1 資料模型（`layer/entry_id/timestamp/last_accessed`）+ `decay_report()`/`integrity_warnings()` 唯讀輸出；**不改行為**。
2. Phase B（enforce，**改預設行為**）：P2 升格閘門 + `remember` 初始信心上限**預設生效**（非預設關閉旗標）；舊資料遷移（dry-run→正式）。詳規見 §9。
3. Phase C（feedback）：P4 用後交叉驗證 + 碎片收斂 + decay 由 observe 轉 enforce。
4. Phase D（gate）：由非實作方重跑 Phase 1E replay 驗 score，達標才凍結。

---

## 6. 測試與獨立驗證（不可自我驗證）

- 單元 `tests/<epoch>/test_agent_memory_promotion.py`：`remember(category="strategy")` 不再產生 L4；`promote()` 在 occurrences/cross-context 不足時被擋。
- 衰減 `test_agent_memory_decay.py`：零使用策略隨時間信心下降、跨 min_confidence 觸發 archive/remove 建議。
- 回歸：v060–v077 既有 395 測試全綠，weakest-link ≥ 0.95 不得下降。
- 驗收：由 `replay/sandbox/` 獨立重跑 Phase 1E 產出新 score；由非實作方確認 PASS。

---

## 7. 風險與非目標

- 風險：收斂三重策略儲存可能影響 `execute()` 行為 → feature flag + 影子比對先驗等價。
- 風險：enforce 衰減誤刪有效記憶 → 先 observe 兩週期、保留 archive 緩衝。
- 非目標：不擴張文明治理層、不引入自主升格、不降低既有閾值。

---

## 8. 對應原始碼定位（審閱用）

- 後門：`agents/memory.py`（`remember` 第 94–116 行、`MemoryEntry` 第 27–37 行、`_evict` 第 197–208 行）
- 閘門（未用）：`memory/ontology/promotion_rules.py`（`check_promotion_eligibility` 第 112–147 行）
- 衰減（未接）：`memory/ontology/decay_engine.py`（`sweep` 第 182–228 行）、`memory/ontology/decay_rules.py`
- 層級定義：`memory/ontology/layer_definition.py`
- 碎片化：`agents/base.py`（`_strategies` 第 127、168–188 行）、`agents/specialists.py`（`execute`/`find_strategy`）

---

## 9. Phase B 詳規（enforce，改預設行為）

> 定位：Phase B 是預設行為變更——升格閘門與初始信心上限預設生效，不是「預設關閉的 feature flag」。
> 唯一旗標是緊急回退用 `AMBIENT_OS_MEMORY_ENFORCE`（預設 `"1"` = 啟用），僅供異常時人工回退。
> 凍結紀律：預設行為改變後，仍需由非實作方通過 9.5 驗收（含 Phase 1E replay）才可標記 verified/frozen。

### 9.1 `MemoryEntry` 必要補強

`check_promotion_eligibility` 期望 `entry.layer` 為 `MemoryLayer`（取 `.name`），並用 adapter 取統計：`access_count/occurrence_count/execution_count`、`success_rate()`、`contextual_applicability/contexts_validated`。Phase A 的 `layer` 為 `int`，故需補：

```python
# agents/memory.py - MemoryEntry additions (Phase B)
success_count: int = 0
failure_count: int = 0
contexts_validated: list[str] = field(default_factory=list)

@property
def access_count(self) -> int:          # adapter -> promotion occurrences
    return self.uses

def success_rate(self) -> float:        # adapter -> promotion success_rate
    total = self.success_count + self.failure_count
    return (self.success_count / total) if total else 0.0

def layer_enum(self) -> "MemoryLayer":  # int -> MemoryLayer for ontology calls
    return MemoryLayer(self.layer)
```

### 9.2 `remember()` 預設語意變更（後門關閉核心）

簽章不變（呼叫端零修改），但預設行為變更：

```python
INITIAL_CONFIDENCE_CAP: float = 0.5  # L1 entry cap

def remember(self, content, category="knowledge", tags=None,
             confidence=1.0, metadata=None) -> MemoryEntry:
    """Phase B default behavior:
      - new entries ALWAYS enter at L1 (regardless of category);
      - confidence is capped: min(confidence, INITIAL_CONFIDENCE_CAP);
      - requested high layer is recorded ONLY as candidate target
        (metadata['target_layer']), never granted on write.
    """
```

| 呼叫 | Phase A（現況） | Phase B（預設） |
|---|---|---|
| `remember(c, category="strategy", confidence=1.0)` | `layer=4, confidence=1.0` | `layer=1, confidence=0.5, target_layer=4` |
| 取得 L4 的唯一路徑 | 無閘門（後門） | 只能經 `promote()` 過閘門 |

`seed_knowledge()` 供預載專用，強制 `layer=L1`、`confidence ≤ 0.5`、`metadata.origin="preloaded"`：

```python
def seed_knowledge(self, content, *, tags=None,
                   confidence=0.5, metadata=None) -> MemoryEntry: ...
```

### 9.3 升格閘門 `promote()`（擋住 L3/L4 直注）

```python
@dataclass
class PromotionResult:
    ok: bool
    entry_id: str
    from_layer: int
    to_layer: int | None
    blocking_reasons: list[str]

def promote(
    self,
    entry: MemoryEntry,
    target_layer: "MemoryLayer",
    *,
    governance_token: "GuardianDecision | None" = None,  # L2->L3, L3->L4 need ALLOW
    verifier: "PromotionVerifier | None" = None,          # L3->L4 required, must differ from author
) -> PromotionResult:
    """Single-step promotion: pick rule from PROMOTION_RULES ->
    check_promotion_eligibility; if requires_governance verify
    governance_token == ALLOW; if requires_verifier verify
    verifier.identity != entry.author (no self-verification).
    On fail: ok=False with blocking_reasons, layer unchanged."""
```

- 治理串接：`requires_governance` → 呼叫端先取得 `guardian_check` 的 `ALLOW` 作為 `governance_token`。
- 獨立驗證：`requires_verifier`（僅 L3→L4）→ `verifier.identity` 必須不同於 `entry.metadata['author']`；同源驗證一律拒絕（對應 freeze「不得自我驗證升格」）。

### 9.4 既有資料遷移（append-only，不就地竄改）

```python
# scripts/migrate_agent_memory_layers.py
def migrate(root: Path, *, dry_run: bool = True) -> MigrationReport: ...
```

- 掃 `state/agents/*/memory/entries.jsonl`，補 `layer/entry_id/success_count/failure_count/contexts_validated`。
- 依 Phase 1E 結論：FE-STRAT-001/002 重標為 L2、`confidence=0.3`；修正 FE-KNOW/FE-FAIL 類別。
- 寫新檔 + 審計記錄至 `observability/evolution_audit/`，保留原檔；預設 `dry_run=True`，需顯式關閉才正式套用。

### 9.5 驗收準則（Phase B Definition of Done；不可自我驗證）

行為（單元）：
- `remember(category="strategy", confidence=1.0)` → `entry.layer == 1 且 confidence == 0.5`；`metadata['target_layer'] == 4`。
- `integrity_warnings()` 對「剛寫入的策略」回傳空（後門特徵消失）。
- `promote(entry, L3)` 在 occurrences/cross-context/confidence 任一不足時 `ok=False` 且 `blocking_reasons` 非空，`entry.layer` 不變。
- `promote(entry, L4)` 缺 `verifier` 或 `verifier.identity == author` 時被拒。
- 遷移 dry-run 報告顯示 FE-STRAT-001/002 → L2 / 0.3，且原檔不變。

回歸與整合：
- `tests/agent_memory` + `tests/ontology` + `tests/test_ontology` + `tests/test_integration` 全綠；v060–v077 既有全套全綠。
- weakest-link lineage integrity ≥ 0.95 不得下降；不得降低任何既有閾值。

獨立驗證（gate，非實作方執行）：
- 由 `replay/sandbox/` 重跑 Phase 1E：False Strategy Resistance ≥ 0.85、Promotion chain integrity ≥ 0.80。
- 直接以 `conf=1.0` 注入 L3/L4 的路徑數 = 0。
- 由非實作身分確認 PASS 後，方可將狀態由 DRAFT 改為 verified/frozen。

### 9.6 回退與相容

- 呼叫端零修改（`remember` 簽章不變）；變的是儲存語意（layer/confidence），此即本期「改預設行為」的標的。
- 緊急回退：設 `AMBIENT_OS_MEMORY_ENFORCE=0` 可暫退回 Phase A observe 語意（僅供事故處置，預設為強制）。
- decay 的 enforce（實際 archive/remove）不在 Phase B；維持 observe，留待 Phase C，避免誤刪有效記憶。
