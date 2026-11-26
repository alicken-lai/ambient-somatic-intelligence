# 2026 範圍決策

格式依 `docs/SDD_ASI_GOVERNANCE_SUBSTRATE_2026-11-20.md` 第 7.3 節。本檔只追加決策，不改寫既有閘門報告。

### [2026-11-20] Work Item: P7 沙盒試點計畫與度量收集器

**Decision:** APPROVED  
**Rationale:** 產品核心，對齊 P7。通過邊界檢查：只治理提案、授權與證據，不重做前沿模型的推理或電腦操作。本週產品釋出依賴的是可審查的沙盒與度量，而不是現場 Astra。範圍限於兩個新模組、一個測試與一份計畫。操作者已同意新增這些檔案。  
**P-Phase:** P7  
**Decided by:** user/operator

### [2026-11-20] Work Item: P4 對齊缺口說明

**Decision:** APPROVED  
**Rationale:** 產品核心的驗證交接，不是新的治理層。只寫缺口，不改申訴原始碼，因此不是零碎補丁。獨立驗證者仍待指派，本項不產生 PASS。  
**P-Phase:** P4  
**Decided by:** user/operator

### [2026-11-20] Work Item: 修改 P4 envelope 與申訴所涵蓋模組

**Decision:** DEFERRED  
**Rationale:** 操作者禁止修改 P4 申訴原始碼。SDD 亦要求在獨立驗證 FAIL 之後給修復清單，而不是在待驗期間改寫內容定址的檔案。欄位缺口見 `docs/proposals/ASI_P4_SDD_ALIGNMENT_GAP_2026-11-20.md`。  
**P-Phase:** P4  
**Decided by:** user/operator

### [2026-11-20] Work Item: 由本代理宣告 P4 或 P7 獨立驗證 PASS

**Decision:** REJECTED  
**Rationale:** 邊界檢查通過「這不是產品能力」這一關之前就已失敗：自證會把實作者變成驗證者。SDD 與 canonical rules 都禁止。沙盒報告的 `pilot_acceptance` 固定為 `not_claimed`。  
**P-Phase:** NONE  
**Decided by:** user/operator

### [2026-11-20] Work Item: 另建 asi/ 平行套件

**Decision:** DEFERRED  
**Rationale:** 分類屬治理基礎設施的重複，不屬本週阻斷項。現有單一實作在 `hermes/orchestration`。另建套件會增加治理程式碼，且不讓 P7 沙盒演示成立。操作者若要遷移路徑，需另下明示指示。  
**P-Phase:** NONE  
**Decided by:** cursor-agent

### [2026-11-20] Work Item: P1 G0–G6 與 Hermes 0.21.2 切換

**Decision:** DEFERRED  
**Rationale:** 環境工具，不是產品釋出阻斷項。SDD 建議選項 A。操作者本回合確認依選項 A 延後。G2 仍是操作者環境的既有阻斷，不在本週產品工作內排除。可繼續以目前的 Hermes v0.16.0 描述產品邊界。  
**P-Phase:** P1  
**Decided by:** user/operator

### [2026-11-20] Work Item: P5 證據清理

**Decision:** DEFERRED  
**Rationale:** SDD 排在第 9 週之後。本週產品演示不依賴它。  
**P-Phase:** P5  
**Decided by:** cursor-agent

### [2026-11-20] Work Item: P6 現實債務

**Decision:** DEFERRED  
**Rationale:** SDD 標為證據不足、尚不可執行。  
**P-Phase:** P6  
**Decided by:** cursor-agent

### [2026-11-20] Work Item: P8 全庫文件對帳

**Decision:** DEFERRED  
**Rationale:** SDD 排在第 8 週。本週只新增試點計畫、缺口清單與本決策檔，不做全庫文件對帳。  
**P-Phase:** P8  
**Decided by:** cursor-agent

### [2026-11-20] Work Item: 現場 Astra 與正式部署

**Decision:** REJECTED  
**Rationale:** 競爭邊界：本週不實作模型呼叫。SDD 非目標包含正式部署。操作者禁止正式 Astra。模型識別碼與 base URL 仍未驗證。  
**P-Phase:** P7  
**Decided by:** user/operator

### [2026-11-20] Work Item: 每週五範圍覆核模板

**Decision:** APPROVED  
**Rationale:** 防漂移機制，對齊 SDD 第 4.3 節。檔案是 `docs/governance/WEEKLY_SCOPE_REVIEW.md`。它不新增閘門，只要求既有工作項填決策模板。  
**P-Phase:** NONE  
**Decided by:** user/operator

### [2026-11-20] Work Item: 從第 1–2 週繼續到 P8 的本機交付

**Decision:** APPROVED  
**Rationale:** 操作者明示繼續開發到 P8。範圍是本機 P7 沙盒度量報告、獨立審查包，以及 P8 文件對帳。不呼叫外部 API，不部署 Astra，不改 P4 申訴模組，不把沙盒或對帳寫成 PASS，不發布 tag。P1/G2–G6 的選項 A 延後維持有效。P5 依 SDD 第 5.2 節在 P8 之後，本增量不開始。P6 維持延後。  
**P-Phase:** P7, P8  
**Decided by:** user/operator

### [2026-11-24] Work Item: P4–P7 本機續作與文件對齊

**Decision:** APPROVED  
**Rationale:** 操作者要求忽略週次，完成本機 P4、P5、P6、P7。結果組裝已記入 cost、actual_changes、replay_pointer。P5 沿用既有證據閘。P6 歷史分數維持 NOT_PROMOTED。P7 沙盒 pilot_acceptance 維持 not_claimed。P4 對齊文件改為 IMPLEMENTED_AWAITING_INDEPENDENT_REVIEW，不改 FAIL 原文，不發 PASS。現場 Astra、獨立審查者與新 tag 仍待操作者。  
**P-Phase:** P4, P5, P6, P7, P8  
**Decided by:** user/operator

### [2026-11-26] Work Item: v0.9.1 MVP governance substrate

**Decision:** APPROVED  
**Rationale:** 操作者要求以 SDD 第 3.4 與第 5.3 節選項 A 完成 P0–P8 的 MVP。P1 與 P2 記為 MVP_DEFERRED_DOCUMENTED，不執行 G2–G6，也不宣稱 Hermes 已升到 v0.21.2。P6 記為 MVP_DEFERRED，歷史分數維持 NOT_PROMOTED。P7 金絲雀的 pilot_acceptance 是 mvp_operator_reviewed，審查標籤是 OPERATOR_SELF_REVIEW，不是 independent_pass。P4 邊界測試檔由操作者改名。  
**P-Phase:** P0, P1, P2, P3, P4, P5, P6, P7, P8  
**Decided by:** user/operator
