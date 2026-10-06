# ASI 更新工程檢查點與 Release 決策

日期：2026-10-06。狀態：工程準備中，非 Release-ready。

操作者已授權自行判斷 commit、安全 push 與 Release 時機。本次 Git 範圍僅限
這份公開狀態文件；工作區既有程式變更、執行候選、私人資料、記憶體與稽核原件
保持原位，不納入本次提交。文件提交不是功能驗收或 Gate promotion。

## 固定版本與授權邊界

Hermes 目標仍為使用者接受的 unsigned v0.21.2，固定 commit
`939e45c91d751fadd94dcd1b873ac3cb44846213`。不宣稱這是當日最新版，也不將
Hermes 上游版本與 ASI 的 Release 版本混為一談。

隔離作業仍限兩份 DB 的私有還原與遷移，不包含刪除、覆寫原備份、額外解密
或正式切換。Git／Release 時機授權不取代 DB maintenance 或付費／外部資料處理
所需的人類決策。所有原失敗、BLOCK 與 UNKNOWN 均保留。

## 本輪有界成果

- 既有兩份備份還原、唯讀 inspection 與 expectation02 已完成各自有限覆核。
  target migration 與 rollback compatibility 尚未完成。
- 公開 native cache fixture 保存 26 項實測；獨立核對 28 項證據一致，信心 0.96。
  26 = 4 trigger + 7 positive + 5 race + 5 link + 5 ACL。先前 27 為預估錯誤，
  未補造檢查；外層程序 exit 仍 UNKNOWN。
- 公開 import06 在前置完整 hash 查驗因非執行期 pytest cache 不可讀而失敗。
  沒有 HOME／Hermes 載入／DB 階段，不重跑或修改權限。靜態 hash 一致不等於
  執行時可讀；原因與子檔案實體身分不作推測。
- 07 準備版本、07b 編譯失敗及 07c 的錯誤 runtime pin HOLD 保留。07d 僅排除五項確切
  非執行期 cache 綁定，保存原映射並在解析／讀取／載入前明確拒絕該目錄；
  必要來源、依賴及 runtime 不省略。
- 07d 獨立靜態檢查：46 項、37,038 個 hash 相符，STATIC_ACCEPT 0.96。
  獨立報告 SHA256：
  `26897dcf829c7a61fd33622d92026ed3cba4a340a5a30de9d52471ea9a69afb7`。
- 另核准單次 owner hash-only 查驗。已找到保存結果：
  `OWNER_HASH_ONLY_CHECK_COMPLETE`、37,038 項，未載入 Hermes／WMI、未建立 HOME
  或讀私有資料。結果 SHA256：
  `10857a9d2b5396753f8801b875b19c6aa6cf104e7c05c84c0e9965024537cef8`。
  外層工具收據與獨立實際結果覆核仍待補齊，不推定 exit 或核准實際載入。
- STATE r2 已保存來源綁定的 11 項 loader 與 20 項真實追蹤連線支持檢查；最新
  native 端點檢查修正仍待測試。支持檢查不等於完整 SessionDB、私有入口、
  schema／FTS 守恆驗收。

實際來源與 native 包裝不是 OS sandbox；可信任 startup／bytecode 的歸屬限制
仍明列。局部成功不代替完整 G0／G3／G4／G5／G6，也不作 reality-replay 補分。

## 接續順序

1. 在原獨立覆核能力恢復後，核對 owner hash-only 的實際結果及外層歸屬。
   保持凍結，不重跑同一輸出；取得結論後才另核准公開載入。
2. 分別完成 Kanban／STATE 防護流程的真實公開載入及獨立結果覆核。
3. 凍結隔離私有入口、來源／ACL／sidecar／連線關閉／typed data／FTS 守恆合約，
   獨立預檢後，逐份單次執行已授權遷移。
4. 完成 rollback、當下 writer inventory、正式 launcher、完整合約矩陣與整體覆核；
   maintenance／切換、正式訊息授權及付費模型試跑仍按各自決策邊界處理。

## Git 與 Release 決策

既有工作分支為 `codex/deliberation-kernels`。本次只提交此狀態文件，推送前
再核對遠端分支未移動，使用一般 fast-forward push；不推 main、不 force、不改
Git 設定、不建立 tag，也不打包記憶體、備份、manifest 或執行期資料。

目前 **暫緩 Release**：實際載入／私有遷移／rollback／必要 gate 與真實觀察仍有
缺口，獨立覆核再次遇用量上限。待既定驗收與相關人類決策成立後，再判斷 tag、
Release 與正式切換；不以文件提交、測試數量或用量中斷宣告整體完成。

## 同日續記：公開載入已完成限定覆核

上文是首次文件提交時的快照；後續在原角色與設定恢復工作，未更換身分規避
用量限制。首次文件已以 `4c17d26` 安全推送至原工作分支；未發布 tag／Release。

- owner hash-only 原外層 exit 0 已取回，沒有重跑；獨立26項保存證據核對及
  37,038現況綁定一致，限定接受0.96。外層總耗時仍UNKNOWN。
- 另行單次授權的公開 import07d 實際 exit 0，獨立限定接受0.96。
  920是端點／斷言核對，不是920種測試情境；涵蓋264載入檔、325 read-posthash、
  3 compiled-bootstrap及130可信任startup現況綁定。DB／migration／gate false。
  判決SHA256 `3f867c8e699d6e628668a115a8fe2ec5f7ff789b1a2e719b73ab81212acf7d6a`。
  不是所有37,038未使用依賴的after-hash或歷史startup bytecode／完整OS sandbox。
- STATE r2 另有單次唯讀37,104端點查驗，實際exit 0及限定接受0.96，沒有
  Hermes／DLL載入、WMI、SQL、HOME或私有存取。判決SHA256
  `17863f44c7f3fe194bc4688c3a6e4ed344453d7ccd135b6525d7f5a59158187d`。
  此觀測不是public STATE import或私有migration接受。
- STATE後續公開guard與Kanban私有09預檢仍HOLD：bytes路徑在記錄拒絕前
  TypeError，以及Windows inventory鍵分隔符不一致。皆在執行前發現，沒有
  target DB操作；另編最小修正，原候選、失敗與固定準則保留，不擴大權限。
- 舊版乾淨來源有本機既存Git物件路徑，但只有作者唯讀盤點，不是rollback。
  乾淨來源相容性不代替完整historical dirty-runtime recovery；沒有額外解密。

原用量中斷保留為歷史，不再用它代替目前具體HOLD理由。Release仍暫緩，
私有遷移、rollback及其他必要gates尚未完成。本續記仍僅公開文件，無程式／
manifest／記憶／私有產物提交，不提升任何phase gate。

再次續記：原三個代理皆遇用量上限後，主控完成另編候選的本機準備及56項
公開source-bound修正檢查、6項launcher pure-function檢查。新合約保留原綁定，
但尚無獨立新預檢與私有GO，不能自行宣布HOLD已解除。私有DB、原備份與
正式環境仍未操作，Release保持暫緩；未提交候選程式或執行產物。
