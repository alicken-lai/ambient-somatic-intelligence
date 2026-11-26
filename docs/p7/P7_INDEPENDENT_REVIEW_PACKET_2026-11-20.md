# P7 獨立審查包

**日期：** 2026-11-20  
**REVIEW_STATUS：** AWAITING_INDEPENDENT_REVIEWER  
**IMPLEMENTER_VERDICT：** NONE  
**pilot_acceptance：** not_claimed

本文件是給另一位審查者的材料索引。實作者不發 P7 裁決，也不把沙盒分數升成完成。

## 可重跑的本機證據

- 計畫：`docs/p7/P7_ASTRA_PILOT_PLAN_2026-11-20.md`
- 度量報告：`docs/p7/P7_SANDBOX_METRICS_REPORT_2026-11-20.md`
- 產生器：`hermes.orchestration.pilot_report.render_sandbox_report`
- 沙盒：`hermes.orchestration.pilot_sandbox.run_sandbox_rehearsal`
- 測試：`tests/test_p7_pilot_harness.py`、`tests/test_p7_pilot_report.py`

審查者應自行重跑，不沿用本文件的敘述當結果：

```text
python -B -m py_compile hermes\orchestration\pilot_report.py hermes\orchestration\pilot_metrics.py hermes\orchestration\pilot_sandbox.py
python -B -m pytest tests\test_p7_pilot_report.py tests\test_p7_pilot_harness.py tests\test_orchestration_action_envelopes.py -q -p no:cacheprovider
```

## 沙盒已涵蓋與未涵蓋

已在行程內跑過的五個 SDD 情境：多檔重放、憑證不進證據、轉向軌跡保留、未授權 BLOCK、回應用量對帳。另有行程內的提供者名稱互換。

尚未涵蓋，因此不能當成 P7 完成：

- 現場 Astra 或任何外部 API。
- 真人 3 秒內打斷的延遲。
- 結果 envelope 內的成本重放。
- 活的 Claude-only 回滾。
- 獨立審查者對繞過防護的簽核。

## 請審查者判定的問題

1. 沙盒的 BLOCK 是否只證明 `RoutingEngine.route` 這一個入口，而不是所有呼叫面？
2. `ProviderAdapter.invoke` 的直接呼叫是否仍應維持文件化內部邊界？
3. 行程內重放是否足以支持 SDD 的 replay 目標，或必須先有持久化證據？
4. 在 Astra 模型識別碼與 base URL 尚未釘選時，可否把任何分數稱為 pilot 完成？預期答案是否定的。

審查者的結論應另寫，並使用不同的 `verifier_id`。本檔不預填 PASS 或 FAIL。

## 2026-11-26 MVP 附記

本包原文的 `pilot_acceptance： not_claimed` 與 `REVIEW_STATUS： AWAITING_INDEPENDENT_REVIEWER` 維持不變。金絲雀紀錄另見 `docs/p7/P7_MVP_CANARY_METRICS_2026-11-25.md`，其 `pilot_acceptance` 為 `mvp_operator_reviewed`，審查標籤為 `OPERATOR_SELF_REVIEW`。那不是 independent_pass，也不是本包的第三方裁決。
