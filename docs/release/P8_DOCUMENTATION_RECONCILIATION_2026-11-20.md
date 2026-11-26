# P8 文件對帳（2026-11-20）

**P8_RELEASE_TAG：** NOT_REQUESTED  
**P4_INDEPENDENT_VERDICT：** NOT_REISSUED  
**P7_COMPLETION：** NOT_MET  
**P1_GATES：** DEFERRED_OPTION_A  
**P5_STATUS：** EXISTING_GATE_REVERIFIED  
**P6_STATUS：** NOT_PROMOTED

本文件把目前工作樹裡可核對的狀態寫成一份外部說明。它不發布新版本，不改歷史閘門判決，也不宣稱 AGI、自治或 unconstrained production。

英文對照句：this reconciliation does not claim AGI, autonomy, or unconstrained production.

## 文件怎麼讀

| 文件 | 現在的效力 |
|---|---|
| `docs/SDD_ASI_GOVERNANCE_SUBSTRATE_2026-11-20.md` | 產品範圍與 P 階段順序的 SSOT。P4–P8 以它為準 |
| `docs/release/RELEASE_DECISION.md` | 2026-06-15 的 v0.9.0-rc1 標籤決策紀錄。不是 2026-11-20 的新 release，也不是 P4/P7 通過證明 |
| `docs/release/V09_RELEASE_CHECKLIST.md` | rc1 當時的檢查表。勾選項不延伸到本次 P7/P8 |
| `docs/proposals/ASI_P4_PROVIDER_NEUTRAL_ACTION_GOVERNANCE_INDEPENDENT_VERIFICATION.md` | 保留的 P4 FAIL。本回合沒有改寫 |
| `docs/proposals/ASI_P4_PROVIDER_NEUTRAL_ACTION_GOVERNANCE_APPEAL_IMPLEMENTATION.md` | 仍是 `READY_FOR_INDEPENDENT_VERIFICATION`，驗證者仍待指派 |
| `docs/p7/P7_SANDBOX_METRICS_REPORT_2026-11-20.md` | 行程內沙盒報告。`pilot_acceptance` 為 not_claimed |
| `docs/p7/P7_INDEPENDENT_REVIEW_PACKET_2026-11-20.md` | 等待獨立審查者。實作者裁決為 NONE |
| `docs/audit/SCOPE_DECISIONS_2026.md` | 範圍決策只追加。P1/G2–G6 維持選項 A |

## 階段狀態

| 階段 | 狀態 | 證據 |
|---|---|---|
| P0、P3 | 沿用既有完成紀錄 | 不在本回合重開 |
| P4 | 申訴待獨立再驗。原 FAIL 保留 | 缺口文件與既有驗證報告 |
| P7 | 本機五情境與度量報告已產生。完成條件未滿足 | 沙盒報告與審查包 |
| P8 | 本對帳完成的是文件對齊，不是 release | 本檔、README 第 16 節、已知限制第 14 節 |
| P5 | 沿用既有證據閘。未量測或過期為 UNKNOWN，舊報告 PASS 不能直接沿用 | `hermes/evidence_snapshot.py`、`tests/test_p5_evidence_integrity.py` |
| P6 | 歷史分數維持 NOT_PROMOTED。達標也只到獨立審查，不是 PASS | `hermes/reality_debt.py` |
| P1、P2、G0–G6 | 選項 A 延後 | `SCOPE_DECISIONS_2026.md` |

## 與舊路線圖的差異

2026-09-13 路線把 P5、P6 放在 P7 之前。2026-11-20 SDD 把 P7 放在 P5 之前，並把 P6 標成證據不足。衝突時以 SDD 為準。本機後續已重跑既有 P5 證據閘，並以 `NOT_PROMOTED` 保住 P6 歷史分數。兩者都不是通過。

## 刻意沒有改的歷史

- `docs/release/RELEASE_DECISION.md` 的 2026-06-15 決策原文。
- P4 獨立驗證 FAIL 報告與申訴狀態欄。後續本機工作延伸了 envelope 與結果組裝，沒有重發驗證結論。
- 任何 append-only 的 DMN、閘門 journal 或失敗分數。

## 仍須使用者確認才能做的事

- 釘選 Astra 模型識別碼與 base URL，並同意在金絲雀呼叫外部 API。
- 指派獨立審查者做 P4 申訴與 P7 繞過防護。
- 若要發布新 tag 或 commit，需另一次明示指示。本對帳不請求 tag。

## 2026-11-26 MVP 附記

上面的 `P8_RELEASE_TAG： NOT_REQUESTED` 與 `P7_COMPLETION： NOT_MET` 是 2026-11-20 對帳的原文，本附記不刪改那些句子。

操作者於 2026-11-26 要求以 SDD 第 3.4 與第 5.3 節選項 A 發行 v0.9.1 MVP：

| 階段 | MVP 狀態 |
|---|---|
| P0、P3 | 沿用 SDD 矩陣 DONE。P3 獨立驗證文件維持 FAIL |
| P1 | MVP_DEFERRED_DOCUMENTED。G2–G6 未執行。隨 Hermes v0.16.0 出貨，不宣稱 v0.21.2 |
| P2 | MVP_DEFERRED_DOCUMENTED。依賴 P1 與 Guardian 政策，橋接切換未執行 |
| P4 | 結果證據已記入結構化 error。歷史獨立驗證 FAIL 不改寫 |
| P5 | 既有證據閘。未量測維持 UNKNOWN |
| P6 | MVP_DEFERRED。歷史分數維持 NOT_PROMOTED，門檻未下修 |
| P7 | 金絲雀 `pilot_acceptance` 為 `mvp_operator_reviewed`，審查標籤 `OPERATOR_SELF_REVIEW`。不是 independent_pass |
| P8 | 本附記與 `docs/release/KNOWN_LIMITATIONS.md` 第 15 節 |

本附記不宣稱 AGI、自治、正式環境部署或第三方驗證通過。
