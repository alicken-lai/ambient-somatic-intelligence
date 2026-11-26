# 每週範圍覆核

**時區：** Asia/Taipei  
**時間：** 每週五 17:00  
**下次：** 2026-11-27 17:00  
**依據：** `docs/SDD_ASI_GOVERNANCE_SUBSTRATE_2026-11-20.md` 第 4.1–4.3 與第 7.3 節  
**決策落點：** `docs/audit/SCOPE_DECISIONS_2026.md`

這份模板不新增產品能力，也不取代 P4 的獨立驗證。覆核時把每個進行中的工作項填進下方模板，並把結論追加到決策檔。

## 覆核步驟

1. 列出本週仍開著的工作項。
2. 每一項填完決策模板。
3. 標出對不齊 P0–P8、或在重做前沿模型能力的項目。
4. 沒通過邊界檢查的項目，在決策檔寫 REJECTED 或 DEFERRED。
5. 只更新階段進度中已經有證據的部分。沒有獨立驗證的項目維持未完成。

## 2026-11-20 當週快照

| 工作項 | 決策 | 階段 |
|---|---|---|
| P7 沙盒計畫與度量 | APPROVED，完成宣告未做 | P7 |
| P4 缺口說明 | APPROVED，裁決未做 | P4 |
| 修改 P4 申訴原始碼 | DEFERRED | P4 |
| 自證 PASS | REJECTED | NONE |
| 另建 `asi/` | DEFERRED | NONE |
| P1 G0–G6 | DEFERRED（選項 A） | P1 |
| P5 | DEFERRED | P5 |
| P6 | DEFERRED | P6 |
| P8 | DEFERRED | P8 |
| 現場 Astra / 正式部署 | REJECTED（本週） | P7 |

下週覆核時，若沒有新的操作者指示，P1/G2–G6 繼續維持選項 A，不因產品工作受阻而提前切換 Hermes。

## 2026-11-20 同日後續授權

操作者在第 1–2 週交付之後，授權依 SDD 繼續到 P8。當日早上的 DEFERRED 快照保留，作為當時的紀錄。後續本機結果是：

| 工作項 | 後續決定 | 完成宣告 |
|---|---|---|
| P7 沙盒度量報告與審查包 | 已寫入本機證據 | 未完成。`pilot_acceptance` 仍是 not_claimed |
| P8 文件對帳 | 已寫入對帳文件、README 第 16 節、已知限制第 14 節 | 不是新 release |
| P5 | 仍未開始 | 排在 SDD 第 9 週之後 |
| P6 | 仍延後 | 不降歷史門檻 |
| P1/G2–G6 | 仍是選項 A | 不切換 Hermes |
| 現場 Astra | 仍待使用者再確認 | 本增量未呼叫 |

## 決策模板

```markdown
## Work Item: [名稱]

### Classification
- [ ] Product core（ASI 治理能力）
- [ ] Product infrastructure（測試、CI、文件）
- [ ] Environment tooling（操作者流程、Hermes 更新）
- [ ] Governance infrastructure（稽核、合規、閘門）

### P-Phase Alignment
服務哪一階段？ [P0/P1/P2/P3/P4/P5/P6/P7/P8 或 NONE]

若是 NONE：為什麼現在需要？

### Boundary Check
這是在與前沿模型競爭，還是在治理它們？
- [ ] YES，會複製模型能力 → REJECT
- [ ] NO → 繼續

### Blocker Test
目前的產品釋出是否真的被這項擋住？
- [ ] YES → 證據是什麼？
- [ ] NO → 可否延到釋出之後？

### Scope Limit
程式碼上限：[行]
新檔上限：[個]
預計完成：[天，不是月]

估計超過 1000 行或兩週：拆開或延後。
```

## 追加到決策檔的格式

```markdown
### [YYYY-MM-DD] Work Item: [名稱]
**Decision:** APPROVED / REJECTED / DEFERRED
**Rationale:** [模板結果]
**P-Phase:** [P0-P8 或 NONE]
**Decided by:** [user/operator/agent]
```

## 防漂移檢查

- 這項讓使用者看得到能力，或阻止已知的操作失敗嗎？兩者都否，就拒絕或延後。
- 沒有它，P4/P7 的沙盒演示仍能進行嗎？能，就放進環境待辦，不放進產品關鍵路徑。
- 六個月內前沿模型會自己提供的壓縮、重試或任務拆解，用轉接器，不重做。
- 釋出之後才出現的新標準，不回溯套到已釋出版本。
