# ASI / Hermes 更新實作狀態 — 2026-10-28

更新日期：2026-10-29。仍為工程候選與驗證階段。正式遷移、切換、runtime Release 與本次 Git
交付尚未完成；既有失敗、BLOCK 與 UNKNOWN 均保留。

Hermes Agent 基準維持使用者已接受的 unsigned **v0.21.2**，上游標籤
`v2026.9.11`，固定完整 commit
`939e45c91d751fadd94dcd1b873ac3cb44846213`。官方公開標籤來源鏈已核對。
這個版本不代表當日最新版本，也不同於 ASI 既有的 `v0.9.0-rc1` 產品候選；
`v0.7.x-P` 是保留的治理凍結 lineage。

## 已有的驗證範圍

| 元件 | 已保存的獨立結果 | 適用範圍 |
|---|---|---|
| G0 bounded capture | 23 項 fake 測試通過 | 已登記 callback 的生命週期；adapter 整合另驗 |
| G0 writer reconciliation | 13 項 fake 測試通過 | 比對呼叫者提供的觀測，未知情況保留 UNKNOWN |
| Windows snapshot source | 16 項 synthetic assertions 通過 | 假資料 schema、限制及輸出精簡 |
| HEB2 active backup 初版 | 39 項測試通過，另兩項負測發現缺口 | 合成 SQLite、child 程序、認證分塊及 manifest |
| HEB2 manifest/v4 修正版 | 46 項測試及 3 項獨立負測符合預期，review02 限定接受 | 原兩項缺口修正；正式備份仍 HOLD |
| parent ACL／witness 修正、隔離 bootstrap／caller 整合 | 獨立來源／合成覆核限定接受；ACL 15 項、caller 38 項、bootstrap 12 項 | 不放寬既有 parent；明確 runtime pins；不是正式 Gate |
| captured-only 與固定錯誤診斷 | 獨立重跑 84/84，零失敗／錯誤／skip，限定 ACCEPT 0.94 | 歷史密文／manifest 驗證；live coverage 為 UNKNOWN |
| G3 三個實際合成 child | import／version／doctor 均 exit 0；bounded review ACCEPT 0.94 | 完整 G3 仍 INCONCLUSIVE；不代表 doctor 健康或正式 runtime 通過 |

HEB2 的獨立重跑包含 75,894,784-byte 合成 SQLite 的備份、解密及還原。
凍結初版因 `auth.json`／`memories` 保存範圍及 auxiliary inventory
sidecar 邊界缺口被判 BLOCKED；manifest/v4 修正版已修正這兩項，並通過
review02 的限定來源／合成整合覆核。初版 BLOCK 與負測結果仍保留。
依測試推估的記憶體 admission 不是 OS 強制資源上限。

## 正式執行的目前狀態

G0 已在取得限定核准後完成唯讀收集，獨立判定仍待完成。較早的 Guardian
BLOCK、規則 `semantic:unverified_or_missing_backup` 及當時未執行的結果
保留於稽核；原分類及限定覆核保留。歷史參照：
`asi-g0-exact-guardian-block-20261028-01`。收集完成不等於正式 G0 PASS。

歷史 G2 HOLD：review02 之後的操作預檢發現 caller 會先修改既有備份
父目錄 ACL，甚至在拒絕既有 RunId 之前便已改動。此行為需要修正為保留
既有 parent 權限，只建立及驗證新 run 的私有目錄。空 ACL witness 的
清理也應限制在本次成功建立的精確檔案集合。

上述 parent／witness 修正及隔離啟動器整合後，已取得限定的獨立來源與
合成覆核。既有 parent 保留，僅新 run 使用原子私有目錄建立；empty witness
以成功建立及身分追蹤並保留。首次受限沙箱測試的目錄解析權限失敗及後續
經核准擴權重跑結果均保留，沒有移除來源防護來換取通過。

**實際 G2 私有備份已結束，結果為 FAIL／INVALID_INPUT，不再是執行中。**
加密物件與 manifest 已保存；兩份 SQLite 各自的 online backup、完整性檢查
及加密後記憶體還原 smoke 成功，但完整 restore precheck 失敗，不能以部分
成功宣稱 G2 PASS。原 ValueError 精確文字未保留，後來重現的 source drift
不能追認為當次歷史失敗的唯一原因；原失敗與 producer pins 不改。

新 `verify-captured` 與固定診斷來源已經獨立重跑 84 項合成測試。它只驗證
明確指定的歷史 captured artifacts，所有結果明示 `live_coverage=UNKNOWN`、
`point_in_time_coherence=NOT_ESTABLISHED`、`gate_pass=false`；不是原失敗
run 的重試、fresh backup 或正式復原就緒。完整 `verify-run` 對觀察到的 live
drift 仍拒絕，caller 沒有自動轉離線模式。**另行建立隔離 copy 的 worker 及
精確執行方案仍在覆核，尚未完成實際 captured-only replay。**

G3 已完成三個 fresh synthetic home 的 import、version、doctor 實際執行。
有限觀測獲獨立 ACCEPT；完整 G3 仍 INCONCLUSIVE。doctor 的缺 `.env` issue、
未配置／optional warnings 及 2／3／6 項 denial 均保留，exit 0 不是健康。
[唯讀診斷](ASI_G3_DOCTOR_READONLY_DIAGNOSIS_2026-10-29.md) 依固定來源解釋
這些差異，沒有增加「所有 optional warnings 必須為零」的新門檻。

G4–G6 的正式遷移、回復、單一 writer 切換、預定觀察窗及整體發布驗證仍
未完成；本次新增測試及有限覆核沒有產生正式 Gate PASS。

使用者已授權在條件成立後 commit、push、merge to main 與 Release。
公開工程提交可以保存已覆核的開發成果；README 將在正式 Release 後才更新。
正式 runtime Release 仍須有其
完整執行及獨立驗證證據。來源修正完成後，依序更新精確雜湊、覆核、提交
範圍及遠端結果。

[公開交付範圍與測試入口](ASI_UPDATE_PUBLIC_DELIVERY_SCOPE_2026-10-28.md)
列出 20 個來源／測試及 4 份公開文件的精確候選清單、依賴與本地覆核證據
雜湊；copy worker 在覆核完成前不列入。私人 locator、原始稽核
日誌、資料庫、憑證、備份及執行期資料保留在原處。
