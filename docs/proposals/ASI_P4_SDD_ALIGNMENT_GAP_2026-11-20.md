# P4 與 SDD 治理基底的對齊缺口

**日期：** 2026-11-20  
**狀態：** IMPLEMENTED_AWAITING_INDEPENDENT_REVIEW。不是 PASS，也不是申訴改寫。  
**實作者：** cursor-agent  
**獨立驗證者：** 仍待指派

本文件服務 SDD 第 5.1 節第 1–2 週的 P4 核對。它不修改 P4 申訴所涵蓋的原始碼。

## 保留的既有結論

- 獨立驗證：`docs/proposals/ASI_P4_PROVIDER_NEUTRAL_ACTION_GOVERNANCE_INDEPENDENT_VERIFICATION.md`  
  決策維持 **FAIL**。本回合沒有改寫該報告。
- 申訴實作：`docs/proposals/ASI_P4_PROVIDER_NEUTRAL_ACTION_GOVERNANCE_APPEAL_IMPLEMENTATION.md`  
  狀態維持 `READY_FOR_INDEPENDENT_VERIFICATION`，驗證者維持 `pending-independent-assignment`。
- 本代理沒有重算申訴雜湊，沒有重跑當時的完整提供者套件作為閘門證據，也不發新的 P4 裁決。

SDD 寫明：驗證失敗時只給具體修復清單，不做零碎補丁。申訴本身也還沒有新的獨立裁決。因此下列差異只記錄，不在本週改 `hermes/orchestration` 既有模組。

## 路徑

SDD 第 3.2 節用 `asi/capabilities.py`、`asi/adapters/`、`asi/schemas/action_envelope.py`、`asi/schemas/result_envelope.py`、`tests/test_guardian_bypass.py` 描述目標形狀。現行程式的單一詞彙與授權入口在：

| SDD 草稿路徑 | 現有位置 | 本週決定 |
|---|---|---|
| `asi/capabilities.py` | `hermes/orchestration/capabilities.py` | 不另建平行套件 |
| `asi/adapters/` | `hermes/orchestration/adapters.py` | 沿用現有轉接器 |
| `asi/schemas/action_envelope.py` | `hermes/orchestration/envelopes.py` 的 `ProposedActionEnvelope` | 不改欄位 |
| `asi/schemas/result_envelope.py` | `hermes/orchestration/envelopes.py` 的 `ResultEvidenceEnvelope` | 不改欄位 |
| `tests/test_guardian_bypass.py` | `tests/test_orchestration_action_envelopes.py` | 本週不新增該檔名 |

另建 `asi/` 會複製已存在的治理基底，違反 SDD 的防漂移與本儲存庫的重用順序。若操作者以後要搬移路徑，應作為獨立、經過同意的遷移，而不是在申訴待驗期間改寫。

## 欄位缺口

### 提案 envelope

SDD 草稿有 `arguments`、`proposed_by`、`timestamp`。這三個欄位已在 `ProposedActionEnvelope`，並進入 action payload。提案當下的 `authorization_ref` 仍可為空，外部綁定成功後才寫入。模型自填的授權字串不會被當成授權。

副作用詞彙也不相同：

| SDD 草稿 | 現有詞彙 |
|---|---|
| `read_only` / `reversible` / `destructive` | `none` / `read_only` / `local_write` / `external_write` / `terminal_execution` / `mixed_material` |
| 可逆性 `automatic` / `manual` / `irreversible` | `reversible` / `compensatable` / `irreversible` / `unknown` |

範圍在現有程式是 `requested_scope: tuple[str, ...]`，不是一個名為 `ActionScope` 的新類型。

### 結果 envelope

SDD 草稿要求 `action_ref`、`outcome`、`actual_changes`、`error`、`cost`、`replay_pointer`、`verified_by`、`timestamp`。

`ResultEvidenceEnvelope` 仍以 `proposal_id` 連結提案。2026-11-24 的結果組裝會寫入 `actual_changes`、`cost`、`replay_pointer`。`action_ref` 與 `outcome` 由提案識別碼與狀態衍生。`verified_by` 欄位存在，路由留空，實作者不填自己。結構化 `error` 有型別，結果組裝尚未填入；那是下一筆路由修改，本回合不碰 `routing.py`。

### 轉接器

`ProviderAdapter` 已有 `propose_action` 與 `explain_reasoning`。`propose_action` 會丟掉模型自填的 `authorization_ref`。說明文字不是授權證據。工具執行仍留在 Guardian 之後。

### 能力登錄

`authorization_requirement_for` 把實質動作標成 `guardian_allow_required`，其餘為 `not_material`。工具到能力的對應仍在 `routing.classify_tools`，是結構性 token，不讀提示詞。

## 既有測試與 SDD 四項威脅

| SDD 要求 | 現有覆蓋 | 本週額外沙盒 |
|---|---|---|
| 模型輸出不能直接叫工具 | 未授權與偽造授權的測試要求轉接器呼叫數為 0 | 情境 4：BLOCK 且呼叫數為 0 |
| 推理文字不是授權 | 提示詞與意圖不能發明權限 | 情境 2：引用的 ALLOW 不是授權參考 |
| 中途轉向保留完整軌跡 | `test_steering_and_pending_tool_calls_remain_first_class_evidence` | 情境 3 |
| schema 違規必須硬失敗 | envelope 建構即拋 `EnvelopeValidationError` | 沙盒以非法 `side_effect_class` 再確認一次 |

這些沙盒斷言不是獨立驗證。`tests/test_guardian_bypass.py` 沒有在本週建立，因為授權新增的測試檔是 `tests/test_p7_pilot_harness.py`。

## 若獨立驗證者仍判 FAIL，建議的修復單位

以下是清單，不是本週的補丁：

1. 保持 `hermes/orchestration` 為唯一實作，不要平行複製到 `asi/`。
2. 只有在新的獨立 FAIL 指出必要欄位時，才補 `arguments`、`proposed_by`、結果 `cost`、`verified_by`。補欄位時保留現有 digest 與失敗關閉語意。
3. 成本要進 `ResultEvidenceEnvelope` 之後，`cost_replay_coverage` 才能從 0 變成可審查。
4. `propose_action` 若要新增，必須仍把工具執行留在 Guardian 之後。`explain_reasoning` 不得寫入授權欄位。
5. 直接 `ProviderAdapter.invoke` 的內部邊界維持文件化，除非獨立驗證者把它列入必須關閉的入口。
6. 重放仍是行程內。持久化與簽章不在本週範圍。

## 本週明確沒做

- 沒有修改 `hermes/orchestration/routing.py`、`envelopes.py`、`capabilities.py`、`adapters.py`、`guardian.py`、`models.py`、`replay.py`、`audit.py` 或 `tests/test_orchestration_action_envelopes.py`。
- 沒有合併到 main。
- 沒有把申訴狀態改成 PASS。

## 2026-11-20 後續增量的 P5–P8 狀態

此節只對齊後續本機工作，不改變上面的「不是驗證結論」。

| 階段 | 狀態 |
|---|---|
| P5 | `EXISTING_GATE_REVERIFIED`。沿用既有證據閘，未量測維持 UNKNOWN，不是 PASS |
| P6 | `NOT_PROMOTED`。歷史未達標分數保留，不能改標成 BOOTSTRAP_GAP |
| P7 | 沙盒度量報告與獨立審查包已產生。成本已進入沙盒結果證據。`pilot_acceptance` 為 not_claimed，`IMPLEMENTER_VERDICT` 為 NONE |
| P8 | 文件對帳見 `docs/release/P8_DOCUMENTATION_RECONCILIATION_2026-11-20.md`。`P8_RELEASE_TAG` 為 NOT_REQUESTED |

P4 申訴報告與獨立驗證 FAIL 原文仍未改寫。欄位與結果組裝已補上，狀態是 `IMPLEMENTED_AWAITING_INDEPENDENT_REVIEW`，等獨立驗證者裁決。

## 2026-11-26 MVP

2026-11-26 的結果組裝會把回應上的結構化 error 寫入 `ResultEvidenceEnvelope.recorded_error`。上一節「結果組裝尚未填入」保留為當時紀錄。SDD 第 3.2 節點名的測試模組，操作者改為 `tests/test_p4_authorization_boundary.py`。歷史 FAIL 原文沒有改寫。
