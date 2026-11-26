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

## 2026-10-07 續記：單次隔離試行在遷移前安全拒絕

上文保留為歷史快照。Kanban12 後續取得各自獨立限定靜態預檢與精確單次
授權，完成一輪隔離試行；保存結果為 FAIL_CLOSED、worker exit1、後置檢查
exit0。尚未嘗試遷移入口，拒絕點為 baseline index 契約；確切索引差異仍未知。
保存記錄顯示八份副本前後 hash一致，但尚無獨立實際結果覆核，不作 G4 PASS。
原外層工具 final exit 與總耗時未知；沒有重跑、刪除、修補權限或正式切換。

STATE r4 新來源合約已編譯並封存，37,149項映射及22項作者startup支持；
原失敗全部保留。尚無新版獨立預檢、完整匯入或私有STATE遷移。
執行與覆核原角色再次回報用量上限；未更換身分、模型或provider繞過限制。

主控已回收保存憑據、定位公開錯誤常值、另存去識別化交接並追加本機稽核。
目前必要的下一步是獨立核對本次失敗與新版本預檢，不是再次授權既有範圍。
本輪 Git 仍僅提交本公開文件，所有候選、manifest、memory與私有產物留在本機。
沒有 tag／Release；功能驗收、rollback、其餘gates與正式切換準備尚未完成。

## 2026-10-07 後續：保留實際失敗與新版修正準備

原角色一度恢復後，Kanban12保存失敗取得15項公開斷言的限定獨立覆核；
遷移仍HOLD，原次確切索引差異及外層exit／總耗時仍未知。沒有重跑原試行。

STATE r4取得新版限定靜態預檢後單次公開執行，在child240秒等待上限失敗。
未終止或重跑child；晚到結果也為FAIL_CLOSED。原child最終exit、完整外層
後置來源／ACL／目錄與streams驗證仍缺失，不能用晚到結果補稱成功。
獨立檢查支持audit包裝干擾精確hostname呼叫者檢查的機制，原次callback stack
未保存。新版r5另編最小修正與支持草稿，尚未執行或獨立驗收；較長等待上限
僅為新候選提案，不撤銷原失敗。

Kanban新metadata13b完成pure設計支持；metadata14完成公開SQLite callback
形狀觀察及限定獨立覆核。觀察器不是拒絕守衛，公開fixture不是私有DB證據；
metadata15守衛測試仍為準備草稿，沒有新私有執行授權或成功遷移。

原三個角色再次回報用量上限，未更換身份、模型或provider。主控保存續接
文件及append-only稽核，沒有自行認證候選。本次仍只提交去敏感公開進度文件；
不含本機候選、證據、記憶或私有產物。Release及正式切換繼續暫緩。

## 2026-10-08 續記：新版公開合約產出，應用驗收仍分開

原作者與原獨立覆核角色以原設定恢復；先前用量中斷與所有失敗保留，沒有
換身份、模型或provider迴避限制。新版公開支持已完成有限覆核：STATE支援
精確hostname與連線拒絕，但原WMI載入／初始化範圍措辭缺口仍保留；Kanban
公開守衛支持也不是私有DB或完整隔離證明，不因測試數量宣告整體成功。

STATE r5另編compiler03取得精確範圍預檢與單次授權，實際exit0，產生新合約
37,187項映射及真實來源SOUL。獨立保存結果覆核完成1,306項斷言，信心0.96，
僅接受**公開準備產出**。舊37,149映射及固定守恆metadata保留；不是重新讀取
所有歷史端點，也不是full application、private migration或phase Gate PASS。

作者與覆核各有一個保存證據解析失敗，皆保留：大型檔案identity整數不可經
JavaScript有限精度數值往返；原stdout換行bytes與正規化文字digest亦須分開。
另編唯讀檢查確認Python整數內容及產出守恆，沒有重跑compiler、改寫原憑據
或掩蓋失敗。原準備紀錄與後續actual稽核分開追加，English DMN與journal歷史
bytes prefix及原blankline不變；不作reality-replay補分。

下一步STATE public02需要新版合約／launcher／probe專屬的獨立預檢與另次
單次授權。完整新映射預後端點、source-only來源、native載入與有限query、
HOME／SOUL／ACL、零連線、完整streams及實際final exit仍待該次應用觀測。
新版child等待600秒只屬候選設定，預後helper各240秒不變，不能撤銷r4原逾時
與晚到FAIL；原child-final未知與缺失後置證據仍保留。

public16已載入模組來源helper取得設計覆核及另次精確單次公開支持授權。
本追加準備停點尚未收到其actual結果，不推論API已執行或成功；選定端點的
新process觀測不能補成舊process或未來私有process的完整DLL／OS來源證明。
確切執行與新保存結果需另行獨立核對，與STATE application授權完全分開。

兩份DB既有人工範圍不變，Kanban12 baseline差異及STATE新sibling基線未解決。
沒有新私有遷移、額外解密、備份覆寫、權限修補或正式切換；Release仍暫緩。
若另核准Git提交／推送，只限去敏化公開文件，不納入候選、manifest、原始
工具憑據、記憶、SID／ACL細節或私有產物，不發布tag／Release。

## 同日稍後：public16 已返回失敗，原待結果停點保留

上段「actual未收到」保留為當時準備快照。其後public16單次公開支持已返回
exit1、FAIL_CLOSED，錯誤型別AttributeError，沒有running session。原生依賴
載入後未取得選定模組路徑觀測；選定API呼叫次數仍UNKNOWN，不能推論為零
或把一般檔案hash當作載入來源證明。保存欄位顯示來源／檔案identity守恆，
但尚待完整外層憑據與獨立實際結果覆核，不能由作者自行驗收。

沒有重跑、刪除、權限修補或私有DB操作。本次失敗與先前STATE合約的限定
準備產出分開記錄；STATE application仍未啟動，Release及正式切換繼續暫緩。

## 再續記：public16 失敗取得限定覆核，另編修正僅準備

其後完整外層憑據已回收，原獨立覆核以917項保存／公開檔案／AST斷言、
信心0.96核對public16失敗，僅接受失敗證據一致，不接受ABI或選定載入來源。
常值訊息支持整數回傳的value提取可能不相容，實際site／stack與部分API
呼叫次數仍UNKNOWN。原程式、試行結果及失敗保留；另編17只核准最小型別
正規化與pure支持準備，沒有新的native成功或執行授權。

STATE public02亦取得新版獨立static預檢，81項斷言只屬有限唯讀／pure政策
支持，沒有原生WMI query、完整映射wave或應用執行。後續必須另簽單次GO，
明列標準套件native初始化與有限query的能力界線，再取得自身完整實際預後
證據；靜態接受不代替實際接受或私有DB驗收。所有Gate／Release界線不變。

## 同日續接：公開 STATE 匯入已完成，等待實際獨立覆核

原執行者確認額度中斷前只讀取核准文件，尚未啟動；恢復後使用同一份未消耗的
單次核准，沒有重跑或更換角色。公開隔離匯入的 child 與外層程序皆實際退出0，
完整等待及輸出憑據已保存。37,187項邏輯 expected mapping 保留；完整掃描的
前後保存 count／digest／彙總identity，不是逐檔身分歷史。保存來源／ACL／SOUL
守恆、2組有限 WMI query結果、空白拒絕及零DB連線。這些先列為保存
產物觀測，仍待原獨立覆核，不能由實作者自行驗收。

流程總耗時未直接量測，維持UNKNOWN；中途目錄存在不等於成功，沒有以wait總和
補造時間或隱藏先前失敗。歷史逾時、型別與精度問題、有限native／載入來源界線
繼續保留。尚未執行私有DB遷移或SessionDB factory，後續私有預檢及基線差異須
另行核對與核准。Gate、正式切換、tag及Release仍暫緩；本續記不授權發布原始憑據。

## 隨後限定覆核完成：公開匯入接受，不解鎖私有範圍

原獨立覆核以831項來源／保存證據／檔案斷言、信心0.96接受新版公開source-only
匯入；沒有重跑全量掃描、native API、SQL或ACL操作。這不是831個原生場景，也
不是Gate PASS。較早待覆核段落保留為時間點紀錄；掃描彙總不冒充逐檔歷史。
私有資料列／schema／鎖／快取／新兄弟基線與factory仍須另行預檢和核准，正式
切換及Release繼續暫緩。所有失敗、能力限制及原始憑據維持原狀。

## 同日後續：稽核完成，NEW17 失敗仍不放寬必要目標

公開STATE結果已按另次核准追加English記憶與journal，歷史前綴及原blankline保留。
NEW17精確單次公開支持退出1，FAIL_CLOSED／MISSING_FAIL_CLOSED；獨立125項保存／
來源／檔案斷言、信心0.96只核對失敗，不接受選定模組來源或ABI。確切失敗target、
site及部分API次數仍UNKNOWN，不以空白拒絕或extension檔案hash當成功。

另編NEW18只核准有限失敗前追蹤及pure支持準備；必要目標、API與守衛不變，
沒有重跑17、fallback或optionalization，也沒有新native結果或執行核准。
私有DB／siblings基線、正式切換與Release仍分開，沒有因新增紀錄而解鎖。
