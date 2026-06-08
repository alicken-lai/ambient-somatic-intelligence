# 盤點：缺失的 `attention/` 分層子系統（v05x–v07x）

- 狀態：INVENTORY（唯讀盤點，**不含任何實作／stub**）
- 提出來源：cursor-agent
- 目的：量化「完善 v07x 缺失模組」的真實工作量，供決策；遵守 freeze（不捏造、不隱藏失敗、不自我驗證）

---

## 0. 一句話結論

整個分層 `attention/` 架構（kernel / core / forecasting / calibration / consolidation / explainability / runtime 共 **7 個子套件**）在本工作樹**從未被提交**。目前 `attention/` 只有 7 個扁平舊模組，缺口被 **production 程式碼**與 **v05x–v07x 測試**大量引用，導致這些路徑「一 import 就壞」。

## 1. 證據與判定

- `git ls-files attention/` 與 `git log -- attention/forecasting` 皆**空** → 這些子套件不是工作樹被刪，而是**從未實作／提交**，無法用 `git restore` 還原。
- `attention/*/`（子目錄）glob **無結果**；`attention/` 僅有：`__init__.py, attention_state.py, salience_engine.py, escalation_router.py, priority_allocator.py, novelty_detector.py, weak_signal_detector.py`。
- 對照：`governance/cognition/` 等治理子套件**存在**，故缺口集中在 `attention/`。
- pytest 全套：39 個 collection error，全部源於 `No module named 'attention.<sub>'`。

---

## 2. 缺失子套件與符號（由 import 反推）

### 2.1 `attention.core`
- `attention_target.AttentionTarget`（被引用最廣，~30+ 處）
- `salience.SalienceVector`
- `attention_state.AttentionKernelState`
- `precursor_signal.PrecursorSignal`

### 2.2 `attention.kernel`
- `attention_kernel.AttentionKernel`

### 2.3 `attention.runtime`
- `governed_attention_activation.GovernedAttentionActivation`
- `runtime_attention_memory_bridge.RuntimeAttentionMemoryBridge`

### 2.4 `attention.forecasting`
- `attention_forecast.AttentionForecast`, `AttentionForecastResult`（~20+ 處）
- `trajectory_estimator.TrajectoryEstimate`
- `salience_projection.SalienceProjection`, `SalienceProjectionPoint`
- `precursor_forecast.PrecursorForecast`, `PrecursorForecastPoint`
- `salience_pressure_forecast.PressureForecast`, `SaliencePressureForecast`
- `forecast_uncertainty.ForecastUncertainty`, `UncertaintyBand`
- `forecast_window.FORECAST_WINDOWS`, `MAX_HORIZON_SECONDS`
- `replay_trajectory_forecast.ReplayTrajectoryForecast`

### 2.5 `attention.calibration`
- `confidence_cap.ABSOLUTE_MAX_CONFIDENCE`, `ConfidenceCap`, `apply_confidence_cap`
- `forecast_confidence.ForecastConfidenceCalibrator`, `CalibratedConfidence`
- `forecast_humility.ForecastHumility`
- `false_positive_tracker.FalsePositiveTracker`

### 2.6 `attention.consolidation`
- `attention_memory_store.AttentionMemoryStore`
- `attention_memory.AttentionMemory`
- `salience_history.SalienceHistory`
- `benign_pattern_memory.BenignPatternMemory`
- `precursor_memory.PrecursorMemory`
- `attention_trace.AttentionTrace`
- `background_stability.BackgroundStability`
- `anomaly_decay.AnomalyDecay`
- `precursor_weighting.PrecursorWeighting`
- `salience_reinforcement.REINFORCEMENT_CEILING`, `SalienceReinforcement`

### 2.7 `attention.explainability`（最龐大；每個 v0xx 版本約 3 類）
代表性（依版本）：
- v053/054：`forecast_explainer`, `precursor_chain_explainer`, `uncertainty_explainer`, `calibration_explainer`, `confidence_breakdown.ConfidenceBreakdownBuilder`, `uncertainty_reasoning`
- v060：`authority_breakdown.AuthorityBreakdown`, `arbitration_explainer`, `governance_reasoning`
- v061：`constitutional_reasoning`, `governance_boundary_explainer`
- v062：`continuity_breakdown`, `identity_reasoning`, `provenance_explainer`
- v063：`coherence_reasoning`, `contradiction_explainer`, `drift_breakdown`
- v064：`degradation_explainer`, `metacognitive_reasoning`, `reflection_breakdown`
- v065/b/c：`homeostasis_reasoning`/`recovery_breakdown`/`stabilization_explainer`、`compatibility_explainer`/`contamination_breakdown`/`external_doctrine_reasoning`、`precedence_breakdown`/`runtime_external_reasoning`/`sovereignty_explainer`
- v070–v077：每版 3 類（civilization/reality/temporal/semantic/value/intent/purpose/agency 系列的 `*_reasoning` + `*_breakdown` + `*_explainer`）

> 粗估：core/kernel/runtime/forecasting/calibration/consolidation ≈ 30+ 類別/常數；explainability ≈ 45+ 類別。**合計 ~75+ 公開符號、橫跨 ~50+ 模組檔**。

---

## 3. 由真實用法推斷的基礎 API（重建起點）

取自 `v060_runtime/simulations.py`、`governance/cognition/cognitive_governor.py`：

```python
# attention.core.attention_target
AttentionTarget(source_domain: str, signal_type: str, raw_value: float,
                metadata: dict | None = None)

# attention.kernel.attention_kernel
AttentionKernel(max_focus: int, max_queue: int)
kernel.tick() -> None

# attention.consolidation.attention_memory_store
AttentionMemoryStore(max_entries: int)

# attention.runtime.runtime_attention_memory_bridge
RuntimeAttentionMemoryBridge(kernel, store)
bridge.store            # attribute
bridge.precursor_memory # attribute (PrecursorMemory)
bridge.ingest_target(target: AttentionTarget) -> None

# attention.forecasting.attention_forecast
AttentionForecast(kernel, store, precursor_memory)
forecaster.ingest(target: AttentionTarget) -> None
# AttentionForecastResult: result type consumed by observability scorers

# attention.runtime.governed_attention_activation
GovernedAttentionActivation(kernel, store)
governed.submit_governed_target(target, raw_confidence: float)
governed.arbitrate_claims(claims: list[SalienceClaim], uncertainty: float) -> dict
#   -> out["arbitration"]["arbitration_fairness"]: float

# attention.calibration.confidence_cap
ABSOLUTE_MAX_CONFIDENCE: float       # hard ceiling (< 1.0)
apply_confidence_cap(value: float) -> float
class ConfidenceCap: ...
```

> 注意：observability scorers（如 `evidence_from_governed_forecaster`、`evaluate_cognitive_governance_stability`）對 forecaster/bridge 取用更多方法與欄位；且 v0xx 測試斷言**特定數值分數**，故每個類別不只要存在、還要產生**特定數值行為**才能讓測試轉綠。

---

## 4. 影響面（為何不能只塞 stub）

- **Production**：`governance/cognition/cognitive_governor.py`、`governance/constitution/epistemic_limit.py`、~30 個 `observability/v0xx/*`、`v05x–v07x_runtime/simulations.py` 直接 import 這些缺失模組 → 這些檔案在本工作樹**無法 import**。
- **測試**：39 個 v05x–v07x 測試檔在 collection 階段即失敗，且通過條件是**數值分數門檻**（例：False Strategy 類、stability score ≥ 門檻）。
- 用空殼／回傳定值的 stub 可讓 import 過、甚至假性湊出分數 → **等同捏造系統行為、掩蓋真實缺口**，違反 freeze 紀律與「不得自我驗證」。故**不採用 stub 路線**。

---

## 5. 建議重建順序（若決定真正實作）

由底層往上、每層附獨立測試、分階段交付：

1. `attention.core`（`AttentionTarget` / `SalienceVector` / `PrecursorSignal` / `AttentionKernelState`）——最底層、被依賴最多。
2. `attention.kernel`（`AttentionKernel.tick` 等）。
3. `attention.consolidation`（記憶/痕跡/衰減/強化）。
4. `attention.forecasting`（`AttentionForecast` 及各 forecast/projection 類）。
5. `attention.calibration`（confidence cap / humility / false positive）。
6. `attention.runtime`（bridge / governed activation）。
7. `attention.explainability`（最龐大；按 v0xx 版本逐版補）。

每階段：實作 → 該層單元測試綠 → 再讓對應 v0xx 測試逐版轉綠（數值門檻由**非實作方**確認，符合 freeze）。

### 工作量級別
- 非小修補：~50+ 檔、~75+ 符號，且需符合既有 observability/測試的**數值語意**。
- 實務上等同**重建 Ambient OS 的注意力認知層**，建議視為獨立的多階段專案，而非單一回合任務。

---

## 6. 給決策者的選項

- A：僅維持本盤點，缺口列為已知 backlog（最安全）。
- B：從 `attention.core` 開始逐層真正重建（可長期推進、每層可驗證）。
- C：全量重建直到 v07x 測試全綠（工作量極大、需多輪、且數值門檻無法由實作方自我保證）。

> 本文件不修改任何既有檔案、不新增 stub；僅供決策。
